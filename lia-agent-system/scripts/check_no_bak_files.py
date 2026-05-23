#!/usr/bin/env python3
"""
Sensor anti-regressão · W4-033 (2026-05-23)

Verifica que NENHUM arquivo `.bak.*` (backup de audit/refactor) está tracked
no git. .bak files são scar tissue de audit/fixes — ficam no histórico git
mas não pertencem no working tree.

Pattern violação:
- Audit/fix script cria `.bak.before-fix` e esquece de limpar
- Refactor manual com `cp file.py file.py.bak` deixado pra trás

Mensagem PT-BR + fix sugerido em sintaxe exata.
Modo: BLOCKING por default.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    # Use git ls-files para detectar TRACKED .bak files (working tree purges
    # podem deixar archivos untracked que serão pegos pelo .gitignore)
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print("⚠️  git ls-files failed (não é repo?). Skipping.", file=sys.stderr)
        return 0

    bak_files = [
        line for line in result.stdout.strip().split("\n")
        if ".bak." in line and not line.startswith(".gitignore")
    ]

    if bak_files:
        print(
            f"W4-033 dead code · {len(bak_files)} .bak file(s) tracked no git:",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for f in bak_files[:10]:
            print(f"  ❌ {f}", file=sys.stderr)
        if len(bak_files) > 10:
            print(f"  ... +{len(bak_files) - 10} more", file=sys.stderr)
        print(file=sys.stderr)
        print(
            "FIX: remover via git rm:\n"
            "  git rm $(git ls-files | grep -E '\\.bak\\.')\n"
            "OR adicionar `*.bak.*` em .gitignore + git rm --cached.",
            file=sys.stderr,
        )
        if args.warn_only:
            return 0
        return 1

    print("✅ Zero .bak files tracked (W4-033 cleanup mantido)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
