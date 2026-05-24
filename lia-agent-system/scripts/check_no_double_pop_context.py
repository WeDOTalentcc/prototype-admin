#!/usr/bin/env python3
"""Sprint 2.5-C sensor canonical — anti-double-pop _context bug.

Detecta o pattern:

    context = _extract_context(kwargs)                          # pop _context
    ...                                                          # (poucas linhas)
    company_id = require_company_id_from_context(kwargs, ...)   # tries pop again → raise
    OR
    context = context_or_raise(kwargs, ...)                     # idem

Origem: Sprint 2.2 G2 migration esqueceu de remover `_extract_context`
quando introduziu `require_company_id_from_context` como canonical helper.

Resultado runtime: tools sempre raise ToolContextMissingError. Fail-loud
canonical protegeu LGPD (não vazou cross-tenant) mas tools nunca rodavam.

Descoberto via Datadog LLM Obs trace 2026-05-24.

Exit codes:
    0 — sem violations
    1 — violations encontradas (modo blocking)

Uso CI:
    python3 scripts/check_no_double_pop_context.py
    python3 scripts/check_no_double_pop_context.py --warn-only

Refs:
- context_helpers.py (canonical helpers)
- Sprint 2.5-A `a4f704e5f` (14 sites fix)
- Sprint 2.5-B `567e8b87d` (11 sites fix)
- Datadog LLM Obs discovery
"""
from __future__ import annotations

import ast
import argparse
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
TOOLS_DIRS = [
    WORKSPACE / "app" / "domains",
    WORKSPACE / "app" / "tools",
]

EXTRACT_CALLS = {"_extract_context"}
SECOND_POP_CALLS = {
    "require_company_id_from_context",
    "context_or_raise",
}

# Files explicitly EXEMPT (canonical helper itself, etc.)
EXEMPT_FILES = {
    "context_helpers.py",  # the canonical helper file itself
}

# Marker for opt-out per-line: `# DOUBLE-POP-EXEMPT: <reason>`
EXEMPT_MARKER = "DOUBLE-POP-EXEMPT"


def find_double_pop_violations(src: str, filename: str) -> list[tuple[int, int, str]]:
    """Returns [(extract_line, second_pop_line, function_name)] for each violation."""
    try:
        tree = ast.parse(src, filename=filename)
    except SyntaxError:
        return []

    violations = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # Find first call to _extract_context in function body
        extract_line = None
        extract_kwargs_arg = False
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = _get_func_name(child)
                if func_name in EXTRACT_CALLS:
                    if extract_line is None:
                        extract_line = child.lineno
                        # check if arg is "kwargs" identifier
                        if child.args and isinstance(child.args[0], ast.Name) and child.args[0].id == "kwargs":
                            extract_kwargs_arg = True

        if extract_line is None or not extract_kwargs_arg:
            continue

        # Find a subsequent call to require_company_id_from_context or context_or_raise
        # within the same function body (after extract_line)
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = _get_func_name(child)
                if (
                    func_name in SECOND_POP_CALLS
                    and child.lineno > extract_line
                    # also check kwargs arg
                    and child.args
                    and isinstance(child.args[0], ast.Name)
                    and child.args[0].id == "kwargs"
                ):
                    # Check exempt marker on extract_line
                    extract_line_text = src.splitlines()[extract_line - 1] if extract_line <= len(src.splitlines()) else ""
                    if EXEMPT_MARKER in extract_line_text:
                        continue
                    violations.append((extract_line, child.lineno, node.name))
                    break

    return violations


def _get_func_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def scan() -> list[tuple[Path, int, int, str]]:
    """Returns list of (file, extract_line, second_pop_line, function_name)."""
    all_violations = []
    for tools_dir in TOOLS_DIRS:
        if not tools_dir.exists():
            continue
        for py_file in tools_dir.rglob("*.py"):
            if py_file.name in EXEMPT_FILES:
                continue
            if "__pycache__" in str(py_file):
                continue
            try:
                src = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            violations = find_double_pop_violations(src, str(py_file))
            for el, sl, fn in violations:
                all_violations.append((py_file, el, sl, fn))
    return all_violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warn-only", action="store_true", help="Exit 0 even with violations")
    parser.add_argument("--max-violations", type=int, default=0, help="Allowed baseline (default 0)")
    args = parser.parse_args()

    violations = scan()

    if not violations:
        print(f"✅ check_no_double_pop_context: 0 violations (baseline OK)")
        return 0

    print(f"❌ check_no_double_pop_context: {len(violations)} violation(s):\n")
    for fpath, el, sl, fn in violations:
        rel = fpath.relative_to(WORKSPACE)
        print(f"  {rel}:{el}  function={fn}  → second pop at line {sl}")
        print(f"    Fix: replace `context = _extract_context(kwargs)` + second pop with:")
        print(f"         context = context_or_raise(kwargs, \"{fn}\")")
        print(f"         company_id = require_company_id_from_obj(context, \"{fn}\")")
        print(f"    Or add  # DOUBLE-POP-EXEMPT: <reason>  on the _extract_context line.")
        print()

    if args.warn_only or len(violations) <= args.max_violations:
        print(f"WARN-ONLY (or under baseline {args.max_violations}). Exit 0.")
        return 0

    print(f"BLOCKING: {len(violations)} > {args.max_violations}. Exit 1.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
