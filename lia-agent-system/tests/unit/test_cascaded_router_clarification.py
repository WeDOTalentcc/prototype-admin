"""
Testes unitários para CascadedRouter — clarification_needed e VectorSemanticCache tier.

Cobertura:
  - test_clarification_when_all_tiers_fail           — todos os tiers falham → clarification
  - test_no_clarification_when_fast_router_succeeds  — fast router match não gera clarification
  - test_clarification_result_has_question_and_options — ClarificationOutput tem campos corretos
  - test_vector_tier_stats_tracked                   — stats["vector_hits"] incrementa corretamente
  - test_no_clarification_when_redis_hits            — redis hit não gera clarification
  - test_no_clarification_when_llm_cascade_succeeds  — LLM cascade evita clarification
  - test_clarification_issued_stat_incremented       — stat clarification_issued incrementa
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field
from typing import Optional, List

from app.orchestrator.routing.cascaded_router import (
    CascadedRouter,
    RouteResult,
    _build_clarification_question,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_router(
    fast_match=None,
    redis_hit=None,
    vector_hit=None,
    llm_cascade_result=None,
) -> CascadedRouter:
    """Cria CascadedRouter com mocks injetados."""
    router = CascadedRouter()

    router._redis_cache = MagicMock()
    router._redis_cache.get = AsyncMock(return_value=redis_hit)
    router._redis_cache.set = AsyncMock()

    if vector_hit is not None:
        mock_vector = MagicMock()
        mock_vector.get = AsyncMock(return_value=vector_hit)
        mock_vector.set = AsyncMock()
        mock_vector.threshold = 0.92
        router._vector_cache = mock_vector
    else:
        mock_vector = MagicMock()
        mock_vector.get = AsyncMock(return_value=None)
        mock_vector.set = AsyncMock()
        mock_vector.threshold = 0.92
        router._vector_cache = mock_vector

    router.fast = MagicMock()
    router.fast.match = MagicMock(return_value=fast_match)

    router._llm_cascade_result = llm_cascade_result

    return router


# ---------------------------------------------------------------------------
# test_clarification_when_all_tiers_fail
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clarification_when_all_tiers_fail():
    """Quando todos os tiers falham, deve retornar needs_clarification=True."""
    router = _make_router(
        fast_match=None,
        redis_hit=None,
        vector_hit=None,
    )
    router.llm_fallback = None

    async def _no_cascade(*args, **kwargs):
        return None

    with patch.object(router, "_route_via_llm_cascade", new=AsyncMock(return_value=None)):
        result = await router.route("xkcd randomfoo xyz 12345")

    assert result.needs_clarification is True
    assert result.source == "clarification_needed"
    assert result.clarification_question is not None
    assert len(result.clarification_question) > 0


# ---------------------------------------------------------------------------
# test_no_clarification_when_fast_router_succeeds
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_clarification_when_fast_router_succeeds():
    """Fast router match com alta confiança não deve gerar clarification."""
    from app.orchestrator.routing.fast_router import FastRouteResult

    fast_hit = FastRouteResult(
        domain_id="job_management",
        confidence=0.95,
        matched_pattern="criar vaga",
        matched_text="criar uma vaga de desenvolvedor",
    )
    router = _make_router(fast_match=fast_hit)

    with patch.object(router, "_route_via_llm_cascade", new=AsyncMock(return_value=None)):
        result = await router.route("criar uma vaga de desenvolvedor")

    assert result.needs_clarification is False
    assert result.domain_id == "job_management"
    assert result.source == "fast_router"


# ---------------------------------------------------------------------------
# test_clarification_result_has_question
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clarification_result_has_question():
    """RouteResult de clarification deve ter question preenchido."""
    router = _make_router()
    router.llm_fallback = None

    with patch.object(router, "_route_via_llm_cascade", new=AsyncMock(return_value=None)):
        result = await router.route("gibberish text 9999")

    assert result.needs_clarification is True
    assert isinstance(result.clarification_question, str)
    assert len(result.clarification_question) > 10


# ---------------------------------------------------------------------------
# test_vector_tier_stats_tracked
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vector_tier_stats_tracked():
    """Quando VectorSemanticCache hit, stats['vector_hits'] deve incrementar."""
    vector_result = {
        "domain_id": "sourcing",
        "confidence": 0.93,
        "source": "fast_router",
        "cache_source": "vector_cache",
    }
    router = _make_router(vector_hit=vector_result)

    result = await router.route("buscar candidatos qualificados para engenharia")

    assert router._stats["vector_hits"] == 1
    assert result.domain_id == "sourcing"
    assert result.source == "vector_cache"


# ---------------------------------------------------------------------------
# test_no_clarification_when_redis_hits
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_clarification_when_redis_hits():
    """Redis cache hit não deve gerar clarification."""
    redis_result = {
        "domain_id": "cv_screening",
        "confidence": 0.85,
        "matched_pattern": "triagem",
    }
    router = _make_router(redis_hit=redis_result)

    result = await router.route("fazer triagem de candidatos")

    assert result.needs_clarification is False
    assert result.domain_id == "cv_screening"
    assert result.source == "redis_cache"
    assert result.cached is True


# ---------------------------------------------------------------------------
# test_no_clarification_when_llm_cascade_succeeds
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_clarification_when_llm_cascade_succeeds():
    """LLM cascade com resultado válido deve evitar clarification."""
    cascade_result = RouteResult(
        domain_id="analytics",
        confidence=0.78,
        source="llm_cascade:haiku",
    )
    router = _make_router()
    router.llm_fallback = None

    with patch.object(router, "_route_via_llm_cascade", new=AsyncMock(return_value=cascade_result)):
        result = await router.route("mostrar relatório de contratações do mês")

    assert result.needs_clarification is False
    assert result.domain_id == "analytics"


# ---------------------------------------------------------------------------
# test_clarification_issued_stat_incremented
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clarification_issued_stat_incremented():
    """Stat clarification_issued deve incrementar a cada clarification emitida."""
    router = _make_router()
    router.llm_fallback = None

    with patch.object(router, "_route_via_llm_cascade", new=AsyncMock(return_value=None)):
        await router.route("fdjksahf 999 xyz")
        await router.route("zxcvbnm qwerty")

    assert router._stats["clarification_issued"] == 2
    assert router._stats["total"] == 2


# ---------------------------------------------------------------------------
# test_build_clarification_question
# ---------------------------------------------------------------------------

def test_build_clarification_question_with_message():
    """_build_clarification_question deve incluir trecho da mensagem."""
    question, options = _build_clarification_question("criar uma vaga urgente")
    assert "criar uma vaga urgente" in question


def test_build_clarification_question_empty():
    """_build_clarification_question com mensagem vazia deve retornar texto padrão."""
    question, options = _build_clarification_question("")
    assert len(question) > 0
    assert "?" in question
    assert isinstance(options, list)
    assert len(options) >= 3


def test_build_clarification_question_with_partial_matches():
    """_build_clarification_question com partial matches gera opções contextuais."""
    partial = [
        {"domain_id": "job_planner"},
        {"domain_id": "sourcing"},
    ]
    question, options = _build_clarification_question("preciso de ajuda", partial_matches=partial)
    assert len(question) > 0
    assert len(options) >= 1


# ---------------------------------------------------------------------------
# test_get_stats_includes_vector_hit_rate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_stats_includes_vector_hit_rate():
    """get_stats() deve incluir vector_hit_rate."""
    router = _make_router()
    stats = router.get_stats()

    assert "vector_hits" in stats
    assert "vector_hit_rate" in stats
    assert "clarification_issued" in stats
    assert "clarification_rate" in stats


# ---------------------------------------------------------------------------
# test_vector_cache_hit_stored_in_memory_cache
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vector_cache_hit_stored_in_memory_cache():
    """Hit de vector cache deve ser armazenado no LRU in-process."""
    vector_result = {
        "domain_id": "job_management",
        "confidence": 0.94,
        "source": "fast_router",
        "cache_source": "vector_cache",
    }
    router = _make_router(vector_hit=vector_result)

    msg = "criar uma nova vaga para desenvolvedor python"
    await router.route(msg)

    import hashlib
    key = hashlib.md5(msg.lower().strip().encode()).hexdigest()
    assert key in router._memory_cache
    assert router._memory_cache[key].domain_id == "job_management"
