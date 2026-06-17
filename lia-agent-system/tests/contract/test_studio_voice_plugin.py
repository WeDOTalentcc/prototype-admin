"""
Sprint 3.6 W4-1 V2 — StudioVoicePlugin canonical contract tests.

Pins:
- VoiceCorePlugin protocol compliance (ABC implementation)
- plugin_name == "studio_custom_agent"
- on_session_initiated: annotates session metadata + emits canonical audit row
- get_next_question: 1st turn → initial_greeting OR description-based fallback;
  subsequent turns → None (core LLM owns the conversation)
- on_session_finalized: summary via canonical llm_service + canonical billing
  via record_execution + compute_voice_credits + audit completion row
- CustomAgentRuntime._invoke_voice wires StudioVoicePlugin from agent config
- Best-effort: audit/billing failures NEVER block the voice call

Multi-tenancy: company_id is captured at plugin construction; plugin NEVER
trusts external input.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.voice.plugins.studio_voice_plugin import StudioVoicePlugin
from app.domains.voice.protocols.voice_core_plugin import VoiceCorePlugin


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _make_session(
    *,
    session_id: str = "sess-1",
    candidate_id: str = "cand-1",
    job_id: str | None = "job-1",
    company_id: str = "co-1",
    transcript_segments: list[dict[str, Any]] | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
):
    """Build a real VoiceScreeningSession dataclass instance for tests."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningSession,
    )
    return VoiceScreeningSession(
        session_id=session_id,
        candidate_id=candidate_id,
        candidate_name="João",
        job_title="Engenheiro Senior",
        company_id=company_id,
        phone_number="+5511999999999",
        job_id=job_id,
        call_sid="CA-test-1",
        status="in_progress",
        transcript_segments=transcript_segments or [],
        started_at=started_at,
        ended_at=ended_at,
    )


def _make_plugin(
    *,
    agent_id: str = "agent-uuid-1",
    company_id: str = "co-1",
    initial_greeting: str | None = None,
    description: str | None = None,
    allowed_tools: list[str] | None = None,
    pricing_tier: str = "pro",
) -> StudioVoicePlugin:
    cfg: dict[str, Any] = {
        "system_prompt": "Voce e entrevistador.",
        "allowed_tools": allowed_tools or [],
        "initial_greeting": initial_greeting,
        "description": description,
        "persona": {"name": "LIA"},
        "pricing_tier": pricing_tier,
    }
    return StudioVoicePlugin(
        agent_id=agent_id,
        agent_config=cfg,
        company_id=company_id,
    )


# ────────────────────────────────────────────────────────────────────────────
# Protocol compliance
# ────────────────────────────────────────────────────────────────────────────

class TestStudioVoicePluginProtocol:
    def test_subclass_of_voice_core_plugin(self):
        assert issubclass(StudioVoicePlugin, VoiceCorePlugin)

    def test_plugin_name_is_canonical(self):
        plugin = _make_plugin()
        assert plugin.plugin_name == "studio_custom_agent"

    def test_constructor_stores_agent_id_and_company_id(self):
        plugin = StudioVoicePlugin(
            agent_id="aid", agent_config={}, company_id="cid"
        )
        assert plugin.agent_id == "aid"
        assert plugin.company_id == "cid"

    def test_constructor_accepts_none_config(self):
        plugin = StudioVoicePlugin(
            agent_id="aid", agent_config=None, company_id="cid"
        )
        assert plugin.config == {}

    def test_constructor_coerces_uuid_to_str(self):
        from uuid import uuid4
        u = uuid4()
        plugin = StudioVoicePlugin(
            agent_id=u, agent_config={}, company_id="cid"
        )
        assert plugin.agent_id == str(u)


# ────────────────────────────────────────────────────────────────────────────
# on_session_initiated
# ────────────────────────────────────────────────────────────────────────────

