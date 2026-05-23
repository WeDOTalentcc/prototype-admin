"""
Testes unitários para ContextAdapter.
Cobre: normalização de contexto de cada canal, mapeamento de context_page,
validação de IDOR, e conversão para orchestrator context.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.orchestrator.context.context_adapter import (
    ContextAdapter,
    UniversalContext,
    PAGE_TO_CONTEXT_TYPE,
)


# ---------------------------------------------------------------------------
# UniversalContext.to_orchestrator_context()
# ---------------------------------------------------------------------------

class TestUniversalContextToOrchestratorContext:
    def test_basic_mapping(self):
        ctx = UniversalContext(
            message="teste",
            user_id="u1",
            company_id="c1",
            context_page="sourcing",
            context_type="talent_funnel",
            entity_id="42",
        )
        result = ctx.to_orchestrator_context()
        assert result["context_type"] == "talent_funnel"
        assert result["context_id"] == "42"
        assert result["channel"] == "rest"

    def test_includes_candidates(self):
        candidates = [{"id": 1, "name": "Ana"}, {"id": 2, "name": "Bob"}]
        ctx = UniversalContext(
            message="top 5",
            user_id="u1",
            company_id="c1",
            candidates=candidates,
        )
        result = ctx.to_orchestrator_context()
        assert result["candidates"] == candidates

    def test_includes_job_context(self):
        job = {"id": "10", "title": "Dev"}
        ctx = UniversalContext(
            message="analise",
            user_id="u1",
            company_id="c1",
            job_context=job,
        )
        result = ctx.to_orchestrator_context()
        assert result["job_context"] == job

    def test_no_none_values_for_missing_optional(self):
        ctx = UniversalContext(message="hi", user_id="u", company_id="c")
        result = ctx.to_orchestrator_context()
        assert "job_context" not in result
        assert "search_context" not in result
        assert "target_job" not in result


# ---------------------------------------------------------------------------
# ContextAdapter.from_rest()
# ---------------------------------------------------------------------------

class TestContextAdapterFromRest:
    def test_basic(self):
        ctx = ContextAdapter.from_rest(
            message="busca Python",
            user_id="u1",
            company_id="c1",
        )
        assert ctx.message == "busca Python"
        assert ctx.user_id == "u1"
        assert ctx.company_id == "c1"
        assert ctx.channel == "rest"
        assert ctx.context_type == "general"

    def test_context_page_mapped_correctly(self):
        for page, expected_type in PAGE_TO_CONTEXT_TYPE.items():
            ctx = ContextAdapter.from_rest(
                message="x",
                user_id="u",
                company_id="c",
                context_page=page,
            )
            assert ctx.context_type == expected_type, f"page={page}"

    def test_unknown_context_page_defaults_to_general(self):
        ctx = ContextAdapter.from_rest(
            message="x",
            user_id="u",
            company_id="c",
            context_page="pagina_desconhecida",
        )
        assert ctx.context_type == "general"

    def test_entity_id_and_type_passed(self):
        ctx = ContextAdapter.from_rest(
            message="x",
            user_id="u",
            company_id="c",
            entity_id="99",
            entity_type="job",
        )
        assert ctx.entity_id == "99"
        assert ctx.entity_type == "job"


# ---------------------------------------------------------------------------
# ContextAdapter.from_talent_chat()
# ---------------------------------------------------------------------------

class TestContextAdapterFromTalentChat:
    def _make_request(self, sourcing_id=None):
        req = MagicMock()
        req.message = "top 5 candidatos"
        req.candidates = [{"id": 1}]
        req.selected_candidate_ids = None
        req.search_context = {"sourcing_id": sourcing_id} if sourcing_id else None
        req.conversation_id = "conv-1"
        req.company_id = "comp-1"
        req.target_job = None
        return req

    def test_context_type_is_talent_funnel(self):
        ctx = ContextAdapter.from_talent_chat(
            self._make_request(), user_id="u1", company_id="c1"
        )
        assert ctx.context_type == "talent_funnel"
        assert ctx.context_page == "sourcing"

    def test_sourcing_id_extracted_as_entity_id(self):
        ctx = ContextAdapter.from_talent_chat(
            self._make_request(sourcing_id=42), user_id="u1", company_id="c1"
        )
        assert ctx.entity_id == "42"
        assert ctx.entity_type == "sourcing"

    def test_no_sourcing_id(self):
        ctx = ContextAdapter.from_talent_chat(
            self._make_request(), user_id="u1", company_id="c1"
        )
        assert ctx.entity_id is None

    def test_candidates_passed_through(self):
        ctx = ContextAdapter.from_talent_chat(
            self._make_request(), user_id="u1", company_id="c1"
        )
        assert ctx.candidates == [{"id": 1}]


# ---------------------------------------------------------------------------
# ContextAdapter.from_job_chat()
# ---------------------------------------------------------------------------

class TestContextAdapterFromJobChat:
    def _make_request(self, job_id=None):
        req = MagicMock()
        req.message = "analise candidatos"
        req.job_context = {"id": job_id, "title": "Dev"} if job_id else {"title": "Dev"}
        req.candidates = []
        req.selected_candidate_ids = None
        req.conversation_id = None
        req.company_id = "comp-1"
        return req

    def test_context_type_is_job_management(self):
        ctx = ContextAdapter.from_job_chat(
            self._make_request(), user_id="u1", company_id="c1"
        )
        assert ctx.context_type == "job_management"
        assert ctx.context_page == "job"

    def test_job_id_extracted_as_entity_id(self):
        ctx = ContextAdapter.from_job_chat(
            self._make_request(job_id="10"), user_id="u1", company_id="c1"
        )
        assert ctx.entity_id == "10"
        assert ctx.entity_type == "job"


# ---------------------------------------------------------------------------
# ContextAdapter.from_ws()
# ---------------------------------------------------------------------------

class TestContextAdapterFromWs:
    def test_basic_ws_context(self):
        ctx = ContextAdapter.from_ws(
            session_id="sess-123",
            message_frame={
                "content": "mover candidato",
                "domain": "pipeline",
                "context": {},
            },
            jwt_payload={"sub": "user-1", "company_id": "comp-1"},
        )
        assert ctx.message == "mover candidato"
        assert ctx.user_id == "user-1"
        assert ctx.company_id == "comp-1"
        assert ctx.channel == "ws"
        assert ctx.context_type == "pipeline"
        assert ctx.conversation_id == "sess-123"

    def test_entity_id_from_context(self):
        ctx = ContextAdapter.from_ws(
            session_id="s",
            message_frame={
                "content": "x",
                "domain": "sourcing",
                "context": {"sourcing_id": 55},
            },
            jwt_payload={"sub": "u", "company_id": "c"},
        )
        assert ctx.entity_id == "55"


# ---------------------------------------------------------------------------
# ContextAdapter.from_rabbitmq()
# ---------------------------------------------------------------------------

class TestContextAdapterFromRabbitMQ:
    def test_basic_rabbitmq_message(self):
        msg = {
            "question": "top candidatos python",
            "domain": "sourced_profile_sourcing",
            "sourcing_id": 99,
            "user_id": "u1",
            "company_id": "c1",
            "context_data": {},
        }
        ctx = ContextAdapter.from_rabbitmq(msg)
        assert ctx.message == "top candidatos python"
        assert ctx.user_id == "u1"
        assert ctx.company_id == "c1"
        assert ctx.channel == "rabbitmq"
        assert ctx.entity_id == "99"
        assert ctx.entity_type == "sourcing"

    def test_rabbitmq_without_domain_defaults_general(self):
        msg = {"question": "oi", "user_id": "u", "company_id": "c"}
        ctx = ContextAdapter.from_rabbitmq(msg)
        assert ctx.context_type == "general"


# ---------------------------------------------------------------------------
# ContextAdapter.validate_entity_ownership() — IDOR prevention
# ---------------------------------------------------------------------------

class TestValidateEntityOwnership:
    @pytest.mark.asyncio
    async def test_returns_true_when_no_entity_id(self):
        result = await ContextAdapter.validate_entity_ownership(
            entity_id="", entity_type="sourcing", company_id="c1", db=None
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_for_unknown_entity_type(self):
        result = await ContextAdapter.validate_entity_ownership(
            entity_id="1", entity_type="unknown_type", company_id="c1", db=MagicMock()
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_when_entity_belongs_to_company(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)  # found
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await ContextAdapter.validate_entity_ownership(
            entity_id="42", entity_type="sourcing", company_id="c1", db=mock_db
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_entity_belongs_to_other_company(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # not found = different company
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await ContextAdapter.validate_entity_ownership(
            entity_id="42", entity_type="sourcing", company_id="c-other", db=mock_db
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_on_db_exception_graceful_degradation(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB unavailable"))

        result = await ContextAdapter.validate_entity_ownership(
            entity_id="42", entity_type="job", company_id="c1", db=mock_db
        )
        assert result is True  # graceful degradation — não bloqueia
