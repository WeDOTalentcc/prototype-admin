"""
SearchFeedback Repository — data access layer for search feedback.
Extracted from app/api/v1/search_feedback.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.search_feedback import SearchFeedback

logger = logging.getLogger(__name__)


class SearchFeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        search_type: str | None = None,
        rating: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SearchFeedback], int]:
        q = select(SearchFeedback).where(SearchFeedback.company_id == company_id)
        if search_type:
            q = q.where(SearchFeedback.search_type == search_type)
        if rating is not None:
            q = q.where(SearchFeedback.rating == rating)
        q = q.order_by(SearchFeedback.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(q)
        items = list(result.scalars().all())

        cq = select(func.count(SearchFeedback.id)).where(SearchFeedback.company_id == company_id)
        total = (await self.db.execute(cq)).scalar() or 0
        return items, total

    async def get_by_id(self, feedback_id: UUID) -> SearchFeedback | None:
        result = await self.db.execute(
            select(SearchFeedback).where(SearchFeedback.id == feedback_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> SearchFeedback:
        fb = SearchFeedback(**data)
        self.db.add(fb)
        await self.db.flush()
        await self.db.refresh(fb)
        return fb

    async def update(self, feedback: SearchFeedback, data: dict) -> SearchFeedback:
        for key, value in data.items():
            setattr(feedback, key, value)
        await self.db.flush()
        await self.db.refresh(feedback)
        return feedback

    async def delete(self, feedback: SearchFeedback) -> None:
        await self.db.delete(feedback)
        await self.db.flush()

    async def get_stats(self, company_id: str) -> dict:
        from sqlalchemy import func as f
        total_q = select(f.count(SearchFeedback.id)).where(SearchFeedback.company_id == company_id)
        total = (await self.db.execute(total_q)).scalar() or 0
        avg_q = select(f.avg(SearchFeedback.rating)).where(SearchFeedback.company_id == company_id)
        avg = (await self.db.execute(avg_q)).scalar()
        return {"total": total, "avg_rating": float(avg) if avg else None}

    async def get_by_user_and_candidate(
        self,
        user_id: str,
        candidate_id: str,
        job_id: str | None,
    ) -> SearchFeedback | None:
        from sqlalchemy import and_
        job_filter = (
            SearchFeedback.job_id == job_id if job_id else SearchFeedback.job_id.is_(None)
        )
        result = await self.db.execute(
            select(SearchFeedback).where(
                and_(
                    SearchFeedback.user_id == user_id,
                    SearchFeedback.candidate_id == candidate_id,
                    job_filter,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self,
        feedback_id: str,
        user_id: str,
    ) -> SearchFeedback | None:
        from sqlalchemy import and_
        result = await self.db.execute(
            select(SearchFeedback).where(
                and_(SearchFeedback.id == feedback_id, SearchFeedback.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: str,
        job_id: str | None = None,
    ) -> list[SearchFeedback]:
        q = select(SearchFeedback).where(SearchFeedback.user_id == user_id)
        if job_id:
            q = q.where(SearchFeedback.job_id == job_id)
        q = q.order_by(SearchFeedback.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def list_for_job(self, job_id: str) -> list[SearchFeedback]:
        result = await self.db.execute(
            select(SearchFeedback)
            .where(SearchFeedback.job_id == job_id)
            .order_by(SearchFeedback.created_at.desc())
        )
        return list(result.scalars().all())
