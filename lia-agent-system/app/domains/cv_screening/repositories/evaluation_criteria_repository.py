"""EvaluationCriteriaRepository — DB access for EvaluationCriteria.

Extracted from app/domains/cv_screening/services/evaluation_criteria_service.py per ADR-001.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.evaluation_criteria import EvaluationCriteria


class EvaluationCriteriaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_all(self) -> int:
        result = await self.db.scalar(
            select(func.count()).select_from(EvaluationCriteria)
        )
        return int(result or 0)

    async def list_active(self) -> list[EvaluationCriteria]:
        result = await self.db.execute(
            select(EvaluationCriteria).where(EvaluationCriteria.is_active)
        )
        return list(result.scalars().all())

    async def list_active_by_category(
        self,
        *,
        category: str | None = None,
    ) -> list[EvaluationCriteria]:
        query = select(EvaluationCriteria).where(EvaluationCriteria.is_active)
        if category:
            query = query.where(EvaluationCriteria.category == category)
        query = query.order_by(EvaluationCriteria.effectiveness_score.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, criteria_id: UUID) -> EvaluationCriteria | None:
        result = await self.db.execute(
            select(EvaluationCriteria).where(EvaluationCriteria.id == criteria_id)
        )
        return result.scalar_one_or_none()

    def add(self, criteria: EvaluationCriteria) -> None:
        self.db.add(criteria)

    async def flush(self) -> None:
        await self.db.flush()
