"""
JobAudit Repository — data access for JobVacancyAuditLog.

Per ADR-001 extracted from app/domains/job_management/services/job_audit_service.py.
"""
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.job_vacancy_audit import JobVacancyAuditLog


class JobAuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_for_job(self, where_conditions) -> int:
        # TENANT-EXEMPT: dynamic builder — caller (job_audit_service)
        # composes ``where_conditions`` with JobVacancyAuditLog.company_id
        # filter; AST sensor cannot trace upstream tenant gate.
        result = await self.db.execute(
            select(func.count())
            .select_from(JobVacancyAuditLog)
            .where(where_conditions)
        )
        return result.scalar() or 0

    async def list_for_job(
        self, where_conditions, *, limit: int, offset: int
    ) -> list[JobVacancyAuditLog]:
        # TENANT-EXEMPT: dynamic builder — see count_for_job above.
        result = await self.db.execute(
            select(JobVacancyAuditLog)
            .where(where_conditions)
            .order_by(desc(JobVacancyAuditLog.changed_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
