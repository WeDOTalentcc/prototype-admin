"""
Unit tests for admin_token_budget API endpoints.

Covers: TokenBudgetStatusResponse schema, BudgetCheckResponse schema,
get_company_token_budget endpoint, check_company_budget endpoint,
500 error handling, enterprise plan responses.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.v1.admin_token_budget import (
    TokenBudgetStatusResponse,
    BudgetCheckResponse,
)


# ---------------------------------------------------------------------------
# TokenBudgetStatusResponse schema
# ---------------------------------------------------------------------------

class TestTokenBudgetStatusResponseSchema:
    def test_all_fields_accessible(self):
        resp = TokenBudgetStatusResponse(
            company_id="corp-1",
            plan_code="pro",
            daily_limit=100_000,
            used_today=25_000,
            remaining=75_000,
            usage_pct=25.0,
            budget_exhausted=False,
            reset_at="2026-03-09T00:00:00+00:00",
        )
        assert resp.company_id == "corp-1"
        assert resp.plan_code == "pro"
        assert resp.daily_limit == 100_000
        assert resp.used_today == 25_000
        assert resp.remaining == 75_000
        assert resp.usage_pct == 25.0
        assert resp.budget_exhausted is False

    def test_budget_exhausted_true(self):
        resp = TokenBudgetStatusResponse(
            company_id="c", plan_code="starter",
            daily_limit=10_000, used_today=10_000,
            remaining=0, usage_pct=100.0,
            budget_exhausted=True, reset_at="2026-03-09T00:00:00",
        )
        assert resp.budget_exhausted is True
        assert resp.remaining == 0

    def test_enterprise_unlimited_response(self):
        resp = TokenBudgetStatusResponse(
            company_id="big-corp", plan_code="enterprise",
            daily_limit=-1, used_today=0,
            remaining=-1, usage_pct=0.0,
            budget_exhausted=False, reset_at="2026-03-09T00:00:00",
        )
        assert resp.daily_limit == -1
        assert resp.remaining == -1


# ---------------------------------------------------------------------------
# BudgetCheckResponse schema
# ---------------------------------------------------------------------------

class TestBudgetCheckResponseSchema:
    def test_allowed_true(self):
        resp = BudgetCheckResponse(
            company_id="c-1", allowed=True,
            used_today=5000, daily_limit=10_000,
        )
        assert resp.allowed is True

    def test_allowed_false(self):
        resp = BudgetCheckResponse(
            company_id="c-2", allowed=False,
            used_today=10_000, daily_limit=10_000,
        )
        assert resp.allowed is False
        assert resp.used_today == 10_000

    def test_company_id_present(self):
        resp = BudgetCheckResponse(
            company_id="acme", allowed=True,
            used_today=0, daily_limit=100_000,
        )
        assert resp.company_id == "acme"




# ---------------------------------------------------------------------------
# Autouse fixture: patch auth/session deps — tests exercise budget logic, not
# superadmin auth or cross-tenant session machinery.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_admin_auth_deps():
    """Patch require_superadmin + cross_tenant_session for unit test isolation.

    Production path calls require_superadmin when actor_company != queried
    company_id (cross-tenant). Unit tests use plain MagicMock() users with no
    company_id set, so actor_company becomes a MagicMock repr → is_cross_tenant
    is always True → 403 without this fixture.

    cross_tenant_session is also patched to avoid DB connections in unit tests;
    its bypass_db mock accepts .execute() calls transparently.
    """
    from unittest.mock import patch as _patch, AsyncMock as _AsyncMock, MagicMock as _MagicMock
    mock_bypass_db = _MagicMock(execute=_AsyncMock(return_value=None))
    mock_ctx = _MagicMock()
    mock_ctx.__aenter__ = _AsyncMock(return_value=mock_bypass_db)
    mock_ctx.__aexit__ = _AsyncMock(return_value=False)
    with (
        _patch(
            "app.api.v1.admin_token_budget.require_superadmin",
            new_callable=_AsyncMock,
            return_value=None,
        ),
        _patch(
            "app.api.v1.admin_token_budget.cross_tenant_session",
            return_value=mock_ctx,
        ),
    ):
        yield

# ---------------------------------------------------------------------------
# get_company_token_budget endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestGetCompanyTokenBudgetEndpoint:
    async def test_returns_status_response(self):
        from app.api.v1.admin_token_budget import get_company_token_budget
        mock_user = MagicMock()
        budget_data = {
            "company_id": "c-1", "plan_code": "pro",
            "daily_limit": 100_000, "used_today": 10_000,
            "remaining": 90_000, "usage_pct": 10.0,
            "budget_exhausted": False, "reset_at": "2026-03-09T00:00:00+00:00",
        }
        with patch("app.api.v1.admin_token_budget.get_budget_status", new_callable=AsyncMock, return_value=budget_data):
            result = await get_company_token_budget("c-1", plan_code="pro", current_user=mock_user)
        assert isinstance(result, TokenBudgetStatusResponse)
        assert result.company_id == "c-1"
        assert result.used_today == 10_000

    async def test_raises_500_on_exception(self):
        from fastapi import HTTPException
        from app.api.v1.admin_token_budget import get_company_token_budget
        mock_user = MagicMock()
        with patch("app.api.v1.admin_token_budget.get_budget_status", new_callable=AsyncMock, side_effect=Exception("DB down")):
            with pytest.raises(HTTPException) as exc_info:
                await get_company_token_budget("c-1", plan_code=None, current_user=mock_user)
        assert exc_info.value.status_code == 500

    async def test_enterprise_plan_returned_correctly(self):
        from app.api.v1.admin_token_budget import get_company_token_budget
        mock_user = MagicMock()
        budget_data = {
            "company_id": "big-corp", "plan_code": "enterprise",
            "daily_limit": -1, "used_today": 0,
            "remaining": -1, "usage_pct": 0.0,
            "budget_exhausted": False, "reset_at": "2026-03-09T00:00:00+00:00",
        }
        with patch("app.api.v1.admin_token_budget.get_budget_status", new_callable=AsyncMock, return_value=budget_data):
            result = await get_company_token_budget("big-corp", plan_code="enterprise", current_user=mock_user)
        assert result.daily_limit == -1
        assert result.remaining == -1

    async def test_passes_company_id_to_service(self):
        from app.api.v1.admin_token_budget import get_company_token_budget
        mock_user = MagicMock()
        budget_data = {
            "company_id": "specific-company", "plan_code": "starter",
            "daily_limit": 10_000, "used_today": 0,
            "remaining": 10_000, "usage_pct": 0.0,
            "budget_exhausted": False, "reset_at": "2026-03-09T00:00:00",
        }
        mock_get_status = AsyncMock(return_value=budget_data)
        with patch("app.api.v1.admin_token_budget.get_budget_status", mock_get_status):
            await get_company_token_budget("specific-company", plan_code=None, current_user=mock_user)
        mock_get_status.assert_called_once_with("specific-company", None)

    async def test_passes_plan_code_to_service(self):
        from app.api.v1.admin_token_budget import get_company_token_budget
        mock_user = MagicMock()
        budget_data = {
            "company_id": "c", "plan_code": "business",
            "daily_limit": 500_000, "used_today": 100_000,
            "remaining": 400_000, "usage_pct": 20.0,
            "budget_exhausted": False, "reset_at": "2026-03-09T00:00:00",
        }
        mock_get_status = AsyncMock(return_value=budget_data)
        with patch("app.api.v1.admin_token_budget.get_budget_status", mock_get_status):
            await get_company_token_budget("c", plan_code="business", current_user=mock_user)
        mock_get_status.assert_called_once_with("c", "business")


# ---------------------------------------------------------------------------
# check_company_budget endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestCheckCompanyBudgetEndpoint:
    async def test_returns_check_response_when_allowed(self):
        from app.api.v1.admin_token_budget import check_company_budget
        mock_user = MagicMock()
        with patch("app.api.v1.admin_token_budget.check_budget", new_callable=AsyncMock, return_value=(True, 5000, 10_000)):
            result = await check_company_budget("c-1", plan_code="starter", current_user=mock_user)
        assert isinstance(result, BudgetCheckResponse)
        assert result.allowed is True
        assert result.used_today == 5000
        assert result.daily_limit == 10_000

    async def test_returns_check_response_when_blocked(self):
        from app.api.v1.admin_token_budget import check_company_budget
        mock_user = MagicMock()
        with patch("app.api.v1.admin_token_budget.check_budget", new_callable=AsyncMock, return_value=(False, 10_000, 10_000)):
            result = await check_company_budget("c-1", plan_code="starter", current_user=mock_user)
        assert result.allowed is False

    async def test_raises_500_on_exception(self):
        from fastapi import HTTPException
        from app.api.v1.admin_token_budget import check_company_budget
        mock_user = MagicMock()
        with patch("app.api.v1.admin_token_budget.check_budget", new_callable=AsyncMock, side_effect=Exception("Redis down")):
            with pytest.raises(HTTPException) as exc_info:
                await check_company_budget("c-1", plan_code=None, current_user=mock_user)
        assert exc_info.value.status_code == 500

    async def test_company_id_in_response(self):
        from app.api.v1.admin_token_budget import check_company_budget
        mock_user = MagicMock()
        with patch("app.api.v1.admin_token_budget.check_budget", new_callable=AsyncMock, return_value=(True, 0, -1)):
            result = await check_company_budget("enterprise-corp", plan_code="enterprise", current_user=mock_user)
        assert result.company_id == "enterprise-corp"

    async def test_enterprise_unlimited_returned(self):
        from app.api.v1.admin_token_budget import check_company_budget
        mock_user = MagicMock()
        with patch("app.api.v1.admin_token_budget.check_budget", new_callable=AsyncMock, return_value=(True, 0, -1)):
            result = await check_company_budget("big-corp", plan_code="enterprise", current_user=mock_user)
        assert result.allowed is True
        assert result.daily_limit == -1


# ---------------------------------------------------------------------------
# Router structure
# ---------------------------------------------------------------------------

class TestAdminTokenBudgetRouter:
    def test_router_importable(self):
        from app.api.v1.admin_token_budget import router
        assert router is not None

    def test_router_has_correct_prefix(self):
        from app.api.v1.admin_token_budget import router
        assert router.prefix == "/admin/token-budget"

    def test_router_has_required_routes(self):
        from app.api.v1.admin_token_budget import router
        paths = {r.path for r in router.routes}
        assert "/admin/token-budget/{company_id}" in paths
        assert "/admin/token-budget/{company_id}/check" in paths
