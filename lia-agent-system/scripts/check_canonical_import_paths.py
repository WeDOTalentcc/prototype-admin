#!/usr/bin/env python3
"""
Sensor canonical: bloqueia import path drift `libs.models.lia_models.X`.

Contexto (auditoria 2026-05-24):
================================
Bug recorrente "Table 'X' is already defined for this MetaData instance" em
hot-reload do uvicorn. Causa raiz: mistura de paths para mesmo módulo

  - canonical: `from lia_models.X import Y`        (727 sites)
  - drift:     `from libs.models.lia_models.X ...` (13 sites)

Quando AMBOS paths são importados, Python registra módulo 2× em sys.modules
(diferentes names → diferentes entradas) e cada import re-executa o body do
módulo, registrando classes Base 2× → InvalidRequestError em request time.

`extend_existing=True` é workaround (silencia o erro mas não resolve raiz).
ROOT cause é unificar paths em `lia_models.X`.

Pattern detectado:
- `from libs.models.lia_models.X import Y`
- `import libs.models.lia_models.X`
- `from libs.models.lia_models import X`

Honra escape hatch: comentário `# CANONICAL-IMPORT-EXEMPT: <reason>` na
mesma linha do import.

Uso:
    python3 scripts/check_canonical_import_paths.py            # warn-only
    python3 scripts/check_canonical_import_paths.py --blocking # exit 1 se houver
    python3 scripts/check_canonical_import_paths.py --json     # output JSON

Baseline esperado: 0 violations canonical (todos os 13 outliers migrados).
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Iterator

BANNED_PREFIX = "libs.models.lia_models"
CANONICAL_PREFIX = "lia_models"
EXEMPT_MARKER = "# CANONICAL-IMPORT-EXEMPT"


def find_violations(root: Path) -> Iterator[dict]:
    """Walk root and yield {file, line, code, source} for each banned import."""
    for py in root.rglob("*.py"):
        if "__pycache__" in py.parts or ".git" in py.parts or "venv" in py.parts:
            continue
        # Permitir os arquivos do próprio libs/ (eles definem o módulo canonical)
        if "libs/models/lia_models" in str(py):
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        try:
            tree = ast.parse(text, filename=str(py))
        except SyntaxError:
            continue
        lines = text.splitlines()
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
            elif isinstance(node, ast.Import):
                # `import libs.models.lia_models.X`
                for alias in node.names:
                    if alias.name.startswith(BANNED_PREFIX):
                        module = alias.name
                        break
            if not module:
                continue
            if not module.startswith(BANNED_PREFIX):
                continue
            line_no = node.lineno
            source = lines[line_no - 1] if line_no - 1 < len(lines) else ""
            if EXEMPT_MARKER in source:
                continue
            yield {
                "file": str(py.relative_to(root.parent)),
                "line": line_no,
                "module": module,
                "source": source.strip(),
                "fix": f"trocar `{module}` por `{module.removeprefix(BANNED_PREFIX + '.') and CANONICAL_PREFIX + '.' + module.removeprefix(BANNED_PREFIX + '.')}` "
                       f"(canonical path curto, 727:13 majority)",
            }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocking", action="store_true",
                        help="Exit 1 if violations found (default: warn-only)")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON instead of text")
    parser.add_argument("--root", default="app",
                        help="Root directory to scan (default: app)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: root {root} not found", file=sys.stderr)
        sys.exit(2)

    violations = list(find_violations(root))

    if args.json:
        print(json.dumps({"violations": violations, "count": len(violations)}, indent=2))
    else:
        if not violations:
            print(f"OK: 0 violations in {root}")
        else:
            print(f"[canonical-import-paths] {len(violations)} violation(s):")
            for v in violations:
                print(f"  {v['file']}:{v['line']} {v['source']}")
                print(f"    -> {v['fix']}")
            print()
            print(f"Total: {len(violations)} import(s) using drifted path 'libs.models.lia_models.*'.")
            print(f"Canonical = 'lia_models.*' (727:13 majority). Vide CLAUDE.md REGRA 0.")

    if args.blocking and violations:
        sys.exit(1)


if __name__ == "__main__":
    main()
