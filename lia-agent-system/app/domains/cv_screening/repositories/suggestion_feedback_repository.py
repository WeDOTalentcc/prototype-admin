"""SuggestionFeedbackRepository — DB access layer for LIA suggestion feedback.

Extracted from app/api/v1/suggestion_feedback.py as part of Phase 2 refactor.
Tables covered:
  - suggestion_feedbacks
"""
import logging

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback_learning import SuggestionFeedback

logger = logging.getLogger(__name__)


class SuggestionFeedbackRepository:
    """Repository for suggestion feedback recording and stats queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record(
        self,
        company_id: str,
        field_name: str,
        suggested_value,
        actual_value,
        accepted: bool,
        context: dict | None,
        created_by: str | None,
    ) -> SuggestionFeedback:
        """Persist a single suggestion feedback record."""
        feedback = SuggestionFeedback(
            company_id=company_id,
            field_name=field_name,
            suggested_value=suggested_value,
            actual_value=actual_value,
            accepted=1 if accepted else 0,
            context=context,
            created_by=created_by,
        )
        self.db.add(feedback)
        await self.db.flush()
        return feedback

    async def get_total_and_accepted(self, company_id: str) -> tuple[int, int]:
        """Return (total_feedback, accepted_count) for a company."""
        base_filter = SuggestionFeedback.company_id == company_id

        total_q = await self.db.execute(
            select(func.count()).select_from(SuggestionFeedback).where(base_filter)
        )
        total = total_q.scalar() or 0

        accepted_q = await self.db.execute(
            select(func.count()).select_from(SuggestionFeedback).where(
                and_(base_filter, SuggestionFeedback.accepted == 1)
            )
        )
        accepted_total = accepted_q.scalar() or 0
        return total, accepted_total

    async def get_stats_by_field(self, company_id: str) -> list:
        """Return (field_name, total, accepted) rows grouped by field."""
        base_filter = SuggestionFeedback.company_id == company_id

        field_query = (
            select(
                SuggestionFeedback.field_name,
                func.count().label("total"),
                func.sum(case((SuggestionFeedback.accepted == 1, 1), else_=0)).label("accepted"),
            )
            .where(base_filter)
            .group_by(SuggestionFeedback.field_name)
            .order_by(func.count().desc())
        )
        result = await self.db.execute(field_query)
        return result.all()
