"""
W-Channels-A · 3-channel coherence contract tests (revised 2026-05-23).

Sensores canonical para a decisão Paulo (Opção B revisada):

NOTA HISTÓRICA: este arquivo originalmente cobria 4 canais (incluindo
``in_app``). Audit AUDIT_CANDIDATE_CHAT_PUBLIC_2026-05-23.md descobriu que
``in_app`` era gap conceitual — "chat web" entre os 4 canais que Paulo quer
= chat candidato público (já existe em /api/v1/triagem/), NÃO chat lateral
recrutador interno. Migration 186 dropou in_app_enabled.

Canais canonical atuais (3 independentes):
- whatsapp_enabled         — canal WhatsApp
- voice_enabled            — ligação telefônica PSTN
- voip_enabled             — voz no navegador (Twilio VoIP SDK + Gemini Live)

CustomAgentRuntime.execute aceita 4 valores no Literal:
- "text" (default)         — text-only langgraph (uso interno: deployments,
                             test fixtures, marketplace, etc.)
- "voice" / "voip"         — _invoke_voice com voice_mode hint
- "whatsapp"               — _invoke_whatsapp

Aliases legacy "chat" e "in_app" são aceitos via DeprecationWarning → "text".

Refs:
- alembic/versions/186_revert_in_app_enabled.py (DROP COLUMN)
- alembic/versions/183_custom_agent_channel_columns.py (mantém voip_enabled)
- app/domains/agent_studio/custom_agent_runtime.py
- app/api/v1/agent_studio_channels.py (voip endpoint only)
- app/api/v1/agent_studio_voice.py (mode-aware flag gate)
"""
from __future__ import annotations

import warnings
from unittest.mock import AsyncMock, patch

import pytest

from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _make_runtime(company_id: str = "company-uuid-1") -> CustomAgentRuntime:
    return CustomAgentRuntime(
        agent_id="agent-channel-1",
        agent_name="ChannelTestAgent",
        system_prompt="You are a helpful assistant.",
        allowed_tools=[],
        domain="custom",
        company_id=company_id,
    )


# ----------------------------------------------------------------------------
# Migration sentinels — verified manually in dev DB; test DB has no migrations.
# ----------------------------------------------------------------------------
# NOTA (2026-05-23): tests que tocavam information_schema foram removidos pq
# test DB sandbox não tem alembic upgrade aplicado. Verificação manual no dev DB:
#   alembic upgrade head → 186_revert_in_app_enabled
#   SELECT column_name FROM information_schema.columns
#     WHERE table_name='custom_agents' AND column_name='in_app_enabled';
#   → 0 linhas (esperado pós-revert)
# Pre-existing test (4-channel original) já falhava pelo mesmo motivo.


# ----------------------------------------------------------------------------
# Signature contract — execute() default = "text", 4 channels in Literal
# ----------------------------------------------------------------------------

class TestExecuteSignatureUpdated:
    def test_channel_default_is_text(self):
        import inspect
        sig = inspect.signature(CustomAgentRuntime.execute)
        assert sig.parameters["channel"].default == "text"

    def test_channel_literal_contains_canonical_4(self):
        """Type annotation must include text + voice + voip + whatsapp."""
        import inspect
        sig = inspect.signature(CustomAgentRuntime.execute)
        annotation = sig.parameters["channel"].annotation
        ann_str = str(annotation)
        for ch in ("text", "voice", "voip", "whatsapp"):
            assert ch in ann_str, f"channel literal missing '{ch}': {ann_str}"

    def test_channel_literal_does_not_contain_in_app(self):
        """in_app must NOT be in Literal anymore (revert 2026-05-23)."""
        import inspect
        sig = inspect.signature(CustomAgentRuntime.execute)
        annotation = sig.parameters["channel"].annotation
        ann_str = str(annotation)
        # Note: still allowed as runtime alias via DeprecationWarning,
        # but not part of the typed contract.
        # Sanity check: "in_app" can appear in default-value-of-other-field?
        # No — only checking Literal[...]. Use regex precision:
        import re
        # Find the Literal arguments
        m = re.search(r"Literal\[([^\]]+)\]", ann_str)
        assert m, f"channel annotation is not Literal: {ann_str}"
        literal_args = m.group(1)
        assert "in_app" not in literal_args, (
            f"'in_app' must not be in Literal contract: {literal_args}"
        )


# ----------------------------------------------------------------------------
# Backward compat — channel="chat" and channel="in_app" still work via deprecation
# ----------------------------------------------------------------------------

class TestLegacyAliasBackwardCompat:
    @pytest.mark.asyncio
    async def test_chat_alias_emits_deprecation_and_routes_text(self):
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_process_langgraph", new_callable=AsyncMock
        ) as mock_text, patch.object(
            CustomAgentRuntime, "_invoke_voice", new_callable=AsyncMock
        ) as mock_voice:
            from lia_agents_core.agent_interface import AgentOutput
            mock_text.return_value = AgentOutput(message="ok", confidence=1.0, metadata={})

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                await runtime.execute(message="hi", company_id="c-1", channel="chat")

            assert any(
                issubclass(w.category, DeprecationWarning) for w in caught
            ), "channel='chat' must emit DeprecationWarning"
            mock_voice.assert_not_called()
            mock_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_in_app_alias_emits_deprecation_and_routes_text(self):
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_process_langgraph", new_callable=AsyncMock
        ) as mock_text:
            from lia_agents_core.agent_interface import AgentOutput
            mock_text.return_value = AgentOutput(message="ok", confidence=1.0, metadata={})

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                await runtime.execute(message="hi", company_id="c-1", channel="in_app")

            assert any(
                issubclass(w.category, DeprecationWarning) for w in caught
            ), "channel='in_app' must emit DeprecationWarning"
            mock_text.assert_called_once()


