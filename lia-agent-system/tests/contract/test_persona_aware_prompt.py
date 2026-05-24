"""Contract sensor — canonical helper build_system_prompt_with_persona.

Ghost setting fix 2026-05-24: helper único que carrega ai_persona do tenant
e passa ao SystemPromptBuilder.build, eliminando o anti-pattern de 7 callers
chamando build() direto sem ai_persona= (cliente customizava "LIA → Sofia",
chat continuava "LIA").

TDD: estes testes definem contract do helper. Cascata canonical Replit
(canonical-fix → lia-testing) — Red→Green→Refactor.

Constraints capturados:
1. Helper carrega persona via get_ai_persona e passa como kwarg ai_persona=
   ao SystemPromptBuilder.build.
2. Quando load falha (exception), helper LOGA com exc_info=True e prossegue
   com ai_persona=None — falha NUNCA bloqueia o build (anti-silent-fallback
   REGRA 4 do CLAUDE.md: erro é registrado, não silenciado).
3. Kwargs do builder são propagados intactos (extra_instructions, agent_type,
   tenant_context_snippet, etc.).
4. company_id obrigatório — ValueError fail-closed quando vazio/None
   (multi-tenancy fail-closed).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_helper_loads_persona_and_passes_to_builder():
    """Helper canonical: get_ai_persona é chamado, resultado vai ao build()."""
    from app.shared.prompts import persona_aware_prompt

    persona = {"name": "Sofia", "tone": "amigavel"}

    fake_get_persona = AsyncMock(return_value=persona)
    fake_build = MagicMock(return_value="prompt_with_sofia")

    with patch(
        "app.domains.persona.services.ai_persona_service.get_ai_persona",
        fake_get_persona,
    ), patch.object(
        persona_aware_prompt.SystemPromptBuilder, "build", fake_build,
    ):
        result = await persona_aware_prompt.build_system_prompt_with_persona(
            company_id="co-1",
            db=MagicMock(),
            agent_type="orchestrator",
            extra_instructions="any",
        )

    assert result == "prompt_with_sofia"
    fake_get_persona.assert_awaited_once()
    # Builder DEVE receber ai_persona=persona (não None)
    fake_build.assert_called_once()
    _, build_kwargs = fake_build.call_args
    assert build_kwargs["ai_persona"] == persona
    assert build_kwargs["agent_type"] == "orchestrator"
    assert build_kwargs["extra_instructions"] == "any"


@pytest.mark.asyncio
async def test_helper_falls_back_when_load_fails():
    """Falha do load NUNCA bloqueia o build — ai_persona=None passa, build segue."""
    from app.shared.prompts import persona_aware_prompt

    fake_get_persona = AsyncMock(side_effect=RuntimeError("DB down"))
    fake_build = MagicMock(return_value="prompt_default_lia")

    with patch(
        "app.domains.persona.services.ai_persona_service.get_ai_persona",
        fake_get_persona,
    ), patch.object(
        persona_aware_prompt.SystemPromptBuilder, "build", fake_build,
    ):
        result = await persona_aware_prompt.build_system_prompt_with_persona(
            company_id="co-1",
            db=MagicMock(),
            agent_type="orchestrator",
        )

    # Build DEVE ter sido chamado mesmo com load falhando
    assert result == "prompt_default_lia"
    fake_build.assert_called_once()
    _, build_kwargs = fake_build.call_args
    # Persona None = default canonical, sem override (backward-compatible)
    assert build_kwargs["ai_persona"] is None


@pytest.mark.asyncio
async def test_helper_passes_through_kwargs():
    """Kwargs do builder são propagados intactos (não silenciosamente filtrados)."""
    from app.shared.prompts import persona_aware_prompt

    fake_get_persona = AsyncMock(return_value={"name": "LIA", "tone": "profissional"})
    fake_build = MagicMock(return_value="prompt_full")

    history = [{"role": "user", "content": "olá"}]
    with patch(
        "app.domains.persona.services.ai_persona_service.get_ai_persona",
        fake_get_persona,
    ), patch.object(
        persona_aware_prompt.SystemPromptBuilder, "build", fake_build,
    ):
        await persona_aware_prompt.build_system_prompt_with_persona(
            company_id="co-1",
            db=MagicMock(),
            agent_type="cv_screening",
            tenant_context_snippet="empresa X setor Y",
            user_name="Paulo",
            user_role="Recrutador Senior",
            conversation_history=history,
            context_page="recrutar",
            extra_instructions="seja conciso",
        )

    _, build_kwargs = fake_build.call_args
    assert build_kwargs["agent_type"] == "cv_screening"
    assert build_kwargs["tenant_context_snippet"] == "empresa X setor Y"
    assert build_kwargs["user_name"] == "Paulo"
    assert build_kwargs["user_role"] == "Recrutador Senior"
    assert build_kwargs["conversation_history"] == history
    assert build_kwargs["context_page"] == "recrutar"
    assert build_kwargs["extra_instructions"] == "seja conciso"


@pytest.mark.asyncio
async def test_helper_requires_company_id():
    """Multi-tenancy fail-closed: company_id vazio = ValueError, NUNCA build chamado."""
    from app.shared.prompts import persona_aware_prompt

    fake_build = MagicMock()

    with patch.object(persona_aware_prompt.SystemPromptBuilder, "build", fake_build):
        with pytest.raises(ValueError, match="company_id"):
            await persona_aware_prompt.build_system_prompt_with_persona(
                company_id="",
                db=MagicMock(),
                agent_type="orchestrator",
            )

    # Builder NUNCA foi chamado quando company_id ausente
    fake_build.assert_not_called()
