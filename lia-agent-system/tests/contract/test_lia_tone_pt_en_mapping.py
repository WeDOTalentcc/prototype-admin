"""Pin tone PT-BR (canonical UX) → lia_tone EN (legacy dispatcher) mapping.

F3.1 audit 2026-05-24. Service traduz no boundary; dispatcher continua
consumindo enum EN sem mudança. ai_persona.tone permanece PT-BR canonical.

Cobre:
1. Mapping cobre TODOS os tons canonical PT-BR (nenhum buraco silencioso).
2. Mapping values são EN tokens reconhecidos pelo dispatcher legacy
   (ou o default "professional", que é safe fallthrough).
3. update_ai_persona grava `lia_tone` em EN, mas mantém `ai_persona.tone`
   em PT-BR.
4. Mapping é graceful — se algum caller já passar EN (legacy), passa-through.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.persona.services import ai_persona_service
from app.domains.persona.services.ai_persona_validator import (
    CANONICAL_AI_TONES,
    TONE_PT_TO_EN_LEGACY,
)


# Tokens que `communication_dispatcher._apply_tone` reconhece via case
# explícito. Tudo o resto cai no default "professional" (greeting "Olá,").
# Esse set funciona como sensor estático contra o dispatcher; se alguém
# mudar `_apply_tone` adicionando tons novos, atualizar aqui.
DISPATCHER_RECOGNIZED_TONES: set[str] = {"friendly", "formal"}
DISPATCHER_SAFE_DEFAULT: str = "professional"


def test_mapping_covers_all_canonical_tones():
    """Cada tom canonical PT-BR DEVE ter um equivalente EN documentado.

    Adicionar tom novo em CANONICAL_AI_TONES sem entry em
    TONE_PT_TO_EN_LEGACY = lia_tone legacy fica com valor PT-BR não
    reconhecido = outbound silenciosamente cai no default.
    """
    missing = set(CANONICAL_AI_TONES) - set(TONE_PT_TO_EN_LEGACY)
    assert not missing, f"Tons canonical sem mapping EN: {sorted(missing)}"


def test_mapping_values_are_safe_for_dispatcher():
    """Cada valor EN do mapping DEVE ser reconhecido pelo dispatcher
    (case explícito) OU ser o default safe ("professional").

    NOTE: dispatcher só tem case statement para 2 tons. Tudo o resto
    cai no default, que produz greeting genérico "Olá, X." — não é bug,
    mas é fallback silencioso. Aceitar "professional" como passthrough
    seguro; rejeitar qualquer outro valor desconhecido.
    """
    allowed = DISPATCHER_RECOGNIZED_TONES | {DISPATCHER_SAFE_DEFAULT}
    extras = set(TONE_PT_TO_EN_LEGACY.values()) - allowed
    assert not extras, (
        f"Valores EN no mapping fora do contrato do dispatcher: {sorted(extras)}. "
        f"Permitidos: {sorted(allowed)}."
    )


def test_passthrough_when_already_english():
    """Mapping é graceful — input já em EN deve passar inalterado.

    Caller legacy pode passar `tone="professional"` direto antes da
    migration completar. `.get(tone, tone)` no service preserva isso
    sem double-translation.
    """
    # Simula o passthrough que o service faz: .get(tone, tone)
    assert TONE_PT_TO_EN_LEGACY.get("professional", "professional") == "professional"
    assert TONE_PT_TO_EN_LEGACY.get("friendly", "friendly") == "friendly"
    assert TONE_PT_TO_EN_LEGACY.get("formal", "formal") == "formal"


# --- service integration ---------------------------------------------------


def _make_policy(communication_rules: dict | None) -> MagicMock:
    policy = MagicMock()
    policy.communication_rules = communication_rules
    return policy


def _make_repo(policy: MagicMock | None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_company = AsyncMock(return_value=policy)
    repo.create_if_missing = AsyncMock(return_value=policy or _make_policy({}))
    repo.flush = AsyncMock()
    return repo


def _install_repo_mock(repo: MagicMock) -> None:
    import app.domains.persona.services.ai_persona_service as svc_mod
    svc_mod.HiringPolicyRepository = MagicMock(return_value=repo)


@pytest.mark.parametrize(
    "pt_tone,expected_en",
    list(TONE_PT_TO_EN_LEGACY.items()),
)
@pytest.mark.asyncio
async def test_update_ai_persona_writes_translated_lia_tone(pt_tone, expected_en):
    """update_ai_persona DEVE gravar `communication_rules.lia_tone` em EN
    e manter `ai_persona.tone` em PT-BR.

    Parametrizado por todos os 6 tons canonical — qualquer regressão no
    mapping (faltando entry, valor errado) reprova aqui.
    """
    policy = _make_policy({})
    repo = _make_repo(policy)
    _install_repo_mock(repo)

    result = await ai_persona_service.update_ai_persona(
        "co-1", MagicMock(), name=None, tone=pt_tone,
        actor_user_id="user-1",
    )

    # ai_persona.tone permanece PT-BR canonical (UX + SystemPromptBuilder)
    assert result["tone"] == pt_tone
    assert policy.communication_rules["ai_persona"]["tone"] == pt_tone

    # lia_tone legacy é traduzido para EN (dispatcher consumer)
    assert policy.communication_rules["lia_tone"] == expected_en
