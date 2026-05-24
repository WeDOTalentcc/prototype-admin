#!/usr/bin/env python3
"""Sprint 14.1 sensor canonical — verifica TS↔Python parity em canonical pages.

G1 canonical fix (2026-05-24) criou duas fontes paralelas:
- lia-agent-system/app/shared/canonical_pages.py (Python CanonicalPage StrEnum)
- plataforma-lia/src/lib/canonical-pages.ts (TS CANONICAL_PAGES const obj)

Esse sensor previne drift: ambos DEVEM ter mesmas keys + values. Adicionar
page no Python sem mirror no TS (ou vice-versa) = LLM ignora page_type
porque normalize_page() trata como "general".

Exit codes:
    0 — sync OK (mesmas 18 keys/values)
    1 — drift detectado (lista keys faltando em cada lado)

Uso CI:
    python3 scripts/check_canonical_pages_sync.py

Wire em .pre-commit-config.yaml + .github/workflows/frontend-ci.yml.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parent.parent
# scripts/ lives in lia-agent-system/, so workspace = parent
PYTHON_FILE = WORKSPACE / "app" / "shared" / "canonical_pages.py"
# plataforma-lia is sibling
TS_FILE = WORKSPACE.parent / "plataforma-lia" / "src" / "lib" / "canonical-pages.ts"


def extract_python_pages(src: str) -> set[tuple[str, str]]:
    """Parse `KEY = "value"` lines inside the StrEnum class block."""
    # Match lines like `HOME = "home"` (indented, all uppercase keys)
    pattern = re.compile(r'^\s{4}([A-Z][A-Z_]*)\s*=\s*"([a-z_]+)"', re.MULTILINE)
    return set(pattern.findall(src))


def extract_ts_pages(src: str) -> set[tuple[str, str]]:
    """Parse `KEY: "value"` lines inside the CANONICAL_PAGES const object."""
    pattern = re.compile(r'^\s+([A-Z][A-Z_]*):\s*"([a-z_]+)"', re.MULTILINE)
    return set(pattern.findall(src))


def main() -> int:
    if not PYTHON_FILE.exists():
        print(f"❌ Python canonical file not found: {PYTHON_FILE}", file=sys.stderr)
        return 1
    if not TS_FILE.exists():
        print(f"❌ TS canonical file not found: {TS_FILE}", file=sys.stderr)
        return 1

    py_pages = extract_python_pages(PYTHON_FILE.read_text())
    ts_pages = extract_ts_pages(TS_FILE.read_text())

    only_py = py_pages - ts_pages
    only_ts = ts_pages - py_pages

    if not only_py and not only_ts:
        print(f"✅ canonical pages sync OK ({len(py_pages)} pages, Python ≡ TS)")
        return 0

    print("❌ Drift detectado em canonical_pages:")
    if only_py:
        print(f"\n  Pages só em Python ({PYTHON_FILE.name}):")
        for key, value in sorted(only_py):
            print(f"    - {key} = \"{value}\"")
        print(f"  → Fix: adicionar em {TS_FILE.relative_to(WORKSPACE.parent)}")
    if only_ts:
        print(f"\n  Pages só em TS ({TS_FILE.name}):")
        for key, value in sorted(only_ts):
            print(f"    - {key}: \"{value}\"")
        print(f"  → Fix: adicionar em {PYTHON_FILE.relative_to(WORKSPACE)}")
    print("\nLembrar: ambos arquivos devem espelhar 1-pra-1. PAGE_DESCRIPTIONS_PT_BR")
    print("e canonicalPageLabel() também precisam de entry pro novo page.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
