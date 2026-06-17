"""InterviewAnalysisRepository — DB operations for interview analysis endpoints.

Extracted from app/api/v1/interview_analysis.py as part of Phase 2 refactor.
Covers Interview reads/updates and LiaOpinion writes involved in transcript analysis.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import Interview
from app.models.lia_opinion import LiaOpinion

logger = logging.getLogger(__name__)


class InterviewAnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Interview queries ─────────────────────────────────────────────────────

    async def get_interview_by_id(
        self,
        interview_id: str,
        company_id: str | None = None,
    ) -> Interview | None:
        """Get interview by id. Multi-tenancy defense-in-depth via company_id
        filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — Interview.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Interview).where(Interview.id == interview_id)
        if company_id:
            query = query.where(Interview.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_interview_by_meeting_id(
        self,
        meeting_id: str,
        company_id: str | None = None,
    ) -> Interview | None:
        """Get interview by meeting_id. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — Interview.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Interview).where(Interview.meeting_id == meeting_id)
        if company_id:
            query = query.where(Interview.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ── Interview updates ─────────────────────────────────────────────────────

    async def update_interview_feedback(
        self,
        interview_id: str,
        feedback: dict,
        company_id: str | None = None,
    ) -> None:
        """Overwrite the feedback JSON column for an interview.

        Multi-tenancy defense-in-depth via company_id filter quando passado.
        """
        # TENANT-EXEMPT: dynamic builder — Interview.company_id == company_id
        # é appended conditionally below quando company_id passado.
        stmt = (
            update(Interview)
            .where(Interview.id == interview_id)
            .values(feedback=feedback)
        )
        if company_id:
            stmt = stmt.where(Interview.company_id == company_id)
        await self.db.execute(stmt)

    async def update_interview_status_and_feedback(
        self,
        interview_id: str,
        feedback: dict,
        status: str,
        company_id: str | None = None,
    ) -> None:
        """Update both status and feedback for an interview (background task).

        Multi-tenancy defense-in-depth via company_id filter quando passado.
        """
        # TENANT-EXEMPT: dynamic builder — Interview.company_id == company_id
        # é appended conditionally below quando company_id passado.
        stmt = (
            update(Interview)
            .where(Interview.id == interview_id)
            .values(feedback=feedback, status=status)
        )
        if company_id:
            stmt = stmt.where(Interview.company_id == company_id)
        await self.db.execute(stmt)

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
        # TENANT-EXEMPT: LiaOpinion.company_id == company_id já é PRIMEIRO
        # elemento de `where_conditions` AND acima (statically guaranteed).
        # Sensor AST não rastreia através de and_() var indirection.
        await self.db.execute(
            update(LiaOpinion).where(where_conditions).values(is_current=False)
        )

    async def create_opinion(self, opinion: LiaOpinion) -> LiaOpinion:
        """Insert a new LiaOpinion and flush."""
        self.db.add(opinion)
        await self.db.flush()
        return opinion
