"""
CandidateFeedbackRepository — session-in-constructor pattern.
Encapsulates DB operations for the CandidateFeedback model.
ADR-001: keeps CandidateFeedbackService free of inline SQL.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate_feedback import CandidateFeedback

logger = logging.getLogger(__name__)


class CandidateFeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, feedback_id: str) -> CandidateFeedback | None:
        """Return a single CandidateFeedback by primary key, or None."""
        result = await self.db.execute(
            select(CandidateFeedback).where(CandidateFeedback.id == feedback_id)
        )
        return result.scalar_one_or_none()

    async def list_recent(
        self,
        days: int = 30,
        vacancy_id: str | None = None,
    ) -> list[CandidateFeedback]:
        """Return CandidateFeedbacks created within the last ``days``,
        optionally scoped to a single vacancy.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        conditions = [CandidateFeedback.created_at >= cutoff_date]
        if vacancy_id:
            conditions.append(CandidateFeedback.vacancy_id == vacancy_id)

        result = await self.db.execute(
            select(CandidateFeedback).where(and_(*conditions))
        )
        return list(result.scalars().all())
