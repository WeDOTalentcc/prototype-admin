"""
Tests — Z5-03: Threshold Semântico configurável + A/B flag no CascadedRouter.

Cobre:
  1.  settings inclui ROUTER_VECTOR_SIMILARITY_THRESHOLD com default 0.85
  2.  settings inclui ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN com default 0.05
  3.  settings inclui ROUTER_VECTOR_CACHE_ENABLED com default True
  4.  VectorSemanticCache usa threshold do settings quando não passado explicitamente
  5.  VectorSemanticCache aceita threshold explícito
  6.  CascadedRouter._init_vector_cache retorna None quando ROUTER_VECTOR_CACHE_ENABLED=False
  7.  CascadedRouter._init_vector_cache passa threshold correto ao VectorSemanticCache
  8.  CascadedRouter pula Tier 3 quando vector cache desabilitado
  9.  near-miss logging ocorre quando similaridade está dentro da margem
  10. Z5-02: shim emite DeprecationWarning
  11. Z5-02: canonical import funciona sem warning
"""
import warnings
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── 1-3. Settings contêm os novos campos ──────────────────────────────────────

def test_settings_has_vector_similarity_threshold():
    from app.core.config import settings
    assert hasattr(settings, "ROUTER_VECTOR_SIMILARITY_THRESHOLD")
    assert 0 < settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD <= 1.0
    assert settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD == 0.85


def test_settings_has_near_miss_log_margin():
    from app.core.config import settings
    assert hasattr(settings, "ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN")
    assert 0 < settings.ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN < 0.5


def test_settings_has_vector_cache_enabled():
    from app.core.config import settings
    assert hasattr(settings, "ROUTER_VECTOR_CACHE_ENABLED")
    assert settings.ROUTER_VECTOR_CACHE_ENABLED is True


# ── 4. VectorSemanticCache usa threshold do settings ─────────────────────────

def test_vector_cache_uses_settings_threshold():
    from app.orchestrator.memory.vector_semantic_cache import VectorSemanticCache
    with patch("lia_config.config.settings") as mock_settings:
        mock_settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD = 0.85
        cache = VectorSemanticCache()
        assert cache.threshold == 0.85


# ── 5. VectorSemanticCache aceita threshold explícito ────────────────────────

def test_vector_cache_accepts_explicit_threshold():
    from app.orchestrator.memory.vector_semantic_cache import VectorSemanticCache
    cache = VectorSemanticCache(similarity_threshold=0.75)
    assert cache.threshold == 0.75


# ── 6. CascadedRouter desabilita Tier 3 quando flag=False ─────────────────────

def test_router_disables_vector_cache_when_flag_false():
    from app.orchestrator.routing.cascaded_router import CascadedRouter
    with patch("app.orchestrator.routing.cascaded_router.settings") as mock_settings:
        mock_settings.ROUTER_VECTOR_CACHE_ENABLED = False
        mock_settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD = 0.92
        mock_settings.ROUTER_CACHE_MAX_SIZE = 1000
        mock_settings.ROUTER_CACHE_TTL = 3600
        router = CascadedRouter.__new__(CascadedRouter)
        result = router._init_vector_cache()
    assert result is None


# ── 7. CascadedRouter passa threshold correto ao VectorSemanticCache ─────────

def test_router_passes_threshold_to_vector_cache():
    from app.orchestrator.routing.cascaded_router import CascadedRouter
    with patch("app.orchestrator.routing.cascaded_router.settings") as mock_settings, \
         patch("app.orchestrator.memory.vector_semantic_cache.VectorSemanticCache") as MockVSC:
        mock_settings.ROUTER_VECTOR_CACHE_ENABLED = True
        mock_settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD = 0.88
        mock_settings.ROUTER_CACHE_MAX_SIZE = 1000
        mock_settings.ROUTER_CACHE_TTL = 3600
        MockVSC.return_value = MagicMock()
        router = CascadedRouter.__new__(CascadedRouter)
        router._init_vector_cache()
    MockVSC.assert_called_once_with(similarity_threshold=0.88)


# ── 8. CascadedRouter pula Tier 3 quando desabilitado (route()) ──────────────

@pytest.mark.asyncio
async def test_router_skips_tier3_when_disabled():
    from app.orchestrator.routing.cascaded_router import CascadedRouter
    from app.orchestrator.routing.fast_router import FastRouter

    fast_router = MagicMock(spec=FastRouter)
    fast_router.match.return_value = MagicMock(
        domain_id="sourcing", confidence=0.95, matched_pattern="buscar candidatos"
    )

    router = CascadedRouter.__new__(CascadedRouter)
    router.fast = fast_router
    router.llm_fallback = None
    router.registry = None
    router._memory_cache = {}
    router._cache_max_size = 1000
    router._vector_cache = None  # desabilitado
    router._stats = {
        "memory_hits": 0, "redis_hits": 0, "vector_hits": 0,
        "fast_hits": 0, "llm_hits": 0, "clarification_issued": 0, "total": 0,
    }
    redis_cache_mock = MagicMock()
    redis_cache_mock.get = AsyncMock(return_value=None)
    redis_cache_mock.set = AsyncMock()
    router._redis_cache = redis_cache_mock

    with patch.object(router, "_apply_adaptive_adjustments", AsyncMock(side_effect=lambda r, c: r)):
        result = await router.route("buscar candidatos para vaga senior", context={})

    assert result.domain_id == "sourcing"
    assert result.source == "fast_router"
    assert router._stats["vector_hits"] == 0


# ── 9. near-miss logging ocorre dentro da margem ─────────────────────────────

@pytest.mark.asyncio
async def test_near_miss_logging_fires_within_margin(caplog):
    import logging
    from app.orchestrator.memory.vector_semantic_cache import VectorSemanticCache

    cache = VectorSemanticCache(similarity_threshold=0.92)

    # Simula: query principal retorna None (miss), near-miss retorna sim=0.89
    async def _fake_get_db():
        session = AsyncMock()
        # primeira chamada: miss (row=None)
        # segunda chamada: near-miss (sim=0.89)
        session.execute = AsyncMock(
            side_effect=[
                MagicMock(fetchone=MagicMock(return_value=None)),
                MagicMock(fetchone=MagicMock(return_value=("sourcing", 0.89))),
            ]
        )
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        return session

    with patch.object(cache, "_get_embedding", AsyncMock(return_value=[0.1, 0.2, 0.3])), \
         patch.object(cache, "_get_db", _fake_get_db), \
         patch("lia_config.config.settings") as mock_s:
        mock_s.ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN = 0.05
        with caplog.at_level(logging.DEBUG, logger="app.orchestrator.memory.vector_semantic_cache"):
            result = await cache._query_similar([0.1, 0.2, 0.3])

    assert result is None
    assert any("near-miss" in r.message for r in caplog.records)


# ── 10. Z5-02: shim emite DeprecationWarning ─────────────────────────────────

def test_shim_emits_deprecation_warning():
    import sys
    # Remove do cache para forçar re-import
    sys.modules.pop("app.agents.policy_setup_agent", None)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        import app.agents.policy_setup_agent  # noqa
        sys.modules.pop("app.agents.policy_setup_agent", None)
    assert any(issubclass(warning.category, DeprecationWarning) for warning in w)


# ── 11. Z5-02: canonical import funciona sem DeprecationWarning ──────────────

def test_canonical_import_no_warning():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from app.domains.policy.agents.agent import PolicySetupAgent  # noqa
    deprecations = [x for x in w if issubclass(x.category, DeprecationWarning)
                    and "policy_setup_agent" in str(x.message)]
    assert len(deprecations) == 0
    assert PolicySetupAgent is not None
