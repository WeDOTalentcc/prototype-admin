"""
Testes E2E para CascadedRouter — 6 tiers em cascata completa.

Valida o fluxo de roteamento end-to-end com mocks por tier, garantindo que:
- Stats são contabilizadas corretamente por tier
- Fallback ClarificationOutput é emitido quando todos os tiers falham
- Cache em memória funciona na segunda chamada
- Domínios canônicos são retornados
- Degradação graceful quando tiers estão indisponíveis

Camada 3 (Integração) da pirâmide — mocks de Redis/pgvector/LLM.

Task #1144: toda chamada a router.route() DEVE passar context={"company_id": ...}
(multi-tenancy invariante — ENVIRONMENT=production no Replit faz
record_namespace_violation lançar RuntimeError quando company_id ausente).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Constante de tenant para testes — UUID fixo, não conflita com prod
# ---------------------------------------------------------------------------

_TEST_COMPANY_ID = "00000000-test-cccc-aaaa-000000000001"
_TEST_CONTEXT = {"company_id": _TEST_COMPANY_ID}


# ---------------------------------------------------------------------------
# Helpers — RouteResult mock
# ---------------------------------------------------------------------------

def _make_route_result(
    domain_id: str = "job_management",
    confidence: float = 0.95,
    source: str = "fast_router",
    cached: bool = False,
    needs_clarification: bool = False,
    clarification_question: Optional[str] = None,
    clarification_options: Optional[list] = None,
):
    from app.orchestrator.routing.cascaded_router import RouteResult
    return RouteResult(
        domain_id=domain_id,
        confidence=confidence,
        source=source,
        cached=cached,
        needs_clarification=needs_clarification,
        clarification_question=clarification_question,
        clarification_options=clarification_options or [],
    )


def _make_router_with_mocks(
    memory_hit=None,
    redis_hit=None,
    vector_hit=None,
    fast_match=None,
    llm_result=None,
):
    """Cria CascadedRouter com todos os tiers mockados.

    Task #1144: todos os callers DEVEM passar context=_TEST_CONTEXT para
    satisfazer o invariante de multi-tenancy (company_id obrigatório na
    chave Redis). ENVIRONMENT=production no Replit faz
    record_namespace_violation lançar RuntimeError quando ausente.
    """
    from app.orchestrator.routing.cascaded_router import CascadedRouter

    router = CascadedRouter()

    # Tier 0: MemoryResolver (in-process LRU)
    router._memory_cache.clear()
    if memory_hit:
        router._memory_cache["hash_key_test"] = memory_hit

    # Tier 1: Redis hash
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=redis_hit)
    mock_redis.set = AsyncMock()
    router._redis_cache = mock_redis

    # Tier 2: VectorSemanticCache (pgvector)
    mock_vector = MagicMock()
    mock_vector.get = AsyncMock(return_value=vector_hit)
    mock_vector.set = AsyncMock()
    router._vector_cache = mock_vector

    # Tier 3: FastRouter (regex)
    router.fast = MagicMock()
    router.fast.match = MagicMock(return_value=fast_match)

    # Tier 4: LLM Cascade
    router._route_via_llm_cascade = AsyncMock(return_value=llm_result)

    return router


# ---------------------------------------------------------------------------
# Seção 1: Tier Fast Router (Tier 3)
# ---------------------------------------------------------------------------

class TestCascadedRouterFastTier:

    @pytest.mark.asyncio
    async def test_fast_router_tier_returns_result(self):
        """Quando FastRouter dá match, retorna resultado com source=fast_router."""
        fast_result = MagicMock()
        fast_result.domain_id = "job_management"
        fast_result.confidence = 0.9

        router = _make_router_with_mocks(fast_match=fast_result)
        result = await router.route("criar vaga de desenvolvedor", context=_TEST_CONTEXT)

        assert result.domain_id == "job_management"
        assert result.source == "fast_router"

    @pytest.mark.asyncio
    async def test_fast_router_increments_stats(self):
        """Fast router hit incrementa stats[fast_hits]."""
        fast_result = MagicMock()
        fast_result.domain_id = "sourcing"
        fast_result.confidence = 0.85

        router = _make_router_with_mocks(fast_match=fast_result)
        router._stats["fast_hits"] = 0

        await router.route("buscar candidatos", context=_TEST_CONTEXT)
        assert router._stats.get("fast_hits", 0) >= 1

    @pytest.mark.asyncio
    async def test_fast_router_confidence_meets_threshold(self):
        """Resultado do fast router tem confidence >= threshold."""
        fast_result = MagicMock()
        fast_result.domain_id = "cv_screening"
        fast_result.confidence = 0.88

        router = _make_router_with_mocks(fast_match=fast_result)
        result = await router.route("analisar cv do candidato", context=_TEST_CONTEXT)

        assert result.confidence >= 0.7


# ---------------------------------------------------------------------------
# Seção 2: Cache em Memória (Tier 0 — 2ª chamada)
# ---------------------------------------------------------------------------

class TestCascadedRouterMemoryCache:

    @pytest.mark.asyncio
    async def test_second_call_uses_memory_cache(self):
        """Segunda chamada com mesma query usa cache em memória."""
        fast_result = MagicMock()
        fast_result.domain_id = "job_management"
        fast_result.confidence = 0.9
        router = _make_router_with_mocks(fast_match=fast_result)

        # Primeira chamada
        result1 = await router.route("criar vaga de desenvolvedor", context=_TEST_CONTEXT)
        # Segunda chamada — deve bater no cache
        result2 = await router.route("criar vaga de desenvolvedor", context=_TEST_CONTEXT)

        assert result2.cached is True
        assert result2.domain_id == result1.domain_id

    @pytest.mark.asyncio
    async def test_memory_cache_hit_increments_stats(self):
        """Cache em memória incrementa memory_hits nas stats."""
        fast_result = MagicMock()
        fast_result.domain_id = "analytics"
        fast_result.confidence = 0.9
        router = _make_router_with_mocks(fast_match=fast_result)
        router._stats["memory_hits"] = 0

        await router.route("relatório de pipeline", context=_TEST_CONTEXT)
        await router.route("relatório de pipeline", context=_TEST_CONTEXT)  # segunda chamada → cache

        assert router._stats.get("memory_hits", 0) >= 1


# ---------------------------------------------------------------------------
# Seção 3: ClarificationOutput (fallback quando todos os tiers falham)
# ---------------------------------------------------------------------------

class TestCascadedRouterClarification:

    @pytest.mark.asyncio
    async def test_clarification_when_all_tiers_fail(self):
        """Quando todos os tiers falham, retorna clarification_needed=True."""
        router = _make_router_with_mocks(
            memory_hit=None,
            redis_hit=None,
            vector_hit=None,
            fast_match=None,
            llm_result=None,
        )
        result = await router.route("xyzzy nonsense 999 aaa bbb ccc", context=_TEST_CONTEXT)

        assert result.needs_clarification is True
        assert result.source == "clarification_needed"
        assert result.domain_id == "recruiter_assistant"

    @pytest.mark.asyncio
    async def test_clarification_has_question(self):
        """Resultado de clarification tem clarification_question não vazio."""
        router = _make_router_with_mocks(fast_match=None, llm_result=None)
        result = await router.route("algo absolutamente ambíguo 0xdeadbeef", context=_TEST_CONTEXT)

        assert result.needs_clarification is True
        assert result.clarification_question is not None
        assert len(result.clarification_question) > 5

    @pytest.mark.asyncio
    async def test_clarification_has_options(self):
        """Resultado de clarification tem lista de opções."""
        router = _make_router_with_mocks(fast_match=None, llm_result=None)
        result = await router.route("xyz abc def 12345", context=_TEST_CONTEXT)

        assert result.needs_clarification is True
        assert isinstance(result.clarification_options, list)
        assert len(result.clarification_options) >= 2

    @pytest.mark.asyncio
    async def test_no_clarification_when_fast_router_succeeds(self):
        """Quando fast router dá match, NÃO há clarification."""
        fast_result = MagicMock()
        fast_result.domain_id = "sourcing"
        fast_result.confidence = 0.9
        router = _make_router_with_mocks(fast_match=fast_result)

        result = await router.route("buscar candidatos para vaga", context=_TEST_CONTEXT)
        assert result.needs_clarification is False

    @pytest.mark.asyncio
    async def test_clarification_stat_incremented(self):
        """clarification_needed incrementa stats[clarification_issued]."""
        router = _make_router_with_mocks(fast_match=None, llm_result=None)
        router._stats["clarification_issued"] = 0

        await router.route("incompreensível xyzzy 99999", context=_TEST_CONTEXT)
        assert router._stats.get("clarification_issued", 0) >= 1


# ---------------------------------------------------------------------------
# Seção 4: RouteResult — campos e domínios canônicos
# ---------------------------------------------------------------------------

class TestRouteResultContract:

    @pytest.mark.asyncio
    async def test_route_result_has_domain_id(self):
        """RouteResult sempre tem domain_id."""
        fast_result = MagicMock()
        fast_result.domain_id = "communication"
        fast_result.confidence = 0.8
        router = _make_router_with_mocks(fast_match=fast_result)

        result = await router.route("enviar email para candidato", context=_TEST_CONTEXT)
        assert result.domain_id is not None
        assert result.domain_id != ""

    @pytest.mark.asyncio
    async def test_route_result_has_confidence(self):
        """RouteResult sempre tem confidence float."""
        fast_result = MagicMock()
        fast_result.domain_id = "ats_integration"
        fast_result.confidence = 0.75
        router = _make_router_with_mocks(fast_match=fast_result)

        result = await router.route("sincronizar gupy", context=_TEST_CONTEXT)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_route_result_has_source(self):
        """RouteResult sempre tem source identificando o tier."""
        fast_result = MagicMock()
        fast_result.domain_id = "job_management"
        fast_result.confidence = 0.9
        router = _make_router_with_mocks(fast_match=fast_result)

        result = await router.route("criar vaga", context=_TEST_CONTEXT)
        assert result.source in (
            "memory_cache", "redis_cache", "vector_cache",
            "fast_router", "llm_cascade", "clarification_needed"
        )

    @pytest.mark.asyncio
    async def test_canonical_domain_ids_only(self):
        """Router retorna apenas domain_ids canônicos."""
        CANONICAL = {
            "sourcing", "job_management", "cv_screening",
            "communication", "analytics", "interview_scheduling",
            "ats_integration", "automation", "recruiter_assistant",
        }
        queries = [
            ("buscar candidatos", "sourcing"),
            ("criar vaga", "job_management"),
            ("analisar cv", "cv_screening"),
            ("enviar email candidato", "communication"),
        ]
        for query, expected_domain in queries:
            fast_result = MagicMock()
            fast_result.domain_id = expected_domain
            fast_result.confidence = 0.9
            router = _make_router_with_mocks(fast_match=fast_result)

            result = await router.route(query, context=_TEST_CONTEXT)
            assert result.domain_id in CANONICAL, (
                f"Query {query} retornou domain_id não canônico: {result.domain_id}"
            )


# ---------------------------------------------------------------------------
# Seção 5: Stats e observabilidade
# ---------------------------------------------------------------------------

class TestCascadedRouterStats:

    @pytest.mark.asyncio
    async def test_get_stats_returns_dict(self):
        """get_stats() retorna dicionário com contadores."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()
        stats = router.get_stats()
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_stats_keys_present(self):
        """Stats contém chaves esperadas."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()
        stats = router.get_stats()
        for key in ("memory_hits", "fast_hits"):
            assert key in stats, f"Stats não tem chave {key}"

    @pytest.mark.asyncio
    async def test_stats_increment_on_route(self):
        """Stats incrementam após route() bem-sucedido."""
        fast_result = MagicMock()
        fast_result.domain_id = "automation"
        fast_result.confidence = 0.9
        router = _make_router_with_mocks(fast_match=fast_result)
        initial_total = sum(router._stats.values())

        await router.route("criar tarefa urgente", context=_TEST_CONTEXT)
        final_total = sum(router._stats.values())
        assert final_total > initial_total
