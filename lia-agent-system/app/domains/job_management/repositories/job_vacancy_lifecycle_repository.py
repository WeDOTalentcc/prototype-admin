from datetime import datetime
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.job_vacancy import JobVacancy
import uuid as uuid_lib


class JobVacancyLifecycleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_vacancy_by_id_and_company(self, vacancy_id, company_id):
        """Get a job vacancy by ID and company_id."""
        result = await self.db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.id == vacancy_id, JobVacancy.company_id == company_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_vacancy_by_uuid_str(
        self,
        vacancy_id_str: str,
        company_id: Any | None = None,
    ):
        """Get a job vacancy by string UUID. ``company_id`` optional but
        recommended for defense-in-depth (REGRA ZERO multi-tenancy)."""
        # TENANT-EXEMPT: dynamic builder — JobVacancy.company_id appended
        # conditionally when caller passes it; legacy compat surface.
        query = select(JobVacancy).where(JobVacancy.id == uuid_lib.UUID(vacancy_id_str))
        if company_id:
            query = query.where(JobVacancy.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def publish_vacancy(self, job: JobVacancy) -> JobVacancy:
        """Set vacancy status to Ativa and set open_date."""
        job.status = "Ativa"
        job.open_date = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def publish_vacancy_v2(self, job: JobVacancy) -> JobVacancy:
        """Set vacancy status to Ativa and update timestamps (full version)."""
        job.status = "Ativa"
        job.open_date = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def unpublish_vacancy(self, job: JobVacancy) -> tuple[JobVacancy, bool]:
        """Phase C.2 — clear published_* flags + last_published_at. Idempotent.

        Returns (job, changed) where ``changed`` is False when the vacancy was
        already unpublished (so the route can respond {changed: false} without
        emitting an audit event).

        Status itself is NOT changed here: the recruiter explicitly chooses
        "Pausar" or "Concluir" via the JobStatusModal as a separate action.
        Symmetric counterpart to publish_vacancy / publish_vacancy_v2.
        """
        before = (
            bool(getattr(job, "published_linkedin", False)),
            bool(getattr(job, "published_indeed", False)),
            bool(getattr(job, "published_website", False)),
            getattr(job, "last_published_at", None),
        )
        job.published_linkedin = False
        job.published_indeed = False
        job.published_website = False
        job.last_published_at = None
        job.updated_at = datetime.utcnow()
        after = (False, False, False, None)
        changed = before != after
        if changed:
            await self.db.flush()
            await self.db.refresh(job)
        return job, changed

    async def close_vacancy(self, vacancy: JobVacancy) -> JobVacancy:
        """Set vacancy status to Concluída and set closed_at."""
        vacancy.status = "Concluída"
        vacancy.closed_at = datetime.utcnow()
        return vacancy

    async def rollback(self):
        """Rollback current transaction."""
        await self.db.rollback()

    async def update_vacancy_status(self, job: JobVacancy, new_status: str) -> JobVacancy:
        """Update vacancy status and updated_at timestamp."""
        job.status = new_status
        job.updated_at = datetime.utcnow()
        if new_status == "Ativa" and not job.open_date:
            job.open_date = datetime.utcnow()
        elif new_status in ["Concluída", "Cancelada", "Arquivada"] and not job.closed_at:
            job.closed_at = datetime.utcnow()
        return job

    async def update_vacancy_recruiter(
        self, job: JobVacancy, recruiter_name: str, recruiter_email: str
    ) -> JobVacancy:
        """Assign a recruiter to a vacancy."""
        job.recruiter = recruiter_name
        job.recruiter_email = recruiter_email
        job.updated_at = datetime.utcnow()
        return job
