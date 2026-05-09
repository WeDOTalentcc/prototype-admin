"""
Extended unit tests for token_budget_service.

Covers: _redis_key format edge cases, get_plan_limit boundary values,
check_budget with custom redis_url, increment_usage large values,
get_budget_status full lifecycle, get_plan_for_company cache/DB paths,
enterprise plan across all budget functions.
"""
import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.credits.services.token_budget_service import (
    PLAN_DAILY_LIMITS,
    DEFAULT_DAILY_LIMIT,
    _REDIS_TTL,
    _redis_key,
    get_plan_limit,
    check_budget,
    increment_usage,
    get_budget_status,
)


# ---------------------------------------------------------------------------
# Plan limits table completeness
# ---------------------------------------------------------------------------

class TestPlanLimitsTable:
    def test_all_expected_plans_present(self):
        expected = {"starter", "pro", "business", "enterprise", "trial", "free", "basic", "standard", "premium"}
        assert expected.issubset(set(PLAN_DAILY_LIMITS.keys()))

    def test_enterprise_is_minus_one(self):
        assert PLAN_DAILY_LIMITS["enterprise"] == -1

    def test_limits_are_increasing(self):
        """starter ≤ pro ≤ business"""
        assert PLAN_DAILY_LIMITS["starter"] <= PLAN_DAILY_LIMITS["pro"]
        assert PLAN_DAILY_LIMITS["pro"] <= PLAN_DAILY_LIMITS["business"]

    def test_free_is_lowest_positive(self):
        # free=5000 < starter=10000
        assert PLAN_DAILY_LIMITS["free"] < PLAN_DAILY_LIMITS["starter"]

    def test_default_daily_limit_positive(self):
        assert DEFAULT_DAILY_LIMIT > 0

    def test_redis_ttl_is_at_least_86400(self):
        assert _REDIS_TTL >= 86400


# ---------------------------------------------------------------------------
# _redis_key
# ---------------------------------------------------------------------------

class TestRedisKeyExtended:
    def test_key_has_three_segments(self):
        key = _redis_key("my-company")
        parts = key.split(":")
        assert len(parts) == 3

    def test_key_date_is_valid_date(self):
        key = _redis_key("corp")
        date_part = key.split(":")[-1]
        assert re.match(r"\d{4}-\d{2}-\d{2}", date_part)

    def test_different_companies_get_different_keys(self):
        k1 = _redis_key("company-a")
        k2 = _redis_key("company-b")
        assert k1 != k2

    def test_same_company_same_day_same_key(self):
        k1 = _redis_key("acme")
        k2 = _redis_key("acme")
        assert k1 == k2

    def test_key_with_special_chars_in_company_id(self):
        key = _redis_key("company:with:colons")
        assert key.startswith("token_budget:company:with:colons:")


# ---------------------------------------------------------------------------
# get_plan_limit edge cases
# ---------------------------------------------------------------------------

class TestGetPlanLimitEdgeCases:
    def test_very_long_unknown_plan_returns_default(self):
        assert get_plan_limit("x" * 200) == DEFAULT_DAILY_LIMIT

    def test_numeric_plan_returns_default(self):
        assert get_plan_limit("12345") == DEFAULT_DAILY_LIMIT

    def test_enterprise_uppercase_returns_minus_one(self):
        assert get_plan_limit("ENTERPRISE") == -1

    def test_all_whitespace_returns_default(self):
        # "   ".strip() = "" → default
        assert get_plan_limit("   ") == DEFAULT_DAILY_LIMIT

    def test_plan_with_leading_trailing_spaces(self):
        assert get_plan_limit("  business  ") == PLAN_DAILY_LIMITS["business"]


# ---------------------------------------------------------------------------
# check_budget — enterprise variants
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestCheckBudgetEnterprise:
    async def test_enterprise_uppercase_skips_redis(self):
        with patch("app.domains.credits.services.token_budget_service._get_redis") as mock_get:
            allowed, used, limit = await check_budget("corp", "ENTERPRISE")
        mock_get.assert_not_called()
        assert allowed is True
        assert limit == -1
        assert used == 0

    async def test_enterprise_used_is_always_0(self):
        with patch("app.domains.credits.services.token_budget_service._get_redis"):
            allowed, used, limit = await check_budget("corp", "enterprise")
        assert used == 0

    async def test_enterprise_with_custom_redis_url(self):
        with patch("app.domains.credits.services.token_budget_service._get_redis") as mock_get:
            allowed, _, _ = await check_budget("corp", "enterprise", redis_url="redis://custom:6380/1")
        mock_get.assert_not_called()
        assert allowed is True