class TestOnSessionInitiated:
    @pytest.mark.asyncio
    async def test_annotates_metadata_with_agent_id_and_plugin_name(self):
        plugin = _make_plugin(agent_id="aid-X")
        session = _make_session()

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAudit:
            MockAudit.return_value.log_decision = AsyncMock()
            await plugin.on_session_initiated(session, db=MagicMock())

        assert session.metadata["studio_agent_id"] == "aid-X"
        assert session.metadata["plugin_name"] == "studio_custom_agent"

    @pytest.mark.asyncio
    async def test_calls_canonical_audit_log_decision(self):
        plugin = _make_plugin(agent_id="aid-Y", allowed_tools=["search"])
        session = _make_session(session_id="s-Y")

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAudit:
            mock_log = AsyncMock()
            MockAudit.return_value.log_decision = mock_log
            await plugin.on_session_initiated(session, db=MagicMock())

        mock_log.assert_awaited_once()
        kwargs = mock_log.call_args.kwargs
        assert kwargs["company_id"] == "co-1"
        assert kwargs["action"] == "voice_session_initiated"
        assert kwargs["decision"] == "started"
        assert "aid-Y" in kwargs["agent_name"]
        # Reasoning must mention agent_id + session_id
        assert any("aid-Y" in r for r in kwargs["reasoning"])
        assert any("s-Y" in r for r in kwargs["reasoning"])

    @pytest.mark.asyncio
    async def test_audit_failure_is_non_blocking(self):
        plugin = _make_plugin()
        session = _make_session()

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAudit:
            MockAudit.return_value.log_decision = AsyncMock(
                side_effect=RuntimeError("audit DB down")
            )
            # Must not raise
            await plugin.on_session_initiated(session, db=MagicMock())

        # metadata still annotated despite audit failure
        assert session.metadata["studio_agent_id"] == plugin.agent_id


# ────────────────────────────────────────────────────────────────────────────
# get_next_question
# ────────────────────────────────────────────────────────────────────────────

class TestGetNextQuestion:
    @pytest.mark.asyncio
    async def test_first_turn_returns_configured_initial_greeting(self):
        plugin = _make_plugin(initial_greeting="Bem-vindo a entrevista!")
        session = _make_session(transcript_segments=[])

        q = await plugin.get_next_question(session, db=None)

        assert q == "Bem-vindo a entrevista!"

    @pytest.mark.asyncio
    async def test_first_turn_fallback_greeting_uses_description(self):
        plugin = _make_plugin(
            initial_greeting=None, description="a vaga de Eng Senior"
        )
        session = _make_session(transcript_segments=[])

        q = await plugin.get_next_question(session, db=None)

        assert q is not None
        assert "a vaga de Eng Senior" in q
        assert "LIA" in q

    @pytest.mark.asyncio
    async def test_first_turn_fallback_when_no_description(self):
        plugin = _make_plugin(initial_greeting=None, description=None)
        session = _make_session(transcript_segments=[])

        q = await plugin.get_next_question(session, db=None)

        assert q is not None
        assert "vaga" in q.lower() or "lia" in q.lower()

    @pytest.mark.asyncio
    async def test_subsequent_turn_returns_none(self):
        plugin = _make_plugin(initial_greeting="hello")
        session = _make_session(
            transcript_segments=[
                {"role": "lia", "text": "hello"},
                {"role": "candidate", "text": "ola"},
            ]
        )

        q = await plugin.get_next_question(session, db=None)

        assert q is None

    @pytest.mark.asyncio
    async def test_empty_initial_greeting_treated_as_unset(self):
        plugin = _make_plugin(initial_greeting="   ", description="X")
        session = _make_session(transcript_segments=[])

        q = await plugin.get_next_question(session, db=None)

        # Falls through to fallback greeting (initial_greeting blanked)
        assert q is not None
        assert "X" in q


# ────────────────────────────────────────────────────────────────────────────
# on_session_finalized
# ────────────────────────────────────────────────────────────────────────────

