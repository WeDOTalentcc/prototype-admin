#!/usr/bin/env python3
"""Onda 1 F9 (2026-05-27) — sensor white-label canonical em pages-agent-studio.

White-label canonical (CLAUDE.md project_white_label_ai_assistant 2026-05-25):
toda renderização de nome de agente em UI passa pelo hook `useAiPersona()`
da cliente — cliente pode renomear "LIA" via Configurações sem editar código.

Sensor detecta anti-pattern:
  - {agent.name} / {agent_name} renderizado direto em JSX
  - sem `useAiPersona()` no mesmo file

Modo: BLOCKING por default (promovido 2026-05-29, Agent B batch pós-Fase 2).
Baseline 0 confirmado. Use `--warn-only` para opt-out (legacy ratchet em
branches atrasadas), exit 1 quando violations existem.

Mensagem otimizada pra consumo de LLM:
  - aponta arquivo:linha
  - Sugestão: importar `useAiPersona` de @/hooks/company/use-ai-persona
  - Fallback canonical: `agent.name || persona?.name || "Agente"`

Honra marker: // PERSONA-EXEMPT: <reason> na linha
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src" / "components" / "pages-agent-studio"

# Padrão: {something.name} OR {something_name} em JSX. Heurística — pode dar
# false positives para nomes não-agente. Aceitamos warn-only por isso.
# Restringe a expressões cujo identifier começa com "agent" / "Agent" para
# reduzir falsos positivos massivamente.
AGENT_NAME_RE = re.compile(
    r"\{(?:[A-Za-z_]+\.)?(?:agent|Agent)[A-Za-z_]*(?:\.name|_name)\}"
)
USE_PERSONA_RE = re.compile(r"\buseAiPersona\s*\(")
EXEMPT_RE = re.compile(r"PERSONA-EXEMPT")


def main() -> int:
    # Promovido a BLOCKING default 2026-05-29 (Agent B batch pós-Fase 2,
    # baseline 14→0). Opt-out via --warn-only para ratchet em branches atrasadas.
    warn_only = "--warn-only" in sys.argv
    blocking = not warn_only
    violations: list[tuple[Path, int, str]] = []
    for tsx in ROOT.rglob("*.tsx"):
        # Skip tests + Drawer canonical (já lida com persona).
        if "__tests__" in str(tsx):
            continue
        text = tsx.read_text(encoding="utf-8")
        uses_persona = bool(USE_PERSONA_RE.search(text))
        if uses_persona:
            continue  # arquivo já tá canonical
        for ln, line in enumerate(text.splitlines(), 1):
            if EXEMPT_RE.search(line):
                continue
            if AGENT_NAME_RE.search(line):
                violations.append((tsx, ln, line.strip()[:100]))

    if not violations:
        print("✅ pages-agent-studio: 0 anti-pattern usages de agent.name sem useAiPersona.")
        return 0

    print(f"⚠ pages-agent-studio: {len(violations)} usages de agent.name sem useAiPersona detectados.\n")
    for path, line, snippet in violations[:30]:
        rel = path.relative_to(ROOT.parent.parent)
        print(f"  [{rel}:{line}] {snippet}")
        print(
            "    → Fix: importar `useAiPersona` de @/hooks/company/use-ai-persona "
            "+ usar fallback `agent.name || persona?.name || \"Agente\"`."
        )
        print()
    if len(violations) > 30:
        print(f"  ... e mais {len(violations) - 30} ocorrências")
    print(f"\nTotal: {len(violations)} violação(ões).")
    print("Modo: warn-only (exit 0)" if not blocking else "Modo: BLOCKING (exit 1)")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
