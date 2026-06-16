#!/usr/bin/env python3
"""Sensor — wrapper functions in app/domains/*/tools/ must delegate via
``normalize_wrapper_kwargs`` (canonical helper) instead of manually building
SimpleNamespace from kwargs.company_id/user_id.

Anti-pattern detectado (saga 2026-05-24, regressão Sprint 8 NS-2):

    async def _wrap_search_jobs(**kwargs):
        company_id = kwargs.pop("company_id", "")     # ← ignora _context do executor
        user_id = kwargs.pop("user_id", "")
        ctx = SimpleNamespace(company_id=company_id, user_id=user_id)
        return await search_jobs(_context=ctx, **kwargs)
        #                 ↑ TypeError: multiple values for keyword argument '_context'
        #                   (executor já injetou _context em kwargs)

Canonical (após commit fix-tools-context-normalize 2026-05-24):

    async def _wrap_search_jobs(**kwargs):
        return await search_jobs(**normalize_wrapper_kwargs(kwargs))

O helper canonical em ``app/tools/context_helpers.py:normalize_wrapper_kwargs``
trata ambos os dispatch paths (Global ToolExecutor injeta ``_context`` vs
tool_handler decorator injeta ``company_id``/``user_id``).

REGRESSÃO HISTÓRICA:
- Sensor 1 (G2): bloqueia ``kwargs.get('company_id', '')`` em handlers canonical
- Sensor 2 (silent_context_fallback): bloqueia ``ctx.company_id if ctx else None``
- Sensor 3 (este): bloqueia wrappers `_wrap_*` que **simulam** o tool_handler
  ContextVar pattern sem checar se ``_context`` já está em kwargs.

Output otimizado para consumo LLM: file:line + sugestão de fix com 4 linhas
canonical. Roda como pre-commit + CI block.

Usage:
    python scripts/check_wrappers_prefer_context.py
    python scripts/check_wrappers_prefer_context.py --json
    python scripts/check_wrappers_prefer_context.py --blocking
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_GLOBS = [
    "app/domains/*/tools/*.py",
    "app/domains/*/tools/**/*.py",
]
EXEMPT_MARKER = "WRAPPER-NORMALIZE-OK:"


@dataclass
class Violation:
    file: str
    line: int
    wrapper_name: str
    reason: str

    def as_dict(self) -> dict:
        return asdict(self)


def _is_normalize_call(node: ast.AST) -> bool:
    """Returns True for ``normalize_wrapper_kwargs(kwargs)``."""
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name) and f.id == "normalize_wrapper_kwargs":
            return True
        if isinstance(f, ast.Attribute) and f.attr == "normalize_wrapper_kwargs":
            return True
    return False


def _wrapper_uses_normalize(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Walk body; return True if any call to normalize_wrapper_kwargs."""
    for node in ast.walk(func):
        if _is_normalize_call(node):
            return True
    return False


def _wrapper_pops_company_id_with_simplenamespace(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Detect the anti-pattern: pop(company_id) + SimpleNamespace(_context=...)."""
    saw_pop_or_get_company_id = False
    saw_simplenamespace = False
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            f = node.func
            # kwargs.pop("company_id", ...) or kwargs.get("company_id", ...)
            if (
                isinstance(f, ast.Attribute)
                and f.attr in ("pop", "get")
                and isinstance(f.value, ast.Name)
                and f.value.id == "kwargs"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value in ("company_id", "user_id")
            ):
                saw_pop_or_get_company_id = True
            # SimpleNamespace(...)
            if (
                isinstance(f, ast.Name) and f.id == "SimpleNamespace"
            ) or (
                isinstance(f, ast.Attribute) and f.attr == "SimpleNamespace"
            ):
                saw_simplenamespace = True
    return saw_pop_or_get_company_id and saw_simplenamespace


def _scan_file(path: Path) -> list[Violation]:
    violations: list[Violation] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as e:
        violations.append(
            Violation(
                file=str(path.relative_to(REPO_ROOT)),
                line=e.lineno or 0,
                wrapper_name="<syntax error>",
                reason=f"failed to parse: {e}",
            )
        )
        return violations

    src_lines = path.read_text(encoding="utf-8").splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        if not node.name.startswith("_wrap_"):
            continue
        # Exempt marker check (line above def)
        if node.lineno >= 2 and EXEMPT_MARKER in src_lines[node.lineno - 2]:
            continue
        if _wrapper_uses_normalize(node):
            continue
        if _wrapper_pops_company_id_with_simplenamespace(node):
            violations.append(
                Violation(
                    file=str(path.relative_to(REPO_ROOT)),
                    line=node.lineno,
                    wrapper_name=node.name,
                    reason=(
                        f"`{node.name}` pops kwargs.company_id/user_id and "
                        f"builds SimpleNamespace manually. After Sprint 8 NS-2 "
                        f"(commit 06b199d4), the ToolExecutor injects `_context` "
                        f"into kwargs — this wrapper either drops it (Path A bug) "
                        f"or collides on the keyword arg. Use "
                        f"`normalize_wrapper_kwargs(kwargs)` from "
                        f"`app/tools/context_helpers.py` instead. Suggested fix:\n"
                        f"\n"
                        f"    async def {node.name}(**kwargs):\n"
                        f"        return await <canonical_name>(**normalize_wrapper_kwargs(kwargs))\n"
                        f"\n"
                        f"If this wrapper has legitimate need to do something "
                        f"custom that normalize_wrapper_kwargs can't handle, "
                        f"add `# WRAPPER-NORMALIZE-OK: <reason>` above the def."
                    ),
                )
            )

    return violations


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--blocking", action="store_true",
                        help="exit 1 if any violation found")
    args = parser.parse_args(argv)

    all_files: list[Path] = []
    for glob in TARGET_GLOBS:
        all_files.extend(REPO_ROOT.glob(glob))

    violations: list[Violation] = []
    for path in sorted(set(all_files)):
        if path.is_file() and path.suffix == ".py":
            violations.extend(_scan_file(path))

    if args.json:
        print(json.dumps({"violations": [v.as_dict() for v in violations]}, indent=2))
    else:
        if violations:
            print(f"❌ {len(violations)} wrapper(s) with anti-pattern:\n")
            for v in violations:
                print(f"  {v.file}:{v.line}  {v.wrapper_name}")
                print(f"    → {v.reason}\n")
        else:
            print("✅ All wrappers use normalize_wrapper_kwargs canonical pattern.")

    if args.blocking and violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
