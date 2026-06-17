#!/usr/bin/env python3
"""Sensor #15: AgentStudioPage nao pode ter sub-tabs.

SSOT (Studio Restructure F1+F2+F3 — 2026-05-26):
  - AgentStudioPage tem 2 abas topo apenas (my-agents + digital-twins).
  - Marketplace foi extraido para rota dedicada /agents/marketplace.
  - Sub-tabs (type MySubTab, state mySubTab, useState<MySubTab>) foram colapsadas.

Regras detectadas (3):
  1. Type MySubTab declaration
  2. useState<MySubTab> ou variavel mySubTab
  3. Import MarketplaceTab dentro de AgentStudioPage.tsx

Fix: ver mensagens inline.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src" / "components" / "pages-agent-studio"
TARGET = ROOT / "AgentStudioPage.tsx"

violations: list[str] = []


def check(rule_id: str, pattern: str, msg: str, content: str, path: str) -> None:
    rx = re.compile(pattern)
    for i, line in enumerate(content.splitlines(), 1):
        if rx.search(line):
            violations.append(f"{path}:{i}: [{rule_id}] {msg}\n  -> {line.strip()}")


if TARGET.exists():
    text = TARGET.read_text(encoding="utf-8")
    check(
        "MYSUBTAB_TYPE",
        r"^type\s+MySubTab\b",
        "Type MySubTab proibido. Sub-tabs colapsadas — use type MainTab apenas.",
        text,
        TARGET.as_posix(),
    )
    check(
        "MYSUBTAB_STATE",
        r"useState<MySubTab>|\bmySubTab\b",
        "State mySubTab proibido. AgentStudioPage tem 2 abas topo apenas.",
        text,
        TARGET.as_posix(),
    )
    check(
        "MARKETPLACE_IMPORT",
        r"import.*MarketplaceTab.*from.*MarketplaceTab",
        "MarketplaceTab vive em rota /agents/marketplace. Nao importar em AgentStudioPage.",
        text,
        TARGET.as_posix(),
    )

if violations:
    print("\n".join(violations))
    print(
        f"\n{len(violations)} violations. Canonical: AgentStudioPage tem 2 abas topo apenas "
        "(my-agents + digital-twins). Marketplace em /agents/marketplace."
    )
    sys.exit(1)

print("OK")
sys.exit(0)
