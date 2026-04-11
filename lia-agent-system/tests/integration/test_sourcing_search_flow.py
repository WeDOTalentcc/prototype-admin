"""
Integração — Sourcing → RAG search → comunicação → FairnessGuard (Sprint K2).

Camada 3 da pirâmide de testes.
Cobre:
- SourcingReActAgent.process aceita AgentInput e retorna AgentOutput
- RAGPipelineService integrado com sourcing (alpha blend)
- FairnessGuard stub logado no RAG top-10
- company_id preservado em todas as chamadas (multi-tenant)
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


COMPANY_ID = "c-sourcing-001"
THREAD_ID = str(uuid.uuid4())
JOB_ID = str(uuid.uuid4())
SESSION_ID = "ws-sourcing-session"


def _make_db():
    db = AsyncMock()
    result = MagicMock()
    result.fetchall.return_value = []
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


def _make_agent_input(company_id=COMPANY_ID):
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(
        message="buscar desenvolvedores Python sênior",
        thread_id=THREAD_ID,
        session_id=SESSION_ID,
        company_id=company_id,
        user_id="user-recruiter-1",
        context={"job_id": JOB_ID, "query": "dev Python sênior"},
    )


# ---------------------------------------------------------------------------
# SourcingReActAgent
# ---------------------------------------------------------------------------

class TestSourcingReActAgent:

    def _make_agent(self):
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        return SourcingReActAgent()

    def test_domain_name_is_sourcing(self):
        agent = self._make_agent()
        assert "sourcing" in agent.domain_name.lower()

    @pytest.mark.asyncio
    async def test_process_returns_agent_output(self):
        from lia_agents_core.agent_interface import AgentOutput
        agent = self._make_agent()
        agent_input = _make_agent_input()
        mock_output = AgentOutput(
            message="Encontrei 15 candidatos para dev Python",
            thread_id=THREAD_ID,
            session_id=SESSION_ID,
        )

        with patch.object(agent, "_process_langgraph", new_callable=AsyncMock, return_value=mock_output):
            result = await agent.process(agent_input)

        assert result is not None
        assert result.message == "Encontrei 15 candidatos para dev Python"

    def test_company_id_preserved_in_input(self):
        agent_input = _make_agent_input(company_id="company-xyz")
        assert agent_input.company_id == "company-xyz"


# ---------------------------------------------------------------------------
# RAG + FairnessGuard
# ---------------------------------------------------------------------------

class TestRAGWithFairness:

    @pytest.mark.asyncio
    async def test_fairness_check_called_on_rag_top10(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService()
        db = _make_db()

        with patch.object(svc, "_bm25_search", new_callable=AsyncMock, return_value=[]), \
             patch.object(svc, "_semantic_search", new_callable=AsyncMock, return_value=[]), \
             patch("app.services.rag_pipeline_service._check_fairness", return_value=True) as mock_fairness:
            await svc.search("dev Python", COMPANY_ID, db, limit=10)

        # FairnessGuard deve ser chamado (mesmo que stub)
        mock_fairness.assert_called_once()

    @pytest.mark.asyncio
    async def test_rag_results_bounded_by_limit(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService()
        db = _make_db()

        many_results = [
            {"id": str(uuid.uuid4()), "name": "C", "company_id": COMPANY_ID, "bm25_score": 0.9}
            for _ in range(20)
        ]
        with patch.object(svc, "_bm25_search", new_callable=AsyncMock, return_value=many_results), \
             patch.object(svc, "_semantic_search", new_callable=AsyncMock, return_value=[]):
            result = await svc.search("dev", COMPANY_ID, db, limit=5, alpha=0.0)

        assert len(result.results) <= 5

    @pytest.mark.asyncio
    async def test_rag_source_label_bm25(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService()
        db = _make_db()

        with patch.object(svc, "_bm25_search", new_callable=AsyncMock, return_value=[]), \
             patch.object(svc, "_semantic_search", new_callable=AsyncMock, return_value=[]):
            result = await svc.search("dev", COMPANY_ID, db, limit=5, alpha=0.0)

        assert result.source == "bm25"


# ---------------------------------------------------------------------------
# HITL — company_id multi-tenant no fluxo de sourcing
# ---------------------------------------------------------------------------

class TestSourcingHITL:

    @pytest.mark.asyncio
    async def test_hitl_sourcing_stores_company_id(self):
        """HITLService deve persistir company_id no fluxo de sourcing (G1)."""
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory = {}

        with patch("app.services.hitl_service._db_save_pending", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id=THREAD_ID,
                action="contact_candidates",
                description="Autorizar contato com 3 candidatos",
                data={"candidate_ids": ["c1", "c2", "c3"]},
                ws_session_id=SESSION_ID,
                domain="sourcing",
                company_id=COMPANY_ID,
            )

        stored = svc._load(f"hitl:{THREAD_ID}:{pending_id}")
        assert stored["company_id"] == COMPANY_ID
        assert stored["domain"] == "sourcing"

    @pytest.mark.asyncio
    async def test_hitl_resume_info_sourcing_domain(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory = {}

        await svc.store_resume_info(
            thread_id=THREAD_ID,
            domain="sourcing",
            session_id=SESSION_ID,
            agent_input_dict={"job_id": JOB_ID, "company_id": COMPANY_ID},
        )

        info = await svc.get_resume_info(THREAD_ID)
        assert info["domain"] == "sourcing"
        assert info["agent_input"]["company_id"] == COMPANY_ID
