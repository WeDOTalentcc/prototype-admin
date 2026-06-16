#!/usr/bin/env python3
"""Sensor: silent fallback when extracting tenant context from tool kwargs.

The antipattern (saga G2, 2026-05-24):

    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    # ↑ Silent: None propagates to WHERE company_id = NULL → 0 rows.

Canonical (G2 fix):

    from app.tools.context_helpers import require_company_id_from_context
    company_id = require_company_id_from_context(kwargs, "<tool_name>")
    # Raises ToolContextMissingError if missing — orchestrator-level bug.

Pattern detection covers:
- `<name> = <ctx>.company_id if <ctx> else None`
- `<name> = (<ctx>.company_id if <ctx> else None)`
- `<name> = getattr(<ctx>, "company_id", None)`

Output is LLM-optimized: file:line, suggested fix, escape hatch.

Usage:
    python scripts/check_silent_context_fallback_in_tools.py
    python scripts/check_silent_context_fallback_in_tools.py --json
    python scripts/check_silent_context_fallback_in_tools.py --blocking
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = [
    "app/domains",
    "app/tools",
    "app/shared/tools",
]
EXEMPT_MARKER = "TENANT-FALLBACK-OK:"


@dataclass
class Violation:
    file: str
    line: int
    col: int
    pattern: str
    raw: str
    suggestion: str

    def as_dict(self) -> dict:
        return asdict(self)


def _has_exempt(src_lines: list[str], lineno: int) -> bool:
    candidates = []
    if 1 <= lineno <= len(src_lines):
        candidates.append(src_lines[lineno - 1])
    if 2 <= lineno <= len(src_lines):
        candidates.append(src_lines[lineno - 2])
    return any(EXEMPT_MARKER in c for c in candidates)


def _suggestion(target_name: str) -> str:
    return (
        f"Replace with canonical fail-loud helper:\n"
        f"    from app.tools.context_helpers import "
        f"require_company_id_from_context\n"
        f"    {target_name} = require_company_id_from_context("
        f"kwargs, \"<tool_name>\")\n"
        f"This raises ToolContextMissingError when _context is missing, "
        f"preventing the WHERE company_id = NULL → 0 rows silent failure. "
        f"If this site is intentionally allowed to fall back (rare — e.g. "
        f"admin cross-tenant query), add `# TENANT-FALLBACK-OK: <reason>` "
        f"above the assignment."
    )


class Walker(ast.NodeVisitor):
    def __init__(self, src_lines: list[str], path: Path):
        self.src_lines = src_lines
        self.path = path
        self.violations: list[Violation] = []

    # Detect: `<lhs> = <ctx>.<attr> if <ctx> else None`
    def visit_Assign(self, node: ast.Assign) -> None:
        val = node.value
        if isinstance(val, ast.IfExp):
            # x.y if x else None
            body = val.body
            orelse = val.orelse
            test = val.test
            # x.y as body, x as test (or Name), None as orelse
            if (
                isinstance(body, ast.Attribute)
                and isinstance(test, ast.Name)
                and isinstance(orelse, ast.Constant)
                and orelse.value is None
                and isinstance(body.value, ast.Name)
                and body.value.id == test.id
            ):
                if not _has_exempt(self.src_lines, node.lineno):
                    target_name = (
                        node.targets[0].id
                        if node.targets and isinstance(node.targets[0], ast.Name)
                        else "company_id"
                    )
                    raw = (
                        self.src_lines[node.lineno - 1]
                        if 0 < node.lineno <= len(self.src_lines)
                        else ""
                    ).strip()
                    self.violations.append(
                        Violation(
                            file=str(self.path.relative_to(REPO_ROOT)),
                            line=node.lineno,
                            col=node.col_offset,
                            pattern="x.attr if x else None",
                            raw=raw[:200],
                            suggestion=_suggestion(target_name),
                        )
                    )
        # Detect: `<lhs> = getattr(<ctx>, "<attr>", None)`
        elif isinstance(val, ast.Call):
            func = val.func
            if (
                isinstance(func, ast.Name)
                and func.id == "getattr"
                and len(val.args) >= 3
                and isinstance(val.args[2], ast.Constant)
                and val.args[2].value is None
                and isinstance(val.args[1], ast.Constant)
                and isinstance(val.args[1].value, str)
                and "company" in val.args[1].value.lower()
            ):
                if not _has_exempt(self.src_lines, node.lineno):
                    target_name = (
                        node.targets[0].id
                        if node.targets and isinstance(node.targets[0], ast.Name)
                        else "company_id"
                    )
                    raw = (
                        self.src_lines[node.lineno - 1]
                        if 0 < node.lineno <= len(self.src_lines)
                        else ""
                    ).strip()
                    self.violations.append(
                        Violation(
                            file=str(self.path.relative_to(REPO_ROOT)),
                            line=node.lineno,
                            col=node.col_offset,
                            pattern='getattr(ctx, "company_id", None)',
                            raw=raw[:200],
                            suggestion=_suggestion(target_name),
                        )
                    )
        self.generic_visit(node)


def scan_file(path: Path) -> list[Violation]:
    try:
        src = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        print(f"warn: syntax error {path}: {e}", file=sys.stderr)
        return []
    walker = Walker(src.splitlines(), path)
    walker.visit(tree)
    return walker.violations


def iter_py_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            yield root
            continue
        if not root.is_dir():
            continue
        for p in root.rglob("*.py"):
            parts = set(p.parts)
            if "__pycache__" in parts or "tests" in parts or "test" in parts:
                continue
            yield p


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", nargs="*", default=DEFAULT_PATHS)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-violations", type=int, default=None)
    parser.add_argument("--blocking", action="store_true",
                        help="alias for --max-violations 0")
    parser.add_argument("--warn-only", action="store_true",
                        help="never exit non-zero (default)")
    args = parser.parse_args()

    roots = [REPO_ROOT / p for p in args.paths]
    all_v: list[Violation] = []
    for f in iter_py_files(roots):
        all_v.extend(scan_file(f))

    if args.json:
        print(json.dumps({
            "violations": [v.as_dict() for v in all_v],
            "total": len(all_v),
        }, indent=2))
    else:
        if not all_v:
            print("OK silent_context sensor clean: no `x.attr if x else None` "
                  "or `getattr(ctx, 'company_id', None)` patterns in tool code.")
        else:
            print(f"FAIL {len(all_v)} silent tenant-context fallback(s):\n")
            by_file: dict[str, list[Violation]] = {}
            for v in all_v:
                by_file.setdefault(v.file, []).append(v)
            for file, vs in sorted(by_file.items()):
                print(f"  {file}")
                for v in vs:
                    print(f"    L{v.line:>4}  [{v.pattern}]")
                    print(f"        {v.raw[:150]}")
                print()
            print("Canonical fix per site:")
            print("    from app.tools.context_helpers import "
                  "require_company_id_from_context")
            print("    company_id = require_company_id_from_context("
                  "kwargs, \"<tool_name>\")")
            print()
            print("Escape hatch:")
            print("    # TENANT-FALLBACK-OK: <reason — e.g. admin cross-tenant>")

    if args.warn_only:
        return 0
    if args.blocking:
        return 1 if all_v else 0
    if args.max_violations is None:
        return 0
    return 1 if len(all_v) > args.max_violations else 0


if __name__ == "__main__":
    sys.exit(main())
