"""
F-10 + F-11 canonical sensor: voice system prompt MUST consume:
  - SystemPromptBuilder.build (E2.3 persona override)
  - build_company_agent_context (lia_field_toggles canonical)
  - get_ai_persona (AI Persona per-tenant)

Audit ref: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-10 + F-11.

Bug pré-fix: voice orchestrator construía system_prompt manualmente em
`generate_lia_response` + `_build_job_presentation_instruction`, sem ler
AI Persona (E2.3) nem lia_field_toggles. Cliente customizava nome/tom da
LIA em Configurações → afetava chat (outbound + chat lateral) mas NÃO
afetava voz. Ghost setting parcial.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_voice_prompt_uses_systemprompt_builder():
    """F-10: build_voice_system_prompt deve delegar para SystemPromptBuilder.build."""
    from app.shared.prompts.voice_system_prompt import build_voice_system_prompt

    db_mock = AsyncMock()

    with patch(
        "app.shared.prompts.voice_system_prompt.SystemPromptBuilder.build",
        return_value="MOCKED_FULL_PROMPT",
    ) as builder_mock, patch(
        "app.shared.prompts.voice_system_prompt.build_company_agent_context",
        new=AsyncMock(return_value="company-ctx-snippet"),
    ), patch(
        "app.shared.prompts.voice_system_prompt.get_ai_persona",
        new=AsyncMock(return_value={"name": "LIA", "tone": "profissional"}),
    ):
        result = await build_voice_system_prompt(
            company_id="company-uuid",
            db=db_mock,
            job_context={"title": "Engenheiro", "department": "tech"},
        )

    assert builder_mock.called, "SystemPromptBuilder.build deve ser chamado"
    assert "MOCKED_FULL_PROMPT" in result


@pytest.mark.asyncio
async def test_voice_prompt_applies_ai_persona_per_tenant():
    """F-10 + F-11 / E2.3: tenant custom name+tone deve atingir SystemPromptBuilder."""
    from app.shared.prompts.voice_system_prompt import build_voice_system_prompt

    db_mock = AsyncMock()

    captured = {}

    def _capture(**kwargs):
        captured.update(kwargs)
        return "PROMPT_OUT"

    with patch(
        "app.shared.prompts.voice_system_prompt.SystemPromptBuilder.build",
        side_effect=_capture,
    ), patch(
        "app.shared.prompts.voice_system_prompt.build_company_agent_context",
        new=AsyncMock(return_value=""),
    ), patch(
        "app.shared.prompts.voice_system_prompt.get_ai_persona",
        new=AsyncMock(return_value={"name": "Aria", "tone": "amigavel"}),
    ):
        await build_voice_system_prompt(
            company_id="company-uuid",
            db=db_mock,
            job_context=None,
        )

    assert "ai_persona" in captured, "ai_persona kwarg deve ser passado"
    assert captured["ai_persona"] == {"name": "Aria", "tone": "amigavel"}, (
        "ai_persona deve ser passado exatamente como retornado por get_ai_persona"
    )


@pytest.mark.asyncio
async def test_voice_prompt_consumes_lia_field_toggles():
    """F-11: build_company_agent_context deve ser chamado com company_id + db + job_context."""
    from app.shared.prompts.voice_system_prompt import build_voice_system_prompt

    db_mock = AsyncMock()
    job_ctx = {"title": "Senior Backend", "department": "tech"}

    ctx_mock = AsyncMock(return_value="LIA-FIELD-FILTERED-CTX")

    with patch(
        "app.shared.prompts.voice_system_prompt.build_company_agent_context",
        new=ctx_mock,
    ), patch(
        "app.shared.prompts.voice_system_prompt.SystemPromptBuilder.build",
        return_value="P",
    ), patch(
        "app.shared.prompts.voice_system_prompt.get_ai_persona",
        new=AsyncMock(return_value={"name": "LIA", "tone": "profissional"}),
    ):
        await build_voice_system_prompt(
            company_id="company-uuid",
            db=db_mock,
            job_context=job_ctx,
        )

    ctx_mock.assert_awaited_once_with(
        company_id="company-uuid",
        db=db_mock,
        job_context=job_ctx,
    )


@pytest.mark.asyncio
async def test_voice_specific_instructions_appended():
    """F-10: voice-specific guidance (frases curtas, sem markdown) deve aparecer."""
    from app.shared.prompts.voice_system_prompt import build_voice_system_prompt

    db_mock = AsyncMock()

    captured = {}

    def _capture(**kwargs):
        captured.update(kwargs)
        return "PROMPT_OUT"

    with patch(
        "app.shared.prompts.voice_system_prompt.SystemPromptBuilder.build",
        side_effect=_capture,
    ), patch(
        "app.shared.prompts.voice_system_prompt.build_company_agent_context",
        new=AsyncMock(return_value=""),
    ), patch(
        "app.shared.prompts.voice_system_prompt.get_ai_persona",
        new=AsyncMock(return_value={"name": "LIA", "tone": "profissional"}),
    ):
        await build_voice_system_prompt(
            company_id="company-uuid",
            db=db_mock,
        )

    extra = captured.get("extra_instructions", "")
    assert "voz" in extra.lower() or "audio" in extra.lower() or "áudio" in extra.lower(), (
        "extra_instructions deve mencionar guidance de voz"
    )
    # frases curtas / sem markdown:
    assert "frases curtas" in extra.lower() or "sem markdown" in extra.lower() or "max" in extra.lower(), (
        "Voice-specific guidance must include short-sentence or no-markdown directive"
    )


@pytest.mark.asyncio
async def test_persona_failure_falls_back_gracefully():
    """F-10: se get_ai_persona falhar, NÃO deve crashar — fallback canonical default."""
    from app.shared.prompts.voice_system_prompt import build_voice_system_prompt

    db_mock = AsyncMock()

    async def _fail(*args, **kwargs):
        raise RuntimeError("persona service down")

    with patch(
        "app.shared.prompts.voice_system_prompt.SystemPromptBuilder.build",
        return_value="FALLBACK_PROMPT",
    ), patch(
        "app.shared.prompts.voice_system_prompt.build_company_agent_context",
        new=AsyncMock(return_value=""),
    ), patch(
        "app.shared.prompts.voice_system_prompt.get_ai_persona",
        side_effect=_fail,
    ):
        # Should not raise
        result = await build_voice_system_prompt(
            company_id="company-uuid",
            db=db_mock,
        )

    assert isinstance(result, str)
    assert len(result) > 0
