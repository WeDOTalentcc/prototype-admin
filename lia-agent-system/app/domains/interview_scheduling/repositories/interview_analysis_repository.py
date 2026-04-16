"""InterviewAnalysisRepository — DB operations for interview analysis endpoints.

Extracted from app/api/v1/interview_analysis.py as part of Phase 2 refactor.
Covers Interview reads/updates and LiaOpinion writes involved in transcript analysis.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.interview import Interview
from lia_models.lia_opinion import LiaOpinion

logger = logging.getLogger(__name__)


class InterviewAnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Interview queries ─────────────────────────────────────────────────────

    async def get_interview_by_id(self, interview_id: str) -> Interview | None:
        result = await self.db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        return result.scalar_one_or_none()

    async def get_interview_by_meeting_id(self, meeting_id: str) -> Interview | None:
        result = await self.db.execute(
            select(Interview).where(Interview.meeting_id == meeting_id)
        )
        return result.scalar_one_or_none()

    # ── Interview updates ─────────────────────────────────────────────────────

    async def update_interview_feedback(
        self,
        interview_id: str,
        feedback: dict,
    ) -> None:
        """Overwrite the feedback JSON column for an interview."""
        await self.db.execute(
            update(Interview)
            .where(Interview.id == interview_id)
            .values(feedback=feedback)
        )

    async def update_interview_status_and_feedback(
        self,
        interview_id: str,
        feedback: dict,
        status: str,
    ) -> None:
        """Update both status and feedback for an interview (used by background task)."""
        await self.db.execute(
            update(Interview)
            .where(Interview.id == interview_id)
            .values(feedback=feedback, status=status)
        )

    # ── LiaOpinion writes ─────────────────────────────────────────────────────

    async def deactivate_current_opinions(
        self,
        candidate_id: UUID,
        opinion_type: str,
        company_id: str,
        job_vacancy_id: UUID | None = None,
    ) -> None:
        """Mark all current opinions for a candidate/type as not current."""
        where_conditions = and_(
            LiaOpinion.candidate_id == candidate_id,
            LiaOpinion.opinion_type == opinion_type,
            LiaOpinion.company_id == company_id,
            LiaOpinion.is_current,
        )
        if job_vacancy_id:
            where_conditions = and_(
                where_conditions,
                LiaOpinion.job_vacancy_id == job_vacancy_id,
            )
        await self.db.execute(
            update(LiaOpinion).where(where_conditions).values(is_current=False)
        )

    async def create_opinion(self, opinion: LiaOpinion) -> LiaOpinion:
        """Insert a new LiaOpinion and flush."""
        self.db.add(opinion)
        await self.db.flush()
        return opinion
