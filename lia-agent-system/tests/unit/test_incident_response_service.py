"""UC-P0-11: IncidentResponseService registers incidents and alerts admin."""
import logging
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from lia_models.incident import IncidentSeverity, IncidentStatus
from app.domains.lgpd.services.incident_response_service import IncidentResponseService


def _make_mock_incident(
    incident_id="test-id",
    company_id="company-001",
    severity=IncidentSeverity.HIGH,
    title="Unauthorized data access",
    status=IncidentStatus.OPEN,
):
    mock = MagicMock()
    mock.id = incident_id
    mock.company_id = company_id
    mock.severity = severity
    mock.title = title
    mock.status = status
    mock.created_at = datetime.now(timezone.utc)
    mock.incident_detected_at = datetime.now(timezone.utc)
    return mock


def _make_mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_register_incident_creates_record():
    """register_incident() adds a DataIncident to the DB session and commits."""
    service = IncidentResponseService()
    mock_db = _make_mock_db()
    mock_incident = _make_mock_incident()

    with patch(
        "app.domains.lgpd.services.incident_response_service.DataIncident",
        return_value=mock_incident,
    ):
        result = await service.register_incident(
            mock_db,
            company_id="company-001",
            title="Unauthorized data access",
            description="Candidate data was accessed without authorization",
            severity=IncidentSeverity.HIGH,
        )

    mock_db.add.assert_called_once_with(mock_incident)
    mock_db.flush.assert_awaited_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(mock_incident)
    assert result == mock_incident


@pytest.mark.asyncio
async def test_register_incident_triggers_admin_alert(caplog):
    """register_incident() emits a CRITICAL log containing LGPD-ART48-ALERT."""
    service = IncidentResponseService()
    mock_db = _make_mock_db()
    mock_incident = _make_mock_incident(severity=IncidentSeverity.CRITICAL, title="Database breach")

    with patch(
        "app.domains.lgpd.services.incident_response_service.DataIncident",
        return_value=mock_incident,
    ):
        with caplog.at_level(logging.CRITICAL):
            await service.register_incident(
                mock_db,
                company_id="company-001",
                title="Database breach",
                description="Unauthorized access to candidate DB",
            )

    assert "LGPD-ART48-ALERT" in caplog.text
    assert "company-001" in caplog.text


@pytest.mark.asyncio
async def test_alert_failure_does_not_prevent_registration():
    """_alert_admin_team() failure must not propagate and block incident registration."""
    service = IncidentResponseService()
    mock_db = _make_mock_db()
    mock_incident = _make_mock_incident()

    # Force _alert_admin_team to raise
    async def bad_alert(incident):
        raise RuntimeError("monitoring system down")

    service._alert_admin_team = bad_alert

    with patch(
        "app.domains.lgpd.services.incident_response_service.DataIncident",
        return_value=mock_incident,
    ):
        # Should not raise even if alert fails
        result = await service.register_incident(
            mock_db,
            company_id="company-001",
            title="Test",
            description="desc",
        )

    mock_db.commit.assert_awaited_once()
    assert result == mock_incident


@pytest.mark.asyncio
async def test_update_status_to_reported_anpd():
    """update_status(REPORTED_ANPD) sets anpd_reported_at timestamp."""
    service = IncidentResponseService()
    mock_db = AsyncMock()

    mock_incident = _make_mock_incident()
    mock_incident.anpd_reported_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    result = await service.update_status(mock_db, "test-id", IncidentStatus.REPORTED_ANPD)

    assert result == mock_incident
    assert mock_incident.status == IncidentStatus.REPORTED_ANPD
    assert mock_incident.anpd_reported_at is not None
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_status_not_found():
    """update_status() returns None when incident_id does not exist."""
    service = IncidentResponseService()
    mock_db = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await service.update_status(mock_db, "nonexistent", IncidentStatus.RESOLVED)

    assert result is None
