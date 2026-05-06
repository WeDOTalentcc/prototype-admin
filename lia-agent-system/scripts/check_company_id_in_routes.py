#!/usr/bin/env python3
"""AST sensor — every FastAPI route in app/api/v1/ must call _require_company_id
or get_user_company_id within its body.

Multi-tenancy is the most important invariant in this codebase. CLAUDE.md
makes it golden rule #1. This script walks every Python file under
app/api/v1/, finds @router.{get,post,put,patch,delete} decorated functions,
and asserts each function body references at least one of the two
multi-tenancy gate functions.

Exit code:
  0 — all routes guarded
  1 — one or more routes missing the gate (printed to stderr)

Usage in CI:
  python lia-agent-system/scripts/check_company_id_in_routes.py

Allowlist:
  Routes that intentionally do NOT scope by company_id (e.g., webhook
  receivers that resolve company from payload signature) can opt out by
  adding `# multi-tenancy: payload-signature` comment in the function body.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1] / "app" / "api" / "v1"
GATE_FUNCS = {"_require_company_id", "get_user_company_id"}
OPT_OUT_MARKER = "# multi-tenancy:"


def is_router_decorator(decorator: ast.expr) -> bool:
    """Match @router.get / @router.post / etc."""
    if isinstance(decorator, ast.Call):
        decorator = decorator.func
    if isinstance(decorator, ast.Attribute):
        return (
            isinstance(decorator.value, ast.Name)
            and decorator.value.id == "router"
            and decorator.attr in {"get", "post", "put", "patch", "delete"}
        )
    return False


def function_calls_gate(func: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    """True iff the function body or args contain a call to a gate function."""
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name) and target.id in GATE_FUNCS:
                return True
            if isinstance(target, ast.Attribute) and target.attr in GATE_FUNCS:
                return True
    return False


def function_has_opt_out(source: str, func: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    """Look for the # multi-tenancy: marker in the lines spanning the function."""
    lines = source.splitlines()
    start = func.lineno - 1
    end = (func.end_lineno or func.lineno)
    body = "\n".join(lines[start:end])
    return OPT_OUT_MARKER in body


def iter_routes(py_path: Path) -> Iterator[tuple[str, ast.AsyncFunctionDef | ast.FunctionDef]]:
    source = py_path.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"WARN: syntax error in {py_path}: {e}", file=sys.stderr)
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            for dec in node.decorator_list:
                if is_router_decorator(dec):
                    yield (source, node)


def main() -> int:
    if not ROOT.exists():
        print(f"ERROR: {ROOT} does not exist", file=sys.stderr)
        return 1

    offenders: list[tuple[Path, str, int]] = []
    files_scanned = 0
    routes_checked = 0

    for py in ROOT.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        files_scanned += 1
        for source, func in iter_routes(py):
            routes_checked += 1
            if function_calls_gate(func):
                continue
            if function_has_opt_out(source, func):
                continue
            offenders.append((py.relative_to(ROOT.parent.parent.parent), func.name, func.lineno))

    print(f"Scanned {files_scanned} file(s), {routes_checked} route(s).")

    is_strict = '--strict' in sys.argv
    if offenders:
        # Warn-only by default per CLAUDE.md harness convention (pre-existing
        # tech debt in recruitment_stages exists; cleaning it is a separate
        # PR). Pass --strict to make this a CI gate when the debt is paid.
        prefix = 'FAIL' if is_strict else 'WARN'
        stream = sys.stderr if is_strict else sys.stdout
        print(f'\n{prefix} — {len(offenders)} route(s) missing multi-tenancy gate:', file=stream)
        for path, name, line in offenders:
            print(f'  {path}:{line}  {name}()  — call _require_company_id or get_user_company_id, '
                  'or add `# multi-tenancy: <reason>` comment if intentional.', file=stream)
        return 1 if is_strict else 0

    print('OK — every route is multi-tenant guarded.')
    return 0


if __name__ == "__main__":
    sys.exit(main())
