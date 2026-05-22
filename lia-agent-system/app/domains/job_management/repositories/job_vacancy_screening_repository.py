from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.job_vacancy import JobVacancy


class JobVacancyScreeningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_vacancy_by_id(
        self,
        job_id: UUID,
        company_id: Any | None = None,
    ):
        """Get a job vacancy by its UUID. ``company_id`` optional but
        recommended for defense-in-depth (REGRA ZERO multi-tenancy)."""
        # TENANT-EXEMPT: dynamic builder — JobVacancy.company_id appended
        # conditionally when caller passes it; legacy compat surface.
        query = select(JobVacancy).where(JobVacancy.id == job_id)
        if company_id:
            query = query.where(JobVacancy.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_screening_config(self, job: JobVacancy, merged_config: dict) -> JobVacancy:
        """Persist a merged screening config onto the vacancy and flush."""
        job.screening_config = merged_config
        job.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def update_screening_status(self, job: JobVacancy, existing_config: dict) -> JobVacancy:
        """Persist an updated screening_config (with status changes) and flush."""
        job.screening_config = existing_config
        job.updated_at = datetime.utcnow()
        flag_modified(job, "screening_config")
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def rollback(self):
        """Rollback current transaction."""
        await self.db.rollback()
