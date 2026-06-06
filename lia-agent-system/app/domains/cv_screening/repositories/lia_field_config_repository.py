"""LiaFieldConfigRepository — DB access for LIA field-config related models.

Extracted from app/domains/cv_screening/services/lia_field_config_service.py per ADR-001.
Cross-domain models (CompanyProfile, JobVacancy) are accessed via foreign-domain
read patterns; these stay inline today (sprint 6 follow-up to consolidate).
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class LiaFieldConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_field_toggles(self, company_uuid: UUID):
        from lia_models.lia_field_toggles import LiaFieldToggle  # type: ignore
        result = await self.db.execute(
            select(LiaFieldToggle).where(LiaFieldToggle.company_id == company_uuid)
        )
        return list(result.scalars().all())

    async def get_company_profile(self, company_uuid: UUID):
        from app.models.company import CompanyProfile
        # Eager-load ORM relationships consumed as canonical LIA field_keys
        # (departments, benefits) plus the other CompanyProfile relationships.
        # A blind getattr on these in LiaFieldConfigService._get_company_value
        # would otherwise trigger an async lazy-load outside the active
        # greenlet -> sqlalchemy.exc.MissingGreenlet, which is swallowed by
        # build_company_agent_context and silently empties the toggle-filtered
        # company context delivered to every agent. selectinload fixes it at
        # the producer (canonical-fix: load eagerly, do not lazy-load).
        result = await self.db.execute(
            select(CompanyProfile)
            .where(CompanyProfile.id == company_uuid)
            .options(
                selectinload(CompanyProfile.departments),
                selectinload(CompanyProfile.benefits),
                selectinload(CompanyProfile.culture_values),
                selectinload(CompanyProfile.compensation_policies),
            )
        )
        return result.scalar_one_or_none()

    async def get_culture_profile(self, company_uuid: UUID):
        """Load the CompanyCultureProfile for a company (separate query — there
        is NO ORM relationship from CompanyProfile to it). Home of the narrative
        fields (mission/vision/values/tech_stack/...). Without this load those
        toggles are inert: the recruiter flips them ON but the value never
        reaches any agent prompt (FASE 0 ghost fix, audit 2026-06-06)."""
        from lia_models.company_culture import CompanyCultureProfile  # type: ignore
        result = await self.db.execute(
            select(CompanyCultureProfile).where(
                CompanyCultureProfile.company_id == company_uuid
            )
        )
        return result.scalars().first()

    async def list_recent_jobs_for_company(
        self,
        *,
        company_id: str,
        limit: int = 20,
    ):
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        from app.models.job_vacancy import JobVacancy
        result = await self.db.execute(
            select(JobVacancy)
            .where(JobVacancy.company_id == company_id)
            .order_by(JobVacancy.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_recruiter_preferences(
        self,
        *,
        recruiter_id: str,
        company_id: str,
    ):
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        from lia_models.recruiter_profile import RecruiterFieldPreference
        result = await self.db.execute(
            select(RecruiterFieldPreference).where(
                RecruiterFieldPreference.recruiter_id == recruiter_id,
                RecruiterFieldPreference.company_id == company_id,
            )
        )
        return list(result.scalars().all())

    async def get_recruiter_preference_for_field(
        self,
        *,
        recruiter_id: str,
        company_id: str,
        field_name: str,
    ):
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        from lia_models.recruiter_profile import RecruiterFieldPreference
        result = await self.db.execute(
            select(RecruiterFieldPreference).where(
                RecruiterFieldPreference.recruiter_id == recruiter_id,
                RecruiterFieldPreference.company_id == company_id,
                RecruiterFieldPreference.field_name == field_name,
            )
        )
        return result.scalar_one_or_none()
