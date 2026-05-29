#!/usr/bin/env python3
"""Onda 4 F8 (2026-05-28) — sensor canonical AgentKpis consumption.

Garante que TODO componente em `src/app/[locale]/(dashboard)/agent-studio/[id]/kpis/`
consome KPIs via o hook canonical `useAgentKpis` (em `src/hooks/agents/use-agent-kpis.ts`),
NÃO via fetch inline ou outro hook.

Motivação:
  - useAgentKpis encapsula React Query + auth header + staleTime canonical.
  - Fetch inline em página de KPIs duplica lógica, evita cache, perde dedup,
    e geralmente vem sem auth header → 401.
  - Sensor protege contra regressão de futuras edits.

Modo:
  - BLOCKING por default (exit 1 quando viola). Promovido Onda 5.4 (2026-05-28)
    apos confirmar baseline 0.
  - --warn-only opt-out para branches legadas (mantem exit 0).

Output otimizado pra consumo de LLM:
  - aponta arquivo:linha
  - sugere uso de useAgentKpis com snippet correto

Falsos positivos esperados: 0. Se aparecer, abrir issue + adicionar SKIP em
EXEMPT_FILES com motivo.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Resolve raiz do plataforma-lia (parent do scripts/).
ROOT = Path(__file__).resolve().parent.parent / "src"
KPIS_DIR = ROOT / "app" / "[locale]" / "(dashboard)" / "agent-studio" / "[id]" / "kpis"

# Patterns proibidos dentro de arquivos em KPIS_DIR
FETCH_INLINE_PATTERNS = [
    re.compile(r"fetch\s*\(\s*['\"`].*custom-agents/.*kpis", re.IGNORECASE),
    re.compile(r"useSWR\s*\(", re.IGNORECASE),
    re.compile(r"apiFetch\s*\(\s*['\"`].*kpis", re.IGNORECASE),
]
REQUIRED_IMPORT_PATTERN = re.compile(
    r"from\s+['\"]@/hooks/agents/use-agent-kpis['\"]"
)

EXEMPT_FILES: dict[str, str] = {
    # Sem exempts no momento. Adicionar aqui com motivo se justificado.
}


def find_violations() -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []
    if not KPIS_DIR.exists():
        # Sensor sai limpo se feature ainda não foi adicionada.
        return violations

    for tsx in KPIS_DIR.rglob("*.tsx"):
        if tsx.name == "page.tsx":
            # Server component sem hook — ok.
            continue
        rel = str(tsx.relative_to(ROOT.parent))
        if rel in EXEMPT_FILES:
            continue

        text = tsx.read_text(encoding="utf-8")

        # Check fetch inline patterns
        for pat in FETCH_INLINE_PATTERNS:
            for m in pat.finditer(text):
                line = text[: m.start()].count("\n") + 1
                violations.append((
                    tsx,
                    line,
                    f"fetch inline para KPIs detectado. Use useAgentKpis() em vez disso.",
                ))

        # Check required import is present in client components that render KPIs
        if "AgentKpiResponse" in text or "AgentKpiBucket" in text:
            if not REQUIRED_IMPORT_PATTERN.search(text):
                violations.append((
                    tsx,
                    1,
                    "Componente consome AgentKpiResponse mas não importa useAgentKpis canonical.",
                ))

    return violations


def main() -> int:
    # Onda 5.4 — promovido a BLOCKING por default (baseline 0 confirmado).
    warn_only = "--warn-only" in sys.argv
    violations = find_violations()
    if not violations:
        print("✅ check_agent_kpi_consumes_canonical: 0 violations.")
        return 0

    print(
        "⚠️  check_agent_kpi_consumes_canonical: "
        f"{len(violations)} violation(s) encontradas:\n"
    )
    for path, line, reason in violations:
        print(f"  [{path}:{line}] {reason}")
        print("    → Fix: import { useAgentKpis } from '@/hooks/agents/use-agent-kpis'")
        print(
            "    → Uso: const { data, isLoading } = useAgentKpis(agentId, period)"
        )
        print()

    if warn_only:
        print(f"Modo: warn-only opt-out (exit 0). {len(violations)} violations.")
        return 0
    print(f"Modo: BLOCKING — exit 1 ({len(violations)} violations).")
    print("Use --warn-only para opt-out em branches legadas.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
