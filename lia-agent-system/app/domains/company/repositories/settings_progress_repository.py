"""SettingsProgressRepository — multi-model DB queries for settings progress calculation.

Extracted from app/api/v1/settings_progress.py as part of Phase 2 refactor.
Aggregates data from Company, Department, Benefit, Approver, RecruitmentTemplate,
RecruitmentSLA, RecruitmentAutomation, and GlobalSearchSettings.
"""
import logging
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Approver, Benefit, CompanyProfile, Department, GlobalSearchSettings
from app.models.recruitment_journey import RecruitmentAutomation, RecruitmentSLA, RecruitmentTemplate

logger = logging.getLogger(__name__)


class SettingsProgressRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_default_company(self) -> CompanyProfile | None:
        """Get the default company or the first available."""
        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.is_default).limit(1)
        )
        company = result.scalar_one_or_none()
        if not company:
            result = await self.db.execute(
                select(CompanyProfile).order_by(CompanyProfile.created_at).limit(1)
            )
            company = result.scalar_one_or_none()
        return company

    async def count_active_departments(self, company_id) -> int:
        result = await self.db.execute(
            select(func.count(Department.id)).where(
                Department.company_id == company_id,
                Department.is_active,
            )
        )
        return result.scalar() or 0

    async def count_active_benefits(self, company_id) -> int:
        result = await self.db.execute(
            select(func.count(Benefit.id)).where(
                Benefit.company_id == company_id,
                Benefit.is_active,
            )
        )
        return result.scalar() or 0

    async def count_active_approvers(self, company_id) -> int:
        result = await self.db.execute(
            select(func.count(Approver.id)).where(
                Approver.company_id == company_id,
                Approver.is_active,
            )
        )
        return result.scalar() or 0

    async def count_active_templates(self, company_id, category: str | None = None) -> int:
        stmt = select(func.count(RecruitmentTemplate.id)).where(
            RecruitmentTemplate.company_id == company_id,
            RecruitmentTemplate.is_active,
        )
        if category and hasattr(RecruitmentTemplate, "category"):
            stmt = stmt.where(RecruitmentTemplate.category == category)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_active_slas(self, company_id) -> int:
        result = await self.db.execute(
            select(func.count(RecruitmentSLA.id)).where(
                RecruitmentSLA.company_id == company_id,
                RecruitmentSLA.is_active,
            )
        )
        return result.scalar() or 0

    async def count_enabled_automations(self, company_id) -> int:
        result = await self.db.execute(
            select(func.count(RecruitmentAutomation.id)).where(
                RecruitmentAutomation.company_id == company_id,
                RecruitmentAutomation.is_enabled,
            )
        )
        return result.scalar() or 0

    async def get_culture_profile(self, company_id) -> dict[str, Any] | None:
        try:
            result = await self.db.execute(
                text("SELECT additional_data FROM company_culture_profiles WHERE company_id = :cid LIMIT 1"),
                {"cid": str(company_id)},
            )
            row = result.mappings().first()
            if row:
                return {"additional_data": row.get("additional_data")}
            return None
        except Exception as exc:
            logger.warning("get_culture_profile query failed for company_id=%s: %s", company_id, exc)
            return None

    async def get_global_search_settings(self, company_id) -> GlobalSearchSettings | None:
        """Fetch GlobalSearchSettings for a company."""
        try:
            company_id_str = str(company_id)
            result = await self.db.execute(
                select(GlobalSearchSettings).where(
                    GlobalSearchSettings.company_id == company_id_str
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error checking global search settings: {e}")
            return None
