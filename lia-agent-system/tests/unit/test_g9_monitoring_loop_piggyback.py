"""G9 canonical contract — MonitoringLoop triggers ProactiveDetectorService.

Without celery worker running, the beat task `proactive.detect_hints_hourly`
never fires and proactive_actions stays empty. MonitoringLoop already runs
hourly via uvicorn lifespan — we piggyback on its iteration to invoke the
detector service, restoring the proactive pipeline end-to-end.

Tests:
1. _run_all_tenants invokes proactive_detector_service.run_for_company
   for each active tenant (in addition to MonitoringLoop's own checks).
2. Detector failure does NOT crash the MonitoringLoop iteration
   (defense-in-depth — own checks must complete even if detector breaks).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_monitoring_loop_invokes_proactive_detector_service():
    """G9: each tenant should get both MonitoringLoop checks AND
    ProactiveDetectorService.run_for_company invocation."""
    from app.domains.recruiter_assistant.services.monitoring_loop import (
        MonitoringLoop,
    )

    instance = MonitoringLoop.__new__(MonitoringLoop)
    instance._running = True
    instance._idle_backoff_count = 0
    instance._last_run = {}
    instance._alert_store = {}

    # Patch the run_checks (existing path) to count calls.
    run_checks_mock = AsyncMock(return_value=[])
    detector_mock = AsyncMock(return_value={"persisted": 2})

    # Mock the AsyncSessionLocal context manager for tenant fetch.
    fake_rows = [("tenant-a",), ("tenant-b",)]
    fake_result = MagicMock()
    fake_result.fetchall = MagicMock(return_value=fake_rows)

    fake_session = MagicMock()
    fake_session.__aenter__ = AsyncMock(return_value=fake_session)
    fake_session.__aexit__ = AsyncMock(return_value=False)
    fake_session.execute = AsyncMock(return_value=fake_result)

    with patch.object(instance, "run_checks", run_checks_mock), \
         patch(
             "lia_config.database.AsyncSessionLocal",
             return_value=fake_session,
         ), \
         patch(
             "app.shared.services.proactive_detector_service."
             "proactive_detector_service.run_for_company",
             detector_mock,
         ):
        result = await instance._run_all_tenants()

    assert result is True
    # run_checks called for both tenants (existing behavior preserved)
    assert run_checks_mock.call_count == 2
    # G9: detector ALSO called for both tenants
    assert detector_mock.call_count == 2
    called_tenants = {call.args[1] for call in detector_mock.call_args_list}
    assert called_tenants == {"tenant-a", "tenant-b"}


@pytest.mark.asyncio
async def test_detector_failure_does_not_break_iteration():
    """G9 defense-in-depth: if detector raises, MonitoringLoop's own
    checks still complete for the remaining tenants."""
    from app.domains.recruiter_assistant.services.monitoring_loop import (
        MonitoringLoop,
    )

    instance = MonitoringLoop.__new__(MonitoringLoop)
    instance._running = True
    instance._idle_backoff_count = 0
    instance._last_run = {}
    instance._alert_store = {}

    run_checks_mock = AsyncMock(return_value=[])
    detector_mock = AsyncMock(side_effect=RuntimeError("detector broke"))

    fake_rows = [("tenant-a",), ("tenant-b",)]
    fake_result = MagicMock()
    fake_result.fetchall = MagicMock(return_value=fake_rows)
    fake_session = MagicMock()
    fake_session.__aenter__ = AsyncMock(return_value=fake_session)
    fake_session.__aexit__ = AsyncMock(return_value=False)
    fake_session.execute = AsyncMock(return_value=fake_result)

    with patch.object(instance, "run_checks", run_checks_mock), \
         patch(
             "lia_config.database.AsyncSessionLocal",
             return_value=fake_session,
         ), \
         patch(
             "app.shared.services.proactive_detector_service."
             "proactive_detector_service.run_for_company",
             detector_mock,
         ):
        result = await instance._run_all_tenants()

    # Iteration completed despite detector failure.
    assert result is True
    # run_checks called for both tenants (defense-in-depth — own checks not blocked)
    assert run_checks_mock.call_count == 2
    # detector_mock called for both tenants (each iteration tries
    # independently)
    assert detector_mock.call_count == 2


@pytest.mark.asyncio
async def test_no_tenants_returns_false_skips_detector():
    """When no active tenants, _run_all_tenants returns False (idle
    backoff signal) and skips both checks AND detector — no wasted work."""
    from app.domains.recruiter_assistant.services.monitoring_loop import (
        MonitoringLoop,
    )

    instance = MonitoringLoop.__new__(MonitoringLoop)
    instance._running = True
    instance._idle_backoff_count = 0

    run_checks_mock = AsyncMock(return_value=[])
    detector_mock = AsyncMock(return_value={})

    fake_result = MagicMock()
    fake_result.fetchall = MagicMock(return_value=[])  # no tenants
    fake_session = MagicMock()
    fake_session.__aenter__ = AsyncMock(return_value=fake_session)
    fake_session.__aexit__ = AsyncMock(return_value=False)
    fake_session.execute = AsyncMock(return_value=fake_result)

    with patch.object(instance, "run_checks", run_checks_mock), \
         patch(
             "lia_config.database.AsyncSessionLocal",
             return_value=fake_session,
         ), \
         patch(
             "app.shared.services.proactive_detector_service."
             "proactive_detector_service.run_for_company",
             detector_mock,
         ):
        result = await instance._run_all_tenants()

    assert result is False
    assert run_checks_mock.call_count == 0
    assert detector_mock.call_count == 0
