#!/usr/bin/env python3
"""
Sensor #5 — bloqueia reintrodução do state showCreateModal no AgentStudioPage.

Sprint 5 (2026-05-25) decommissionou o CreateAgentModal antigo (path #3 sector
tile). O state showCreateModal + setSelectedTemplate + função inline
CreateAgentModal foram removidos; sector tile click agora abre o wizard
canonical (CreateAgentWizard) via openWizard(...).

Este sensor garante que ninguem reintroduza o pattern legado especificamente
em AgentStudioPage.tsx (showCreateModal eh nome generico usado em outros
componentes do projeto — escopo intencionalmente narrow).

Pattern detectado:
- `const [showCreateModal, setShowCreateModal] = useState(...)` em AgentStudioPage.tsx
- `setShowCreateModal(...)` em AgentStudioPage.tsx
- `function CreateAgentModal(...)` inline em AgentStudioPage.tsx
- `const [selectedTemplate, setSelectedTemplate] = ...<SectorTemplate...>` (state
  exclusivo do modal antigo)

Refs:
- AGENT_STUDIO_IMPLEMENTATION_PLAN.md §6 Sprint 5
- AGENT_STUDIO_DEEP_AUDIT.md A.7

Modo: BLOCKING por default (Sprint 5+). Exit 1 quando violations existem.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Escopo narrow: apenas AgentStudioPage.tsx (showCreateModal eh nome generico).
SCOPED_FILES = [
    "src/components/pages-agent-studio/AgentStudioPage.tsx",
]

PATTERNS = [
    (
        re.compile(r"\[\s*showCreateModal\s*,\s*setShowCreateModal\s*\]"),
        "state showCreateModal — use openWizard(...) canonical em vez de modal legado",
    ),
    (
        re.compile(r"\bsetShowCreateModal\s*\("),
        "chamada setShowCreateModal — wizard CreateAgentWizard absorveu este path",
    ),
    (
        re.compile(r"\bfunction\s+CreateAgentModal\s*\("),
        "função inline CreateAgentModal — modal legado removido em Sprint 5",
    ),
    (
        re.compile(
            r"\[\s*selectedTemplate\s*,\s*setSelectedTemplate\s*\]\s*=\s*useState<\s*SectorTemplate"
        ),
        "state selectedTemplate<SectorTemplate> — era exclusivo do modal legado",
    ),
]


def scan_file(path: Path) -> list[tuple[int, str]]:
    if not path.exists():
        return []
    violations: list[tuple[int, str]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for pattern, msg in PATTERNS:
            if pattern.search(line):
                violations.append((lineno, f"{msg} | line: {line.strip()[:120]}"))
    return violations


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    total = 0
    for rel in SCOPED_FILES:
        path = root / rel
        violations = scan_file(path)
        for lineno, msg in violations:
            print(f"{rel}:{lineno}: {msg}")
            print(
                f"  -> Fix: substitua por openWizard(goal, {{ prefilledSector, name, description }}) — wizard canonical em src/components/pages-agent-studio/create-agent-wizard/"
            )
            total += 1
    if total == 0:
        print("OK — sensor #5 (no showCreateModal in AgentStudioPage): 0 violations")
        return 0
    print(f"\nFAIL — {total} violation(s) do sensor #5 (Sprint 5 decommission)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
