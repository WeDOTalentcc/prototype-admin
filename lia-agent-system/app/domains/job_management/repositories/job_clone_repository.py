"""
JobClone Repository — cross-domain reads for cloning operations.

Per ADR-001, cross-domain reads (VacancyCandidate from candidates domain)
should still go through repo layer — extracted from job_clone_service.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import VacancyCandidate


class JobCloneRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_candidates_for_vacancy(self, vacancy_id: UUID) -> list[VacancyCandidate]:
        result = await self.db.execute(
            select(VacancyCandidate).where(VacancyCandidate.vacancy_id == vacancy_id)
        )
        return list(result.scalars().all())
