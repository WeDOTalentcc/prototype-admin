"""
Unit Tests — Token budget dependency: HTTP 429 e graceful degradation (Task #53, Item 7).

Testa o comportamento REAL do require_token_budget:
- Budget esgotado (allowed=False) → lança HTTP 429 com estrutura correta
- Budget disponível (allowed=True) → retorna None (não bloqueia)
- Sem company_id → não bloqueia (graceful)
- Erro interno em check_budget → não bloqueia (graceful degradation)
- get_plan_for_company é chamado com o company_id correto
- HTTP 429 detail inclui 'budget_exhausted', 'used_today', 'daily_limit'
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Seção 1 — Budget esgotado → HTTP 429
# ---------------------------------------------------------------------------

class TestTokenBudgetExhausted:

    @pytest.mark.asyncio
    async def test_exhausted_budget_raises_http_429(self):
        """Budget esgotado deve lançar HTTPException com status_code 429."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = "company-test-429"

        with patch("app.dependencies.token_budget.get_plan_for_company",
                   new_callable=AsyncMock, return_value="pro"), \
             patch("app.dependencies.token_budget.check_budget",
                   new_callable=AsyncMock, return_value=(False, 50000, 40000)):
            with pytest.raises(HTTPException) as exc_info:
                await require_token_budget(current_user=mock_user)

        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_exhausted_budget_detail_has_budget_exhausted_error(self):
        """HTTP 429 detail deve conter error='budget_exhausted'."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = "company-budget-check"

        with patch("app.dependencies.token_budget.get_plan_for_company",
                   new_callable=AsyncMock, return_value="starter"), \
             patch("app.dependencies.token_budget.check_budget",
                   new_callable=AsyncMock, return_value=(False, 10000, 8000)):
            with pytest.raises(HTTPException) as exc_info:
                await require_token_budget(current_user=mock_user)

        detail = exc_info.value.detail
        assert detail["error"] == "budget_exhausted"

    @pytest.mark.asyncio
    async def test_exhausted_budget_detail_contains_usage_numbers(self):
        """HTTP 429 detail deve conter used_today e daily_limit."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = "company-usage"

        with patch("app.dependencies.token_budget.get_plan_for_company",
                   new_callable=AsyncMock, return_value="enterprise"), \
             patch("app.dependencies.token_budget.check_budget",
                   new_callable=AsyncMock, return_value=(False, 100_000, 95_000)):
            with pytest.raises(HTTPException) as exc_info:
                await require_token_budget(current_user=mock_user)

        detail = exc_info.value.detail
        assert "used_today" in detail
        assert "daily_limit" in detail
        assert detail["used_today"] == 100_000
        assert detail["daily_limit"] == 95_000

    @pytest.mark.asyncio
    async def test_exhausted_budget_message_mentions_midnight(self):
        """HTTP 429 message deve mencionar renovação à meia-noite."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = "company-midnight"

        with patch("app.dependencies.token_budget.get_plan_for_company",
                   new_callable=AsyncMock, return_value="pro"), \
             patch("app.dependencies.token_budget.check_budget",
                   new_callable=AsyncMock, return_value=(False, 5000, 4000)):
            with pytest.raises(HTTPException) as exc_info:
                await require_token_budget(current_user=mock_user)

        detail = exc_info.value.detail
        assert "meia-noite" in detail["message"] or "UTC" in detail["message"]


# ---------------------------------------------------------------------------
# Seção 2 — Budget disponível → nenhum bloqueio
# ---------------------------------------------------------------------------

class TestTokenBudgetAllowed:

    @pytest.mark.asyncio
    async def test_allowed_budget_returns_none(self):
        """Budget disponível deve retornar None (não bloquear request)."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = "company-allowed"

        with patch("app.dependencies.token_budget.get_plan_for_company",
                   new_callable=AsyncMock, return_value="pro"), \
             patch("app.dependencies.token_budget.check_budget",
                   new_callable=AsyncMock, return_value=(True, 1000, 40000)):
            result = await require_token_budget(current_user=mock_user)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_plan_called_with_correct_company_id(self):
        """get_plan_for_company deve ser chamado com o company_id do usuário."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = "company-plan-check"

        mock_get_plan = AsyncMock(return_value="enterprise")
        mock_check_budget = AsyncMock(return_value=(True, 0, 100000))

        with patch("app.dependencies.token_budget.get_plan_for_company", mock_get_plan), \
             patch("app.dependencies.token_budget.check_budget", mock_check_budget):
            await require_token_budget(current_user=mock_user)

        mock_get_plan.assert_awaited_once_with("company-plan-check")

    @pytest.mark.asyncio
    async def test_check_budget_called_with_company_id_and_plan(self):
        """check_budget deve ser chamado com company_id e plan_code corretos."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = "company-cb-check"

        mock_get_plan = AsyncMock(return_value="starter")
        mock_check_budget = AsyncMock(return_value=(True, 500, 10000))

        with patch("app.dependencies.token_budget.get_plan_for_company", mock_get_plan), \
             patch("app.dependencies.token_budget.check_budget", mock_check_budget):
            await require_token_budget(current_user=mock_user)

        mock_check_budget.assert_awaited_once_with("company-cb-check", "starter")


# ---------------------------------------------------------------------------
# Seção 3 — Sem company_id → não bloquear (graceful)
# ---------------------------------------------------------------------------

class TestTokenBudgetNoCompanyId:

    @pytest.mark.asyncio
    async def test_no_company_id_does_not_raise(self):
        """Usuário sem company_id não deve bloquear o request."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = None
        mock_user.organization_id = None

        result = await require_token_budget(current_user=mock_user)
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_company_id_does_not_raise(self):
        """company_id vazio string não deve bloquear."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = ""
        mock_user.organization_id = ""

        result = await require_token_budget(current_user=mock_user)
        assert result is None


# ---------------------------------------------------------------------------
# Seção 4 — Erros internos → graceful degradation
# ---------------------------------------------------------------------------

class TestTokenBudgetGracefulDegradation:

    @pytest.mark.asyncio
    async def test_redis_error_does_not_block_request(self):
        """Erro ao acessar Redis/check_budget não deve bloquear a request (graceful)."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = "company-redis-fail"

        with patch("app.dependencies.token_budget.get_plan_for_company",
                   new_callable=AsyncMock, side_effect=ConnectionError("Redis offline")):
            result = await require_token_budget(current_user=mock_user)

        assert result is None

    @pytest.mark.asyncio
    async def test_check_budget_exception_does_not_block(self):
        """Exceção em check_budget deve resultar em None — não em 429."""
        from app.dependencies.token_budget import require_token_budget

        mock_user = MagicMock()
        mock_user.company_id = "company-exception"

        with patch("app.dependencies.token_budget.get_plan_for_company",
                   new_callable=AsyncMock, return_value="pro"), \
             patch("app.dependencies.token_budget.check_budget",
                   new_callable=AsyncMock, side_effect=RuntimeError("DB timeout")):
            result = await require_token_budget(current_user=mock_user)

        assert result is None
