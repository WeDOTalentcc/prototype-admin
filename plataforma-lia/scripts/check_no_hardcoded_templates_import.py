#!/usr/bin/env python3
"""Sensor harness #3 — bloqueia reintrodução do legacy agent-templates-data.

Sprint 3 Parte 2: o arquivo foi DELETADO; canonical é agent_template_catalog
backend + adapter. Qualquer import = regressão.

Exit codes:
  0 = OK (0 violations)
  1 = violations (BLOCKING)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PATTERN = re.compile(r"""from\s+['"][^'"]*agent-templates-data['"]""")

EXCLUDE_PATHS = (
    "node_modules", ".next", ".turbo", "scripts/check_no_hardcoded_templates_import.py",
)


def main() -> int:
    violations: list[tuple[str, int, str]] = []
    for path in SRC.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in (".ts", ".tsx", ".js", ".jsx"):
            continue
        if any(part in path.as_posix() for part in EXCLUDE_PATHS):
            continue
        try:
            for i, line in enumerate(path.read_text().splitlines(), 1):
                if PATTERN.search(line):
                    rel = path.relative_to(ROOT)
                    violations.append((str(rel), i, line.strip()))
        except Exception:
            continue
    if violations:
        print("❌ Sensor #3 — import legacy agent-templates-data PROIBIDO")
        print("   (Sprint 3 deletou o arquivo; consumir agent_template_catalog backend)")
        print()
        for f, ln, src in violations:
            print(f"  {f}:{ln}  {src}")
            print(f"   → Fix: import useLegacyAgentTemplates from "
                  f"'@/hooks/agents/use-legacy-agent-templates'")
        print()
        print(f"Total: {len(violations)} violation(s)")
        return 1
    print("✅ Sensor #3 baseline 0 — nenhum import legacy agent-templates-data")
    return 0


if __name__ == "__main__":
    sys.exit(main())
