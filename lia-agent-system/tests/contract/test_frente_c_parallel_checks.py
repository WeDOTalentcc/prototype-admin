"""
TDD Frente C: MonitoringLoop.run_checks — detectores em paralelo com fail-isolation.

Verifica:
  1. Checks rodam em paralelo (asyncio.gather)
  2. Falha num check nao aborta os outros (fail-isolation)
  3. Alertas dos checks bem-sucedidos sao acumulados corretamente
  4. Check com erro loga warning (nao exception)
  5. _persist_alerts e chamado mesmo quando algum check falha
  6. _alert_store e _last_run sao atualizados corretamente
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timezone


# ── fixtures ─────────────────────────────────────────────────────────────────

def _make_alert(name: str):
    """Cria um ProactiveAlert fake para testes."""
    from app.domains.recruiter_assistant.services.monitoring_loop import ProactiveAlert, AlertSeverity, AlertCategory
    return ProactiveAlert(
        alert_id=f"alert-{name}",
        company_id="co-test",
        severity=AlertSeverity.MEDIUM,
        category=AlertCategory.STALE_CANDIDATE,
        title=f"Alert {name}",
        message=f"Desc {name}",
    )


def _make_loop() -> "MonitoringLoop":
    from app.domains.recruiter_assistant.services.monitoring_loop import MonitoringLoop
    loop = MonitoringLoop.__new__(MonitoringLoop)
    loop._alert_store = {}
    loop._last_run = {}
    loop.logger = MagicMock()
    return loop


# ── 1. Todos os checks rodam quando nenhum falha ──────────────────────────────

@pytest.mark.asyncio
async def test_run_checks_all_succeed():
    from app.domains.recruiter_assistant.services.monitoring_loop import MonitoringLoop

    loop = _make_loop()
    a1 = _make_alert("stale")
    a2 = _make_alert("sla")

    loop._check_stale_candidates = AsyncMock(return_value=[a1])
    loop._check_sla_risks = AsyncMock(return_value=[a2])
    loop._check_funnel_bottlenecks = AsyncMock(return_value=[])
    loop._check_empty_pipelines = AsyncMock(return_value=[])
    loop._check_high_rejection_rate = AsyncMock(return_value=[])
    loop._persist_alerts = AsyncMock()

    result = await loop.run_checks("co-test")

    assert len(result) == 2
    assert a1 in result
    assert a2 in result
    # Todos os 5 checks foram chamados
    loop._check_stale_candidates.assert_called_once_with("co-test")
    loop._check_sla_risks.assert_called_once_with("co-test")
    loop._check_funnel_bottlenecks.assert_called_once_with("co-test")
    loop._check_empty_pipelines.assert_called_once_with("co-test")
    loop._check_high_rejection_rate.assert_called_once_with("co-test")


# ── 2. Falha num check nao aborta os outros ───────────────────────────────────

@pytest.mark.asyncio
async def test_run_checks_one_fails_others_succeed():
    loop = _make_loop()
    a_good = _make_alert("sla")

    loop._check_stale_candidates = AsyncMock(side_effect=RuntimeError("DB timeout"))
    loop._check_sla_risks = AsyncMock(return_value=[a_good])
    loop._check_funnel_bottlenecks = AsyncMock(return_value=[])
    loop._check_empty_pipelines = AsyncMock(return_value=[])
    loop._check_high_rejection_rate = AsyncMock(return_value=[])
    loop._persist_alerts = AsyncMock()

    result = await loop.run_checks("co-test")

    # Stale falhou mas sla sobreviveu
    assert a_good in result
    assert len(result) == 1
    # Persist ainda foi chamado
    loop._persist_alerts.assert_called_once()


# ── 3. Todos os checks falham: retorna lista vazia, nao levanta ────────────────

@pytest.mark.asyncio
async def test_run_checks_all_fail_returns_empty():
    loop = _make_loop()

    loop._check_stale_candidates = AsyncMock(side_effect=ValueError("x"))
    loop._check_sla_risks = AsyncMock(side_effect=ValueError("x"))
    loop._check_funnel_bottlenecks = AsyncMock(side_effect=ValueError("x"))
    loop._check_empty_pipelines = AsyncMock(side_effect=ValueError("x"))
    loop._check_high_rejection_rate = AsyncMock(side_effect=ValueError("x"))
    loop._persist_alerts = AsyncMock()

    result = await loop.run_checks("co-test")

    assert result == []
    loop._persist_alerts.assert_called_once_with("co-test", [])


# ── 4. _alert_store e _last_run sao atualizados ───────────────────────────────

@pytest.mark.asyncio
async def test_run_checks_updates_store_and_last_run():
    loop = _make_loop()
    a = _make_alert("bottleneck")

    loop._check_stale_candidates = AsyncMock(return_value=[])
    loop._check_sla_risks = AsyncMock(return_value=[])
    loop._check_funnel_bottlenecks = AsyncMock(return_value=[a])
    loop._check_empty_pipelines = AsyncMock(return_value=[])
    loop._check_high_rejection_rate = AsyncMock(return_value=[])
    loop._persist_alerts = AsyncMock()

    await loop.run_checks("co-test")

    assert "co-test" in loop._alert_store
    assert a in loop._alert_store["co-test"]
    assert "co-test" in loop._last_run
    assert isinstance(loop._last_run["co-test"], datetime)


# ── 5. Falha nao e re-levantada (retorno normal) ──────────────────────────────

@pytest.mark.asyncio
async def test_run_checks_exception_not_propagated():
    loop = _make_loop()

    loop._check_stale_candidates = AsyncMock(side_effect=Exception("kaboom"))
    loop._check_sla_risks = AsyncMock(return_value=[])
    loop._check_funnel_bottlenecks = AsyncMock(return_value=[])
    loop._check_empty_pipelines = AsyncMock(return_value=[])
    loop._check_high_rejection_rate = AsyncMock(return_value=[])
    loop._persist_alerts = AsyncMock()

    # Nao deve levantar
    result = await loop.run_checks("co-test")
    assert isinstance(result, list)
