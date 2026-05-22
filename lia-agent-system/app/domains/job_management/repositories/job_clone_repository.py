"""
JobClone Repository — cross-domain reads for cloning operations.

Per ADR-001, cross-domain reads (VacancyCandidate from candidates domain)
should still go through repo layer — extracted from job_clone_service.
"""
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import VacancyCandidate


class JobCloneRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_candidates_for_vacancy(
        self,
        vacancy_id: UUID,
        company_id: Any | None = None,
    ) -> list[VacancyCandidate]:
        """List candidates for a vacancy. ``company_id`` optional for backwards-compat
        (caller in job_clone_service already verified vacancy ownership upstream)."""
        # TENANT-EXEMPT: dynamic builder — VacancyCandidate.company_id is
        # appended below when caller passes it. Caller (job_clone_service)
        # verifies vacancy tenant ownership in get_job_summary_for_clone
        # before invoking this.
        query = select(VacancyCandidate).where(VacancyCandidate.vacancy_id == vacancy_id)
        if company_id:
            query = query.where(VacancyCandidate.company_id == company_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())
