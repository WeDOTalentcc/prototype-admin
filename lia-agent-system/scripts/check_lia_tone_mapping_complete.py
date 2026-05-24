"""Sensor: TONE_PT_TO_EN_LEGACY DEVE cobrir todos CANONICAL_AI_TONES.

Background: F3.1 audit 2026-05-24. Service traduz PT-BR → EN no boundary
para o dispatcher legacy (communication_dispatcher._apply_tone). Adicionar
novo tom em CANONICAL_AI_TONES sem adicionar entry no mapping = lia_tone
legacy fica com valor PT-BR não reconhecido pelo dispatcher = outbound
(email + WhatsApp) silenciosamente ignora a config do recrutador.

Uso:
    python scripts/check_lia_tone_mapping_complete.py

Exit 0 = todos os tons mapeados. Exit 1 = drift detectado, instrução de
fix incluída na mensagem (otimizado pra consumo de LLM coding agent).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        from app.domains.persona.services.ai_persona_validator import (
            CANONICAL_AI_TONES,
            TONE_PT_TO_EN_LEGACY,
        )
    except ImportError as exc:
        print(f"❌ Sensor não conseguiu importar ai_persona_validator: {exc}")
        print("   Verifique se o arquivo existe em app/domains/persona/services/.")
        sys.exit(2)

    missing = set(CANONICAL_AI_TONES) - set(TONE_PT_TO_EN_LEGACY)
    if missing:
        print("❌ Drift detectado: tons canonical PT-BR sem mapping EN para dispatcher:")
        for tone in sorted(missing):
            print(f"  • {tone}")
        print()
        print("Fix: adicionar entry em TONE_PT_TO_EN_LEGACY em")
        print("  app/domains/persona/services/ai_persona_validator.py")
        print()
        print("Mapeie cada tom PT-BR a um valor EN reconhecido pelo dispatcher")
        print('(communication_dispatcher._apply_tone aceita "friendly", "formal",')
        print('default "professional"). Use closest match — vide comentários da')
        print("constante para o critério canonical.")
        sys.exit(1)

    # Defesa adicional: valores EN do mapping não podem ser strings vazias
    # ou Nones (silent failure no dispatcher).
    bad_values = [
        (k, v) for k, v in TONE_PT_TO_EN_LEGACY.items()
        if not isinstance(v, str) or not v.strip()
    ]
    if bad_values:
        print("❌ Mapping com valores EN inválidos:")
        for k, v in bad_values:
            print(f"  • {k!r} → {v!r}")
        print()
        print("Fix: valor EN deve ser string não-vazia (ex.: 'professional',")
        print("'friendly', 'formal').")
        sys.exit(1)

    print(
        f"✅ Tone mapping sensor: {len(CANONICAL_AI_TONES)} tons PT-BR cobertos "
        f"→ {len(set(TONE_PT_TO_EN_LEGACY.values()))} valores EN distintos"
    )


if __name__ == "__main__":
    main()
