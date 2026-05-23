"""
W-Channels-A · 4-channel coherence contract tests (registered 2026-05-23).

Sensores canonical para a decisão Paulo (Opção B):
- 4 canais independentes: in_app, whatsapp, voice (PSTN), voip
- channel="chat" continua aceito como alias legacy → DeprecationWarning + roteia in_app
- Voice e VoIP têm flags separadas (voice_enabled vs voip_enabled)
- Migration 183 adiciona voip_enabled + in_app_enabled

Refs:
- alembic/versions/183_custom_agent_channel_columns.py
- app/domains/agent_studio/custom_agent_runtime.py
- app/api/v1/agent_studio_channels.py
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
# Migration sentinel — columns must exist
# ----------------------------------------------------------------------------

class TestMigration183Columns:
    @pytest.mark.asyncio
    async def test_migration_adds_voip_and_in_app_columns(self):
        """Migration 183 must add voip_enabled + in_app_enabled to custom_agents."""
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text(
                    """
                    SELECT column_name, column_default, is_nullable
                    FROM information_schema.columns
                    WHERE table_name='custom_agents'
                      AND column_name IN ('voip_enabled', 'in_app_enabled')
                    ORDER BY column_name
                    """
                )
            )
            rows = list(result)
            cols = {row[0]: (row[1], row[2]) for row in rows}

        assert "voip_enabled" in cols, "voip_enabled column missing — migration 183 not applied"
        assert "in_app_enabled" in cols, "in_app_enabled column missing — migration 183 not applied"
        # Default values per ADR
        assert "false" in (cols["voip_enabled"][0] or "").lower()
        assert "true" in (cols["in_app_enabled"][0] or "").lower()


# ----------------------------------------------------------------------------
# Signature contract — execute() accepts 5 channels canonical
# ----------------------------------------------------------------------------

class TestExecuteSignatureUpdated:
    def test_channel_default_is_in_app(self):
        import inspect
        sig = inspect.signature(CustomAgentRuntime.execute)
        assert sig.parameters["channel"].default == "in_app"

    def test_channel_literal_includes_voip_and_in_app(self):
        """Type annotation must include all 4 canonical channels + chat alias."""
        import inspect
        sig = inspect.signature(CustomAgentRuntime.execute)
        annotation = sig.parameters["channel"].annotation
        # str(annotation) contains literal values in any modern Python
        ann_str = str(annotation)
        for ch in ("in_app", "chat", "voice", "voip", "whatsapp"):
            assert ch in ann_str, f"channel literal missing '{ch}': {ann_str}"


# ----------------------------------------------------------------------------
# Backward compat — channel="chat" still works (alias to in_app)
# ----------------------------------------------------------------------------

class TestChatAliasBackwardCompat:
    @pytest.mark.asyncio
    async def test_chat_alias_does_not_call_voice(self):
        """channel='chat' (legacy) MUST NOT hit voice handler — same as in_app."""
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_invoke_voice", new_callable=AsyncMock
        ) as mock_voice, patch.object(
            CustomAgentRuntime, "_process_langgraph", new_callable=AsyncMock
        ) as mock_chat:
            from lia_agents_core.agent_interface import AgentOutput
            mock_chat.return_value = AgentOutput(message="ok", confidence=1.0, metadata={})

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                await runtime.execute(message="hi", company_id="c-1", channel="chat")
            mock_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_alias_emits_deprecation_warning(self):
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_process_langgraph", new_callable=AsyncMock
        ) as mock_chat:
            from lia_agents_core.agent_interface import AgentOutput
            mock_chat.return_value = AgentOutput(message="ok", confidence=1.0, metadata={})

            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                await runtime.execute(message="hi", company_id="c-1", channel="chat")

            deprecation_messages = [str(w.message) for w in captured if issubclass(w.category, DeprecationWarning)]
            assert any("chat" in m and "in_app" in m for m in deprecation_messages), (
                f"Expected DeprecationWarning mentioning chat→in_app; got: {deprecation_messages}"
            )


# ----------------------------------------------------------------------------
# Canonical channel — in_app
# ----------------------------------------------------------------------------

class TestInAppCanonical:
    @pytest.mark.asyncio
    async def test_in_app_routes_to_langgraph_not_voice(self):
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_invoke_voice", new_callable=AsyncMock
        ) as mock_voice, patch.object(
            CustomAgentRuntime, "_process_langgraph", new_callable=AsyncMock
        ) as mock_chat, patch.object(
            CustomAgentRuntime, "_invoke_whatsapp", new_callable=AsyncMock
        ) as mock_wa:
            from lia_agents_core.agent_interface import AgentOutput
            mock_chat.return_value = AgentOutput(message="ok", confidence=1.0, metadata={})

            await runtime.execute(message="hi", company_id="c-1", channel="in_app")

            mock_voice.assert_not_called()
            mock_wa.assert_not_called()
            mock_chat.assert_called_once()


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
                context={"voice_mode": "voip"},  # caller override
            )
            kwargs = mock_voice.call_args.kwargs
            # setdefault preserved caller value
            assert kwargs["context"]["voice_mode"] == "voip"


# ----------------------------------------------------------------------------
# 4 channels independent — REST gate semantics
# ----------------------------------------------------------------------------

class TestPerAgentFlagsAreIndependent:
    """The 4 toggles on CustomAgent must be independent columns.

    This is a *DB schema* + *model contract* test — no FastAPI client needed.
    """

    @pytest.mark.asyncio
    async def test_can_persist_all_4_combinations_independently(self):
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            # Verify schema has 4 distinct boolean columns
            result = await db.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name='custom_agents'
                      AND column_name IN (
                        'voice_enabled', 'voip_enabled',
                        'in_app_enabled', 'whatsapp_enabled'
                      )
                    """
                )
            )
            cols = {row[0] for row in result}

        expected = {"voice_enabled", "voip_enabled", "in_app_enabled", "whatsapp_enabled"}
        assert cols == expected, (
            f"All 4 channel columns must exist as independent toggles. Got: {cols}"
        )

    def test_model_to_dict_exposes_all_4_flags(self):
        """CustomAgent.to_dict must surface the 4 canonical channel flags."""
        from lia_models.custom_agent import CustomAgent

        # Synthetic in-memory instance (no DB write needed)
        agent = CustomAgent(
            name="t",
            company_id="c-1",
            system_prompt="x",
            allowed_tools=[],
            domain="custom",
        )
        agent.voice_enabled = True
        agent.voip_enabled = False
        agent.in_app_enabled = True
        agent.whatsapp_enabled = False

        d = agent.to_dict()
        assert d["voice_enabled"] is True
        assert d["voip_enabled"] is False
        assert d["in_app_enabled"] is True
        assert d["whatsapp_enabled"] is False


# ----------------------------------------------------------------------------
# In_app default semantics — backward compat for existing rows
# ----------------------------------------------------------------------------

class TestInAppDefaultTrue:
    def test_in_app_enabled_defaults_true_when_attr_missing(self):
        """ORM default + to_dict fallback: in_app_enabled True when None."""
        from lia_models.custom_agent import CustomAgent

        agent = CustomAgent(
            name="t",
            company_id="c-1",
            system_prompt="x",
            allowed_tools=[],
            domain="custom",
        )
        # Don't set in_app_enabled explicitly; to_dict must fallback to True.
        d = agent.to_dict()
        assert d["in_app_enabled"] is True, (
            "in_app_enabled default must be True (backward compat with rows "
            "predating migration 183)"
        )
