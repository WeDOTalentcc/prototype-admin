"""
SharedSearchRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/shared_searches.py.
"""
import logging
import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate, VacancyCandidate
from app.models.email_template import EmailTemplate
from app.models.shared_search import (
    FeedbackDecision,
    SharedSearch,
    SharedSearchAccess,
    SharedSearchFeedback,
    SharedSearchStatus,
    ShareType,
)

logger = logging.getLogger(__name__)


class SharedSearchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── SharedSearch CRUD ───────────────────────────────────────────────────

    async def get_by_id_and_company(
        self, search_id: UUID, company_uuid: UUID
    ) -> SharedSearch | None:
        result = await self.db.execute(
            select(SharedSearch).where(
                and_(
                    SharedSearch.id == search_id,
                    SharedSearch.company_id == company_uuid,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_shared_searches(
        self,
        company_uuid: UUID,
        status: str | None = None,
        share_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[SharedSearch]]:
        query = select(SharedSearch).where(SharedSearch.company_id == company_uuid)

        if status:
            query = query.where(SharedSearch.status == SharedSearchStatus(status))

        if share_type:
            query = query.where(SharedSearch.share_type == ShareType(share_type))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset(offset).limit(limit).order_by(SharedSearch.created_at.desc())
        result = await self.db.execute(query)
        searches = result.scalars().all()

        return total, list(searches)

    async def create_shared_search(self, shared_search: SharedSearch) -> SharedSearch:
        self.db.add(shared_search)
        await self.db.flush()
        return shared_search

    async def update_shared_search(
        self,
        search: SharedSearch,
        status: str | None = None,
        expires_at: datetime | None = None,
        description: str | None = None,
    ) -> SharedSearch:
        if status is not None:
            if status == "revoked":
                search.status = SharedSearchStatus.revoked
            elif status == "active":
                search.status = SharedSearchStatus.active
            elif status == "expired":
                search.status = SharedSearchStatus.expired

        if expires_at is not None:
            search.expires_at = expires_at

        if description is not None:
            search.description = description

        search.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(search)
        return search

    async def revoke_shared_search(self, search: SharedSearch) -> None:
        search.status = SharedSearchStatus.revoked
        search.updated_at = datetime.utcnow()
        await self.db.commit()

    # ── SharedSearchAccess ──────────────────────────────────────────────────

    async def create_access_record(self, access_record: SharedSearchAccess) -> None:
        self.db.add(access_record)

    async def get_access_by_search(self, search_id: UUID) -> list[SharedSearchAccess]:
        result = await self.db.execute(
            select(SharedSearchAccess).where(
                SharedSearchAccess.shared_search_id == search_id
            )
        )
        return list(result.scalars().all())

    async def get_access_by_email(
        self, search_id: UUID, email: str
    ) -> SharedSearchAccess | None:
        result = await self.db.execute(
            select(SharedSearchAccess).where(
                and_(
                    SharedSearchAccess.shared_search_id == search_id,
                    SharedSearchAccess.email == email,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_access_otp(
        self,
        access_record: SharedSearchAccess,
        otp_hash: str,
        otp_expires_at: datetime,
    ) -> None:
        access_record.otp_hash = otp_hash
        access_record.otp_expires_at = otp_expires_at
        await self.db.commit()

    # ── SharedSearchFeedback ────────────────────────────────────────────────

    async def get_feedbacks_by_search(
        self, search_id: UUID
    ) -> list[SharedSearchFeedback]:
        result = await self.db.execute(
            select(SharedSearchFeedback).where(
                SharedSearchFeedback.shared_search_id == search_id
            )
        )
        return list(result.scalars().all())

    async def get_approved_feedbacks(
        self, search_id: UUID
    ) -> list[SharedSearchFeedback]:
        result = await self.db.execute(
            select(SharedSearchFeedback).where(
                and_(
                    SharedSearchFeedback.shared_search_id == search_id,
                    SharedSearchFeedback.decision == FeedbackDecision.approved,
                )
            )
        )
        return list(result.scalars().all())

    # ── Candidate snapshot ──────────────────────────────────────────────────

    async def get_candidates_by_ids(
        self, candidate_ids: list[UUID]
    ) -> list[Candidate]:
        if not candidate_ids:
            return []
        result = await self.db.execute(
            select(Candidate).where(Candidate.id.in_(candidate_ids))
        )
        return list(result.scalars().all())

    # ── VacancyCandidate ────────────────────────────────────────────────────

    async def get_vacancy_candidate(
        self, job_vacancy_id: UUID, candidate_id: UUID
    ) -> VacancyCandidate | None:
        result = await self.db.execute(
            select(VacancyCandidate).where(
                and_(
                    VacancyCandidate.vacancy_id == job_vacancy_id,
                    VacancyCandidate.candidate_id == candidate_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_vacancy_candidate(
        self, vacancy_candidate: VacancyCandidate
    ) -> None:
        self.db.add(vacancy_candidate)

    # ── EmailTemplate ───────────────────────────────────────────────────────

    async def get_share_template(
        self, channel: str, company_id: str | None = None
    ) -> EmailTemplate | None:
        try:
            if company_id:
                result = await self.db.execute(
                    select(EmailTemplate).where(
                        EmailTemplate.situation == "share_with_manager",
                        EmailTemplate.channel == channel,
                        EmailTemplate.is_active,
                        EmailTemplate.company_id == company_id,
                    )
                )
                template = result.scalar_one_or_none()
                if template:
                    return template

            result = await self.db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.situation == "share_with_manager",
                    EmailTemplate.channel == channel,
                    EmailTemplate.is_active,
                    EmailTemplate.is_system_template,
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Error fetching share template for channel={channel}: {e}")
            return None

    # ── CompanyProfile fallback ─────────────────────────────────────────────

    async def get_default_company_id(self) -> UUID | None:
        from app.models.company import CompanyProfile

        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.is_default).limit(1)
        )
        default_company = result.scalar_one_or_none()
        return default_company.id if default_company else None


    # ── SharedSearchAccess by token ─────────────────────────────────────────

    async def get_access_by_token(self, access_token: str) -> SharedSearchAccess | None:
        result = await self.db.execute(
            select(SharedSearchAccess).where(
                SharedSearchAccess.access_token == access_token
            )
        )
        return result.scalar_one_or_none()

    async def get_shared_search_by_id(self, search_id) -> SharedSearch | None:
        result = await self.db.execute(
            select(SharedSearch).where(SharedSearch.id == search_id)
        )
        return result.scalar_one_or_none()

    async def get_feedback_by_candidate_and_reviewer(
        self,
        search_id: UUID,
        candidate_id: UUID,
        reviewer_email: str,
    ) -> SharedSearchFeedback | None:
        result = await self.db.execute(
            select(SharedSearchFeedback).where(
                and_(
                    SharedSearchFeedback.shared_search_id == search_id,
                    SharedSearchFeedback.candidate_id == candidate_id,
                    SharedSearchFeedback.reviewer_email == reviewer_email,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_feedbacks_by_reviewer(
        self,
        search_id: UUID,
        reviewer_email: str,
    ) -> list[SharedSearchFeedback]:
        result = await self.db.execute(
            select(SharedSearchFeedback).where(
                and_(
                    SharedSearchFeedback.shared_search_id == search_id,
                    SharedSearchFeedback.reviewer_email == reviewer_email,
                )
            ).order_by(SharedSearchFeedback.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_feedbacks_by_search_and_reviewer(
        self,
        search_id: UUID,
        reviewer_email: str,
    ) -> list[SharedSearchFeedback]:
        return await self.get_feedbacks_by_reviewer(search_id, reviewer_email)

    async def create_feedback(self, feedback: SharedSearchFeedback) -> SharedSearchFeedback:
        self.db.add(feedback)
        await self.db.flush()
        await self.db.refresh(feedback)
        return feedback

    async def mark_access_otp_used(self, access: SharedSearchAccess) -> None:
        access.otp_hash = None
        access.otp_expires_at = None

    async def record_access_view(self, access: SharedSearchAccess) -> None:
        from datetime import datetime as _dt
        now = _dt.utcnow()
        if not access.first_accessed_at:
            access.first_accessed_at = now
        access.last_accessed_at = now
        access.total_views = (access.total_views or 0) + 1

    # ── commit / rollback helpers ───────────────────────────────────────────

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    async def refresh(self, obj: object) -> None:
        await self.db.refresh(obj)
