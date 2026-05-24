#!/usr/bin/env python3
"""
Sensor canonical: detecta duplicações de rotas FastAPI no MESMO arquivo.

Contexto: F10 (2026-05-24) descobriu duas duplicações silenciosas em
`app/api/v1/candidates/candidates_crud.py`:
  - PUT /{candidate_id}/skills  (lines 750 + 808)
  - PUT /{candidate_id}/identity (lines 870 + 947)

Em FastAPI, declarar `@router.<method>("<path>")` 2x no mesmo arquivo é
silencioso: o último handler sobrescreve o primeiro no mapeamento de
rotas, mas ambos ficam declarados como funções (dead code). Provável
causa: commit absorption multi-agent no Replit.

Este sensor é COMPUTACIONAL (AST, não regex), zero falsos positivos.

Modes:
  - default (warn-only): exit 0, lista violations
  - --blocking: exit 1 se houver violations

Honra marker `# CANONICAL-DUPLICATE-EXEMPT: <reason>` na linha do
decorador (caso raro de duplicação intencional, ex: A/B endpoints
versionados).
"""
import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path


def find_duplicates(root: Path) -> dict[tuple[str, tuple[str, str]], list[tuple[int, str]]]:
    """Return {(file, (METHOD, path)): [(lineno, func_name), ...]} for dups."""
    same_file_routes: dict[tuple[str, tuple[str, str]], list[tuple[int, str]]] = defaultdict(list)

    for py_file in root.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            for dec in node.decorator_list:
                if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                    continue
                if not (isinstance(dec.func.value, ast.Name) and dec.func.value.id == "router"):
                    continue
                method = dec.func.attr.upper()
                if not (dec.args and isinstance(dec.args[0], ast.Constant)):
                    continue
                path = dec.args[0].value
                # Check EXEMPT marker on decorator line
                lines = source.splitlines()
                dec_line = lines[dec.lineno - 1] if dec.lineno - 1 < len(lines) else ""
                if "CANONICAL-DUPLICATE-EXEMPT" in dec_line:
                    continue
                key = (str(py_file), (method, path))
                same_file_routes[key].append((node.lineno, node.name))

    return {k: v for k, v in same_file_routes.items() if len(v) > 1}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true", help="Exit 1 on violations.")
    parser.add_argument("--root", default="app", help="Root dir to scan (default: app)")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"❌ Root dir not found: {root}", file=sys.stderr)
        return 2

    print("check_no_duplicate_routes.py")
    print(f"Scanning {root} for duplicate FastAPI routes within same file...\n")

    dups = find_duplicates(root)
    if not dups:
        print("✅ 0 violations — nenhuma rota FastAPI duplicada (method+path) no mesmo arquivo.")
        return 0

    total = sum(len(sites) - 1 for sites in dups.values())  # n dups = n-1 extras
    for (fp, (method, path)), sites in sorted(dups.items()):
        sites_str = ", ".join(f"L{ln} ({fn})" for ln, fn in sites)
        print(f"  ❌ {fp}")
        print(f"     {method} {path} appears {len(sites)}x: {sites_str}")
        print(f"     → Fix: remover handler(s) duplicado(s). FastAPI silenciosamente")
        print(f"            sobrescreve o primeiro com o último; ambos ficam no")
        print(f"            arquivo. Provável causa: commit absorption multi-agent.")
        print(f"     → Marker se intencional: # CANONICAL-DUPLICATE-EXEMPT: <reason>")
        print()

    print(f"Total: {total} extra handler(s) duplicado(s) em {len(dups)} rota(s).")
    return 1 if args.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
