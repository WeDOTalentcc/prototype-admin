"""SettingsProgressRepository — multi-model DB queries for settings progress calculation.

Aggregates data from Company, Department, Benefit, Approver, RecruitmentTemplate,
RecruitmentSLA, RecruitmentAutomation, RecruitmentStage, ScreeningQuestion,
IntegrationConnection, AlertConfig, and GlobalSearchSettings.

Section IDs aligned with the 7-item settings menu (Task #210):
  minha-empresa, pipeline, screening, templates-assinatura,
  comunicacao-alertas, usuarios-departamentos, integracoes
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
                text("""
                    SELECT mission, vision, values, core_competencies, evp_bullets,
                           work_model, tech_stack, engineering_culture, default_languages,
                           seniority_levels, default_salary_ranges,
                           additional_data
                    FROM company_culture_profiles
                    WHERE company_id = :cid LIMIT 1
                """),
                {"cid": str(company_id)},
            )
            row = result.mappings().first()
            if row:
                return dict(row)
            return None
        except Exception as exc:
            logger.warning("get_culture_profile query failed for company_id=%s: %s", company_id, exc)
            return None

    async def get_global_search_settings(self, company_id) -> GlobalSearchSettings | None:
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

    async def count_active_stages(self, company_id) -> int:
        try:
            result = await self.db.execute(
                text("""
                    SELECT COUNT(*) FROM recruitment_stages
                    WHERE company_id = :cid AND is_active = true
                """),
                {"cid": str(company_id)},
            )
            return result.scalar() or 0
        except Exception as exc:
            logger.warning("count_active_stages failed: %s", exc)
            return 0

    async def count_active_screening_questions(self, company_id) -> int:
        try:
            result = await self.db.execute(
                text("""
                    SELECT COUNT(*) FROM company_screening_questions
                    WHERE company_id = :cid AND is_active = true
                """),
                {"cid": str(company_id)},
            )
            return result.scalar() or 0
        except Exception as exc:
            logger.warning("count_active_screening_questions failed: %s", exc)
            return 0

    async def has_email_signature(self, company_id) -> bool:
        try:
            result = await self.db.execute(
                text("""
                    SELECT COUNT(*) FROM company_culture_profiles
                    WHERE company_id = :cid
                    AND additional_data IS NOT NULL
                    AND additional_data->>'email_signature' IS NOT NULL
                    AND additional_data->>'email_signature' != ''
                """),
                {"cid": str(company_id)},
            )
            return (result.scalar() or 0) > 0
        except Exception:
            return False

    async def count_active_alert_configs(self, company_id) -> int:
        try:
            result = await self.db.execute(
                text("""
                    SELECT COUNT(*) FROM alert_configs
                    WHERE company_id = :cid AND is_active = true
                """),
                {"cid": str(company_id)},
            )
            return result.scalar() or 0
        except Exception:
            return 0

    async def has_lgpd_schedule(self, company_id) -> bool:
        try:
            result = await self.db.execute(
                text("""
                    SELECT COUNT(*) FROM company_culture_profiles
                    WHERE company_id = :cid
                    AND additional_data IS NOT NULL
                    AND additional_data->>'communication_schedule' IS NOT NULL
                """),
                {"cid": str(company_id)},
            )
            return (result.scalar() or 0) > 0
        except Exception:
            return False

    async def count_active_users(self, company_id) -> int:
        try:
            result = await self.db.execute(
                text("""
                    SELECT COUNT(*) FROM users
                    WHERE company_id = :cid AND is_active = true
                """),
                {"cid": str(company_id)},
            )
            return result.scalar() or 0
        except Exception as exc:
            logger.warning("count_active_users failed: %s", exc)
            return 0

    async def count_active_integrations(self, company_id) -> int:
        try:
            result = await self.db.execute(
                text("""
                    SELECT COUNT(*) FROM integration_connections
                    WHERE company_id = :cid AND is_active = true
                """),
                {"cid": str(company_id)},
            )
            return result.scalar() or 0
        except Exception:
            return 0
