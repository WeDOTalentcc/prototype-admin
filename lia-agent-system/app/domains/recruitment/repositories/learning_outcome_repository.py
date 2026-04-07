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
