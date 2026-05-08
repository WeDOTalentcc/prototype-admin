"""
WizardStep Repository — data access for wizard step service (job draft +
company-context lookups).

Per ADR-001 extracted from
app/domains/job_management/services/wizard_step_service.py and
app/domains/job_management/services/wizard_step_service/service.py.

NOTE on imports: original services use mixed import paths
(app.models.company / lia_models.company). This repo lazy-imports inside
each method to remain compatible with both forms — the model class is
resolved at call time.
"""
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.job_draft import JobDraft


class WizardStepRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_draft_by_conversation(self, conv_uuid: UUID):
        result = await self.db.execute(
            select(JobDraft).where(JobDraft.conversation_id == conv_uuid)
        )
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

    async def get_active_company_profile(self):
        try:
            from lia_models.company import CompanyProfile
        except ImportError:
            from app.models.company import CompanyProfile
        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.is_active).limit(1)
        )
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
