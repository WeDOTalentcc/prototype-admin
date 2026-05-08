"""
JobReport Repository — cross-domain reads (VacancyCandidate joined with
Candidate) used by job_report_service for PDF generation.

Per ADR-001 extracted from app/domains/job_management/services/job_report_service.py.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import Candidate, VacancyCandidate


class JobReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_candidates_with_profile(self, job_id: UUID):
        result = await self.db.execute(
            select(VacancyCandidate, Candidate)
            .join(Candidate, VacancyCandidate.candidate_id == Candidate.id)
            .where(VacancyCandidate.vacancy_id == job_id)
            .order_by(VacancyCandidate.created_at.desc())
        )
        return list(result.all())
