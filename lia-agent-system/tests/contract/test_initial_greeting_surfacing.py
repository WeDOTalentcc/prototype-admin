"""C.3 contract: initial_greeting surfacing canonical.

Workstream C ticket 3 (2026-05-23).

Audit doc requested "agent talks first" — LIA must surface a greeting
immediately after voice session bootstrap (not wait for first inbound
audio). Canonical approach: after _on_session_initiated, orchestrator
calls _plugin_next_question on the empty-transcript bootstrap turn and
caches the result in session.metadata["initial_greeting"]. Downstream
consumers (frontend, Twilio TwiML callback, /voice/initiate response)
can render this without making a round trip.

Pins:
  1. After initiate_voip_session w/ StudioVoicePlugin → session.metadata
     contains "initial_greeting" key (non-empty string).
  2. initial_greeting matches plugin.get_next_question's first-turn output.
  3. Without plugins → metadata has no initial_greeting (no fallback noise).
  4. _invoke_voice on Studio runtime returns initial_greeting in its
     metadata.initial_greeting for new session bootstrap.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime
from app.domains.voice.plugins.studio_voice_plugin import StudioVoicePlugin
from app.domains.voice.services.voice_screening_orchestrator import (
    VoiceCoreOrchestrator,
    VoiceScreeningSession,
)


def _make_runtime(company_id: str = "company-uuid-c3") -> CustomAgentRuntime:
    return CustomAgentRuntime(
        agent_id="agent-c3-1",
        agent_name="C3GreetingTestAgent",
        system_prompt="You are LIA, conducting a voice screening.",
        allowed_tools=[],
        domain="custom",
        company_id=company_id,
        initial_greeting="Olá! Vamos conversar sobre a vaga de Backend.",
    )


# ----------------------------------------------------------------------------
# Plugin-side first-turn greeting contract
# ----------------------------------------------------------------------------

class TestStudioPluginInitialGreeting:
    @pytest.mark.asyncio
    async def test_plugin_returns_configured_greeting_on_first_turn(self):
        """C.3: StudioVoicePlugin.get_next_question returns initial_greeting
        when session has no transcript segments yet."""
        plugin = StudioVoicePlugin(
            agent_id="agent-c3-1",
            agent_config={
                "initial_greeting": "Olá! Vamos conversar.",
                "description": "Vaga de Backend",
                "allowed_tools": [],
                "system_prompt": "prompt",
            },
            company_id="company-uuid-c3",
        )
        session = VoiceScreeningSession(
            session_id="s-c3-1",
            candidate_id="c-1",
            candidate_name="C",
            job_title="Backend",
            company_id="company-uuid-c3",
            phone_number="+5511999999999",
        )
        # transcript_segments defaults to []
        result = await plugin.get_next_question(session, db=None)
        assert result == "Olá! Vamos conversar."

    @pytest.mark.asyncio
    async def test_plugin_skips_greeting_after_first_turn(self):
        """C.3: after first turn (transcript non-empty), get_next_question → None
        so core LLM owns the conversation."""
        plugin = StudioVoicePlugin(
            agent_id="agent-c3-1",
            agent_config={"initial_greeting": "Olá!"},
            company_id="company-uuid-c3",
        )
        session = VoiceScreeningSession(
            session_id="s-c3-2",
            candidate_id="c-2",
            candidate_name="C",
            job_title="Backend",
            company_id="company-uuid-c3",
            phone_number="+5511999999999",
        )
        session.transcript_segments.append({"speaker": "candidate", "text": "Olá!"})
        result = await plugin.get_next_question(session, db=None)
        assert result is None


# ----------------------------------------------------------------------------
# Orchestrator surfacing contract — session.metadata["initial_greeting"]
# ----------------------------------------------------------------------------

class TestOrchestratorSurfacesGreeting:
    @pytest.mark.asyncio
    async def test_session_metadata_contains_initial_greeting_post_init(self):
        """C.3: after _on_session_initiated, session.metadata["initial_greeting"]
        is populated from _plugin_next_question (StudioVoicePlugin path)."""
        plugin = StudioVoicePlugin(
            agent_id="agent-c3-2",
            agent_config={"initial_greeting": "Olá, eu sou a LIA!"},
            company_id="company-uuid-c3",
        )
        # Use AsyncMock so on_session_initiated audit calls do not block.
        plugin.on_session_initiated = AsyncMock(return_value=None)

        orch = VoiceCoreOrchestrator(plugins=[plugin])
        session = VoiceScreeningSession(
            session_id="s-c3-3",
            candidate_id="c-3",
            candidate_name="C",
            job_title="Backend",
            company_id="company-uuid-c3",
            phone_number="+5511999999999",
        )

        # Internally orchestrator must call _on_session_initiated which fans out
        # plugin hooks + populate metadata. We invoke directly.
        await orch._on_session_initiated(session, db=None)

        assert session.metadata.get("initial_greeting") == "Olá, eu sou a LIA!", (
            f"C.3: session.metadata.initial_greeting must be populated after "
            f"_on_session_initiated. Got: {session.metadata!r}"
        )

    @pytest.mark.asyncio
    async def test_no_plugins_means_no_initial_greeting_key(self):
        """C.3: orchestrator with zero plugins → no initial_greeting key in
        metadata (avoid surfacing noise)."""
        orch = VoiceCoreOrchestrator(plugins=[])
        session = VoiceScreeningSession(
            session_id="s-c3-4",
            candidate_id="c-4",
            candidate_name="C",
            job_title="Backend",
            company_id="company-uuid-c3",
            phone_number="+5511999999999",
        )
        await orch._on_session_initiated(session, db=None)
        assert "initial_greeting" not in session.metadata, (
            f"C.3: without plugins, no initial_greeting should be inserted. "
            f"Got: {session.metadata!r}"
        )


# ----------------------------------------------------------------------------
# Runtime-side surfacing — _invoke_voice returns initial_greeting in metadata
# ----------------------------------------------------------------------------

class TestRuntimeSurfacesGreeting:
    @pytest.mark.asyncio
    async def test_invoke_voice_returns_initial_greeting_in_metadata(self):
        """C.3: CustomAgentRuntime._invoke_voice on session bootstrap returns
        metadata.initial_greeting (from session.metadata) for frontend UX."""
        runtime = _make_runtime()

        # Build fake orchestrator that mimics post-_on_session_initiated state.
        fake_session = MagicMock()
        fake_session.session_id = "s-bootstrap-1"
        fake_session.call_sid = None
        fake_session.status = "ready"
        fake_session.voice_provider = "twilio"
        fake_session.metadata = {"initial_greeting": "Olá! Sou a LIA."}

        orch = MagicMock()
        orch.initiate_voip_session = AsyncMock(return_value=fake_session)

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
            return_value=orch,
        ), patch(
            "app.core.feature_flags.is_enabled", return_value=True
        ):
            out = await runtime.execute(
                message="",
                user_id="user-1",
                session_id="sess-bootstrap",
                channel="voice",
                audio_chunk=b"\xff" * 200,  # passes "no_payload" guard
                voice_session_id=None,  # bootstrap path
            )

        assert out.metadata.get("initial_greeting") == "Olá! Sou a LIA.", (
            f"C.3: _invoke_voice must surface session.metadata.initial_greeting "
            f"in AgentOutput.metadata so frontend can render 'agent talks first' "
            f"UX. Got: {out.metadata!r}"
        )
