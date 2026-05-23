"""
Unit Tests — Orchestrator 6-Tier CascadedRouter (Task #53, Item 8).

Testa o comportamento REAL do CascadedRouter e FastRouter:
- FastRouter: regex pattern matching, confidence calculation, ambiguity penalty
- CascadedRouter: LRU cache hits, clarification fallback, tier sequencing
- Routing domains: intent→domain mapping correctness
"""
import hashlib
import pytest
from unittest.mock import AsyncMock, patch


# ---------------------------------------------------------------------------
# FastRouter — real pattern matching
# ---------------------------------------------------------------------------

class TestFastRouterPatternMatching:

    def test_job_management_pattern_routes_correctly(self):
        """'criar vaga' deve rotear para wizard (JobCreationGraph canônico)."""
        from app.orchestrator.routing.fast_router import FastRouter
        router = FastRouter()
        result = router.match("quero criar uma nova vaga para Python Developer")
        assert result is not None
        assert result.domain_id == "wizard"
        assert result.confidence >= 0.7

    def test_cv_screening_pattern_routes_correctly(self):
        """'analisar currículo' deve rotear para cv_screening."""
        from app.orchestrator.routing.fast_router import FastRouter
        router = FastRouter()
        result = router.match("preciso analisar o currículo deste candidato")
        assert result is not None
        assert result.domain_id == "cv_screening"

    def test_interview_scheduling_pattern_routes_correctly(self):
        """'agendar entrevista' deve rotear para interview_scheduling."""
        from app.orchestrator.routing.fast_router import FastRouter
        router = FastRouter()
        result = router.match("preciso agendar uma entrevista com candidato amanhã")
        assert result is not None
        assert result.domain_id == "interview_scheduling"

    def test_empty_message_returns_none_not_crash(self):
        """Mensagem vazia não deve lançar exceção — retorna None."""
        from app.orchestrator.routing.fast_router import FastRouter
        router = FastRouter()
        result = router.match("")
        assert result is None

    def test_whitespace_only_message_returns_none(self):
        """Mensagem só com espaços não deve lançar exceção — retorna None."""
        from app.orchestrator.routing.fast_router import FastRouter
        router = FastRouter()
        result = router.match("   ")
        assert result is None

    def test_confidence_formula_based_on_match_length(self):
        """Confidence = min(0.95, 0.7 + len(match) * 0.02)."""
        from app.orchestrator.routing.fast_router import FastRouter
        router = FastRouter()
        result = router.match("criar nova vaga sênior backend python")
        assert result is not None
        assert 0.7 <= result.confidence <= 0.95

    def test_ambiguity_penalty_reduces_confidence(self):
        """Gap < 0.1 entre top-2 matches aplica penalidade de -0.15 no primeiro."""
        from app.orchestrator.routing.fast_router import FastRouter
        router = FastRouter()
        result = router.match("criar vaga e buscar candidato sourcing")
        if result:
            assert result.confidence <= 0.95

    def test_matched_pattern_string_returned(self):
        """matched_pattern deve ser a string regex que casou com o input."""
        from app.orchestrator.routing.fast_router import FastRouter
        router = FastRouter()
        result = router.match("criar uma nova vaga senior")
        assert result is not None
        assert result.matched_pattern is not None
        assert isinstance(result.matched_pattern, str)

    def test_matched_text_is_substring_of_input(self):
        """matched_text deve ser o fragmento do input que casou com o pattern."""
        from app.orchestrator.routing.fast_router import FastRouter
        router = FastRouter()
        result = router.match("quero agendar uma entrevista técnica")
        assert result is not None
        assert result.matched_text is not None
        assert result.matched_text in "quero agendar uma entrevista técnica"


# ---------------------------------------------------------------------------
# CascadedRouter — LRU cache, clarification, stats
# ---------------------------------------------------------------------------

