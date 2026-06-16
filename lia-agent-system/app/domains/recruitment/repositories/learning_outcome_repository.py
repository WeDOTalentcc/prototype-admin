"""
LearningOutcome Repository — data access layer for job outcomes and feedback learning.
Extracted from app/api/v1/learning_outcomes.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback_learning import JobOutcome

logger = logging.getLogger(__name__)


class LearningOutcomeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        outcome_type=None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[JobOutcome], int]:
        q = select(JobOutcome).where(JobOutcome.company_id == company_id)
        if outcome_type is not None:
            q = q.where(JobOutcome.outcome_type == outcome_type)
        q = q.order_by(JobOutcome.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(q)
        items = list(result.scalars().all())

        cq = select(func.count(JobOutcome.id)).where(JobOutcome.company_id == company_id)
        total = (await self.db.execute(cq)).scalar() or 0
        return items, total

    async def get_by_id(self, outcome_id: UUID) -> JobOutcome | None:
        result = await self.db.execute(
            select(JobOutcome).where(JobOutcome.id == outcome_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> JobOutcome:
        o = JobOutcome(**data)
        self.db.add(o)
        await self.db.flush()
        await self.db.refresh(o)
        return o

    async def update(self, outcome: JobOutcome, data: dict) -> JobOutcome:
        for key, value in data.items():
            setattr(outcome, key, value)
        await self.db.flush()
        await self.db.refresh(outcome)
        return outcome

    async def delete(self, outcome: JobOutcome) -> None:
        await self.db.delete(outcome)
        await self.db.flush()

    async def list_paginated(
        self,
        company_id: str,
        *,
        outcome_type=None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobOutcome]:
        q = select(JobOutcome).where(JobOutcome.company_id == company_id)
        if outcome_type is not None:
            q = q.where(JobOutcome.outcome == outcome_type)
        q = q.order_by(JobOutcome.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_stats(self, company_id: str) -> dict:
        from sqlalchemy import and_, case, func
        from app.models.feedback_learning import JobOutcomeType

        base_filter = JobOutcome.company_id == company_id

        total = (
            await self.db.execute(
                select(func.count()).select_from(JobOutcome).where(base_filter)
            )
        ).scalar() or 0

        filled = (
            await self.db.execute(
                select(func.count()).select_from(JobOutcome).where(
                    and_(base_filter, JobOutcome.outcome == JobOutcomeType.FILLED)
                )
            )
        ).scalar() or 0

        cancelled = (
            await self.db.execute(
                select(func.count()).select_from(JobOutcome).where(
                    and_(base_filter, JobOutcome.outcome == JobOutcomeType.CANCELLED)
                )
            )
        ).scalar() or 0

        expired = (
            await self.db.execute(
                select(func.count()).select_from(JobOutcome).where(
                    and_(base_filter, JobOutcome.outcome == JobOutcomeType.EXPIRED)
                )
            )
        ).scalar() or 0

        avg_row = (
            await self.db.execute(
                select(
                    func.avg(JobOutcome.time_to_fill_days),
                    func.avg(JobOutcome.candidate_count_total),
                    func.avg(JobOutcome.candidate_count_screened),
                    func.avg(JobOutcome.candidate_count_interviewed),
                ).where(base_filter)
            )
        ).one_or_none()

        return {
            "total": total,
            "filled": filled,
            "cancelled": cancelled,
            "expired": expired,
            "avg_row": avg_row,
        }

    async def get_patterns(self, company_id: str, group_by: str, limit: int = 20) -> list:
        from sqlalchemy import and_, case, func
        from app.models.feedback_learning import JobOutcomeType

        group_col = getattr(JobOutcome, group_by)
        base_filter = and_(
            JobOutcome.company_id == company_id,
            group_col.isnot(None),
        )

        query = (
            select(
                group_col,
                func.count().label("sample_size"),
                func.avg(JobOutcome.time_to_fill_days).label("avg_ttf"),
                func.avg(JobOutcome.candidate_count_total).label("avg_candidates"),
                func.sum(
                    case((JobOutcome.outcome == JobOutcomeType.FILLED, 1), else_=0)
                ).label("filled"),
            )
            .where(base_filter)
            .group_by(group_col)
            .having(func.count() >= 1)
            .order_by(func.count().desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.all()
