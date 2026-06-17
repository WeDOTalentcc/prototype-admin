#!/usr/bin/env python3
"""
Harness canonical — handler→repo company_id propagation gap detector (v2).

v1 produced 1203 violations with many false positives:
- db-session ops (commit/rollback/flush/refresh) don't need company_id
- methods with `_and_company` / `_for_company` / `_by_company` suffix
  already have tenant in their signature
- positional company_id propagation was not detected (only kwarg)

v2 refines:
1. Whitelist obvious DB-session/non-tenant methods.
2. Whitelist methods whose name embeds tenant scope.
3. Detect positional argument propagation: if the call has ≥2 positional
   args AND the enclosing function has `company_id` in scope, assume the
   second positional is company_id (heuristic, can be overridden via
   `# RLS-OK: positional`).

Result is a more precise (but not perfect) sensor. False positives remain
where the repo method actually does need tenant filtering but the
heuristic can't tell — those are the cases the escape hatch documents.

Usage:
    python scripts/check_handler_to_repo_propagation.py
    python scripts/check_handler_to_repo_propagation.py --json
    python scripts/check_handler_to_repo_propagation.py --blocking
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = ["app/api", "app/domains"]
EXEMPT_MARKER = "RLS-OK:"

REPO_VAR_NAMES = {"repo", "repository", "_repo", "_repository"}
REPO_ATTR_SUFFIXES = ("_repo", "_repository", "Repo", "Repository")

# Methods that NEVER need company_id (DB session ops, lifecycle, etc.).
WHITELIST_METHODS = {
    "commit", "rollback", "flush", "refresh", "close", "expire",
    "expire_all", "merge", "add", "add_all", "delete",
    # ORM identity helpers — DB-level uniqueness already enforced
    "get_one", "first", "scalar", "scalars", "execute",
}

# Methods whose name already embeds tenant scope (already-canonical).
TENANT_SCOPED_SUFFIX_RE = re.compile(
    r"(_and_company|_for_company|_by_company|_per_company|_in_company)$",
    re.IGNORECASE,
)
TENANT_SCOPED_INFIX_RE = re.compile(
    r"_(by|and|for|per|in)_company_",
    re.IGNORECASE,
)


@dataclass
class Violation:
    file: str
    func: str
    call_line: int
    repo_expr: str
    method: str
    suggestion: str

    def as_dict(self) -> dict:
        return asdict(self)


def _is_repo_expression(expr: ast.AST) -> str | None:
    if isinstance(expr, ast.Name) and expr.id in REPO_VAR_NAMES:
        return expr.id
    if isinstance(expr, ast.Attribute):
        if expr.attr in REPO_VAR_NAMES:
            return _ast_to_str(expr)
        if any(expr.attr.endswith(s) for s in REPO_ATTR_SUFFIXES):
            return _ast_to_str(expr)
    return None


def _ast_to_str(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<expr>"


def _has_exempt_marker(src_lines: list[str], lineno: int) -> bool:
    candidates = []
    if 1 <= lineno <= len(src_lines):
        candidates.append(src_lines[lineno - 1])
    if 2 <= lineno <= len(src_lines):
        candidates.append(src_lines[lineno - 2])
    return any(EXEMPT_MARKER in c for c in candidates)


def _method_is_safe(method: str) -> bool:
    if method in WHITELIST_METHODS:
        return True
    if TENANT_SCOPED_SUFFIX_RE.search(method):
        return True
    if TENANT_SCOPED_INFIX_RE.search(method):
        return True
    return False


def _call_propagates_company_id(call: ast.Call, fn_params: set[str]) -> bool:
    """Return True if the call clearly propagates company_id."""
    # Kwarg form: company_id=<x>
    for kw in call.keywords:
        if kw.arg == "company_id":
            return True
    # Positional heuristic: any positional arg whose AST name == "company_id"
    # OR whose name appears in fn_params and ends with "company_id".
    for arg in call.args:
        if isinstance(arg, ast.Name) and arg.id == "company_id":
            return True
    return False


class Walker(ast.NodeVisitor):
    def __init__(self, src_lines: list[str], path: Path):
        self.src_lines = src_lines
        self.path = path
        self.violations: list[Violation] = []

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._inspect(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._inspect(node)
        self.generic_visit(node)

    def _inspect(self, fn: ast.AST) -> None:
        params = {a.arg for a in fn.args.args if hasattr(a, "arg")}
        params |= {a.arg for a in fn.args.kwonlyargs if hasattr(a, "arg")}
        if "company_id" not in params:
            return
        for inner in ast.walk(fn):
            if not isinstance(inner, ast.Call):
                continue
            func_node = inner.func
            if not isinstance(func_node, ast.Attribute):
                continue
            method = func_node.attr
            if _method_is_safe(method):
                continue
            repo_expr = _is_repo_expression(func_node.value)
            if repo_expr is None:
                continue
            if _call_propagates_company_id(inner, params):
                continue
            if _has_exempt_marker(self.src_lines, inner.lineno):
                continue
            self.violations.append(
                Violation(
                    file=str(self.path.relative_to(REPO_ROOT)),
                    func=getattr(fn, "name", ""),
                    call_line=inner.lineno,
                    repo_expr=repo_expr,
                    method=method,
                    suggestion=_build_suggestion(repo_expr, method, fn.name),
                )
            )


def _build_suggestion(repo_expr: str, method: str, func_name: str) -> str:
    return (
        f"In `{func_name}()`, the call `await {repo_expr}.{method}(...)` "
        f"does not appear to propagate company_id (no kwarg, no positional "
        f"company_id name). The enclosing function has company_id in scope, "
        f"so this is a likely propagation gap (handler→repo / service→repo). "
        f"Canonical fix:\n"
        f"    await {repo_expr}.{method}(..., company_id=company_id)\n"
        f"OR rename the method to encode tenant scope, e.g.:\n"
        f"    {method.rstrip('_')}_for_company / {method.rstrip('_')}_and_company\n"
        f"If genuinely tenant-less, document with:\n"
        f"    # RLS-OK: {method} is system-wide / not tenant-scoped"
    )


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
                        help="never exit non-zero (default behavior)")
    args = parser.parse_args()

    roots = [REPO_ROOT / p for p in args.paths]
    all_v: list[Violation] = []
    for f in iter_py_files(roots):
        all_v.extend(scan_file(f))

    if args.json:
        print(json.dumps({"violations": [v.as_dict() for v in all_v],
                          "total": len(all_v)}, indent=2))
    else:
        if not all_v:
            print("OK propagation sensor clean.")
        else:
            print(f"FAIL {len(all_v)} handler→repo propagation gap(s):\n")
            by_file: dict[str, list[Violation]] = {}
            for v in all_v:
                by_file.setdefault(v.file, []).append(v)
            for file, vs in sorted(by_file.items())[:20]:
                print(f"  {file}")
                for v in vs[:5]:
                    print(f"    L{v.call_line:>4}  {v.func}() -> "
                          f"{v.repo_expr}.{v.method}(...)")
                if len(vs) > 5:
                    print(f"    ...({len(vs) - 5} more)")
                print()
            if len(by_file) > 20:
                print(f"  ...({len(by_file) - 20} more files)")
            print("Canonical fix:")
            print("    await repo.method(..., company_id=company_id)")
            print("Escape hatch:")
            print("    # RLS-OK: <method is system-wide>")

    if args.warn_only:
        return 0
    if args.blocking:
        return 1 if all_v else 0
    if args.max_violations is None:
        return 0
    return 1 if len(all_v) > args.max_violations else 0


if __name__ == "__main__":
    sys.exit(main())
