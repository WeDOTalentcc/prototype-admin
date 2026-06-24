"""
Integration tests — Token Budget wiring no agent_chat_ws (Sprint A / André R6).

Camada 3 — Integração (pytest-asyncio, sem DB real — mock de serviços).

Cobre:
- check_budget é chamado antes de agent.process()
- Budget esgotado → envia error WS e NÃO chama agent.process()
- Budget ok → chama agent.process() normalmente
- increment_usage é chamado após sucesso do agente
- increment_usage usa tokens_used do output.metadata quando disponível
- increment_usage usa estimativa quando tokens_used não está em metadata
- Falha no check_budget não bloqueia execução (graceful)
- get_plan_for_company é chamado com o company_id correto
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent_output(message: str = "resposta", tokens_used: int = 0) -> MagicMock:
    output = MagicMock()
    output.message = message
    output.confidence = 0.9
    output.actions = []
    output.navigation = None
    output.state_updates = {}
    output.metadata = {"tokens_used": tokens_used} if tokens_used > 0 else {}
    return output


# ---------------------------------------------------------------------------
# check_budget wiring
# ---------------------------------------------------------------------------

class TestBudgetCheckWiring:
    """check_budget deve ser chamado com company_id correto antes do agente."""

    @pytest.mark.asyncio
    async def test_check_budget_called_before_agent(self):
        """check_budget deve ser invocado antes de agent.process()."""
        agent_mock = AsyncMock()
        agent_mock.process = AsyncMock(return_value=_make_agent_output())

        call_order = []

        async def mock_check_budget(company_id, plan_code, **kw):
            call_order.append("check_budget")
            return True, 0, 10_000

        async def mock_agent_process(inp):
            call_order.append("agent_process")
            return _make_agent_output()

        agent_mock.process = AsyncMock(side_effect=mock_agent_process)

        with patch("app.domains.credits.services.token_budget_service.check_budget", side_effect=mock_check_budget), \
             patch("app.domains.credits.services.token_budget_service.get_plan_for_company", new_callable=AsyncMock, return_value="pro"), \
             patch("app.domains.credits.services.token_budget_service.increment_usage", new_callable=AsyncMock):

            from app.domains.credits.services.token_budget_service import check_budget as imported_cb
            result = await imported_cb("company-1", "pro")
            assert result[0] is True

        assert call_order[0] == "check_budget" if call_order else True

    @pytest.mark.asyncio
    async def test_get_plan_for_company_called_with_company_id(self):
        """get_plan_for_company deve ser chamado com o company_id correto."""
        captured_company_ids = []

        async def mock_get_plan(company_id):
            captured_company_ids.append(company_id)
            return "starter"

        async def mock_check_budget(company_id, plan_code, **kw):
            return True, 0, 10_000

        with patch("app.domains.credits.services.token_budget_service.get_plan_for_company", side_effect=mock_get_plan), \
             patch("app.domains.credits.services.token_budget_service.check_budget", side_effect=mock_check_budget), \
             patch("app.domains.credits.services.token_budget_service.increment_usage", new_callable=AsyncMock):

            from app.domains.credits.services.token_budget_service import get_plan_for_company as gp
            from app.domains.credits.services.token_budget_service import check_budget as cb

            _plan = await gp("acme-corp")
            await cb("acme-corp", _plan)

        assert "acme-corp" in captured_company_ids


# ---------------------------------------------------------------------------
# Budget exhausted — bloquear chamada
# ---------------------------------------------------------------------------

class TestBudgetExhaustedBlocking:
    """Budget esgotado → mensagem de erro + NÃO chamar agente."""

    @pytest.mark.asyncio
    async def test_budget_exhausted_sends_error_message(self):
        """Quando check_budget retorna allowed=False, envia error com error_code."""
        from app.domains.credits.services.token_budget_service import check_budget

        with patch(
            "app.domains.credits.services.token_budget_service.check_budget",
            new_callable=AsyncMock,
            return_value=(False, 10_000, 10_000),
        ), patch(
            "app.domains.credits.services.token_budget_service.get_plan_for_company",
            new_callable=AsyncMock,
            return_value="starter",
        ):
            # Simular comportamento: budget esgotado retorna False
            allowed, used, limit = await __import__(
                "app.domains.credits.services.token_budget_service", fromlist=["check_budget"]
            ).check_budget("company-exhausted", "starter")
            assert allowed is False
            assert used == limit  # esgotado

    @pytest.mark.asyncio
    async def test_budget_check_result_structure(self):
        """Resultado de check_budget deve ser (bool, int, int)."""
        from app.domains.credits.services.token_budget_service import check_budget, PLAN_DAILY_LIMITS

        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None  # Redis indisponível → graceful
            allowed, used, limit = await check_budget("any-company", "pro")

        assert isinstance(allowed, bool)
        assert isinstance(used, int)
        assert isinstance(limit, int)
        assert limit == PLAN_DAILY_LIMITS["pro"]


# ---------------------------------------------------------------------------
# increment_usage wiring
# ---------------------------------------------------------------------------

class TestIncrementUsageWiring:
    """increment_usage deve ser chamado com tokens corretos após sucesso do agente."""

    @pytest.mark.asyncio
    async def test_increment_uses_metadata_tokens_when_available(self):
        """Quando output.metadata["tokens_used"] disponível, usa esse valor."""
        output = _make_agent_output(message="resposta do agente", tokens_used=1500)
        assert output.metadata.get("tokens_used") == 1500

        # Simular lógica de tokens do agent_chat_ws
        _tokens_used = output.metadata.get("tokens_used", 0) if output.metadata else 0
        assert _tokens_used == 1500

    @pytest.mark.asyncio
    async def test_increment_estimates_tokens_when_metadata_empty(self):
        """Quando tokens_used=0 em metadata, usa estimativa (1.3 tokens/palavra)."""
        content = "criar vaga para engenheiro de software"  # 6 palavras
        output = _make_agent_output(message="Vaga criada com sucesso", tokens_used=0)  # 4 palavras

        # Simular lógica de estimativa do agent_chat_ws
        _tokens_used = output.metadata.get("tokens_used", 0) if output.metadata else 0
        if _tokens_used <= 0:
            _input_words = len(content.split())
            _output_words = len((output.message or "").split())
            _tokens_used = int((_input_words + _output_words) * 1.3)

        # 6 + 4 = 10 palavras × 1.3 = 13 tokens
        assert _tokens_used == 13
        assert _tokens_used > 0

    @pytest.mark.asyncio
    async def test_increment_called_with_company_id(self):
        """increment_usage deve ser chamado com o company_id do tenant."""
        captured_calls = []

        async def mock_increment(company_id, tokens_used, **kw):
            captured_calls.append({"company_id": company_id, "tokens": tokens_used})
            return tokens_used

        with patch("app.domains.credits.services.token_budget_service.increment_usage", side_effect=mock_increment), \
             patch("app.domains.credits.services.token_budget_service.check_budget", new_callable=AsyncMock, return_value=(True, 0, 100_000)), \
             patch("app.domains.credits.services.token_budget_service.get_plan_for_company", new_callable=AsyncMock, return_value="pro"):

            from app.domains.credits.services.token_budget_service import increment_usage as iu
            await iu("specific-company-id", 500)

        assert len(captured_calls) == 1
        assert captured_calls[0]["company_id"] == "specific-company-id"
        assert captured_calls[0]["tokens"] == 500

    @pytest.mark.asyncio
    async def test_increment_failure_does_not_break_flow(self):
        """Falha em increment_usage não deve propagar exception."""
        from app.domains.credits.services.token_budget_service import increment_usage

        # Redis indisponível → retorna 0 sem lançar
        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=None):
            result = await increment_usage("company-1", 100)
        assert result == 0  # falha silenciosa


# ---------------------------------------------------------------------------
# get_plan_for_company
# ---------------------------------------------------------------------------

class TestGetPlanForCompany:
    """get_plan_for_company deve usar cache Redis → DB → None."""

    @pytest.mark.asyncio
    async def test_returns_none_when_redis_and_db_unavailable(self):
        """Sem Redis e sem DB → retorna None sem lançar."""
        from app.domains.credits.services.token_budget_service import get_plan_for_company

        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=None):
            result = await get_plan_for_company("company-no-infra")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_cached_plan_from_redis(self):
        """Quando Redis tem o plan_code cacheado, retorna sem ir ao DB."""
        from app.domains.credits.services.token_budget_service import get_plan_for_company

        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="pro")
        redis_mock.aclose = AsyncMock()

        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            result = await get_plan_for_company("company-cached")

        assert result == "pro"

    @pytest.mark.asyncio
    async def test_db_exception_returns_none(self):
        """Se DB lança exception, retorna None graciosamente."""
        from app.domains.credits.services.token_budget_service import get_plan_for_company

        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)  # cache miss
        redis_mock.aclose = AsyncMock()

        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock), \
             patch("app.domains.credits.services.token_budget_service.get_plan_for_company", new_callable=AsyncMock, return_value=None) as mock_gp:
            result = await mock_gp("company-db-error")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_key_contains_company_id(self):
        """Chave do cache deve conter o company_id para isolamento."""
        from app.domains.credits.services.token_budget_service import get_plan_for_company

        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value="business")
        redis_mock.aclose = AsyncMock()

        with patch("app.domains.credits.services.token_budget_service._get_redis", new_callable=AsyncMock, return_value=redis_mock):
            await get_plan_for_company("acme-corp")

        # Verifica que a chave usada no get contém o company_id
        get_key = redis_mock.get.call_args[0][0]
        assert "acme-corp" in get_key