# ----------------------------------------------------------------------------
# Default text channel routes to langgraph (not voice, not whatsapp)
# ----------------------------------------------------------------------------

class TestTextChannelCanonical:
    @pytest.mark.asyncio
    async def test_text_routes_to_langgraph_not_voice(self):
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_invoke_voice", new_callable=AsyncMock
        ) as mock_voice, patch.object(
            CustomAgentRuntime, "_process_langgraph", new_callable=AsyncMock
        ) as mock_text, patch.object(
            CustomAgentRuntime, "_invoke_whatsapp", new_callable=AsyncMock
        ) as mock_wa:
            from lia_agents_core.agent_interface import AgentOutput
            mock_text.return_value = AgentOutput(message="ok", confidence=1.0, metadata={})

            await runtime.execute(message="hi", company_id="c-1", channel="text")

            mock_voice.assert_not_called()
            mock_wa.assert_not_called()
            mock_text.assert_called_once()


# ----------------------------------------------------------------------------
# Voice + VoIP routing — both hit _invoke_voice with voice_mode hint
# ----------------------------------------------------------------------------

class TestVoiceAndVoipRouting:
    @pytest.mark.asyncio
    async def test_channel_voice_passes_voice_mode_pstn(self):
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_invoke_voice", new_callable=AsyncMock
        ) as mock_voice:
            from lia_agents_core.agent_interface import AgentOutput
            mock_voice.return_value = AgentOutput(message="vc", confidence=1.0, metadata={})

            await runtime.execute(
                message="",
                company_id="c-1",
                channel="voice",
                audio_chunk=b"\x00",
            )
            kwargs = mock_voice.call_args.kwargs
            assert kwargs["context"]["voice_mode"] == "pstn"

    @pytest.mark.asyncio
    async def test_channel_voip_passes_voice_mode_voip(self):
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_invoke_voice", new_callable=AsyncMock
        ) as mock_voice:
            from lia_agents_core.agent_interface import AgentOutput
            mock_voice.return_value = AgentOutput(message="vp", confidence=1.0, metadata={})

            await runtime.execute(
                message="",
                company_id="c-1",
                channel="voip",
                audio_chunk=b"\x00",
            )
            kwargs = mock_voice.call_args.kwargs
            assert kwargs["context"]["voice_mode"] == "voip"

    @pytest.mark.asyncio
    async def test_channel_voice_does_not_overwrite_existing_voice_mode(self):
        """If caller passes voice_mode in context, runtime must NOT clobber it."""
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_invoke_voice", new_callable=AsyncMock
        ) as mock_voice:
            from lia_agents_core.agent_interface import AgentOutput
            mock_voice.return_value = AgentOutput(message="vc", confidence=1.0, metadata={})

            await runtime.execute(
                message="",
                company_id="c-1",
                channel="voice",
                audio_chunk=b"\x00",
                context={"voice_mode": "voip"},
            )
            kwargs = mock_voice.call_args.kwargs
            assert kwargs["context"]["voice_mode"] == "voip"


# ----------------------------------------------------------------------------
# 3 channels independent — REST gate semantics (no in_app)
# ----------------------------------------------------------------------------

class TestPerAgentFlagsAreIndependent:
    """The 3 toggles on CustomAgent must be independent columns.

    in_app_enabled was REMOVED by migration 186 (gap conceitual).
    """

    # NOTA: test_can_persist_3_channel_columns_independently removido — same DB
    # infra limitation acima. Verificação manual: \d custom_agents no dev DB.

    def test_model_to_dict_exposes_3_channel_flags(self):
        """CustomAgent.to_dict must surface the 3 canonical channel flags."""
        from lia_models.custom_agent import CustomAgent

        agent = CustomAgent(
            name="t",
            company_id="c-1",
            system_prompt="x",
            allowed_tools=[],
            domain="custom",
        )
        agent.voice_enabled = True
        agent.voip_enabled = False
        agent.whatsapp_enabled = False

        d = agent.to_dict()
        assert d["voice_enabled"] is True
        assert d["voip_enabled"] is False
        assert d["whatsapp_enabled"] is False

    def test_model_does_not_expose_in_app_enabled(self):
        """to_dict must NOT contain in_app_enabled anymore (revert)."""
        from lia_models.custom_agent import CustomAgent

        agent = CustomAgent(
            name="t",
            company_id="c-1",
            system_prompt="x",
            allowed_tools=[],
            domain="custom",
        )
        d = agent.to_dict()
        assert "in_app_enabled" not in d, (
            "in_app_enabled must not appear in to_dict — "
            "migration 186 removed the column."
        )
