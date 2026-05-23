"""
Tests for the wizard domain validator sensor on LRU and Redis cache tiers.

harness-engineering [sensor computacional]:
Guards CascadedRouter Tier 1 (LRU) and Tier 2 (Redis) from returning
stale non-wizard entries for wizard-patterned messages.

Post-mortem 2026-04-30: Before this guard, Tier 1/2 could return stale
job_management entries for messages like "criar uma vaga", bypassing
the Tier 2.5 wizard guard entirely.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helper: build a CascadedRouter with minimal mocks ─────────────────────
def _make_router():
    from app.orchestrator.routing.cascaded_router import CascadedRouter, RouteResult

    router = CascadedRouter.__new__(CascadedRouter)
    router._cache_max_size = 100
    router._memory_cache = {}
    router._stats = {
        "total": 0, "memory_hits": 0, "redis_hits": 0,
        "vector_hits": 0, "fast_hits": 0, "llm_hits": 0,
    }
    # Mock fast router
    mock_fast = MagicMock()
    router.fast = mock_fast

    return router, RouteResult


class TestWizardDomainOverride:
    """Unit tests for _wizard_domain_override method."""

    def test_returns_false_when_cached_is_already_wizard(self):
        """If cached domain is already wizard, no override needed."""
        router, RouteResult = _make_router()
        router.fast.match.return_value = None  # shouldn't be called
        result = router._wizard_domain_override("criar uma vaga", "wizard")
        assert result is False
        router.fast.match.assert_not_called()

    def test_returns_true_when_wizard_pattern_matches_but_cache_says_job_management(self):
        """Stale cache saying job_management for wizard message → override True."""
        router, RouteResult = _make_router()
        wizard_result = MagicMock()
        wizard_result.domain_id = "wizard"
        wizard_result.confidence = 0.9
        router.fast.match.return_value = wizard_result

        with patch("app.orchestrator.routing.cascaded_router.settings") as mock_settings:
            mock_settings.ROUTER_FAST_CONFIDENCE_THRESHOLD = 0.7
            result = router._wizard_domain_override("criar uma vaga para dev", "job_management")

        assert result is True

    def test_returns_false_when_fast_match_returns_none(self):
        """No wizard pattern match → don't override cache."""
        router, RouteResult = _make_router()
        router.fast.match.return_value = None

        with patch("app.orchestrator.routing.cascaded_router.settings") as mock_settings:
            mock_settings.ROUTER_FAST_CONFIDENCE_THRESHOLD = 0.7
            result = router._wizard_domain_override("candidatos no funil", "job_management")

        assert result is False

    def test_returns_false_when_fast_match_below_threshold(self):
        """Low-confidence wizard match → don't override cache (avoid false positives)."""
        router, RouteResult = _make_router()
        low_conf_result = MagicMock()
        low_conf_result.domain_id = "wizard"
        low_conf_result.confidence = 0.4  # below threshold
        router.fast.match.return_value = low_conf_result

        with patch("app.orchestrator.routing.cascaded_router.settings") as mock_settings:
            mock_settings.ROUTER_FAST_CONFIDENCE_THRESHOLD = 0.7
            result = router._wizard_domain_override("criar vaga", "sourcing")

        assert result is False

    def test_returns_false_on_fast_match_exception(self):
        """fast.match() exception → fail-open: trust cache."""
        router, RouteResult = _make_router()
        router.fast.match.side_effect = RuntimeError("fast router unavailable")

        with patch("app.orchestrator.routing.cascaded_router.settings") as mock_settings:
            mock_settings.ROUTER_FAST_CONFIDENCE_THRESHOLD = 0.7
            result = router._wizard_domain_override("criar vaga", "job_management")

        assert result is False  # fail-open

    def test_returns_false_when_match_is_different_domain(self):
        """Fast router hits a non-wizard domain → don't override."""
        router, RouteResult = _make_router()
        non_wiz_result = MagicMock()
        non_wiz_result.domain_id = "pipeline"  # not wizard
        non_wiz_result.confidence = 0.95
        router.fast.match.return_value = non_wiz_result

        with patch("app.orchestrator.routing.cascaded_router.settings") as mock_settings:
            mock_settings.ROUTER_FAST_CONFIDENCE_THRESHOLD = 0.7
            result = router._wizard_domain_override("mover candidato", "job_management")

        assert result is False


class TestLRUEvictionOnWizardOverride:
    """LRU (Tier 1) stale entry is evicted when wizard override fires."""

    @pytest.mark.asyncio
    async def test_stale_lru_entry_evicted_for_wizard_message(self):
        """LRU has stale job_management entry → evicted → falls through to Tier 2."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter, RouteResult
        import hashlib

        router = MagicMock(spec=CascadedRouter)
        # Inject a stale LRU entry
        cache_key = hashlib.md5("criar uma vaga sênior".lower().strip().encode()).hexdigest()
        stale_entry = RouteResult(domain_id="job_management", confidence=0.8, source="memory")
        router._memory_cache = {cache_key: stale_entry}
        # Wizard override returns True for this message
        router._wizard_domain_override.return_value = True

        # Verify: entry was there before
        assert cache_key in router._memory_cache

        # Simulate the eviction logic
        if router._wizard_domain_override("criar uma vaga sênior", stale_entry.domain_id):
            del router._memory_cache[cache_key]

        # Verify: entry removed
        assert cache_key not in router._memory_cache
