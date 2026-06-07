"""
Unit tests — TokenBudgetService (Sprint A / André R6/P2).

Camada 2 — Unitária (pytest-asyncio, sem Redis real — mock via AsyncMock).

Cobre:
- get_plan_limit: todos os planos + fallback + aliases
- check_budget: enterprise skip, redis indisponível, budget ok, budget esgotado
- increment_usage: tokens <= 0, redis indisponível, incrby + expire
- get_budget_status: ilimitado, limitado, esgotado, redis indisponível
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# get_plan_limit
# ---------------------------------------------------------------------------

from app.domains.credits.services.token_budget_service import get_plan_limit, PLAN_DAILY_LIMITS, DEFAULT_DAILY_LIMIT


class TestGetPlanLimit:
    def test_starter(self):
        assert get_plan_limit("starter") == 10_000

    def test_pro(self):
        assert get_plan_limit("pro") == 100_000

    def test_business(self):
        assert get_plan_limit("business") == 500_000

    def test_enterprise_unlimited(self):
        assert get_plan_limit("enterprise") == -1

    def test_trial_alias(self):
        assert get_plan_limit("trial") == 10_000

    def test_free_alias(self):
        assert get_plan_limit("free") == 5_000

    def test_basic_alias(self):
        assert get_plan_limit("basic") == 10_000

    def test_standard_alias(self):
        assert get_plan_limit("standard") == 100_000

    def test_premium_alias(self):
        assert get_plan_limit("premium") == 500_000

    def test_unknown_returns_default(self):
        assert get_plan_limit("unknown_plan") == DEFAULT_DAILY_LIMIT

    def test_none_returns_default(self):
        assert get_plan_limit(None) == DEFAULT_DAILY_LIMIT

    def test_empty_string_returns_default(self):
        assert get_plan_limit("") == DEFAULT_DAILY_LIMIT

    def test_case_insensitive_pro(self):
        assert get_plan_limit("PRO") == 100_000

    def test_case_insensitive_starter(self):
        assert get_plan_limit("Starter") == 10_000

    def test_whitespace_stripped(self):
        assert get_plan_limit("  pro  ") == 100_000


# ---------------------------------------------------------------------------
# check_budget
# ---------------------------------------------------------------------------

from app.domains.credits.services.token_budget_service import check_budget


@pytest.mark.asyncio
class TestCheckBudget:
    async def test_enterprise_skips_redis(self):
        """Plano enterprise não deve consultar Redis — retorna True imediatamente."""
        with patch("app.domains.credits.services.token_budget_service._get_redis") as mock_get:
            allowed, used, limit = await check_budget("company-1", "enterprise")
        mock_get.assert_not_called()
        assert allowed is True
        assert limit == -1

    async def test_redis_unavailable_allows_call(self):
        """Redis indisponível → graceful degradation (permite chamada)."""
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            allowed, used, limit = await check_budget("company-1", "starter")
        assert allowed is True
        assert used == 0
        assert limit == 10_000

    async def test_budget_within_limit(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="5000")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            allowed, used, limit = await check_budget("company-1", "starter")
        assert allowed is True
        assert used == 5_000
        assert limit == 10_000

    async def test_budget_exactly_at_limit_blocked(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="10000")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            allowed, used, limit = await check_budget("company-1", "starter")
        assert allowed is False
        assert used == 10_000

    async def test_budget_exceeded_blocked(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="15000")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            allowed, used, limit = await check_budget("company-2", "starter")
        assert allowed is False

    async def test_no_usage_yet_allowed(self):
        """Chave Redis inexistente (None) → used=0 → permitido."""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            allowed, used, limit = await check_budget("company-new", "pro")
        assert allowed is True
        assert used == 0

    async def test_redis_exception_allows_call(self):
        """Exception no Redis.get → graceful degradation."""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(side_effect=ConnectionError("redis down"))
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            allowed, used, limit = await check_budget("company-1", "pro")
        assert allowed is True

    async def test_aclose_called_on_success(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="100")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            await check_budget("company-1", "pro")
        redis_mock.aclose.assert_called_once()

    async def test_aclose_called_on_exception(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(side_effect=RuntimeError("boom"))
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            await check_budget("company-1", "pro")
        redis_mock.aclose.assert_called_once()


# ---------------------------------------------------------------------------
# increment_usage
# ---------------------------------------------------------------------------

from app.domains.credits.services.token_budget_service import increment_usage


@pytest.mark.asyncio
class TestIncrementUsage:
    async def test_zero_tokens_skipped(self):
        """tokens_used <= 0 → retorna 0 sem tocar Redis."""
        with patch("app.domains.credits.services.token_budget_service._get_redis") as mock_get:
            result = await increment_usage("company-1", 0)
        mock_get.assert_not_called()
        assert result == 0

    async def test_negative_tokens_skipped(self):
        with patch("app.domains.credits.services.token_budget_service._get_redis") as mock_get:
            result = await increment_usage("company-1", -100)
        mock_get.assert_not_called()
        assert result == 0

    async def test_redis_unavailable_returns_zero(self):
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            result = await increment_usage("company-1", 500)
        assert result == 0

    async def test_incrby_called_with_tokens(self):
        redis_mock = AsyncMock()
        redis_mock.incrby = AsyncMock(return_value=1500)
        redis_mock.expire = AsyncMock()
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            result = await increment_usage("company-1", 500)
        redis_mock.incrby.assert_called_once()
        args = redis_mock.incrby.call_args
        assert args[0][1] == 500  # tokens_used passado como segundo arg
        assert result == 1500

    async def test_expire_called_after_incrby(self):
        redis_mock = AsyncMock()
        redis_mock.incrby = AsyncMock(return_value=100)
        redis_mock.expire = AsyncMock()
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            await increment_usage("company-1", 100)
        redis_mock.expire.assert_called_once()

    async def test_expire_ttl_is_25h(self):
        from app.domains.credits.services.token_budget_service import _REDIS_TTL
        assert _REDIS_TTL == 25 * 3600

    async def test_incrby_exception_returns_zero(self):
        redis_mock = AsyncMock()
        redis_mock.incrby = AsyncMock(side_effect=Exception("redis error"))
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            result = await increment_usage("company-1", 100)
        assert result == 0


# ---------------------------------------------------------------------------
# get_budget_status
# ---------------------------------------------------------------------------

from app.domains.credits.services.token_budget_service import get_budget_status


@pytest.mark.asyncio
class TestGetBudgetStatus:
    async def test_enterprise_is_unlimited(self):
        with patch("app.domains.credits.services.token_budget_service._get_redis") as mock_get:
            status = await get_budget_status("company-1", "enterprise")
        assert status["daily_limit"] == -1
        assert status["remaining"] == -1
        assert status["usage_pct"] == 0.0
        assert status["budget_exhausted"] is False

    async def test_structure_keys_present(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="1000")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("company-1", "pro")
        required_keys = {
            "company_id", "plan_code", "daily_limit", "used_today",
            "remaining", "usage_pct", "budget_exhausted", "reset_at",
        }
        assert required_keys.issubset(status.keys())

    async def test_usage_pct_calculated(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="50000")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("company-1", "pro")
        assert status["used_today"] == 50_000
        assert status["daily_limit"] == 100_000
        assert status["usage_pct"] == 50.0
        assert status["budget_exhausted"] is False
        assert status["remaining"] == 50_000

    async def test_budget_exhausted_flag(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="100000")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("company-1", "pro")
        assert status["budget_exhausted"] is True
        assert status["remaining"] == 0

    async def test_reset_at_is_next_midnight_utc(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="0")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("company-1", "starter")
        # reset_at deve ser uma string ISO com T00:00:00
        assert "T00:00:00" in status["reset_at"]

    async def test_redis_unavailable_returns_used_zero(self):
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            status = await get_budget_status("company-1", "pro")
        assert status["used_today"] == 0
        assert status["remaining"] == 100_000

    async def test_company_id_in_response(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="0")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("acme-corp", "starter")
        assert status["company_id"] == "acme-corp"

    async def test_unknown_plan_fallback(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="0")
        redis_mock.aclose = AsyncMock()
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            status = await get_budget_status("company-1", None)
        assert status["daily_limit"] == DEFAULT_DAILY_LIMIT


# ---------------------------------------------------------------------------
# Redis key format
# ---------------------------------------------------------------------------

from app.domains.credits.services.token_budget_service import _redis_key


class TestRedisKey:
    def test_key_format(self):
        key = _redis_key("acme-corp")
        import re
        # token_budget:acme-corp:YYYY-MM-DD
        assert re.match(r"token_budget:acme-corp:\d{4}-\d{2}-\d{2}", key)

    def test_key_contains_company_id(self):
        key = _redis_key("my-company")
        assert "my-company" in key

    def test_key_prefix(self):
        key = _redis_key("any")
        assert key.startswith("token_budget:")


# ---------------------------------------------------------------------------
# Dev/demo tenant unlimited gate (2026-06-06)
# Contexto: o tenant compartilhado de desenvolvimento (CANONICAL_DEMO_UUID)
# estourava o DEFAULT_DAILY_LIMIT=10k por causa de sessoes paralelas + testes,
# bloqueando o chat unificado (agent_chat_sse/ws gateiam via check_budget).
# Gate SO vale em APP_ENV=development — producao nunca e afetada.
# ---------------------------------------------------------------------------

from app.domains.credits.services.token_budget_service import (
    _is_unlimited_dev_tenant,
    _UNLIMITED_DEV_TENANTS,
)

_DEMO_UUID = "00000000-0000-4000-a000-000000000001"


class TestUnlimitedDevTenant:
    def test_demo_tenant_unlimited_in_development(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "development")
        assert _is_unlimited_dev_tenant(_DEMO_UUID) is True

    def test_demo_tenant_NOT_unlimited_in_production(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        assert _is_unlimited_dev_tenant(_DEMO_UUID) is False

    def test_demo_tenant_NOT_unlimited_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("APP_ENV", raising=False)
        assert _is_unlimited_dev_tenant(_DEMO_UUID) is False

    def test_other_tenant_never_unlimited_even_in_dev(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "development")
        assert _is_unlimited_dev_tenant("31f50aa5-e870-47d7-8e20-249578d03894") is False

    def test_demo_uuid_registered_in_allowlist(self):
        assert _DEMO_UUID in _UNLIMITED_DEV_TENANTS

    def test_env_value_is_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "Development")
        assert _is_unlimited_dev_tenant(_DEMO_UUID) is True
