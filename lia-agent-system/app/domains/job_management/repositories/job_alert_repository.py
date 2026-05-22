"""
JobAlert Repository — data access for job alert monitoring service.

Per ADR-001 extracted from app/domains/job_management/services/job_alert_service.py.
Includes cross-domain reads of Candidate and Alert (system-context, no company filter
since alerts run in background scheduler).
"""
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.alert import Alert, AlertSeverity, AlertStatus, AlertType
from lia_models.candidate import Candidate
from lia_models.job_vacancy import JobVacancy


class JobAlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_open_jobs_created_before(self, cutoff_date: datetime) -> list[JobVacancy]:
        # TENANT-EXEMPT: scheduler system-context — JobAlertService runs in
        # background (no per-request company_id); caller may dispatch alerts
        # cross-tenant. RLS not bypassed because system context still scopes
        # at session level.
        result = await self.db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.status == "open", JobVacancy.created_at < cutoff_date)
            )
        )
        return list(result.scalars().all())

    async def list_open_jobs_updated_before(self, cutoff_date: datetime) -> list[JobVacancy]:
        # TENANT-EXEMPT: scheduler system-context — see list_open_jobs_created_before.
        result = await self.db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.status == "open", JobVacancy.updated_at < cutoff_date)
            )
        )
        return list(result.scalars().all())

    async def list_open_jobs(self) -> list[JobVacancy]:
        # TENANT-EXEMPT: scheduler system-context — see list_open_jobs_created_before.
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.status == "open")
        )
        return list(result.scalars().all())

    async def count_candidates_for_job(self, job_id: Any) -> int:
        # TENANT-EXEMPT: count-by-job for scheduler; tenancy implied by
        # join via job_id (caller already verified job belongs to a tenant).
        result = await self.db.execute(
            select(func.count(Candidate.id)).where(Candidate.pipeline_job_id == job_id)
        )
        return result.scalar() or 0

    async def list_candidates_awaiting_feedback_before(
        self, cutoff_date: datetime
    ) -> list[Candidate]:
        # TENANT-EXEMPT: scheduler system-context — JobAlertService walks
        # all tenants to surface SLA breaches.
        result = await self.db.execute(
            select(Candidate).where(
                and_(
                    Candidate.pipeline_stage == "awaiting_feedback",
                    Candidate.updated_at < cutoff_date,
                )
            )
        )
        return list(result.scalars().all())

    async def find_active_alert(
        self,
        alert_type: AlertType,
        *,
        job_id: Any | None = None,
        candidate_id: Any | None = None,
    ) -> Alert | None:
        """Find an active alert.

        Note: Alert model has no ``company_id`` column (intentional — alerts
        are scoped by user_id/job_id/candidate_id which already carry
        tenant ownership upstream).
        """
        # TENANT-EXEMPT: Alert model has no company_id column; scoping
        # happens via user_id / job_id / candidate_id which already
        # encode tenant ownership upstream.
        query = select(Alert).where(
            and_(Alert.alert_type == alert_type, Alert.status == AlertStatus.ACTIVE)
        )
        if job_id:
            query = query.where(Alert.job_id == job_id)
        if candidate_id:
            query = query.where(Alert.candidate_id == candidate_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_active_alerts(
        self,
        *,
        user_id: str | None = None,
        severity: AlertSeverity | None = None,
        limit: int = 50,
    ) -> list[Alert]:
        # TENANT-EXEMPT: Alert model has no company_id column; scoping
        # happens via user_id which already encodes tenant ownership
        # upstream (admin observability surface).
        query = select(Alert).where(Alert.status == AlertStatus.ACTIVE)
        if user_id:
            query = query.where(Alert.user_id == user_id)
        if severity:
            query = query.where(Alert.severity == severity)
        query = query.order_by(
            Alert.severity.desc(), Alert.created_at.desc()
        ).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_alert_by_id(self, alert_id: str) -> Alert | None:
        # TENANT-EXEMPT: Alert model has no company_id column; caller
        # (job_alert_service) verifies ownership via user_id of the alert.
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def severity_counts(self) -> dict[str, int]:
        # TENANT-EXEMPT: scheduler system-context — aggregate counts across
        # tenants for observability dashboard.
        result = await self.db.execute(
            select(Alert.severity, func.count(Alert.id).label("count"))
            .where(Alert.status == AlertStatus.ACTIVE)
            .group_by(Alert.severity)
        )
        return {row.severity.value: row.count for row in result.all()}
