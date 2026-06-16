"""
IncidentResponseService — LGPD Art.48 compliance.

Registers data security incidents and triggers internal admin alerts.
DOES NOT automatically notify ANPD or end users — that is done manually
via the admin page by the DPO/compliance team.

Alert flow: incident detected → register in DB → CRITICAL log (monitoring
pickup) → DPO reviews → manual ANPD decision if needed (>72h window
advisory only, tracked via incident_detected_at).
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.incident import DataIncident, IncidentSeverity, IncidentStatus

from app.domains.lgpd.repositories.data_incident_repository import (
    DataIncidentRepository,
)

logger = logging.getLogger(__name__)


class IncidentResponseService:

    async def register_incident(
        self,
        db: AsyncSession,
        *,
        company_id: str,
        title: str,
        description: str,
        severity: IncidentSeverity = IncidentSeverity.MEDIUM,
        affected_data_categories: Optional[list] = None,
        affected_users_count: Optional[str] = None,
        incident_detected_at: Optional[datetime] = None,
        reported_by: str = "system",
    ) -> DataIncident:
        """Register a data incident and trigger internal admin alert."""
        incident = DataIncident(
            company_id=company_id,
            title=title,
            description=description,
            severity=severity,
            affected_data_categories=str(affected_data_categories) if affected_data_categories else None,
            affected_users_count=affected_users_count,
            incident_detected_at=incident_detected_at or datetime.now(timezone.utc),
            reported_by=reported_by,
        )
        db.add(incident)
        await db.flush()  # get ID before commit

        logger.warning(
            "[LGPD-ART48] Data incident registered: id=%s company=%s severity=%s title=%r",
            incident.id, company_id, severity, title,
        )

        # Trigger internal admin alert (non-blocking; failure must not prevent registration)
        try:
            await self._alert_admin_team(incident)
        except Exception as e:
            logger.error("[LGPD-ART48] Alert dispatch failed: %s", e)

        await db.commit()
        await db.refresh(incident)
        return incident

    async def _alert_admin_team(self, incident: DataIncident) -> None:
        """Send structured CRITICAL log for monitoring system pickup."""
        try:
            logger.critical(
                "[LGPD-ART48-ALERT] DATA INCIDENT REQUIRES ATTENTION | "
                "id=%s | company=%s | severity=%s | title=%r | "
                "detected_at=%s | LGPD Art.48: 72h window starts now",
                incident.id,
                incident.company_id,
                incident.severity,
                incident.title,
                incident.incident_detected_at.isoformat(),
            )
            # Additional alert channels can be added here:
            # await send_slack_alert(...)  # if Slack webhook configured
            # await send_email_alert(...)  # if email service configured
        except Exception as e:
            # Alert failure must never prevent incident registration
            logger.error("[LGPD-ART48] Failed to send admin alert: %s", e)

    async def get_open_incidents(
        self,
        db: AsyncSession,
        company_id: str,
    ) -> list:
        """Get all open/investigating incidents for a company (for DPO review)."""
        repo = DataIncidentRepository(db)
        return await repo.list_open_for_company(company_id)

    async def update_status(
        self,
        db: AsyncSession,
        incident_id: str,
        new_status: IncidentStatus,
    ) -> Optional[DataIncident]:
        """Update incident status (e.g., mark as REPORTED_ANPD after manual notification)."""
        repo = DataIncidentRepository(db)
        incident = await repo.get_by_id(incident_id)
        if not incident:
            return None
        incident.status = new_status
        if new_status == IncidentStatus.REPORTED_ANPD:
            incident.anpd_reported_at = datetime.now(timezone.utc)
        elif new_status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(incident)
        return incident
