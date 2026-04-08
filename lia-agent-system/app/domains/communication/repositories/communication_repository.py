"""
Communication domain repository -- handles DB operations for CommunicationLog.
"""
import uuid as uuid_mod
from datetime import datetime

from sqlalchemy import and_, func, not_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.services.communication_models import CommunicationLog
from app.models.candidate import VacancyCandidate
from app.models.company import CompanyProfile
from app.models.job_vacancy import JobVacancy

EXCLUDED_STATUSES = ("rejected", "declined", "withdrawn")
ORGANIC_ORIGINS = ("web", "whatsapp")
SOURCING_ORIGINS = ("sourcing", "ats")
DEFAULT_SATURATION_THRESHOLD = 20


class CommunicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_log_by_provider_message_id(
        self, message_id: str, values: dict
    ) -> int:
        """Update CommunicationLog record(s) matching provider_message_id.

        Returns the number of rows updated.
        """
        result = await self.db.execute(
            update(CommunicationLog)
            .where(CommunicationLog.provider_message_id == message_id)
            .values(**values)
        )
        await self.db.commit()
        return result.rowcount  # type: ignore[union-attr]

    async def check_vacancy_saturation(self, vacancy_id: str) -> dict:
        """Check if a vacancy pipeline is saturated for screening invites.

        Returns a dict with saturation status details.
        """
        try:
            vid = uuid_mod.UUID(vacancy_id)
        except (ValueError, TypeError):
            return {"is_saturated": False, "error": "invalid_vacancy_id"}

        result = await self.db.execute(select(JobVacancy).where(JobVacancy.id == vid))
        vacancy = result.scalar_one_or_none()
        if not vacancy:
            return {"is_saturated": False, "error": "vacancy_not_found"}

        company = None
        try:
            cr = await self.db.execute(
                select(CompanyProfile).where(CompanyProfile.id == vacancy.company_id)
            )
            company = cr.scalar_one_or_none()
        except Exception:
            pass
        if not company:
            cr2 = await self.db.execute(
                select(CompanyProfile).where(CompanyProfile.is_default).limit(1)
            )
            company = cr2.scalar_one_or_none()

        sat = {}
        if company and company.additional_data:
            sat = company.additional_data.get("saturation_settings", {})

        governance_rules = vacancy.governance_rules or {}
        threshold_web = governance_rules.get("threshold_web", sat.get("threshold_web", DEFAULT_SATURATION_THRESHOLD))
        threshold_sourcing = governance_rules.get("threshold_sourcing", sat.get("threshold_sourcing", DEFAULT_SATURATION_THRESHOLD))

        disabled_until_str = governance_rules.get("saturation_disabled_until")
        bypass_active = False
        if disabled_until_str:
            try:
                disabled_until = datetime.fromisoformat(disabled_until_str)
                if disabled_until > datetime.utcnow():
                    bypass_active = True
            except (ValueError, TypeError):
                pass

        active_filter = and_(
            VacancyCandidate.vacancy_id == vid,
            not_(VacancyCandidate.status.in_(EXCLUDED_STATUSES)),
        )
        channel_result = await self.db.execute(
            select(
                func.count(VacancyCandidate.id).filter(
                    VacancyCandidate.origin.in_(ORGANIC_ORIGINS) | VacancyCandidate.origin.is_(None)
                ).label("organic"),
                func.count(VacancyCandidate.id).filter(
                    VacancyCandidate.origin.in_(SOURCING_ORIGINS)
                ).label("sourcing"),
            ).where(active_filter)
        )
        row = channel_result.one()
        organic_count = row.organic or 0
        sourcing_count = row.sourcing or 0

        organic_saturated = organic_count >= threshold_web and not bypass_active
        sourcing_saturated = sourcing_count >= threshold_sourcing and not bypass_active
        is_saturated = organic_saturated or sourcing_saturated

        return {
            "is_saturated": is_saturated,
            "bypass_active": bypass_active,
            "organic_count": organic_count,
            "sourcing_count": sourcing_count,
            "threshold_web": threshold_web,
            "threshold_sourcing": threshold_sourcing,
            "organic_saturated": organic_saturated,
            "sourcing_saturated": sourcing_saturated,
        }
