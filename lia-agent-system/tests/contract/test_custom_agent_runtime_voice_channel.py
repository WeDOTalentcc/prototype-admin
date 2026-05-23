"""
Sprint 3.5 W4-1 V2 — CustomAgentRuntime channel="voice" contract tests.

Pins canonical channel routing in Agent Studio custom agent runtime:

* execute() accepts ``channel`` keyword-only param (default "chat")
* channel="chat" path is unaffected by Sprint 3.5 changes (regression sentinel)
* channel="voice" gated by ``voice_screening_v2_enabled`` feature flag (per-tenant)
* channel="voice" requires audio_chunk or voice_session_id
* Multi-tenancy fail-closed: voice without company_id is rejected
* _invoke_voice instantiates VoiceCoreOrchestrator (Sprint 3.2 canonical core)
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _make_runtime(company_id: str = "company-uuid-1") -> CustomAgentRuntime:
    return CustomAgentRuntime(
        agent_id="agent-voice-1",
        agent_name="VoiceTestAgent",
        system_prompt="You are a helpful assistant.",
        allowed_tools=[],
        domain="custom",
        company_id=company_id,
    )


# ----------------------------------------------------------------------------
# Signature contract — execute() accepts channel kwarg
# ----------------------------------------------------------------------------

class TestExecuteSignature:
    def test_channel_param_keyword_only_default_in_app(self):
        """W-Channels-A (2026-05-23): canonical default mudou de "chat" para "in_app".

        Backward compat coberta em test_channel_coherence_4_channels.py
        ::TestChatAliasBackwardCompat — channel="chat" continua aceito como
        alias com DeprecationWarning.
        """
        import inspect
        sig = inspect.signature(CustomAgentRuntime.execute)
        assert "channel" in sig.parameters
        p = sig.parameters["channel"]
        assert p.kind.name == "KEYWORD_ONLY"
        assert p.default == "in_app", (
            "Default canonical é 'in_app' desde W-Channels-A. "
            "Se mudou para outro valor, revisar testes de backward compat."
        )

    def test_audio_chunk_and_voice_session_id_accepted(self):
        import inspect
        sig = inspect.signature(CustomAgentRuntime.execute)
        assert "audio_chunk" in sig.parameters
        assert "voice_session_id" in sig.parameters


# ----------------------------------------------------------------------------
# channel="chat" — regression sentinel: existing path untouched
# ----------------------------------------------------------------------------

class TestChatPathUnaffected:
    @pytest.mark.asyncio
    async def test_chat_path_does_not_call_invoke_voice(self):
        """Sprint 3.5 regression sentinel: channel="chat" (default) NEVER hits
        the voice handler. Adding voice routing must not regress text agents."""
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_invoke_voice", new_callable=AsyncMock
        ) as mock_voice, patch.object(
            CustomAgentRuntime, "_process_langgraph", new_callable=AsyncMock
        ) as mock_chat:
            from lia_agents_core.agent_interface import AgentOutput
            mock_chat.return_value = AgentOutput(message="ok", confidence=1.0, metadata={})

            await runtime.execute(
                message="hello",
                user_id="u1",
                company_id="company-uuid-1",
                session_id="s1",
            )

            mock_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_channel_chat_explicit_does_not_call_voice(self):
        runtime = _make_runtime()
        with patch.object(
            CustomAgentRuntime, "_invoke_voice", new_callable=AsyncMock
        ) as mock_voice, patch.object(
            CustomAgentRuntime, "_process_langgraph", new_callable=AsyncMock
        ) as mock_chat:
            from lia_agents_core.agent_interface import AgentOutput
            mock_chat.return_value = AgentOutput(message="ok", confidence=1.0, metadata={})

            await runtime.execute(message="hello", company_id="c-1", channel="chat")

            mock_voice.assert_not_called()


# ----------------------------------------------------------------------------
# channel="voice" — feature flag gate
# ----------------------------------------------------------------------------

class TestVoiceFeatureFlagGate:
    @pytest.mark.asyncio
    async def test_voice_disabled_returns_feature_not_enabled(self, monkeypatch):
        """Default DEFAULT_FLAGS['voice_screening_v2_enabled'] = False — gated off."""
        monkeypatch.delenv(
            "FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", raising=False,
        )
        monkeypatch.delenv(
            "FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED__company-uuid-1", raising=False,
        )

        runtime = _make_runtime()
        result = await runtime.execute(
            message="",
            company_id="company-uuid-1",
            channel="voice",
            audio_chunk=b"\x00\x01\x02",
        )

        assert result.metadata.get("status") == "feature_not_enabled"
        assert result.metadata.get("flag") == "voice_screening_v2_enabled"
        assert result.metadata.get("channel") == "voice"

    @pytest.mark.asyncio
    async def test_voice_enabled_via_env_calls_voice_handler(self, monkeypatch):
        """Env override FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED=1 flips the gate ON."""
        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "1")

        runtime = _make_runtime()
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            # Sprint 3.6: orchestrator must expose initiate_voip_session because
            # audio_chunk-only (no voice_session_id) routes to VoIP bootstrap.
            MockOrchestrator.return_value = MagicMock(
                initiate_voip_session=AsyncMock(return_value=MagicMock(
                    session_id="sess-x", status="initiated",
                    voice_provider="gemini_live", call_sid=None,
                )),
            )
            result = await runtime.execute(
                message="",
                company_id="company-uuid-1",
                channel="voice",
                audio_chunk=b"\x00\x01\x02\x03",
            )

        # Voice handler reached → orchestrator was constructed
        MockOrchestrator.assert_called_once()
        # Sprint 3.5 baseline metadata (preserved post-3.6)
        assert result.metadata.get("channel") == "voice"
        assert result.metadata.get("orchestrator_ready") is True
        assert result.metadata.get("has_audio_chunk") is True
        assert result.metadata.get("audio_chunk_bytes") == 4

    @pytest.mark.asyncio
    async def test_voice_per_tenant_override(self, monkeypatch):
        """Per-tenant env override beats global."""
        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "0")
        monkeypatch.setenv(
            "FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED__company-uuid-1", "1",
        )

        runtime = _make_runtime()
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            MockOrchestrator.return_value = MagicMock(
                initiate_voip_session=AsyncMock(return_value=MagicMock(
                    session_id="sess-x", status="initiated",
                    voice_provider="gemini_live", call_sid=None,
                )),
            )
            result = await runtime.execute(
                message="",
                company_id="company-uuid-1",
                channel="voice",
                audio_chunk=b"\xff",
            )

        assert result.metadata.get("orchestrator_ready") is True


# ----------------------------------------------------------------------------
# channel="voice" — multi-tenancy + payload checks
# ----------------------------------------------------------------------------

class TestVoiceMultiTenancy:
    @pytest.mark.asyncio
    async def test_voice_requires_company_id(self, monkeypatch):
        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "1")

        # No company_id passed AND construct runtime with empty company_id
        runtime = CustomAgentRuntime(
            agent_id="agent-x",
            agent_name="X",
            system_prompt="p",
            allowed_tools=[],
            company_id="",
        )

        result = await runtime.execute(
            message="",
            company_id="",
            channel="voice",
            audio_chunk=b"\x00",
        )

        assert result.metadata.get("error") == "voice_missing_company_id"
        assert result.metadata.get("channel") == "voice"


class TestVoicePayloadValidation:
    @pytest.mark.asyncio
    async def test_voice_requires_audio_or_session_id(self, monkeypatch):
        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "1")

        runtime = _make_runtime()
        result = await runtime.execute(
            message="",
            company_id="company-uuid-1",
            channel="voice",
            audio_chunk=None,
            voice_session_id=None,
        )

        assert result.metadata.get("error") == "voice_no_payload"

    @pytest.mark.asyncio
    async def test_voice_with_session_id_only_proceeds(self, monkeypatch):
        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "1")

        runtime = _make_runtime()
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            # Sprint 3.6: voice_session_id-only path returns directly with
            # session metadata; no audio_chunk → no audio processing.
            MockOrchestrator.return_value = MagicMock()
            result = await runtime.execute(
                message="",
                company_id="company-uuid-1",
                channel="voice",
                voice_session_id="sess-ongoing-1",
            )

        assert result.metadata.get("orchestrator_ready") is True
        assert result.metadata.get("voice_session_id") == "sess-ongoing-1"
        assert result.metadata.get("has_audio_chunk") is False


# ----------------------------------------------------------------------------
# Architectural — _invoke_voice uses VoiceCoreOrchestrator
# ----------------------------------------------------------------------------

class TestVoiceHandlerArchitectural:
    @pytest.mark.asyncio
    async def test_invoke_voice_uses_voice_core_orchestrator(self, monkeypatch):
        """Sprint 3.6: _invoke_voice instantiates VoiceCoreOrchestrator with
        exactly one StudioVoicePlugin (Sprint 3.5 baseline upgraded — no longer
        an empty plugins list)."""
        from app.domains.voice.plugins.studio_voice_plugin import StudioVoicePlugin

        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "1")

        runtime = _make_runtime()
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            MockOrchestrator.return_value = MagicMock(
                initiate_voip_session=AsyncMock(return_value=MagicMock(
                    session_id="sess-x", status="initiated",
                    voice_provider="gemini_live", call_sid=None,
                )),
            )
            await runtime.execute(
                message="",
                company_id="company-uuid-1",
                channel="voice",
                audio_chunk=b"\x01",
            )
            MockOrchestrator.assert_called_once()
            kwargs = MockOrchestrator.call_args.kwargs
            assert "plugins" in kwargs
            plugins = kwargs["plugins"]
            assert len(plugins) == 1
            assert isinstance(plugins[0], StudioVoicePlugin)

    def test_invoke_voice_does_not_use_legacy_subclass(self):
        """Source sentinel: _invoke_voice must NOT instantiate the WSI-bound
        legacy subclass VoiceScreeningOrchestrator. Use VoiceCoreOrchestrator
        + plugins."""
        import inspect
        from app.domains.agent_studio import custom_agent_runtime as mod
        src = inspect.getsource(mod._invoke_voice if False else CustomAgentRuntime._invoke_voice)
        assert "VoiceCoreOrchestrator" in src
        assert "VoiceScreeningOrchestrator(" not in src
