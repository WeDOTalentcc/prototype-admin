#!/usr/bin/env python3
"""Sensor harness #4 (Sprint 4 v3 — 2026-05-25).

Garante que `sourcing-tab` (ex-MultiStrategySearchPanel) é importado APENAS pelo
consumer canonical: `TalentPoolPage`. Previne dual-mount (a regressão exata que
o Sprint 4 v3 corrigiu — panel duplicado entre Studio e TalentPoolPage).

Saída em PT-BR com instrução de fix embutida (otimizada para consumo de LLM).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Path canonical único: TalentPoolPage onde fica a sub-tab Sourcing.
ALLOWED_SUFFIXES = (
    "pages-talent-pools/TalentPoolPage.tsx",
    "pages-talent-pools/sub-tabs/sourcing-tab.tsx",  # auto-import sibling permitido
)

# Padrão captura tanto `from "./sub-tabs/sourcing-tab"` quanto absolute
# `from "@/components/pages-talent-pools/sub-tabs/sourcing-tab"`.
PATTERN = re.compile(r"""from\s+['"][^'"]*sourcing-tab['"]""")

# Padrão legacy: nome antigo do componente (rejeitar para evitar import errado).
LEGACY_PATTERN = re.compile(r"""from\s+['"][^'"]*MultiStrategySearchPanel['"]""")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    src_root = root / "src"
    if not src_root.exists():
        print(f"src dir nao encontrado em {src_root}", file=sys.stderr)
        return 0

    violations: list[str] = []
    for path in sorted(src_root.rglob("*.tsx")):
        if "__tests__" in path.parts or ".bak." in path.name:
            continue
        relp = path.relative_to(root).as_posix()
        # Allowed: arquivo canonical destino + o proprio sub-tab
        if any(relp.endswith(suf) for suf in ALLOWED_SUFFIXES):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if PATTERN.search(line):
                violations.append(
                    f"{relp}:{i}: import de 'sourcing-tab' fora do consumer canonical.\n"
                    f"  Fix: o panel canonical agora vive em TalentPoolPage (sub-tab Sourcing).\n"
                    f"  Remova este import e use o sub-tab via TalentPoolPage.\n"
                    f"  Allowed: {ALLOWED_SUFFIXES}"
                )
            if LEGACY_PATTERN.search(line):
                violations.append(
                    f"{relp}:{i}: import de 'MultiStrategySearchPanel' (nome legacy).\n"
                    f"  Fix: o componente foi renomeado para 'SourcingTab' e movido para\n"
                    f"  src/components/pages-talent-pools/sub-tabs/sourcing-tab.tsx.\n"
                    f"  Use TalentPoolPage para acessar a sub-tab Captação."
                )

    if violations:
        print("\n".join(violations))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
