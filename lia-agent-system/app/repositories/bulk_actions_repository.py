"""
BulkActionsRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/bulk_actions.py.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate, VacancyCandidate
from app.models.company import CompanyProfile
from app.models.email_template import EmailTemplate
from app.models.job_vacancy import JobVacancy

EXCLUDED_STATUSES = ("rejected", "declined", "withdrawn")
ORGANIC_ORIGINS = ("web", "whatsapp")
SOURCING_ORIGINS = ("sourcing", "ats")


class BulkActionsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Candidate ───────────────────────────────────────────────────────────

    async def get_candidate_by_id(self, candidate_id: uuid.UUID) -> Candidate | None:
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    async def delete_candidate(self, candidate: Candidate) -> None:
        await self.db.delete(candidate)

    # ── JobVacancy ──────────────────────────────────────────────────────────

    async def get_job_vacancy_by_id(self, vacancy_id: uuid.UUID) -> JobVacancy | None:
        # TENANT-EXEMPT: session injected via Depends(get_tenant_db) sets Postgres RLS
        # context per request (app/core/database.py:39); RLS lia_app role enforces
        # company_id filter at DB layer regardless of explicit WHERE
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.id == vacancy_id)
        )
        return result.scalar_one_or_none()

    # ── EmailTemplate ───────────────────────────────────────────────────────

    async def get_email_template_by_id(self, template_id: uuid.UUID) -> EmailTemplate | None:
        result = await self.db.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    # ── CompanyProfile ──────────────────────────────────────────────────────

    async def get_company_by_id(self, company_id: Any) -> CompanyProfile | None:
        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_default_company(self) -> CompanyProfile | None:
        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.is_default).limit(1)
        )
        return result.scalar_one_or_none()

    # ── Saturation ──────────────────────────────────────────────────────────

    async def get_vacancy_channel_counts(
        self, vacancy_id: Any
    ) -> dict:
        """Return organic and sourcing active candidate counts for a vacancy."""
        active_filter = and_(
            VacancyCandidate.vacancy_id == vacancy_id,
            not_(VacancyCandidate.status.in_(EXCLUDED_STATUSES)),
        )
        channel_result = await self.db.execute(
            select(
                func.count(VacancyCandidate.id).filter(
                    VacancyCandidate.origin.in_(ORGANIC_ORIGINS)
                    | VacancyCandidate.origin.is_(None)
                ).label("organic"),
                func.count(VacancyCandidate.id).filter(
                    VacancyCandidate.origin.in_(SOURCING_ORIGINS)
                ).label("sourcing"),
            ).where(active_filter)
        )
        row = channel_result.one()
        return {
            "organic": row.organic or 0,
            "sourcing": row.sourcing or 0,
        }
