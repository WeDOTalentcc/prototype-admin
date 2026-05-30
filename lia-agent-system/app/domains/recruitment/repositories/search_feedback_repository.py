"""
SearchFeedback Repository — data access layer for search feedback.
Extracted from app/api/v1/search_feedback.py as part of Phase 2 refactor.
"""
import logging

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_feedback import SearchFeedback

logger = logging.getLogger(__name__)


class SearchFeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def get_by_user_and_candidate(
        self,
        user_id: str,
        candidate_id: str,
        job_id: str | None,
    ) -> SearchFeedback | None:
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

    async def list_for_user_and_fingerprint(
        self,
        user_id: str,
        search_fingerprint: str,
    ) -> list[SearchFeedback]:
        """Feedback do recrutador para os criterios de UMA busca (fingerprint).

        Re-hidratacao (Fase 2). RLS isola por company automaticamente.
        """
        result = await self.db.execute(
            select(SearchFeedback)
            .where(
                and_(
                    SearchFeedback.user_id == user_id,
                    SearchFeedback.search_fingerprint == search_fingerprint,
                )
            )
            .order_by(SearchFeedback.created_at.desc())
        )
        return list(result.scalars().all())
