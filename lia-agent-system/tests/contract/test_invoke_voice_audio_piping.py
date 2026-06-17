"""C.1 contract: _invoke_voice canonical audio piping (Workstream C ticket 1).

Pins canonical behavior of CustomAgentRuntime._invoke_voice when resuming
voice session with audio_chunk:

  1. process_audio_chunk(session_id, audio_data) is called.
  2. When transcript text is returned, generate_lia_response is called.
  3. When transcript is empty/None, generate_lia_response is NOT called.
  4. Response text from generate_lia_response is surfaced in AgentOutput.message.
  5. Metadata exposes `transcribed` and `lia_response` fields.

Sister test of test_custom_agent_runtime_voice_channel.py; covers the
exact piping seam between Studio runtime and VoiceCoreOrchestrator that
Sprint 3.6 introduced.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime


def _make_runtime(company_id: str = "company-uuid-1") -> CustomAgentRuntime:
    return CustomAgentRuntime(
        agent_id="agent-voice-pipe-1",
        agent_name="VoicePipingTestAgent",
        system_prompt="You are a helpful screening agent.",
        allowed_tools=[],
        domain="custom",
        company_id=company_id,
    )


# ----------------------------------------------------------------------------
# Audio piping contract — C.1
# ----------------------------------------------------------------------------

class TestVoiceAudioPipingContract:
    """Pin canonical audio chunk → transcript → LIA response flow."""

    @pytest.mark.asyncio
    async def test_resume_with_audio_calls_process_chunk(self):
        """C.1: voice_session_id + audio_chunk → orchestrator.process_audio_chunk called."""
        runtime = _make_runtime()
        orch = MagicMock()
        orch.process_audio_chunk = AsyncMock(return_value="Olá tudo bem")
        orch.generate_lia_response = AsyncMock(return_value="Oi! Como vai?")

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
            return_value=orch,
        ), patch(
            "app.core.feature_flags.is_enabled", return_value=True
        ):
            out = await runtime.execute(
                message="",
                user_id="user-1",
                session_id="sess-x",
                channel="voice",
                audio_chunk=b"\xff" * 200,
                voice_session_id="vs-1",
            )

        orch.process_audio_chunk.assert_awaited_once()
        kwargs = orch.process_audio_chunk.call_args.kwargs
        assert kwargs.get("session_id") == "vs-1"
        assert kwargs.get("audio_data") == b"\xff" * 200
        # status must reflect resume path
        assert out.metadata.get("status") == "session_resumed"

    @pytest.mark.asyncio
    async def test_transcript_text_used_in_generate_response(self):
        """C.1: transcript string → generate_lia_response receives it as candidate_utterance."""
        runtime = _make_runtime()
        orch = MagicMock()
        orch.process_audio_chunk = AsyncMock(return_value="Quero saber sobre a vaga")
        orch.generate_lia_response = AsyncMock(return_value="Claro! Posso te contar.")

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
            return_value=orch,
        ), patch(
            "app.core.feature_flags.is_enabled", return_value=True
        ):
            await runtime.execute(
                message="",
                user_id="user-1",
                session_id="sess-y",
                channel="voice",
                audio_chunk=b"\xab" * 200,
                voice_session_id="vs-2",
            )

        orch.generate_lia_response.assert_awaited_once()
        kwargs = orch.generate_lia_response.call_args.kwargs
        assert kwargs.get("session_id") == "vs-2"
        assert kwargs.get("candidate_utterance") == "Quero saber sobre a vaga"

    @pytest.mark.asyncio
    async def test_empty_transcript_does_not_call_generate(self):
        """C.1: process_audio_chunk returns None/empty → generate_lia_response NOT called."""
        runtime = _make_runtime()
        orch = MagicMock()
        orch.process_audio_chunk = AsyncMock(return_value=None)
        orch.generate_lia_response = AsyncMock(return_value="should-not-be-called")

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
            return_value=orch,
        ), patch(
            "app.core.feature_flags.is_enabled", return_value=True
        ):
            out = await runtime.execute(
                message="",
                user_id="user-1",
                session_id="sess-z",
                channel="voice",
                audio_chunk=b"\xcd" * 200,
                voice_session_id="vs-3",
            )

        orch.process_audio_chunk.assert_awaited_once()
        orch.generate_lia_response.assert_not_awaited()
        # Message must still be a valid string (bootstrap-acknowledge fallback)
        assert isinstance(out.message, str)
        assert out.metadata.get("transcribed") is None
        assert out.metadata.get("lia_response") is None

    @pytest.mark.asyncio
    async def test_response_text_returned_in_message_field(self):
        """C.1: AgentOutput.message contains generate_lia_response result text."""
        runtime = _make_runtime()
        orch = MagicMock()
        orch.process_audio_chunk = AsyncMock(return_value="Hi")
        orch.generate_lia_response = AsyncMock(
            return_value="Olá! Bem-vindo à triagem de voz."
        )

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
            return_value=orch,
        ), patch(
            "app.core.feature_flags.is_enabled", return_value=True
        ):
            out = await runtime.execute(
                message="",
                user_id="user-1",
                session_id="sess-w",
                channel="voice",
                audio_chunk=b"\x01" * 200,
                voice_session_id="vs-4",
            )

        assert out.message == "Olá! Bem-vindo à triagem de voz."

    @pytest.mark.asyncio
    async def test_metadata_includes_transcribed_field(self):
        """C.1: AgentOutput.metadata exposes 'transcribed' + 'lia_response' for observability."""
        runtime = _make_runtime()
        orch = MagicMock()
        orch.process_audio_chunk = AsyncMock(return_value="Tudo certo")
        orch.generate_lia_response = AsyncMock(return_value="Ótimo!")

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
            return_value=orch,
        ), patch(
            "app.core.feature_flags.is_enabled", return_value=True
        ):
            out = await runtime.execute(
                message="",
                user_id="user-1",
                session_id="sess-v",
                channel="voice",
                audio_chunk=b"\x02" * 200,
                voice_session_id="vs-5",
            )

        assert out.metadata.get("transcribed") == "Tudo certo"
        assert out.metadata.get("lia_response") == "Ótimo!"
        # Sanity: surface the agent and session identifiers too.
        assert out.metadata.get("voice_session_id") == "vs-5"
        assert out.metadata.get("channel") == "voice"
