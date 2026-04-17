"""Integração — `_wrap_search_candidates` da LIA conversacional (Task #397).

Garante paridade com o endpoint REST: o tool reusa `pearch_service.hybrid_search`,
`enrich_and_filter_candidates` e debita créditos via `credit_service.consume_action`
com a ação correta (`bulk_search` quando inclui Pearch, `search` caso contrário).

Tudo é mockado — sem dependência de banco real, Pearch HTTP, Apify ou Redis.
"""
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


COMPANY_ID = "company-test-001"
USER_ID = "user-recruiter-1"


def _fake_session_factory():
    session = MagicMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()

    @asynccontextmanager
    async def _ctx():
        yield session

    factory = MagicMock(side_effect=lambda: _ctx())
    return factory, session


def _fake_hybrid_response(local_count=2, pearch_count=3, thread_id="thread-xyz"):
    from lia_models.pearch import CandidateProfile, HybridSearchResponse

    local = [CandidateProfile(name=f"Local {i}") for i in range(local_count)]
    pearch = [CandidateProfile(name=f"Pearch {i}") for i in range(pearch_count)]
    return HybridSearchResponse(
        query="dev python sênior",
        thread_id=thread_id,
        local_candidates=local,
        pearch_candidates=pearch,
        local_count=local_count,
        pearch_count=pearch_count,
        total_count=local_count + pearch_count,
    )


async def _passthrough_enrich(_db, candidates):
    from app.api.v1.candidate_search._shared import EnrichmentStats
    return candidates, EnrichmentStats(filtered_no_contact=0, enrichment_attempted=0)


@pytest.mark.asyncio
async def test_search_candidates_reuses_rest_pipeline_with_bulk_search_action():
    """include_pearch=True → ação 'bulk_search' debitada, pipeline completo invocado."""
    from app.domains.sourcing.agents import sourcing_tool_registry
    from lia_models.pearch import HybridSearchRequest

    factory, _session = _fake_session_factory()
    fake_response = _fake_hybrid_response(local_count=2, pearch_count=3)

    hybrid_mock = AsyncMock(return_value=fake_response)
    enrich_mock = AsyncMock(side_effect=_passthrough_enrich)
    consume_mock = AsyncMock(return_value=(True, 42))

    with patch.object(sourcing_tool_registry, "AsyncSessionLocal", factory), \
         patch(
             "app.domains.sourcing.services.pearch_service.pearch_service.hybrid_search",
             hybrid_mock,
         ), \
         patch(
             "app.api.v1.candidate_search._shared.enrich_and_filter_candidates",
             enrich_mock,
         ), \
         patch(
             "app.domains.credits.services.credit_service.credit_service.consume_action",
             consume_mock,
         ):
        result = await sourcing_tool_registry._wrap_search_candidates(
            company_id=COMPANY_ID,
            user_id=USER_ID,
            role="Desenvolvedor Python",
            skills=["python", "django"],
            location="São Paulo",
            experience_level="senior",
            limit=10,
            include_pearch=True,
            pearch_limit=15,
        )

    assert result["success"] is True
    assert result["data"]["total_results"] == 5
    assert result["data"]["local_count"] == 2
    assert result["data"]["pearch_count"] == 3
    assert result["data"]["thread_id"] == "thread-xyz"

    # (a) hybrid_search invocado com a query/limites esperados
    hybrid_mock.assert_awaited_once()
    call_args = hybrid_mock.await_args
    request_arg = call_args.args[1]
    assert isinstance(request_arg, HybridSearchRequest)
    assert "Desenvolvedor Python" in request_arg.query
    assert "python" in request_arg.query
    assert request_arg.local_limit == 10
    assert request_arg.pearch_limit == 15
    assert request_arg.include_pearch is True
    assert request_arg.search_spec["role"] == "Desenvolvedor Python"
    assert request_arg.search_spec["location"] == "São Paulo"
    assert request_arg.search_spec["skills"] == ["python", "django"]
    assert request_arg.search_spec["seniority"] == "senior"

    # (b) enrich_and_filter_candidates invocado com os candidatos combinados
    enrich_mock.assert_awaited_once()
    enriched_arg = enrich_mock.await_args.args[1]
    assert len(enriched_arg) == 5  # 2 local + 3 pearch

    # (c) consume_action debitado com a ação 'bulk_search' (porque include_pearch=True)
    consume_mock.assert_awaited_once()
    consume_kwargs = consume_mock.await_args.kwargs
    consume_args = consume_mock.await_args.args
    # Assinatura: consume_action(self, db, company_id, action_type, ...)
    # Como o patch é no método ligado, args = (db, company_id, action_type)
    assert consume_args[1] == COMPANY_ID
    assert consume_args[2] == "bulk_search"
    assert consume_kwargs.get("reference_type") == "search"
    assert consume_kwargs.get("reference_id") == "thread-xyz"
    assert consume_kwargs.get("performed_by") == USER_ID


@pytest.mark.asyncio
async def test_search_candidates_uses_search_action_when_pearch_disabled():
    """include_pearch=False → ação 'search' (não 'bulk_search') debitada."""
    from app.domains.sourcing.agents import sourcing_tool_registry

    factory, _session = _fake_session_factory()
    fake_response = _fake_hybrid_response(local_count=4, pearch_count=0)

    hybrid_mock = AsyncMock(return_value=fake_response)
    enrich_mock = AsyncMock(side_effect=_passthrough_enrich)
    consume_mock = AsyncMock(return_value=(True, 99))

    with patch.object(sourcing_tool_registry, "AsyncSessionLocal", factory), \
         patch(
             "app.domains.sourcing.services.pearch_service.pearch_service.hybrid_search",
             hybrid_mock,
         ), \
         patch(
             "app.api.v1.candidate_search._shared.enrich_and_filter_candidates",
             enrich_mock,
         ), \
         patch(
             "app.domains.credits.services.credit_service.credit_service.consume_action",
             consume_mock,
         ):
        result = await sourcing_tool_registry._wrap_search_candidates(
            company_id=COMPANY_ID,
            user_id=USER_ID,
            query="data engineer remoto",
            include_pearch=False,
        )

    assert result["success"] is True

    hybrid_mock.assert_awaited_once()
    request_arg = hybrid_mock.await_args.args[1]
    assert request_arg.query == "data engineer remoto"
    assert request_arg.include_pearch is False
    assert request_arg.pearch_limit == 0

    enrich_mock.assert_awaited_once()

    consume_mock.assert_awaited_once()
    consume_args = consume_mock.await_args.args
    assert consume_args[2] == "search"
