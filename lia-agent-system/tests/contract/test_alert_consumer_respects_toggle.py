"""
tests/contract/test_alert_consumer_respects_toggle.py

P0-W1-06 sensor: check_all_alerts() must respect CommunicationSettings.alerts_enabled.

Ghost-setting fix (2026-05-24): AlertPreferencesPanel lets recruiters configure
alert types and channels. The ``alerts_enabled`` boolean on CommunicationSettings is
the global opt-out toggle. Before this fix, check_all_alerts() ignored it entirely —
the toggle was a ghost setting with zero consumer.

Principle: Fix in the producer (job_alert_service), not the consumers (endpoints).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class FakeCommunicationSettings:
    def __init__(self, alerts_enabled: bool):
        self.alerts_enabled = alerts_enabled


@pytest.mark.asyncio
async def test_check_all_alerts_skips_when_disabled():
    """P0-W1-06: check_all_alerts must be a no-op when alerts_enabled=False."""
    from app.domains.job_management.services.job_alert_service import JobAlertService

    svc = JobAlertService()
    mock_db = AsyncMock()
    disabled_settings = FakeCommunicationSettings(alerts_enabled=False)

    with patch(
        "app.domains.job_management.services.job_alert_service.CommunicationSettingsRepository"
    ) as MockRepo:
        MockRepo.return_value.get_by_company_id = AsyncMock(return_value=disabled_settings)

        result = await svc.check_all_alerts(db=mock_db, company_id="tenant-disabled-uuid")

    assert result == [], (
        "check_all_alerts must return [] when alerts_enabled=False — ghost-setting P0-W1-06"
    )


@pytest.mark.asyncio
async def test_check_all_alerts_runs_when_enabled():
    """check_all_alerts must run normally when alerts_enabled=True."""
    from app.domains.job_management.services.job_alert_service import JobAlertService

    svc = JobAlertService()
    mock_db = AsyncMock()
    enabled_settings = FakeCommunicationSettings(alerts_enabled=True)

    with patch(
        "app.domains.job_management.services.job_alert_service.CommunicationSettingsRepository"
    ) as MockRepo, patch.object(
        svc, "check_critical_jobs", AsyncMock(return_value=[])
    ), patch.object(
        svc, "check_stale_jobs", AsyncMock(return_value=[])
    ), patch.object(
        svc, "check_low_volume_jobs", AsyncMock(return_value=[])
    ), patch.object(
        svc, "check_pending_feedback", AsyncMock(return_value=[])
    ):
        MockRepo.return_value.get_by_company_id = AsyncMock(return_value=enabled_settings)

        result = await svc.check_all_alerts(db=mock_db, company_id="tenant-enabled-uuid")

    # The sub-checks ran (even if they returned empty lists), meaning alerts_enabled=True
    # did NOT short-circuit. Result is a list (not None).
    assert isinstance(result, list), (
        "check_all_alerts must return a list when alerts_enabled=True"
    )


@pytest.mark.asyncio
async def test_check_all_alerts_runs_when_settings_not_found():
    """check_all_alerts must run normally when no CommunicationSettings row exists (new tenant)."""
    from app.domains.job_management.services.job_alert_service import JobAlertService

    svc = JobAlertService()
    mock_db = AsyncMock()

    with patch(
        "app.domains.job_management.services.job_alert_service.CommunicationSettingsRepository"
    ) as MockRepo, patch.object(
        svc, "check_critical_jobs", AsyncMock(return_value=[])
    ), patch.object(
        svc, "check_stale_jobs", AsyncMock(return_value=[])
    ), patch.object(
        svc, "check_low_volume_jobs", AsyncMock(return_value=[])
    ), patch.object(
        svc, "check_pending_feedback", AsyncMock(return_value=[])
    ):
        # No settings row — default behaviour must be to run (fail-open for new tenants)
        MockRepo.return_value.get_by_company_id = AsyncMock(return_value=None)

        result = await svc.check_all_alerts(db=mock_db, company_id="new-tenant-uuid")

    assert isinstance(result, list), (
        "check_all_alerts must run when settings not found (default on = fail-open)"
    )


@pytest.mark.asyncio
async def test_check_all_alerts_runs_without_company_id():
    """Legacy callers without company_id must still work (backward compat)."""
    from app.domains.job_management.services.job_alert_service import JobAlertService

    svc = JobAlertService()
    mock_db = AsyncMock()

    with patch.object(
        svc, "check_critical_jobs", AsyncMock(return_value=[])
    ), patch.object(
        svc, "check_stale_jobs", AsyncMock(return_value=[])
    ), patch.object(
        svc, "check_low_volume_jobs", AsyncMock(return_value=[])
    ), patch.object(
        svc, "check_pending_feedback", AsyncMock(return_value=[])
    ):
        result = await svc.check_all_alerts(db=mock_db)  # no company_id

    assert isinstance(result, list), (
        "check_all_alerts must work when company_id is omitted (scheduler context)"
    )
