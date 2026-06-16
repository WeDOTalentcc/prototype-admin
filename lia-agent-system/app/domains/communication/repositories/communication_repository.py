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

    async def check_vacancy_saturation(
        self,
        vacancy_id: str,
        company_id: str | None = None,
    ) -> dict:
        """Check if a vacancy pipeline is saturated for screening invites.

        Returns a dict with saturation status details.
        Multi-tenancy defense-in-depth: pass company_id to filter the vacancy
        lookup at query level (Postgres RLS — Task #1143 — guards by default).
        """
        try:
            vid = uuid_mod.UUID(vacancy_id)
        except (ValueError, TypeError):
            return {"is_saturated": False, "error": "invalid_vacancy_id"}

        conditions = [JobVacancy.id == vid]
        if company_id:
            conditions.append(JobVacancy.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # JobVacancy.company_id filter (conditional, above). Sensor cannot
        # trace through where(*conditions) spread.
        result = await self.db.execute(select(JobVacancy).where(*conditions))
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


    # ------------------------------------------------------------------ #
    # CommunicationLog / PendingApproval / OptOut / Quarantine extensions   #
    # ------------------------------------------------------------------ #

    async def list_logs_since(
        self,
        *,
        candidate_id: str,
        company_id: str,
        since,
        statuses: list,
    ) -> list:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(CommunicationLog).where(
                and_(
                    CommunicationLog.candidate_id == candidate_id,
                    CommunicationLog.company_id == company_id,
                    CommunicationLog.sent_at >= since,
                    CommunicationLog.status.in_(statuses),
                )
            )
        )
        return list(result.scalars())

    async def list_logs_by_candidate_with_filters(
        self,
        *,
        company_id: str,
        candidate_id: str,
        channel: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        from sqlalchemy import desc
        conditions = [
            CommunicationLog.company_id == company_id,
            CommunicationLog.candidate_id == candidate_id,
        ]
        if channel:
            conditions.append(CommunicationLog.channel == channel)
        if status:
            conditions.append(CommunicationLog.status == status)
        result = await self.db.execute(
            select(CommunicationLog)
            .where(and_(*conditions))
            .order_by(desc(CommunicationLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())

    async def list_logs_in_day(
        self,
        *,
        company_id: str,
        day_start,
        day_end,
    ) -> list:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(CommunicationLog).where(
                and_(
                    CommunicationLog.company_id == company_id,
                    CommunicationLog.created_at >= day_start,
                    CommunicationLog.created_at < day_end,
                )
            )
        )
        return list(result.scalars())

    async def list_queued_logs_for_retry(
        self,
        *,
        now,
        queued_status: str,
        limit: int = 100,
    ) -> list:
        from sqlalchemy import or_
        result = await self.db.execute(
            select(CommunicationLog).where(
                and_(
                    CommunicationLog.status == queued_status,
                    or_(
                        CommunicationLog.next_retry_at.is_(None),
                        CommunicationLog.next_retry_at <= now,
                    ),
                )
            ).limit(limit)
        )
        return list(result.scalars())

    async def get_active_optout(
        self,
        *,
        candidate_id: str,
        company_id: str,
        channel_value: str,
        opt_out_type_all: str = "all",
    ):
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        from app.domains.communication.services.communication_models import CandidateOptOut
        from sqlalchemy import or_
        result = await self.db.execute(
            select(CandidateOptOut).where(
                and_(
                    CandidateOptOut.candidate_id == candidate_id,
                    CandidateOptOut.company_id == company_id,
                    CandidateOptOut.is_active,
                    or_(
                        CandidateOptOut.channel == channel_value,
                        CandidateOptOut.opt_out_type == opt_out_type_all,
                    ),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_optout_for_channel(
        self,
        *,
        candidate_id: str,
        company_id: str,
        channel_value: str,
    ):
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        from app.domains.communication.services.communication_models import CandidateOptOut
        result = await self.db.execute(
            select(CandidateOptOut).where(
                and_(
                    CandidateOptOut.candidate_id == candidate_id,
                    CandidateOptOut.company_id == company_id,
                    CandidateOptOut.channel == channel_value,
                    CandidateOptOut.is_active,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_quarantine(
        self,
        *,
        candidate_id: str,
        company_id: str,
        now,
    ):
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        from app.domains.communication.services.communication_models import CandidateQuarantine
        result = await self.db.execute(
            select(CandidateQuarantine).where(
                and_(
                    CandidateQuarantine.candidate_id == candidate_id,
                    CandidateQuarantine.company_id == company_id,
                    CandidateQuarantine.is_active,
                    CandidateQuarantine.quarantine_end > now,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_quarantine_by_id(self, quarantine_id: str):
        from app.domains.communication.services.communication_models import CandidateQuarantine
        result = await self.db.execute(
            select(CandidateQuarantine).where(CandidateQuarantine.id == quarantine_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_approval_by_id(self, approval_id: str):
        from app.domains.communication.services.communication_models import PendingApproval
        result = await self.db.execute(
            select(PendingApproval).where(PendingApproval.id == approval_id)
        )
        return result.scalar_one_or_none()
