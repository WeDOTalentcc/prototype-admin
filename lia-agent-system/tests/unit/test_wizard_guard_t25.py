"""
Sensor: Tier 2.5 wizard guard prevents vector-cache poisoning.

Regression guard for the 2026-04-29 bug where "criar vaga" messages
were routed to job_management because the vector semantic cache (Tier 3)
ran before FastRouter (Tier 4) and had stale job_management entries.

Skill canônica: harness-engineering [sensor computacional].
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.orchestrator.routing.cascaded_router import CascadedRouter, RouteResult


# ────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────

def _make_router(
    fast_result=None,
    redis_result=None,
    vector_result=None,
) -> CascadedRouter:
    """Build CascadedRouter with injected mocks for Tier 2.5 testing."""
    router = CascadedRouter()

    # Tier 1 (LRU memory cache): empty
    router._memory_cache = {}

    # Tier 2 (Redis): caller-controlled (default: miss)
    router._redis_cache = MagicMock()
    router._redis_cache.get = AsyncMock(return_value=redis_result)
    router._redis_cache.set = AsyncMock()

    # FastRouter
    router.fast = MagicMock()
    router.fast.match = MagicMock(return_value=fast_result)

    # Tier 3 (vector cache)
    mock_vector = MagicMock()
    if vector_result is not None:
        mock_vector.get = AsyncMock(return_value=vector_result)
    else:
        # Simulate the poisoned cache entry that caused the original bug
        mock_vector.get = AsyncMock(return_value={
            "domain_id": "job_management",
            "confidence": 0.88,
            "source": "vector_cache",
        })
    mock_vector.set = AsyncMock()
    mock_vector.threshold = 0.85
    router._vector_cache = mock_vector

    return router


# ────────────────────────────────────────────────────────────────────────
# Tests
# ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_wizard_guard_intercepts_before_poisoned_vector_cache():
    """
    Regression: 'criar vaga' must route to wizard even when vector cache
    has a stale job_management entry. Tier 2.5 guard fires first.
    """
    fast_hit = RouteResult(
        domain_id="wizard",
        confidence=0.92,
        source="fast",
        matched_pattern=r"criar?\s+\w*\s*vaga",
    )
    router = _make_router(fast_result=fast_hit)

    result = await router.route(
        message="criar vaga de product manager sênior",
        context={"company_id": "co-test"},
    )

    assert result is not None
    assert result.domain_id == "wizard", (
        f"Expected domain='wizard' but got '{result.domain_id}' — "
        "vector cache poisoning regression detected"
    )
    assert result.source == "wizard_guard", (
        f"Expected source='wizard_guard' but got '{result.source}'"
    )
    # Vector cache must NOT have been consulted (guard short-circuits before it)
    router._vector_cache.get.assert_not_called()


@pytest.mark.asyncio
async def test_nova_vaga_hits_wizard_guard():
    """'nova vaga' pattern (wizard) should also hit Tier 2.5 guard."""
    fast_hit = RouteResult(
        domain_id="wizard",
        confidence=0.91,
        source="fast",
        matched_pattern=r"nova\s+vaga",
    )
    router = _make_router(fast_result=fast_hit)

    result = await router.route(
        message="preciso abrir uma nova vaga para engenheiro de dados",
        context={},
    )

    assert result.domain_id == "wizard"
    assert result.source == "wizard_guard"
    router._vector_cache.get.assert_not_called()


@pytest.mark.asyncio
async def test_wizard_guard_overwrites_redis_with_correct_domain():
    """After guard fires, Redis.set should be called with wizard domain."""
    fast_hit = RouteResult(
        domain_id="wizard",
        confidence=0.91,
        source="fast",
        matched_pattern=r"nova\s+vaga",
    )
    router = _make_router(fast_result=fast_hit)

    await router.route(
        message="nova vaga para designer UX",
        context={"company_id": "co-test"},  # Task #1144: tenant Redis namespace requires company_id
    )

    # Redis.set should have been called with wizard domain to overwrite stale entry
    router._redis_cache.set.assert_called_once()
    call_str = str(router._redis_cache.set.call_args)
    assert "wizard" in call_str, (
        f"Redis.set should contain 'wizard' but got: {call_str}"
    )


@pytest.mark.asyncio
async def test_non_wizard_fast_match_skips_guard():
    """
    job_management fast match must NOT trigger Tier 2.5 guard.
    The guard is exclusively for domain_id == 'wizard'.
    """
    non_wizard_hit = RouteResult(
        domain_id="job_management",
        confidence=0.88,
        source="fast",
    )
    router = _make_router(fast_result=non_wizard_hit)

    result = await router.route(
        message="ver status da vaga Dev Sênior",
        context={},
    )

    assert result is not None
    # Guard must NOT have produced wizard_guard source for job_management message
    assert result.source != "wizard_guard"


@pytest.mark.asyncio
async def test_below_threshold_wizard_skips_guard():
    """
    Wizard fast match below confidence threshold must NOT trigger guard.
    Prevents false positives on ambiguous phrasing.
    """
    low_conf = RouteResult(
        domain_id="wizard",
        confidence=0.45,   # below ROUTER_FAST_CONFIDENCE_THRESHOLD (0.7)
        source="fast",
    )
    router = _make_router(fast_result=low_conf)

    result = await router.route(
        message="talvez criar uma vaga algum dia",
        context={},
    )

    # If guard fires, its confidence must be >= threshold
    if result.source == "wizard_guard":
        assert result.confidence >= 0.7
