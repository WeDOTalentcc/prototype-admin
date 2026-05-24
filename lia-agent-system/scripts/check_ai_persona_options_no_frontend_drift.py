"""Sensor: frontend NÃO pode redeclarar lista hardcoded de tons.

Background: F3.2 audit 2026-05-24. TONE_OPTIONS hardcoded em
AiPersonaPanel.tsx + CANONICAL_TONES literal em use-ai-persona.ts
duplicavam o catálogo canonical do backend (`CANONICAL_AI_TONES` +
`TONE_INSTRUCTIONS` + `TONE_UI_METADATA` em ai_persona_validator.py).
Adicionar tom no backend exigia commit coordenado em 3 lugares — drift
garantido. Endpoint canonical GET /api/v1/company-ai-persona/options
agora é single source of truth; frontend consome via `useAiPersonaOptions()`.

Esse sensor barra reintrodução das constantes hardcoded em arquivos que
JÁ devem consumir o endpoint. Não checa outros arquivos (o sensor
existiria sem o /options também).

Uso:
    python scripts/check_ai_persona_options_no_frontend_drift.py

Exit 0 = sem drift. Exit 1 = violação detectada + instrução de fix.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# plataforma-lia é sibling do lia-agent-system no monorepo Replit
PLATAFORMA_LIA = ROOT.parent / "plataforma-lia"


# ---------------------------------------------------------------------------
# Patterns canonical
# ---------------------------------------------------------------------------

# (regex, fix_message)
FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (
        r"const\s+TONE_OPTIONS\s*[:=]\s*(\[|ToneOption\[\])",
        (
            "TONE_OPTIONS array hardcoded — use useAiPersonaOptions() do "
            "hook canonical em vez de declarar localmente. Backend é "
            "single source of truth via GET /api/v1/company-ai-persona/options."
        ),
    ),
    # NOTE: CANONICAL_TONES literal export ainda existe no hook como deprecated.
    # Sensor não barra a declaração no próprio hook (transitional) — só barra
    # consumo em AiPersonaPanel.tsx ou criação de OUTRA cópia.
    (
        r"const\s+CANONICAL_TONES\s*[:=]\s*(\[|AiPersonaTone\[\])",
        (
            "CANONICAL_TONES array hardcoded em arquivo que NÃO é o hook "
            "canonical — use useAiPersonaOptions().tones e mapeie t.value "
            "se precisar de typed enum. Hook é fonte única."
        ),
    ),
]


# Arquivos sob vigilância. Outros arquivos podem ter TONE_OPTIONS pra outro
# domínio (ex: tom de notificação) — não interferir.
SCAN_PATHS: list[str] = [
    "src/components/settings/AiPersonaPanel.tsx",
]

# Hook canonical (use-ai-persona.ts) é o ÚNICO arquivo onde CANONICAL_TONES
# literal pode existir, marcado como @deprecated. Validamos isso
# explicitamente em vez de só blocking nos outros.
HOOK_CANONICAL_PATH = "src/hooks/company/use-ai-persona.ts"
HOOK_REQUIRED_MARKERS: list[tuple[str, str]] = [
    (
        r"export\s+function\s+useAiPersonaOptions\s*\(",
        (
            "Hook canonical use-ai-persona.ts deve exportar "
            "useAiPersonaOptions(). Removido = frontend não tem mais como "
            "consumir o endpoint /options."
        ),
    ),
    (
        r"@deprecated\s+F3\.2",
        (
            "CANONICAL_TONES literal ainda existe no hook mas perdeu o "
            "marker @deprecated F3.2 — sem ele, novos devs reusarão a "
            "constante e o drift volta. Restaurar JSDoc @deprecated."
        ),
    ),
]


def main() -> int:
    if not PLATAFORMA_LIA.exists():
        print(
            f"⏭️  plataforma-lia não está adjacente ({PLATAFORMA_LIA}) — "
            f"sensor skip (provavelmente rodando fora do monorepo)."
        )
        return 0

    violations: list[str] = []

    # 1) Arquivos sob vigilância: padrões proibidos
    for rel_path in SCAN_PATHS:
        full = PLATAFORMA_LIA / rel_path
        if not full.exists():
            violations.append(
                f"{rel_path}: arquivo esperado não existe. Foi removido "
                f"sem atualizar este sensor?"
            )
            continue
        text = full.read_text(encoding="utf-8")
        for pattern, fix_msg in FORBIDDEN_PATTERNS:
            for match in re.finditer(pattern, text):
                line = text[: match.start()].count("\n") + 1
                violations.append(f"{rel_path}:{line}: {fix_msg}")

    # 2) Hook canonical: markers obrigatórios
    hook_full = PLATAFORMA_LIA / HOOK_CANONICAL_PATH
    if not hook_full.exists():
        violations.append(
            f"{HOOK_CANONICAL_PATH}: hook canonical sumiu. Sem ele não "
            f"há como o frontend consumir /options."
        )
    else:
        hook_text = hook_full.read_text(encoding="utf-8")
        for pattern, fix_msg in HOOK_REQUIRED_MARKERS:
            if not re.search(pattern, hook_text):
                violations.append(f"{HOOK_CANONICAL_PATH}: {fix_msg}")

    # ------------------------------------------------------------------
    # Output otimizado para consumo de LLM (PT-BR, instrução de fix)
    # ------------------------------------------------------------------
    if violations:
        print("❌ Ai Persona /options frontend drift sensor: violations detectadas\n")
        for v in violations:
            print(f"  • {v}")
        print()
        print("Contexto:")
        print("  GET /api/v1/company-ai-persona/options retorna o catálogo")
        print("  canonical (tons + name constraints). Frontend DEVE consumir")
        print("  via useAiPersonaOptions() — não redeclarar arrays locais.")
        print()
        print("Adicionar tom novo (workflow canonical):")
        print("  1. lia-agent-system/app/domains/persona/services/ai_persona_validator.py:")
        print("     - CANONICAL_AI_TONES (tuple)")
        print("     - TONE_INSTRUCTIONS (dict)")
        print("     - TONE_UI_METADATA (dict)")
        print("     - TONE_PT_TO_EN_LEGACY (dict)")
        print("  2. Frontend propaga automaticamente. Zero deploy.")
        return 1

    print(
        f"✅ Ai Persona /options sensor: 0 violations "
        f"(scan: {len(SCAN_PATHS)} arquivos + hook canonical)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