class TestOnSessionFinalized:
    @pytest.mark.asyncio
    async def test_returns_strategy_studio_custom_agent(self):
        plugin = _make_plugin(agent_id="aid-final-1")
        session = _make_session()

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAudit, patch(
            "app.services.agent_marketplace_service.agent_marketplace_service"
        ) as MockMkt, patch(
            "app.domains.voice.plugins.studio_voice_plugin.StudioVoicePlugin._generate_summary",
            new_callable=AsyncMock, return_value="bullet summary",
        ):
            MockAudit.return_value.log_decision = AsyncMock()
            MockMkt.record_execution = AsyncMock()

            result = await plugin.on_session_finalized(
                session, db=MagicMock(), transcript=[{"role": "lia", "text": "oi"}]
            )

        assert result["strategy"] == "studio_custom_agent"
        assert result["agent_id"] == "aid-final-1"
        assert result["transcript_turns"] == 1
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_records_execution_canonical_marketplace(self):
        plugin = _make_plugin(agent_id="aid-bill", pricing_tier="pro")
        session = _make_session(
            started_at=datetime(2026, 5, 22, 10, 0, 0),
            ended_at=datetime(2026, 5, 22, 10, 5, 0),  # 300 sec
        )

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAudit, patch(
            "app.services.agent_marketplace_service.agent_marketplace_service"
        ) as MockMkt, patch(
            "app.domains.voice.plugins.studio_voice_plugin.StudioVoicePlugin._generate_summary",
            new_callable=AsyncMock, return_value="",
        ):
            MockAudit.return_value.log_decision = AsyncMock()
            MockMkt.record_execution = AsyncMock()

            await plugin.on_session_finalized(
                session, db=MagicMock(), transcript=[],
            )

        MockMkt.record_execution.assert_awaited_once()
        kwargs = MockMkt.record_execution.call_args.kwargs
        assert kwargs["agent_id"] == "aid-bill"
        assert kwargs["company_id"] == "co-1"
        assert kwargs["pricing_tier"] == "pro"
        assert kwargs["credits_consumed"] > 0  # 300 sec → non-zero billing

    @pytest.mark.asyncio
    async def test_summary_generated_via_canonical_llm_service(self):
        plugin = _make_plugin()
        session = _make_session()
        transcript = [
            {"role": "lia", "text": "Conte sobre Python"},
            {"role": "candidate", "text": "5 anos com FastAPI"},
        ]

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAudit, patch(
            "app.services.agent_marketplace_service.agent_marketplace_service"
        ) as MockMkt, patch(
            "app.domains.ai.services.llm.llm_service"
        ) as mock_llm:
            MockAudit.return_value.log_decision = AsyncMock()
            MockMkt.record_execution = AsyncMock()
            mock_llm.generate_with_gemini = AsyncMock(
                return_value="- Bullet 1\n- Bullet 2\n- Bullet 3"
            )

            result = await plugin.on_session_finalized(
                session, db=MagicMock(), transcript=transcript,
            )

        mock_llm.generate_with_gemini.assert_awaited_once()
        assert "Bullet 1" in result["summary"]

    @pytest.mark.asyncio
    async def test_audit_finalized_canonical_called(self):
        plugin = _make_plugin(agent_id="aid-audit")
        session = _make_session(session_id="s-audit")

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAudit, patch(
            "app.services.agent_marketplace_service.agent_marketplace_service"
        ) as MockMkt, patch(
            "app.domains.voice.plugins.studio_voice_plugin.StudioVoicePlugin._generate_summary",
            new_callable=AsyncMock, return_value="ok",
        ):
            mock_log = AsyncMock()
            MockAudit.return_value.log_decision = mock_log
            MockMkt.record_execution = AsyncMock()

            await plugin.on_session_finalized(
                session, db=MagicMock(),
                transcript=[{"role": "lia", "text": "x"}],
            )

        mock_log.assert_awaited_once()
        kwargs = mock_log.call_args.kwargs
        assert kwargs["action"] == "voice_session_finalized"
        assert kwargs["decision"] == "completed"
        assert any("aid-audit" in r for r in kwargs["reasoning"])

    @pytest.mark.asyncio
    async def test_billing_failure_does_not_block_audit_or_result(self):
        plugin = _make_plugin()
        session = _make_session()

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAudit, patch(
            "app.services.agent_marketplace_service.agent_marketplace_service"
        ) as MockMkt, patch(
            "app.domains.voice.plugins.studio_voice_plugin.StudioVoicePlugin._generate_summary",
            new_callable=AsyncMock, return_value="ok",
        ):
            MockAudit.return_value.log_decision = AsyncMock()
            MockMkt.record_execution = AsyncMock(
                side_effect=RuntimeError("billing down")
            )
            result = await plugin.on_session_finalized(
                session, db=MagicMock(), transcript=[],
            )

        assert result["strategy"] == "studio_custom_agent"  # still returned

    @pytest.mark.asyncio
    async def test_summary_failure_returns_empty_string_not_raise(self):
        plugin = _make_plugin()
        session = _make_session()

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAudit, patch(
            "app.services.agent_marketplace_service.agent_marketplace_service"
        ) as MockMkt, patch(
            "app.domains.ai.services.llm.llm_service"
        ) as mock_llm:
            MockAudit.return_value.log_decision = AsyncMock()
            MockMkt.record_execution = AsyncMock()
            mock_llm.generate_with_gemini = AsyncMock(
                side_effect=RuntimeError("gemini down")
            )

            result = await plugin.on_session_finalized(
                session, db=MagicMock(),
                transcript=[{"role": "lia", "text": "x"}],
            )

        assert result["summary"] == ""  # graceful empty
        assert result["strategy"] == "studio_custom_agent"


