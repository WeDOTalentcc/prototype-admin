"""
Integração — WSI Interview: estágios → HITL antes de feedback → score (Sprint K2).

Camada 3 da pirâmide de testes.
Cobre:
- WSIInterviewState registra progresso correto entre estágios
- is_complete property: False quando stage != COMPLETE/ERROR
- is_complete property: True quando stage == COMPLETE
- progress_pct() reflete percentual correto baseado em current_question_index
- HITL solicitado antes de gerar feedback final
- company_id e domain passados ao request_approval (G1)
- serialização/deserialização de WSIInterviewState
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


COMPANY_ID = "c-wsi-001"
THREAD_ID = str(uuid.uuid4())
CANDIDATE_ID = str(uuid.uuid4())
JOB_ID = str(uuid.uuid4())
SESSION_ID = "ws-wsi-session"


def _make_db():
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


def _make_question_block(block_id="q1"):
    from app.domains.cv_screening.agents.wsi_interview_graph import WSIQuestionBlock
    return WSIQuestionBlock(
        block_id=block_id,
        block_type="behavioral",
        question=f"Pergunta {block_id}",
        competency="comunicação",
        bloom_level=3,
        dreyfus_level=2,
    )


def _make_state(total_questions=8, current_index=0, stage=None):
    from app.domains.cv_screening.agents.wsi_interview_graph import (
        WSIInterviewState, WSIInterviewStage
    )
    question_blocks = [_make_question_block(f"q{i}") for i in range(total_questions)]
    return WSIInterviewState(
        session_id=SESSION_ID,
        candidate_id=CANDIDATE_ID,
        job_id=JOB_ID,
        company_id=COMPANY_ID,
        question_blocks=question_blocks,
        current_question_index=current_index,
        stage=stage or WSIInterviewStage.GENERATE_QUESTION,
    )


# ---------------------------------------------------------------------------
# WSIInterviewState — estágios e progresso
# ---------------------------------------------------------------------------

class TestWSIInterviewState:

    def test_not_complete_when_stage_is_not_terminal(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewStage
        state = _make_state(stage=WSIInterviewStage.GENERATE_QUESTION)
        assert not state.is_complete

    def test_complete_when_stage_is_complete(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewStage
        state = _make_state(stage=WSIInterviewStage.COMPLETE)
        assert state.is_complete

    def test_complete_when_stage_is_error(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewStage
        state = _make_state(stage=WSIInterviewStage.ERROR)
        assert state.is_complete

    def test_progress_pct_correct(self):
        state = _make_state(total_questions=8, current_index=4)
        assert state.progress_pct == pytest.approx(50.0, rel=0.01)

    def test_progress_pct_zero_at_start(self):
        state = _make_state(total_questions=8, current_index=0)
        assert state.progress_pct == pytest.approx(0.0, rel=0.01)

    def test_progress_pct_100_when_all_done(self):
        state = _make_state(total_questions=8, current_index=8)
        assert state.progress_pct == pytest.approx(100.0, rel=0.01)

    def test_questions_remaining(self):
        state = _make_state(total_questions=8, current_index=3)
        assert state.questions_remaining == 5


# ---------------------------------------------------------------------------
# WSI HITL — interrupt antes de lg_generate_feedback
# ---------------------------------------------------------------------------

class TestWSIHITL:

    @pytest.mark.asyncio
    async def test_hitl_has_wsi_domain(self):
        """HITL para WSI deve ter domain='cv_screening'."""
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory = {}

        with patch("app.services.hitl_service._db_save_pending", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id=THREAD_ID,
                action="generate_feedback",
                description="Gerar feedback final WSI",
                data={"candidate_id": CANDIDATE_ID, "score": 0.78},
                ws_session_id=SESSION_ID,
                domain="cv_screening",
                company_id=COMPANY_ID,
            )

        stored = svc._load(f"hitl:{THREAD_ID}:{pending_id}")
        assert stored["domain"] == "cv_screening"
        assert stored["company_id"] == COMPANY_ID
        assert stored["data"]["score"] == 0.78

    @pytest.mark.asyncio
    async def test_hitl_approved_resolves_correctly(self):
        """Após aprovação, is_approved() retorna True."""
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory = {}

        with patch("app.services.hitl_service._db_save_pending", new_callable=AsyncMock), \
             patch("app.services.hitl_service._db_resolve", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id=THREAD_ID, action="generate_feedback",
                description="Gerar feedback", data={}, ws_session_id=SESSION_ID,
                domain="cv_screening", company_id=COMPANY_ID,
            )
            await svc.receive_approval(
                thread_id=THREAD_ID, pending_id=pending_id,
                approved=True, resolved_by="recruiter-1",
                domain="cv_screening", company_id=COMPANY_ID,
            )

        assert await svc.is_approved(pending_id) is True

    @pytest.mark.asyncio
    async def test_resume_info_includes_cv_screening_domain(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory = {}

        await svc.store_resume_info(
            thread_id=THREAD_ID,
            domain="cv_screening",
            session_id=SESSION_ID,
            agent_input_dict={"candidate_id": CANDIDATE_ID, "company_id": COMPANY_ID},
            hitl_context="aguardando aprovacao feedback wsi",
        )

        info = await svc.get_resume_info(THREAD_ID)
        assert info["domain"] == "cv_screening"
        assert info["hitl_context"] == "aguardando aprovacao feedback wsi"

    def test_state_serialization_roundtrip(self):
        """_wsi_state_to_dict → _wsi_state_from_dict deve preservar dados."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            _wsi_state_to_dict, _wsi_state_from_dict,
            WSIInterviewState, WSIInterviewStage,
        )
        original = WSIInterviewState(
            session_id=SESSION_ID,
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
            company_id=COMPANY_ID,
            question_blocks=[_make_question_block("q1")],
            stage=WSIInterviewStage.GENERATE_QUESTION,
        )
        serialized = _wsi_state_to_dict(original)
        restored = _wsi_state_from_dict(serialized)

        assert restored.session_id == SESSION_ID
        assert restored.company_id == COMPANY_ID
        assert len(restored.question_blocks) == 1
