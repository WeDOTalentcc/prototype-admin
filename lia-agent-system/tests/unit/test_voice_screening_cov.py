"""
Coverage tests for app/domains/voice/services/voice_screening_orchestrator.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any


@pytest.fixture
def orchestrator():
    with patch("app.domains.voice.services.voice_screening_orchestrator.VoiceService"), \
         patch("app.domains.voice.services.voice_screening_orchestrator._twilio_voice_service"):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        orch = VoiceScreeningOrchestrator()
        # F-15: force Redis disabled + clear in-mem fallback per-test isolation.
        async def _no_redis():
            return None
        orch._session_repo._get_redis = _no_redis  # type: ignore[method-assign]
        orch._session_repo._redis = None
        orch._session_repo._redis_available = False
        orch._session_repo._memory_fallback.clear()
        orch._session_repo._memory_active_index.clear()
        orch._session_repo._memory_reverse_index.clear()
        return orch


@pytest.fixture
def sample_session():
    from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningSession
    return VoiceScreeningSession(
        session_id="sess-1",
        candidate_id="cand-1",
        candidate_name="João Silva",
        job_title="Dev Python",
        company_id="comp-1",
        phone_number="+5511999999999",
        job_id="job-1",
        call_sid="CA123",
        status="in_progress",
        language="pt-BR",
        transcript_segments=[
            {"text": "Olá, tudo bem?", "timestamp": "2025-01-01T10:00:00", "role": "lia"},
        ],
        questions_asked=["Pergunta 1"],
        started_at=datetime(2025, 1, 1, 10, 0),
        ended_at=None,
        wsi_result=None,
        error=None,
        consent_verified=True,
        job_context={"title": "Dev Python", "work_model": "remoto", "location": "SP", "benefits": ["VR", "VA"], "salary": "R$ 15k"},
        presentation_done=True,
    )


# ── Session serialization ────────────────────────────────────────────────────

class TestSessionSerialization:
    @pytest.mark.easy
    def test_session_to_state(self, orchestrator, sample_session):
        state = orchestrator._session_to_state(sample_session)
        assert state["session_id"] == "sess-1"
        assert state["candidate_id"] == "cand-1"
        assert state["status"] == "in_progress"
        assert state["consent_verified"] is True
        assert state["started_at"] == "2025-01-01T10:00:00"
        assert state["ended_at"] is None
        assert len(state["transcript_segments"]) == 1

    @pytest.mark.easy
    def test_state_to_session(self, orchestrator, sample_session):
        state = orchestrator._session_to_state(sample_session)
        restored = orchestrator._state_to_session(state)
        assert restored.session_id == "sess-1"
        assert restored.candidate_name == "João Silva"
        assert restored.started_at == datetime(2025, 1, 1, 10, 0)
        assert restored.ended_at is None
        assert restored.consent_verified is True

    @pytest.mark.easy
    def test_round_trip(self, orchestrator, sample_session):
        # F-07 P0 masking (5543c6b3f): phone_number gets masked at every
        # _session_to_state call. Masking is intentionally non-idempotent
        # (progressive: raw → masked-with-tail → shorter mask). For round-trip
        # equality we compare ALL fields EXCEPT phone_number, which is asserted
        # separately as "always masked" (presence check).
        state = orchestrator._session_to_state(sample_session)
        restored = orchestrator._state_to_session(state)
        state2 = orchestrator._session_to_state(restored)
        state_no_phone = {k: v for k, v in state.items() if k != "phone_number"}
        state2_no_phone = {k: v for k, v in state2.items() if k != "phone_number"}
        assert state_no_phone == state2_no_phone
        # F-07: phone is always masked (contains "*" sentinel).
        assert "*" in (state["phone_number"] or "")
        assert "*" in (state2["phone_number"] or "")


# ── Session management ───────────────────────────────────────────────────────

class TestSessionManagement:
    # F-15: orchestrator state now lives in VoiceSessionRedisRepository.
    # Tests use the repo's in-memory fallback (Redis unavailable in unit tests).

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_session_found(self, orchestrator, sample_session):
        await orchestrator._store_session(sample_session)
        result = await orchestrator.get_session("sess-1")
        assert result is not None
        assert result.session_id == sample_session.session_id

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_session_not_found(self, orchestrator):
        assert await orchestrator.get_session("missing") is None

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_session_language(self, orchestrator, sample_session):
        await orchestrator._store_session(sample_session)
        assert await orchestrator._get_session_language("sess-1") == "pt-BR"

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_session_language_default(self, orchestrator):
        assert await orchestrator._get_session_language("missing") == "pt-BR"

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_list_active_sessions(self, orchestrator, sample_session):
        await orchestrator._store_session(sample_session)
        result = await orchestrator.list_active_sessions(company_id="comp-1")
        assert len(result) == 1
        assert result[0]["session_id"] == "sess-1"
        assert result[0]["status"] == "in_progress"

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_list_active_sessions_excludes_completed(self, orchestrator, sample_session):
        sample_session.status = "completed"
        await orchestrator._store_session(sample_session)
        result = await orchestrator.list_active_sessions(company_id="comp-1")
        assert len(result) == 0

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_or_restore_session_from_memory(self, orchestrator, sample_session):
        await orchestrator._store_session(sample_session)
        result = await orchestrator.get_or_restore_session("sess-1")
        assert result is not None
        assert result.session_id == sample_session.session_id

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_or_restore_session_from_db(self, orchestrator, sample_session):
        with patch.object(orchestrator, "_load_session_from_db", new_callable=AsyncMock, return_value=sample_session):
            result = await orchestrator.get_or_restore_session("sess-1", db=MagicMock())
        assert result is sample_session
        # F-15: rehydrated into Redis (in-mem fallback) — verify reachability.
        from_redis = await orchestrator.get_session("sess-1")
        assert from_redis is not None

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_or_restore_session_not_found(self, orchestrator):
        with patch.object(orchestrator, "_load_session_from_db", new_callable=AsyncMock, return_value=None):
            result = await orchestrator.get_or_restore_session("missing", db=MagicMock())
        assert result is None


# ── Static helpers ───────────────────────────────────────────────────────────

class TestStaticHelpers:
    @pytest.mark.easy
    def test_build_job_presentation_instruction_with_context(self, sample_session):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        result = VoiceScreeningOrchestrator._build_job_presentation_instruction(sample_session)
        assert "vaga" in result.lower()
        assert "candidato" in result.lower()

    @pytest.mark.easy
    def test_build_job_presentation_instruction_no_context(self, sample_session):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        sample_session.job_context = None
        result = VoiceScreeningOrchestrator._build_job_presentation_instruction(sample_session)
        assert "Dev Python" in result

    @pytest.mark.easy
    def test_build_fallback_job_presentation_full(self, sample_session):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        result = VoiceScreeningOrchestrator._build_fallback_job_presentation(sample_session)
        assert "Dev Python" in result
        assert "remoto" in result
        assert "SP" in result
        assert "VR" in result
        assert "15k" in result

    @pytest.mark.easy
    def test_build_fallback_job_presentation_minimal(self, sample_session):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        sample_session.job_context = {}
        result = VoiceScreeningOrchestrator._build_fallback_job_presentation(sample_session)
        assert "Dev Python" in result

    @pytest.mark.easy
    def test_mask_transcript_segments(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        segments = [
            {"text": "Meu CPF é 123.456.789-00", "role": "candidate"},
            {"text": "OK entendi", "role": "lia"},
        ]
        result = VoiceScreeningOrchestrator._mask_transcript_segments(segments)
        assert len(result) == 2
        # Original should not be mutated
        assert "123.456.789-00" in segments[0]["text"]


# ── Scripted questions ───────────────────────────────────────────────────────

class TestScriptedQuestions:
    @pytest.mark.easy
    def test_get_next_scripted_question(self, orchestrator, sample_session):
        sample_session.questions_asked = []
        with patch("app.domains.voice.services.voice_screening_orchestrator.check_fairness") as mock_fair:
            mock_fair.return_value = MagicMock(is_blocked=False)
            q = orchestrator._get_next_scripted_question(sample_session)
        assert len(q) > 0
        assert len(sample_session.questions_asked) == 1

    @pytest.mark.easy
    def test_get_next_scripted_custom_questions(self, orchestrator, sample_session):
        sample_session.questions_asked = []
        custom = ["Pergunta A?", "Pergunta B?"]
        with patch("app.domains.voice.services.voice_screening_orchestrator.check_fairness") as mock_fair:
            mock_fair.return_value = MagicMock(is_blocked=False)
            q = orchestrator._get_next_scripted_question(sample_session, questions=custom)
        assert q == "Pergunta A?"

    @pytest.mark.easy
    def test_get_next_scripted_closing(self, orchestrator, sample_session):
        sample_session.questions_asked = list(orchestrator.SCREENING_QUESTIONS_PT)
        with patch("app.domains.voice.services.voice_screening_orchestrator.check_fairness") as mock_fair:
            mock_fair.return_value = MagicMock(is_blocked=False)
            q = orchestrator._get_next_scripted_question(sample_session)
        assert "obrigada" in q.lower() or "encerramos" in q.lower()

    @pytest.mark.easy
    def test_fairness_blocked_scripted(self, orchestrator, sample_session):
        sample_session.questions_asked = []
        with patch("app.domains.voice.services.voice_screening_orchestrator.check_fairness") as mock_fair:
            mock_fair.return_value = MagicMock(is_blocked=True)
            q = orchestrator._get_next_scripted_question(sample_session)
        assert "experiência" in q.lower()


# ── Check fairness on response ───────────────────────────────────────────────

class TestCheckFairness:
    @pytest.mark.easy
    def test_passes_through(self, orchestrator, sample_session):
        with patch("app.domains.voice.services.voice_screening_orchestrator.check_fairness") as mock_fair:
            mock_fair.return_value = MagicMock(is_blocked=False)
            result = orchestrator._check_fairness_on_response("Hello", sample_session)
        assert result == "Hello"

    @pytest.mark.easy
    def test_blocked_replaces(self, orchestrator, sample_session):
        with patch("app.domains.voice.services.voice_screening_orchestrator.check_fairness") as mock_fair:
            mock_fair.return_value = MagicMock(is_blocked=True)
            result = orchestrator._check_fairness_on_response("Bad text", sample_session)
        assert "experiência" in result.lower()

    @pytest.mark.easy
    def test_error_fail_open(self, orchestrator, sample_session):
        with patch("app.domains.voice.services.voice_screening_orchestrator.check_fairness", side_effect=Exception("fail")):
            result = orchestrator._check_fairness_on_response("Hello", sample_session)
        assert result == "Hello"


# ── Persist session ──────────────────────────────────────────────────────────

class TestPersistSession:
    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_persist_session_no_db(self, orchestrator, sample_session):
        await orchestrator._persist_session_state(sample_session, None)

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_build_job_context_summary_full(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        ctx = {
            "title": "Dev Python",
            "description": "Build stuff",
            "department": "Eng",
            "seniority": "Senior",
            "work_model": "remoto",
            "location": "SP",
            "salary_range": "15k-25k",
            "benefits": ["VR", "VA"],
            "skills": ["Python", "Docker"],
            "responsibilities": ["Code", "Review"],
        }
        result = VoiceScreeningOrchestrator._build_job_context_summary(ctx)
        assert "Dev Python" in result

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_build_job_context_summary_empty(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        result = VoiceScreeningOrchestrator._build_job_context_summary({})
        assert isinstance(result, str)


# ── Exception classes ────────────────────────────────────────────────────────

class TestExceptions:
    @pytest.mark.easy
    def test_voice_screening_error(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestratorError
        err = VoiceScreeningOrchestratorError("test")
        assert str(err) == "test"

    @pytest.mark.easy
    def test_consent_not_granted(self):
        from app.domains.voice.services.voice_screening_orchestrator import ConsentNotGrantedError, VoiceScreeningOrchestratorError
        err = ConsentNotGrantedError("no consent")
        assert isinstance(err, VoiceScreeningOrchestratorError)

    @pytest.mark.easy
    def test_screening_questions_pt(self, orchestrator):
        assert len(orchestrator.SCREENING_QUESTIONS_PT) >= 5
