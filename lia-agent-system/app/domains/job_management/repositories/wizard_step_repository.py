"""
WizardStep Repository — data access for wizard step service (job draft +
company-context lookups).

Per ADR-001 extracted from app/domains/job_management/services/wizard_step_service/service.py
(the legacy .py module foi substituído pelo pacote — vide T-08 services consolidation).

NOTE on imports: original services use mixed import paths
(app.models.company / lia_models.company). This repo lazy-imports inside
each method to remain compatible with both forms — the model class is
resolved at call time.
"""
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.job_draft import JobDraft


class WizardStepRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_draft_by_conversation(
        self,
        conv_uuid: UUID,
        company_id: Any | None = None,
    ):
        """Get the draft for a conversation. ``company_id`` optional but
        recommended for defense-in-depth (REGRA ZERO multi-tenancy)."""
        # TENANT-EXEMPT: dynamic builder — JobDraft.company_id appended
        # conditionally below when caller passes it. conversation_id is
        # tenant-scoped upstream (chat session).
        query = select(JobDraft).where(JobDraft.conversation_id == conv_uuid)
        if company_id:
            query = query.where(JobDraft.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_active_company_benefits(self, company_id):
        try:
            from lia_models.company_benefit import CompanyBenefit
        except ImportError:
            from app.models.company_benefit import CompanyBenefit
        result = await self.db.execute(
            select(CompanyBenefit)
            .where(
                and_(
                    CompanyBenefit.company_id == company_id,
                    CompanyBenefit.is_active,
                )
            )
            .order_by(CompanyBenefit.order)
        )
        return list(result.scalars().all())

    async def get_active_company_profile(self, company_id: Any | None = None):
        """Get active CompanyProfile. ``company_id`` optional but recommended
        — when omitted, returns first active (legacy single-tenant fallback)."""
        try:
            from lia_models.company import CompanyProfile
        except ImportError:
            from app.models.company import CompanyProfile
        # TENANT-EXEMPT: dynamic builder — CompanyProfile.id appended
        # conditionally below; legacy single-tenant fallback.
        # TODO(harness): remove legacy fallback after all callers pass
        # company_id (multi-tenancy fail-closed).
        query = select(CompanyProfile).where(CompanyProfile.is_active)
        if company_id:
            query = query.where(CompanyProfile.id == company_id)
        else:
            query = query.limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_departments_for_profile(self, profile_id):
        try:
            from lia_models.company import Department
        except ImportError:
            from app.models.company import Department
        result = await self.db.execute(
            select(Department)
            .where(Department.company_id == profile_id)
            .order_by(Department.name)
        )
        return list(result.scalars().all())
