"""EvaluationCriteriaRepository — data access for EvaluationCriteria model.

ADR-001-EXEMPT: EvaluationCriteria is a GLOBAL catalog model (no company_id).
The catalog is shared across all tenants — it stores the seed methodology
(skills, behavioral competencies, responsibilities) used as a reference
for Andrés evaluation methodology.

Sprint 5.4 (2026-05-07): created during sourcing/services ADR-001 cleanup.
"""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.evaluation_criteria import EvaluationCriteria


class EvaluationCriteriaRepository:
    """Repository for EvaluationCriteria — global catalog (no tenant scoping)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_all(self) -> int:
        """Return total number of rows in the catalog (used by seed_from_catalogs)."""
        result = await self.db.scalar(
            select(func.count()).select_from(EvaluationCriteria)
        )
        return result or 0

    async def list_active(self) -> list[EvaluationCriteria]:
        """List all active criteria (used for fuzzy requirements matching)."""
        result = await self.db.execute(
            select(EvaluationCriteria).where(EvaluationCriteria.is_active)
        )
        return list(result.scalars().all())

    async def list_active_filtered(
        self,
        *,
        category: str | None = None,
    ) -> list[EvaluationCriteria]:
        """List active criteria optionally filtered by category, ordered by effectiveness desc."""
        query = select(EvaluationCriteria).where(EvaluationCriteria.is_active)
        if category:
            query = query.where(EvaluationCriteria.category == category)
        query = query.order_by(EvaluationCriteria.effectiveness_score.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, criteria_id: UUID) -> EvaluationCriteria | None:
        """Get a single criteria row by id."""
        result = await self.db.execute(
            select(EvaluationCriteria).where(EvaluationCriteria.id == criteria_id)
        )
        return result.scalar_one_or_none()