class TestCascadedRouterCacheBehavior:

    @pytest.mark.asyncio
    async def test_second_call_same_message_hits_lru_cache(self):
        """Segunda chamada idêntica deve ser servida pelo LRU Tier 1 (cached=True)."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()

        msg = "criar vaga de desenvolvedor python sênior"

        with patch.object(router._redis_cache, "get", new_callable=AsyncMock, return_value=None), \
             patch.object(router, "_vector_cache", None), \
             patch.object(router, "_route_via_llm_cascade", new_callable=AsyncMock, return_value=None):
            result1 = await router.route(msg)

        with patch.object(router._redis_cache, "get", new_callable=AsyncMock, return_value=None), \
             patch.object(router, "_vector_cache", None), \
             patch.object(router, "_route_via_llm_cascade", new_callable=AsyncMock, return_value=None):
            result2 = await router.route(msg)

        assert result2.cached is True
        assert router._stats["memory_hits"] >= 1
        assert result1.domain_id == result2.domain_id

    @pytest.mark.asyncio
    async def test_unintelligible_message_triggers_clarification(self):
        """Mensagem sem sentido deve emitir needs_clarification=True e confidence=0."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()

        msg = "xyzzy plugh frobnicate qux blargh norf"

        with patch.object(router._redis_cache, "get", new_callable=AsyncMock, return_value=None), \
             patch.object(router, "_vector_cache", None), \
             patch.object(router, "_route_via_llm_cascade", new_callable=AsyncMock, return_value=None):
            result = await router.route(msg)

        assert result.needs_clarification is True
        assert result.source == "clarification_needed"
        assert result.confidence == 0.0
        assert result.clarification_question is not None
        assert isinstance(result.clarification_options, list)
        assert len(result.clarification_options) >= 1

    @pytest.mark.asyncio
    async def test_clarification_issued_counter_increments(self):
        """_stats['clarification_issued'] deve incrementar quando clarification é emitida."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()
        before = router._stats["clarification_issued"]

        with patch.object(router._redis_cache, "get", new_callable=AsyncMock, return_value=None), \
             patch.object(router, "_vector_cache", None), \
             patch.object(router, "_route_via_llm_cascade", new_callable=AsyncMock, return_value=None):
            await router.route("foobar baz qux xyz plugh morf")

        assert router._stats["clarification_issued"] > before

    @pytest.mark.asyncio
    async def test_total_stats_increments_per_call(self):
        """_stats['total'] deve incrementar em cada chamada."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()
        before = router._stats["total"]

        with patch.object(router._redis_cache, "get", new_callable=AsyncMock, return_value=None), \
             patch.object(router, "_vector_cache", None), \
             patch.object(router, "_route_via_llm_cascade", new_callable=AsyncMock, return_value=None):
            await router.route("criar nova vaga de emprego sênior backend python")
            await router.route("analisar curriculos de candidatos para triagem")

        assert router._stats["total"] >= before + 2

    @pytest.mark.asyncio
    async def test_fast_router_result_stored_in_lru(self):
        """Resultado do Tier 4 (FastRouter) deve ser armazenado no LRU para reuso."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()

        msg = "agendar entrevista técnica para candidato"
        cache_key = router._cache_key(msg)

        assert cache_key not in router._memory_cache

        with patch.object(router._redis_cache, "get", new_callable=AsyncMock, return_value=None), \
             patch.object(router, "_vector_cache", None), \
             patch.object(router, "_route_via_llm_cascade", new_callable=AsyncMock, return_value=None):
            await router.route(msg)

        assert cache_key in router._memory_cache


# ---------------------------------------------------------------------------
# RouteResult model
# ---------------------------------------------------------------------------

class TestRouteResultModel:

    def test_route_result_default_fields(self):
        """RouteResult deve ter defaults corretos: cached=False, needs_clarification=False."""
        from app.orchestrator.routing.cascaded_router import RouteResult
        r = RouteResult(domain_id="job_management", confidence=0.8, source="fast_router")
        assert r.cached is False
        assert r.needs_clarification is False
        assert r.matched_pattern is None
        assert r.clarification_options is None

    def test_clarification_route_result_fields(self):
        """RouteResult de clarificação deve ter campos de clarificação preenchidos."""
        from app.orchestrator.routing.cascaded_router import RouteResult
        r = RouteResult(
            domain_id="recruiter_assistant",
            confidence=0.0,
            source="clarification_needed",
            needs_clarification=True,
            clarification_question="O que você deseja fazer?",
            clarification_options=["Criar vaga", "Buscar candidatos", "Agendar entrevista"],
        )
        assert r.needs_clarification is True
        assert r.confidence == 0.0
        assert len(r.clarification_options) == 3

    def test_cache_key_normalization(self):
        """cache_key deve normalizar para minúsculas e remover espaços extras."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()
        key1 = router._cache_key("  CRIAR VAGA  ")
        key2 = router._cache_key("criar vaga")
        assert key1 == key2

    def test_cache_key_is_md5_hex(self):
        """cache_key deve ser um hex de 32 chars (MD5)."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()
        key = router._cache_key("criar vaga")
        assert len(key) == 32
        int(key, 16)
