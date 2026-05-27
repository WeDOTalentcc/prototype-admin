#!/usr/bin/env python3
"""Wave E Sensor 4 — Detecta useState+useEffect(fetch) anti-pattern em pages-agent-studio.

Regra canonical (Settings REGRA 1 — 2026-05-26): server data usa React Query (useQuery),
não useState+useEffect manual. O anti-pattern produz:
- Stale data sem invalidação
- Sem cache/dedup de requests
- Race conditions em concurrent renders

Detecta arquivos em pages-agent-studio que:
1. Usam useEffect com fetch/axios/api call
2. NÃO importam useQuery de @tanstack/react-query

Baseline 2026-05-27: 9 violations existentes (tech debt):
  - CalibrationCardModal.tsx:94
  - CustomAgentsTab.tsx:71,319
  - DigitalTwinComponents.tsx:442,605
  - MarketplaceTab.tsx:106,284,385
  - custom-agents/AgentCreationPreview.tsx:42

Modo: warn-only enquanto baseline não atinge 0.
Promover a --blocking quando todas as 9 violations forem migradas para useQuery.

Honra marker: // SENSOR-EXEMPT: <reason> na linha do useEffect

Exit 0 sempre em modo warn-only. Exit 1 quando --blocking e violations > 0.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src" / "components" / "pages-agent-studio"

USEEFFECT_LINE_RE = re.compile(r'\buseEffect\s*\(')
FETCH_INSIDE_RE = re.compile(r'\bfetch\s*\(\s*[`"\']|backendProxy\.|/api/backend-proxy')
USEQUERY_IMPORT_RE = re.compile(r'from\s+["\']@tanstack/react-query["\'].*\buseQuery\b')

EXEMPT_MARKER = "SENSOR-EXEMPT"

# Baseline atual: violations existentes que ainda não foram migradas
KNOWN_BASELINE = {
    "CalibrationCardModal.tsx": [94],
    "CustomAgentsTab.tsx": [71, 319],
    "DigitalTwinComponents.tsx": [442, 605],
    "MarketplaceTab.tsx": [106, 284, 385],
    "AgentCreationPreview.tsx": [42],
}


def file_has_useeffect_fetch(path: Path) -> list[tuple[int, str]]:
    """Retorna violations (lineno, snippet) se arquivo usa useEffect+fetch sem useQuery."""
    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    # Se tem useQuery importado, skip (padrão correto já adotado)
    if USEQUERY_IMPORT_RE.search(content):
        return []

    violations = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if EXEMPT_MARKER in line:
            i += 1
            continue
        if USEEFFECT_LINE_RE.search(line):
            # Verificar as próximas 15 linhas em busca de fetch
            window = "\n".join(lines[i: i + 15])
            if FETCH_INSIDE_RE.search(window):
                violations.append((i + 1, f"useEffect + fetch sem useQuery: {line.strip()!r}"))
        i += 1

    return violations


def is_known_baseline(path: Path, lineno: int) -> bool:
    """Verifica se violation é do baseline conhecido (tech debt existente)."""
    filename = path.name
    known_lines = KNOWN_BASELINE.get(filename, [])
    # Tolerância de ±3 linhas (commits podem ter mudado a numeração)
    return any(abs(lineno - kl) <= 3 for kl in known_lines)


def main() -> int:
    # Sensor é warn-only por default (baseline > 0)
    # Usar --blocking para promover a BLOCKING quando baseline atingir 0
    blocking = "--blocking" in sys.argv

    all_violations: list[tuple[Path, int, str]] = []
    new_violations: list[tuple[Path, int, str]] = []

    for path in sorted(ROOT.rglob("*.tsx")):
        if "__tests__" in str(path) or ".next" in str(path):
            continue
        for lineno, msg in file_has_useeffect_fetch(path):
            rel = path.relative_to(ROOT.parent.parent)
            all_violations.append((rel, lineno, msg))
            if not is_known_baseline(path, lineno):
                new_violations.append((rel, lineno, msg))

    if not all_violations:
        print(f"[check_useQuery_in_studio] ✅ 0 violations — baseline zerado! Promover para --blocking.")
        return 0

    print(f"[check_useQuery_in_studio] ⚠️  {len(all_violations)} violation(s) totais "
          f"({len(all_violations) - len(new_violations)} baseline, {len(new_violations)} novas):\n")

    for rel_path, lineno, msg in all_violations:
        is_baseline = not any((rel_path, lineno, m) in new_violations for m in [msg])
        tag = "[baseline]" if is_known_baseline(Path(str(rel_path)), lineno) else "[NOVO ❌]"
        print(f"  {tag} [{rel_path}:{lineno}] {msg}")

    if new_violations:
        print(f"\n[check_useQuery_in_studio] ❌ {len(new_violations)} NOVA(S) violation(s) detectadas além do baseline!")
        print(f"  → Fix: usar useQuery de @tanstack/react-query para server data.")
        print(f"    Não adicione novas violations ao baseline — migre imediatamente.")
        if blocking:
            return 1

    print(f"\n[check_useQuery_in_studio] Baseline {len(all_violations) - len(new_violations)}/9 violations pendentes de migração para useQuery.")
    print(f"  → Referência de migração: src/components/settings/FairnessComplianceHub.tsx (84 LOC com useQuery).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
