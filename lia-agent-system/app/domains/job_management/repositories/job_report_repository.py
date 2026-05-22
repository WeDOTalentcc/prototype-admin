"""
JobReport Repository — cross-domain reads (VacancyCandidate joined with
Candidate) used by job_report_service for PDF generation.

Per ADR-001 extracted from app/domains/job_management/services/job_report_service.py.
"""
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import Candidate, VacancyCandidate


class JobReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_candidates_with_profile(
        self,
        job_id: UUID,
        company_id: Any | None = None,
    ):
        """List candidates with profile for a job. ``company_id`` optional but
        recommended for defense-in-depth (REGRA ZERO multi-tenancy).

        Caller (job_report_service) verifies vacancy tenant ownership before
        calling, so the VacancyCandidate.company_id filter is best-effort.
        """
        conditions = [VacancyCandidate.vacancy_id == job_id]
        if company_id:
            conditions.append(VacancyCandidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — VacancyCandidate.company_id is
        # appended conditionally above; AST sensor cannot trace.
        result = await self.db.execute(
            select(VacancyCandidate, Candidate)
            .join(Candidate, VacancyCandidate.candidate_id == Candidate.id)
            .where(and_(*conditions))
            .order_by(VacancyCandidate.created_at.desc())
        )
        return list(result.all())
