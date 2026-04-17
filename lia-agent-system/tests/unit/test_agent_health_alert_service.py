"""
Testes unitários para AgentHealthAlertService — Sprint I2.

Cobertura:
- record_failure retorna contagem incremental (in-memory fallback)
- record_failure dispara WARNING ao atingir FAILURE_THRESHOLD (3)
- record_failure dispara CRITICAL ao atingir CRITICAL_THRESHOLD (5)
- record_success reseta contador
- notify_user_id=None não lança exceção (loga warning)
- Isolamento por company_id + agent_id (chaves distintas não interferem)
- get_failure_count retorna valor correto
- Redis indisponível → fallback in-memory transparente
- Múltiplas falhas acima do threshold continuam enviando CRITICAL
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service():
    from app.shared.observability.agent_health_alert_service import AgentHealthAlertService
    import app.shared.observability.agent_health_alert_service as _mod
    svc = AgentHealthAlertService()
    # Forçar fallback in-memory (sem Redis) — patch _get_redis to always return None
    from unittest.mock import AsyncMock
    svc._get_redis = AsyncMock(return_value=None)
    return svc


async def _fill_failures(svc, company_id, agent_id, n, notify_user_id=None):
    """Registra n falhas consecutivas."""
    counts = []
    for _ in range(n):
        c = await svc.record_failure(company_id, agent_id, "err", notify_user_id)
        counts.append(c)
    return counts


# ---------------------------------------------------------------------------
# record_failure — contagem básica (in-memory)
# ---------------------------------------------------------------------------

class TestRecordFailureCount:

    @pytest.mark.asyncio
    async def test_first_failure_returns_1(self):
        svc = _make_service()
        count = await svc.record_failure("c1", "wizard", "timeout")
        assert count == 1

    @pytest.mark.asyncio
    async def test_consecutive_failures_increment(self):
        svc = _make_service()
        counts = await _fill_failures(svc, "c1", "wizard", 4)
        assert counts == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_different_agents_isolated(self):
        svc = _make_service()
        await svc.record_failure("c1", "wizard", "err")
        await svc.record_failure("c1", "wizard", "err")
        # agent diferente começa do zero
        count_other = await svc.record_failure("c1", "pipeline", "err")
        assert count_other == 1

    @pytest.mark.asyncio
    async def test_different_companies_isolated(self):
        svc = _make_service()
        await svc.record_failure("c1", "wizard", "err")
        await svc.record_failure("c1", "wizard", "err")
        # company diferente começa do zero
        count_other = await svc.record_failure("c2", "wizard", "err")
        assert count_other == 1


# ---------------------------------------------------------------------------
# record_success — reset
# ---------------------------------------------------------------------------

class TestRecordSuccess:

    @pytest.mark.asyncio
    async def test_success_resets_counter(self):
        svc = _make_service()
        await _fill_failures(svc, "c1", "wizard", 3)
        await svc.record_success("c1", "wizard")
        count = await svc.get_failure_count("c1", "wizard")
        assert count == 0

    @pytest.mark.asyncio
    async def test_failure_after_reset_starts_at_1(self):
        svc = _make_service()
        await _fill_failures(svc, "c1", "wizard", 4)
        await svc.record_success("c1", "wizard")
        new_count = await svc.record_failure("c1", "wizard", "err")
        assert new_count == 1

    @pytest.mark.asyncio
    async def test_success_doesnt_affect_other_agent(self):
        svc = _make_service()
        await svc.record_failure("c1", "wizard", "err")
        await svc.record_failure("c1", "wizard", "err")
        await svc.record_failure("c1", "pipeline", "err")
        await svc.record_success("c1", "wizard")
        # pipeline não foi resetado
        count = await svc.get_failure_count("c1", "pipeline")
        assert count == 1


# ---------------------------------------------------------------------------
# Alertas — thresholds WARNING e CRITICAL
# ---------------------------------------------------------------------------

class TestAlerts:

    @pytest.mark.asyncio
    async def test_no_alert_below_threshold(self):
        svc = _make_service()
        with patch.object(svc, "_alert", new_callable=AsyncMock) as mock_alert:
            await svc.record_failure("c1", "wizard", "err", "user-1")
            await svc.record_failure("c1", "wizard", "err", "user-1")
            mock_alert.assert_not_called()

    @pytest.mark.asyncio
    async def test_warning_alert_at_threshold_3(self):
        svc = _make_service()
        with patch.object(svc, "_alert", new_callable=AsyncMock) as mock_alert:
            await _fill_failures(svc, "c1", "wizard", 3, "user-1")
            mock_alert.assert_called_once_with("c1", "wizard", "WARNING", 3, "user-1")

    @pytest.mark.asyncio
    async def test_critical_alert_at_threshold_5(self):
        svc = _make_service()
        with patch.object(svc, "_alert", new_callable=AsyncMock) as mock_alert:
            await _fill_failures(svc, "c1", "wizard", 5, "user-1")
            calls = mock_alert.call_args_list
            # última chamada deve ser CRITICAL com count=5
            last = calls[-1]
            assert last == call("c1", "wizard", "CRITICAL", 5, "user-1")

    @pytest.mark.asyncio
    async def test_critical_continues_above_5(self):
        svc = _make_service()
        with patch.object(svc, "_alert", new_callable=AsyncMock) as mock_alert:
            await _fill_failures(svc, "c1", "wizard", 7, "user-1")
            critical_calls = [c for c in mock_alert.call_args_list if c.args[2] == "CRITICAL"]
            # falhas 5, 6 e 7 → 3 chamadas CRITICAL
            assert len(critical_calls) == 3

    @pytest.mark.asyncio
    async def test_no_alert_when_notify_user_id_none(self):
        """notify_user_id=None não deve lançar exceção — apenas loga warning."""
        svc = _make_service()
        # Não usar patch em _alert — testar o comportamento real de loga e não crasha
        # Precisa de 3 falhas para chegar no threshold
        try:
            await _fill_failures(svc, "c1", "wizard", 3, notify_user_id=None)
        except Exception as exc:
            pytest.fail(f"record_failure com notify_user_id=None levantou exceção: {exc}")


# ---------------------------------------------------------------------------
# get_failure_count
# ---------------------------------------------------------------------------

class TestGetFailureCount:

    @pytest.mark.asyncio
    async def test_initial_count_zero(self):
        svc = _make_service()
        count = await svc.get_failure_count("c1", "wizard")
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_matches_failures(self):
        svc = _make_service()
        await _fill_failures(svc, "c1", "wizard", 4)
        count = await svc.get_failure_count("c1", "wizard")
        assert count == 4

    @pytest.mark.asyncio
    async def test_count_zero_after_reset(self):
        svc = _make_service()
        await _fill_failures(svc, "c1", "wizard", 3)
        await svc.record_success("c1", "wizard")
        count = await svc.get_failure_count("c1", "wizard")
        assert count == 0


# ---------------------------------------------------------------------------
# Redis indisponível → fallback transparente
# ---------------------------------------------------------------------------

class TestRedisFallback:

    @pytest.mark.asyncio
    async def test_fallback_when_redis_unavailable(self):
        from app.shared.observability.agent_health_alert_service import AgentHealthAlertService
        svc = AgentHealthAlertService()
        # Simula Redis indisponível — _get_redis retorna None
        svc._get_redis = AsyncMock(return_value=None)

        count = await svc.record_failure("c1", "wizard", "err")
        assert count == 1

        count2 = await svc.record_failure("c1", "wizard", "err")
        assert count2 == 2

    @pytest.mark.asyncio
    async def test_fallback_reset_works(self):
        from app.shared.observability.agent_health_alert_service import AgentHealthAlertService
        svc = AgentHealthAlertService()
        svc._get_redis = AsyncMock(return_value=None)

        await _fill_failures(svc, "c1", "wizard", 3)
        await svc.record_success("c1", "wizard")
        count = await svc.get_failure_count("c1", "wizard")
        assert count == 0
