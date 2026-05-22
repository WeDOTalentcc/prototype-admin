"""
Contract tests — Token Budget API (Sprint A / André R6/P2).

Camada 5 — Contrato (pytest).

Verifica contratos da API de admin de token budget:
- Endpoint GET /api/v1/admin/token-budget/{company_id} existe e retorna schema correto
- Endpoint GET /api/v1/admin/token-budget/{company_id}/check existe e retorna schema correto
- TokenBudgetStatusResponse tem todos os campos obrigatórios
- BudgetCheckResponse tem todos os campos obrigatórios
- PLAN_DAILY_LIMITS cobre os planos obrigatórios
- check_budget e increment_usage são funções async
- Multi-tenant: chaves Redis são isoladas por company_id
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch


# ---------------------------------------------------------------------------
# Schema contracts
# ---------------------------------------------------------------------------

class TestTokenBudgetResponseContracts:
    """TokenBudgetStatusResponse e BudgetCheckResponse devem ter campos corretos."""

    def test_status_response_schema_fields(self):
        from app.api.v1.admin_token_budget import TokenBudgetStatusResponse
        fields = TokenBudgetStatusResponse.model_fields
        required = {
            "company_id", "plan_code", "daily_limit", "used_today",
            "remaining", "usage_pct", "budget_exhausted", "reset_at",
        }
        assert required.issubset(fields.keys()), f"Campos faltando: {required - fields.keys()}"

    def test_check_response_schema_fields(self):
        from app.api.v1.admin_token_budget import BudgetCheckResponse
        fields = BudgetCheckResponse.model_fields
        required = {"company_id", "allowed", "used_today", "daily_limit"}
        assert required.issubset(fields.keys())

    def test_status_response_instantiation(self):
        from app.api.v1.admin_token_budget import TokenBudgetStatusResponse
        obj = TokenBudgetStatusResponse(
            company_id="acme",
            plan_code="pro",
            daily_limit=100_000,
            used_today=50_000,
            remaining=50_000,
            usage_pct=50.0,
            budget_exhausted=False,
            reset_at="2026-03-09T00:00:00+00:00",
        )
        assert obj.company_id == "acme"
        assert obj.budget_exhausted is False

    def test_check_response_instantiation(self):
        from app.api.v1.admin_token_budget import BudgetCheckResponse
        obj = BudgetCheckResponse(
            company_id="acme",
            allowed=True,
            used_today=1000,
            daily_limit=10_000,
        )
        assert obj.allowed is True


# ---------------------------------------------------------------------------
# Router contract
# ---------------------------------------------------------------------------

class TestTokenBudgetRouterContract:
    """O router deve estar registrado com o prefixo correto."""

    def test_router_prefix(self):
        from app.api.v1.admin_token_budget import router
        assert router.prefix == "/admin/token-budget"

    def test_router_has_get_status_route(self):
        from app.api.v1.admin_token_budget import router
        paths = [r.path for r in router.routes]
        assert any("{company_id}" in p and not p.endswith("/check") for p in paths)

    def test_router_has_get_check_route(self):
        from app.api.v1.admin_token_budget import router
        paths = [r.path for r in router.routes]
        assert any(p.endswith("/check") for p in paths)


# ---------------------------------------------------------------------------
# TokenBudgetService — public API contract
# ---------------------------------------------------------------------------

class TestTokenBudgetServiceContract:
    """Funções públicas do service devem ter assinatura correta."""

    def test_check_budget_is_coroutine(self):
        from app.domains.credits.services.token_budget_service import check_budget
        import inspect
        assert inspect.iscoroutinefunction(check_budget)

    def test_increment_usage_is_coroutine(self):
        from app.domains.credits.services.token_budget_service import increment_usage
        import inspect
        assert inspect.iscoroutinefunction(increment_usage)

    def test_get_budget_status_is_coroutine(self):
        from app.domains.credits.services.token_budget_service import get_budget_status
        import inspect
        assert inspect.iscoroutinefunction(get_budget_status)

    def test_get_plan_limit_returns_int(self):
        from app.domains.credits.services.token_budget_service import get_plan_limit
        result = get_plan_limit("pro")
        assert isinstance(result, int)
        assert result > 0

    def test_enterprise_limit_is_minus_one(self):
        from app.domains.credits.services.token_budget_service import get_plan_limit
        assert get_plan_limit("enterprise") == -1

    def test_plan_daily_limits_has_required_plans(self):
        from app.domains.credits.services.token_budget_service import PLAN_DAILY_LIMITS
        required_plans = {"starter", "pro", "business", "enterprise"}
        assert required_plans.issubset(PLAN_DAILY_LIMITS.keys())


# ---------------------------------------------------------------------------
# Multi-tenant isolation contract
# ---------------------------------------------------------------------------

class TestMultiTenantBudgetIsolation:
    """Redis keys devem ser isoladas por company_id — um tenant não afeta outro."""

    def test_redis_key_different_per_company(self):
        from app.domains.credits.services.token_budget_service import _redis_key
        key_a = _redis_key("company-a")
        key_b = _redis_key("company-b")
        assert key_a != key_b

    def test_redis_key_contains_company_id(self):
        from app.domains.credits.services.token_budget_service import _redis_key
        key = _redis_key("tenant-xyz")
        assert "tenant-xyz" in key

    def test_redis_key_pattern_isolation(self):
        """Chaves de companies diferentes não podem colidir."""
        from app.domains.credits.services.token_budget_service import _redis_key
        keys = [_redis_key(f"company-{i}") for i in range(10)]
        assert len(set(keys)) == 10  # todas únicas

    @pytest.mark.asyncio
    async def test_check_budget_uses_company_specific_key(self):
        """check_budget deve usar chave Redis específica para a company."""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="0")
        redis_mock.aclose = AsyncMock()

        with patch(
            "app.domains.credits.services.token_budget_service._get_redis",
            new_callable=AsyncMock,
            return_value=redis_mock,
        ):
            from app.domains.credits.services.token_budget_service import check_budget
            await check_budget("isolated-company", "pro")

        call_args = redis_mock.get.call_args
        key_used = call_args[0][0]
        assert "isolated-company" in key_used

    @pytest.mark.asyncio
    async def test_increment_usage_uses_company_specific_key(self):
        """increment_usage deve usar chave Redis específica para a company."""
        redis_mock = AsyncMock()
        redis_mock.incrby = AsyncMock(return_value=500)
        redis_mock.expire = AsyncMock()
        redis_mock.aclose = AsyncMock()

        with patch(
            "app.domains.credits.services.token_budget_service._get_redis",
            new_callable=AsyncMock,
            return_value=redis_mock,
        ):
            from app.domains.credits.services.token_budget_service import increment_usage
            await increment_usage("isolated-company-2", 500)

        call_args = redis_mock.incrby.call_args
        key_used = call_args[0][0]
        assert "isolated-company-2" in key_used


# ---------------------------------------------------------------------------
# TimedToolNode — timeout contract
# ---------------------------------------------------------------------------

class TestTimedToolNodeTimeoutContract:
    """TimedToolNode deve expor interface de timeout (André P4)."""

    def test_timed_tool_node_has_default_timeout(self):
        from lia_agents_core.timed_tool_node import TimedToolNode, _HAS_LANGGRAPH
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")
        ttn = TimedToolNode(tools=[], domain="test")
        assert ttn.default_timeout_seconds == 15

    def test_timed_tool_node_accepts_tool_timeouts(self):
        from lia_agents_core.timed_tool_node import TimedToolNode, _HAS_LANGGRAPH
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")
        ttn = TimedToolNode(
            tools=[], domain="test",
            tool_timeouts={"search_candidates": 30, "fetch_cv": 10}
        )
        assert ttn.tool_timeouts["search_candidates"] == 30
        assert ttn.tool_timeouts["fetch_cv"] == 10

    def test_timed_tool_node_ainvoke_is_coroutine(self):
        from lia_agents_core.timed_tool_node import TimedToolNode
        import inspect
        assert inspect.iscoroutinefunction(TimedToolNode.ainvoke)

    def test_timed_tool_node_has_build_timeout_response(self):
        from lia_agents_core.timed_tool_node import TimedToolNode
        assert hasattr(TimedToolNode, "_build_timeout_response")

    def test_timed_tool_node_has_get_tools(self):
        from lia_agents_core.timed_tool_node import TimedToolNode
        assert hasattr(TimedToolNode, "get_tools")