# ────────────────────────────────────────────────────────────────────────────
# CustomAgentRuntime ↔ StudioVoicePlugin integration
# ────────────────────────────────────────────────────────────────────────────

class TestCustomAgentRuntimeVoiceIntegration:
    @pytest.fixture(autouse=True)
    def _force_dev_env_for_checkpointer(self, monkeypatch):
        """Checkpointer canonical (libs/agents-core/lia_agents_core/checkpointer.py)
        raises RuntimeError em APP_ENV='production'/'staging' se
        initialize_checkpointer_async() não rodou no lifespan. Como SSH/CI roda
        com APP_ENV=production e estes testes exercitam CustomAgentRuntime.execute
        sem app lifespan, monkeypatch tanto a env var quanto o settings.APP_ENV
        (Pydantic Settings é cached, env var sozinha não basta).
        Fix audit 2026-05-27 — anterior: 5 testes red bloqueando CI Studio."""
        monkeypatch.setenv("APP_ENV", "development")
        from lia_config.config import settings as _settings
        monkeypatch.setattr(_settings, "APP_ENV", "development", raising=False)

    @pytest.mark.asyncio
    async def test_invoke_voice_builds_studio_plugin_from_agent_config(
        self, monkeypatch,
    ):
        """_invoke_voice MUST construct StudioVoicePlugin with the agent's
        system_prompt, allowed_tools, initial_greeting, persona, description."""
        from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime

        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "1")

        runtime = CustomAgentRuntime(
            agent_id="agent-3", agent_name="Senior",
            system_prompt="Voce e entrevistador Senior", allowed_tools=["search"],
            company_id="company-3",
            initial_greeting="Hello Senior!",
            description="Engenheiro Senior",
            persona={"name": "LIA"},
        )

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrch:
            MockOrch.return_value = MagicMock(
                initiate_voip_session=AsyncMock(return_value=MagicMock(
                    session_id="sess-z", status="initiated",
                    voice_provider="gemini_live", call_sid=None,
                )),
            )
            await runtime.execute(
                message="", company_id="company-3", channel="voice",
                audio_chunk=b"\x01",
            )

        plugins = MockOrch.call_args.kwargs["plugins"]
        assert len(plugins) == 1
        plugin = plugins[0]
        assert plugin.plugin_name == "studio_custom_agent"
        assert plugin.agent_id == "agent-3"
        assert plugin.company_id == "company-3"
        assert plugin.config["initial_greeting"] == "Hello Senior!"
        assert plugin.config["description"] == "Engenheiro Senior"
        assert plugin.config["allowed_tools"] == ["search"]
        assert plugin.config["system_prompt"] == "Voce e entrevistador Senior"

    @pytest.mark.asyncio
    async def test_invoke_voice_voip_when_no_phone_in_context(
        self, monkeypatch,
    ):
        """No candidate_phone in context → initiate_voip_session (not PSTN)."""
        from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime

        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "1")
        runtime = CustomAgentRuntime(
            agent_id="a", agent_name="X", system_prompt="p",
            allowed_tools=[], company_id="co",
        )

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrch:
            voip_mock = AsyncMock(return_value=MagicMock(
                session_id="sess-voip", status="initiated",
                voice_provider="gemini_live", call_sid=None,
            ))
            call_mock = AsyncMock()
            MockOrch.return_value = MagicMock(
                initiate_voip_session=voip_mock,
                initiate_call=call_mock,
            )
            result = await runtime.execute(
                message="", company_id="co", channel="voice",
                audio_chunk=b"\x01",
            )

        voip_mock.assert_awaited_once()
        call_mock.assert_not_awaited()
        assert result.metadata.get("is_voip") is True
        assert result.metadata.get("status") == "session_initiated"
        assert result.metadata.get("voice_session_id") == "sess-voip"

    @pytest.mark.asyncio
    async def test_invoke_voice_pstn_when_candidate_phone_in_context(
        self, monkeypatch,
    ):
        """candidate_phone in context → initiate_call (PSTN/Twilio)."""
        from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime

        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "1")
        runtime = CustomAgentRuntime(
            agent_id="a", agent_name="X", system_prompt="p",
            allowed_tools=[], company_id="co",
        )

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrch:
            voip_mock = AsyncMock()
            call_mock = AsyncMock(return_value=MagicMock(
                session_id="sess-pstn", status="initiated",
                voice_provider="twilio", call_sid="CA-abc",
            ))
            MockOrch.return_value = MagicMock(
                initiate_voip_session=voip_mock,
                initiate_call=call_mock,
            )
            result = await runtime.execute(
                message="", company_id="co", channel="voice",
                audio_chunk=b"\x01",
                context={
                    "candidate_phone": "+5511988887777",
                    "candidate_id": "cand-X",
                    "candidate_name": "Bob",
                    "job_title": "Vaga PSTN",
                    "job_id": "job-1",
                },
            )

        call_mock.assert_awaited_once()
        voip_mock.assert_not_awaited()
        kwargs = call_mock.call_args.kwargs
        assert kwargs["phone_number"] == "+5511988887777"
        assert kwargs["candidate_id"] == "cand-X"
        assert kwargs["company_id"] == "co"
        assert result.metadata.get("is_voip") is False
        assert result.metadata.get("call_sid") == "CA-abc"
        assert result.metadata.get("voice_provider") == "twilio"

    @pytest.mark.asyncio
    async def test_invoke_voice_resume_session_processes_audio(
        self, monkeypatch,
    ):
        """voice_session_id + audio_chunk → process_audio_chunk + generate_lia_response."""
        from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime

        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "1")
        runtime = CustomAgentRuntime(
            agent_id="a", agent_name="X", system_prompt="p",
            allowed_tools=[], company_id="co",
        )

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrch:
            proc_mock = AsyncMock(return_value="Falei de Python por 5 anos.")
            resp_mock = AsyncMock(return_value="Otimo! Pode contar de um projeto?")
            MockOrch.return_value = MagicMock(
                process_audio_chunk=proc_mock,
                generate_lia_response=resp_mock,
            )
            result = await runtime.execute(
                message="", company_id="co", channel="voice",
                voice_session_id="sess-resume-1",
                audio_chunk=b"\x55" * 200,
            )

        proc_mock.assert_awaited_once()
        resp_mock.assert_awaited_once()
        assert result.metadata.get("status") == "session_resumed"
        assert result.metadata.get("transcribed") == "Falei de Python por 5 anos."
        assert result.metadata.get("lia_response") == "Otimo! Pode contar de um projeto?"
        assert result.message == "Otimo! Pode contar de um projeto?"

    @pytest.mark.asyncio
    async def test_invoke_voice_session_id_only_no_audio_does_not_process(
        self, monkeypatch,
    ):
        """voice_session_id without audio_chunk → no audio processing, returns metadata."""
        from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime

        monkeypatch.setenv("FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED", "1")
        runtime = CustomAgentRuntime(
            agent_id="a", agent_name="X", system_prompt="p",
            allowed_tools=[], company_id="co",
        )

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrch:
            proc_mock = AsyncMock()
            MockOrch.return_value = MagicMock(process_audio_chunk=proc_mock)
            result = await runtime.execute(
                message="", company_id="co", channel="voice",
                voice_session_id="sess-handshake",
            )

        proc_mock.assert_not_awaited()
        assert result.metadata.get("status") == "session_resumed"
        assert result.metadata.get("voice_session_id") == "sess-handshake"
        assert result.metadata.get("has_audio_chunk") is False


# ────────────────────────────────────────────────────────────────────────────
# Source sentinel: _invoke_voice must wire StudioVoicePlugin (not plugins=[])
# ────────────────────────────────────────────────────────────────────────────

class TestSourceSentinel:
    def test_invoke_voice_source_references_studio_voice_plugin(self):
        """Sprint 3.6 anti-regression: source of _invoke_voice must
        instantiate StudioVoicePlugin (not the empty plugins=[] baseline)."""
        import inspect
        from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime
        src = inspect.getsource(CustomAgentRuntime._invoke_voice)
        assert "StudioVoicePlugin" in src
        assert "VoiceCoreOrchestrator" in src
        # Sprint 3.6 must NOT regress to empty plugin list
        assert "plugins=[]" not in src
