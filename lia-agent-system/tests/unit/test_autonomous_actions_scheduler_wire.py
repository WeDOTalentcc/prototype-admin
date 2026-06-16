"""F3: AutonomousActionsEngine wired no AutomationScheduler.

Verifica que:
1. AutomationScheduler possui o método _run_autonomous_actions.
2. O job "autonomous_actions" está registrado (id presente no scheduler).
3. _run_autonomous_actions chama process_monitoring_alerts para cada empresa ativa.
4. Falha por empresa não aborta as demais (isolamento).
5. Empresas sem alerts chamam run_checks para popular o store.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# 1. API structural — método existe
# ---------------------------------------------------------------------------
def test_scheduler_has_autonomous_actions_method():
    from app.domains.automation.services.automation_scheduler import AutomationScheduler

    assert hasattr(AutomationScheduler, "_run_autonomous_actions"), (
        "AutomationScheduler deve ter método _run_autonomous_actions (F3)"
    )
    import inspect
    assert inspect.iscoroutinefunction(AutomationScheduler._run_autonomous_actions), (
        "_run_autonomous_actions deve ser async"
    )


# ---------------------------------------------------------------------------
# 2. Job id registrado no source code
# ---------------------------------------------------------------------------
def test_autonomous_actions_job_id_in_source():
    import inspect
    from app.domains.automation.services.automation_scheduler import AutomationScheduler
    source = inspect.getsource(AutomationScheduler)
    assert '"autonomous_actions"' in source or "'autonomous_actions'" in source, (
        "Job id 'autonomous_actions' deve estar registrado no scheduler"
    )


# ---------------------------------------------------------------------------
# 3. _run_autonomous_actions chama process_monitoring_alerts por empresa
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_autonomous_actions_calls_engine():
    from app.domains.automation.services.automation_scheduler import AutomationScheduler

    scheduler = AutomationScheduler.__new__(AutomationScheduler)

    mock_alert_1 = MagicMock()
    mock_alert_2 = MagicMock()
    alerts_by_company = {
        "company-aaa": [mock_alert_1],
        "company-bbb": [mock_alert_2],
    }

    mock_engine = MagicMock()
    mock_engine.process_monitoring_alerts = AsyncMock(return_value=[MagicMock()])

    mock_monitoring = MagicMock()
    mock_monitoring.get_alerts = MagicMock(side_effect=lambda cid: alerts_by_company.get(cid, []))

    with patch(
        "app.domains.automation.services.automation_scheduler.AutomationScheduler._select_active_company_ids",
        new=AsyncMock(return_value=["company-aaa", "company-bbb"]),
    ):
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.domains.automation.services.automation_scheduler.async_session_factory",
            return_value=mock_ctx,
        ):
            with patch(
                "app.domains.recruiter_assistant.services.autonomous_actions_engine.AutonomousActionsEngine.get_instance",
                return_value=mock_engine,
            ):
                with patch(
                    "app.domains.recruiter_assistant.services.monitoring_loop.MonitoringLoop.get_instance",
                    return_value=mock_monitoring,
                ):
                    await scheduler._run_autonomous_actions()

    assert mock_engine.process_monitoring_alerts.call_count == 2
    call_company_ids = {
        c.kwargs.get("company_id") or c.args[0]
        for c in mock_engine.process_monitoring_alerts.call_args_list
    }
    assert "company-aaa" in call_company_ids
    assert "company-bbb" in call_company_ids


# ---------------------------------------------------------------------------
# 4. Empresa sem alerts na memória chama run_checks
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_autonomous_actions_calls_run_checks_when_no_alerts():
    from app.domains.automation.services.automation_scheduler import AutomationScheduler

    scheduler = AutomationScheduler.__new__(AutomationScheduler)

    fresh_alert = MagicMock()
    mock_engine = MagicMock()
    mock_engine.process_monitoring_alerts = AsyncMock(return_value=[])

    mock_monitoring = MagicMock()
    mock_monitoring.get_alerts = MagicMock(return_value=[])
    mock_monitoring.run_checks = AsyncMock(return_value=[fresh_alert])

    with patch(
        "app.domains.automation.services.automation_scheduler.AutomationScheduler._select_active_company_ids",
        new=AsyncMock(return_value=["company-ccc"]),
    ):
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.domains.automation.services.automation_scheduler.async_session_factory",
            return_value=mock_ctx,
        ):
            with patch(
                "app.domains.recruiter_assistant.services.autonomous_actions_engine.AutonomousActionsEngine.get_instance",
                return_value=mock_engine,
            ):
                with patch(
                    "app.domains.recruiter_assistant.services.monitoring_loop.MonitoringLoop.get_instance",
                    return_value=mock_monitoring,
                ):
                    await scheduler._run_autonomous_actions()

    mock_monitoring.run_checks.assert_awaited_once_with("company-ccc")
    mock_engine.process_monitoring_alerts.assert_awaited_once()


# ---------------------------------------------------------------------------
# 5. Falha de uma empresa não aborta as demais
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_autonomous_actions_isolates_company_failures():
    from app.domains.automation.services.automation_scheduler import AutomationScheduler

    scheduler = AutomationScheduler.__new__(AutomationScheduler)

    mock_alert = MagicMock()
    call_log = []

    async def mock_process(company_id, alerts):
        if company_id == "company-fail":
            raise RuntimeError("simulated failure")
        call_log.append(company_id)
        return []

    mock_engine = MagicMock()
    mock_engine.process_monitoring_alerts = mock_process

    mock_monitoring = MagicMock()
    mock_monitoring.get_alerts = MagicMock(return_value=[mock_alert])

    with patch(
        "app.domains.automation.services.automation_scheduler.AutomationScheduler._select_active_company_ids",
        new=AsyncMock(return_value=["company-fail", "company-ok"]),
    ):
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.domains.automation.services.automation_scheduler.async_session_factory",
            return_value=mock_ctx,
        ):
            with patch(
                "app.domains.recruiter_assistant.services.autonomous_actions_engine.AutonomousActionsEngine.get_instance",
                return_value=mock_engine,
            ):
                with patch(
                    "app.domains.recruiter_assistant.services.monitoring_loop.MonitoringLoop.get_instance",
                    return_value=mock_monitoring,
                ):
                    await scheduler._run_autonomous_actions()

    assert "company-ok" in call_log, (
        "company-ok deve ser processada mesmo após falha de company-fail"
    )
