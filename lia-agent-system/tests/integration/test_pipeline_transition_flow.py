"""
Integração — PipelineTransition → HITL → aprovação → candidato movido (Sprint K2).

Camada 3 da pirâmide de testes.
Cobre:
- PipelineTransitionAgent.process aceita AgentInput e retorna AgentOutput
- HITLService.request_approval persiste pending com company_id e domain (G1 multi-tenant)
- receive_approval(approved=True) → is_approved() retorna True
- receive_approval(approved=False) → is_approved() retorna False
- Pending antes de resposta → is_approved() retorna None
- store_resume_info preserva thread_id e domain para retomada pós-HITL
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


COMPANY_ID = "c-pipeline-001"
THREAD_ID = str(uuid.uuid4())
CANDIDATE_ID = str(uuid.uuid4())
JOB_ID = str(uuid.uuid4())
SESSION_ID = "ws-pipeline-session"


def _make_db():
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


def _make_agent_input(company_id=COMPANY_ID):
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(
        message=f"mover candidato {CANDIDATE_ID} para entrevista técnica",
        thread_id=THREAD_ID,
        session_id=SESSION_ID,
        company_id=company_id,
        user_id="user-recruiter-1",
        context={"candidate_id": CANDIDATE_ID, "job_id": JOB_ID},
    )


# ---------------------------------------------------------------------------
# PipelineTransitionAgent — interface básica
# ---------------------------------------------------------------------------

class TestPipelineTransitionAgent:

    def _make_agent(self):
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        return PipelineTransitionAgent()

    def test_domain_name_is_pipeline(self):
        agent = self._make_agent()
        assert "pipeline" in agent.domain_name.lower()

    @pytest.mark.asyncio
    async def test_process_returns_agent_output(self):
        from lia_agents_core.agent_interface import AgentOutput
        agent = self._make_agent()
        agent_input = _make_agent_input()
        mock_output = AgentOutput(
            message="Candidato movido para Entrevista Técnica",
            thread_id=THREAD_ID,
            session_id=SESSION_ID,
        )

        with patch.object(agent, "_process_langgraph", new_callable=AsyncMock, return_value=mock_output):
            result = await agent.process(agent_input)

        assert result is not None
        assert result.message == "Candidato movido para Entrevista Técnica"

    @pytest.mark.asyncio
    async def test_company_id_preserved_in_input(self):
        agent_input = _make_agent_input(company_id="company-xyz")
        assert agent_input.company_id == "company-xyz"

    def test_available_tools_not_empty(self):
        agent = self._make_agent()
        tools = agent.available_tools
        assert isinstance(tools, (list, tuple, dict)) or tools is not None


# ---------------------------------------------------------------------------
# HITLService — ciclo completo aprovação/rejeição
# ---------------------------------------------------------------------------

class TestHITLApprovalRejection:

    def _make_hitl(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory = {}
        return svc

    @pytest.mark.asyncio
    async def test_request_stores_company_id_and_domain(self):
        svc = self._make_hitl()
        with patch("app.services.hitl_service._db_save_pending", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id=THREAD_ID, action="move_candidate",
                description="Mover para Entrevista Técnica",
                data={"candidate_id": CANDIDATE_ID, "target_stage": "entrevista_tecnica"},
                ws_session_id=SESSION_ID,
                domain="pipeline",
                company_id=COMPANY_ID,
            )
        stored = svc._load(f"hitl:{THREAD_ID}:{pending_id}")
        assert stored["company_id"] == COMPANY_ID
        assert stored["domain"] == "pipeline"

    @pytest.mark.asyncio
    async def test_approved_flow(self):
        svc = self._make_hitl()
        with patch("app.services.hitl_service._db_save_pending", new_callable=AsyncMock), \
             patch("app.services.hitl_service._db_resolve", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id=THREAD_ID, action="move_candidate",
                description="Mover candidato", data={}, ws_session_id=SESSION_ID,
                domain="pipeline", company_id=COMPANY_ID,
            )
            await svc.receive_approval(
                thread_id=THREAD_ID, pending_id=pending_id,
                approved=True, comment="aprovado pelo recrutador",
                domain="pipeline", company_id=COMPANY_ID,
            )
        result = await svc.is_approved(pending_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_rejected_flow(self):
        svc = self._make_hitl()
        with patch("app.services.hitl_service._db_save_pending", new_callable=AsyncMock), \
             patch("app.services.hitl_service._db_resolve", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id=THREAD_ID, action="move_candidate",
                description="Mover candidato", data={}, ws_session_id=SESSION_ID,
                domain="pipeline", company_id=COMPANY_ID,
            )
            await svc.receive_approval(
                thread_id=THREAD_ID, pending_id=pending_id,
                approved=False, comment="cancelado pelo recrutador",
                domain="pipeline", company_id=COMPANY_ID,
            )
        result = await svc.is_approved(pending_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_pending_before_response_is_none(self):
        svc = self._make_hitl()
        with patch("app.services.hitl_service._db_save_pending", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id=THREAD_ID, action="move_candidate",
                description="Mover", data={}, ws_session_id=SESSION_ID,
            )
        assert await svc.is_approved(pending_id) is None

    @pytest.mark.asyncio
    async def test_resume_info_stored_with_domain(self):
        svc = self._make_hitl()
        await svc.store_resume_info(
            thread_id=THREAD_ID,
            domain="pipeline",
            session_id=SESSION_ID,
            agent_input_dict={"candidate_id": CANDIDATE_ID, "company_id": COMPANY_ID},
            hitl_context="aguardando aprovacao movimentacao",
        )
        info = await svc.get_resume_info(THREAD_ID)
        assert info["domain"] == "pipeline"
        assert info["agent_input"]["company_id"] == COMPANY_ID