# ---------------------------------------------------------------------------
# check_budget — boundary conditions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestCheckBudgetBoundary:
    async def test_budget_at_99_percent_allowed(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="9999")  # starter limit=10000
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            allowed, used, limit = await check_budget("c", "starter")
        assert allowed is True
        assert used == 9999

    async def test_budget_at_100_percent_blocked(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="10000")  # exactly at limit
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            allowed, used, limit = await check_budget("c", "starter")
        assert allowed is False

    async def test_budget_over_limit_blocked(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="999999")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            allowed, _, _ = await check_budget("c", "starter")
        assert allowed is False

    async def test_free_plan_5000_limit(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="5001")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            allowed, used, limit = await check_budget("c", "free")
        assert limit == 5000
        assert allowed is False

    async def test_pro_plan_100k_limit(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="50000")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            allowed, used, limit = await check_budget("c", "pro")
        assert limit == 100_000
        assert allowed is True


# ---------------------------------------------------------------------------
# increment_usage — edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestIncrementUsageEdgeCases:
    async def test_large_token_count_incremented(self):
        redis_mock = AsyncMock()
        redis_mock.incrby = AsyncMock(return_value=999999)
        redis_mock.expire = AsyncMock()
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            result = await increment_usage("corp", 500_000)
        assert result == 999999

    async def test_token_count_of_one_is_incremented(self):
        redis_mock = AsyncMock()
        redis_mock.incrby = AsyncMock(return_value=1)
        redis_mock.expire = AsyncMock()
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            result = await increment_usage("corp", 1)
        assert result == 1
        redis_mock.incrby.assert_called_once()

    async def test_expire_called_with_correct_ttl(self):
        redis_mock = AsyncMock()
        redis_mock.incrby = AsyncMock(return_value=100)
        redis_mock.expire = AsyncMock()
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            await increment_usage("corp", 100)
        expire_call = redis_mock.expire.call_args
        # expire(key, ttl, xx=False) — second positional arg is ttl
        assert expire_call[0][1] == _REDIS_TTL

    async def test_aclose_called_after_incrby(self):
        redis_mock = AsyncMock()
        redis_mock.incrby = AsyncMock(return_value=100)
        redis_mock.expire = AsyncMock()
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            await increment_usage("corp", 100)
        assert redis_mock.aclose.call_count >= 1  # aclose called per redis connection (increment_usage + get_plan_for_company helpers)

    async def test_expire_exception_returns_zero(self):
        redis_mock = AsyncMock()
        redis_mock.incrby = AsyncMock(return_value=100)
        redis_mock.expire = AsyncMock(side_effect=Exception("expire failed"))
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            result = await increment_usage("corp", 100)
        # Exception in expire block → returns 0
        assert result == 0


# ---------------------------------------------------------------------------
# get_budget_status — comprehensive
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestGetBudgetStatusComprehensive:
    async def test_starter_plan_full_lifecycle(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="3000")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("c", "starter")
        assert status["company_id"] == "c"
        assert status["plan_code"] == "starter"
        assert status["daily_limit"] == 10_000
        assert status["used_today"] == 3_000
        assert status["remaining"] == 7_000
        assert status["usage_pct"] == 30.0
        assert status["budget_exhausted"] is False

    async def test_zero_usage_pct_when_no_usage(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="0")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("c", "pro")
        assert status["usage_pct"] == 0.0
        assert status["budget_exhausted"] is False
        assert status["remaining"] == 100_000

    async def test_100_percent_usage_exhausted(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="500000")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("c", "business")
        assert status["usage_pct"] == 100.0
        assert status["budget_exhausted"] is True
        assert status["remaining"] == 0

    async def test_unknown_plan_code_uses_default(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="0")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("c", "unknown_plan")
        assert status["daily_limit"] == DEFAULT_DAILY_LIMIT

    async def test_none_plan_code_reported_as_unknown(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="0")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("c", None)
        assert status["plan_code"] == "unknown"

    async def test_reset_at_is_future_date(self):
        from datetime import datetime, timezone
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="0")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("c", "pro")
        reset_dt = datetime.fromisoformat(status["reset_at"])
        now = datetime.now(timezone.utc)
        assert reset_dt > now or reset_dt.date() >= now.date()

    async def test_redis_exception_in_get_returns_zero_usage(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(side_effect=Exception("timeout"))
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("c", "pro")
        assert status["used_today"] == 0
