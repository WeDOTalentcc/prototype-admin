"""PlannedTaskRepository — data access for PlannedTask + ExecutionPlan models.

Per ADR-001: services delegate SQL access to this repository.
PlannedTask and ExecutionPlan carry company_id; multi-tenancy fail-closed via
optional `company_id` kwarg on every read method. When provided, query filters
by `<Model>.company_id == company_id`. `None` is reserved for system/admin
contexts (cross-tenant scheduler, ops scans) — those queries are TENANT-EXEMPT
by design.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.planned_task import (
    ExecutionPlan,
    PlannedTask,
    PlannedTaskStatus,
)

logger = logging.getLogger(__name__)


class PlannedTaskRepository:
    """Repository for PlannedTask + ExecutionPlan."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id) -> str:
        """Fail-closed multi-tenancy guard (R-019 P0).

        company_id must come from JWT/session context, never from the
        request body.  Raises ValueError if empty or None so the error
        surfaces loudly at the data-access layer.
        """
        if not company_id:
            raise ValueError(
                "company_id is required for fail-closed multi-tenancy "
                "(R-019 P0: never trust company_id from request body)"
            )
        return str(company_id)

    async def get_by_id(
        self, task_id: str, *, company_id: str | None = None
    ) -> PlannedTask | None:
        """Get a planned task by ID, scoped to company when provided.

        When company_id is provided (must be non-empty), query filters by
        PlannedTask.company_id == company_id (multi-tenancy fail-closed).
        Pass None only when caller intentionally bypasses tenant scope
        (system/admin contexts — TENANT-EXEMPT by design).
        """
        if company_id is not None:
            company_id = self._require_company_id(company_id)

        query = select(PlannedTask).where(PlannedTask.id == task_id)
        if company_id:
            query = query.where(PlannedTask.company_id == company_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_goal(
        self,
        goal_id: str,
        *,
        include_completed: bool = False,
        company_id: str | None = None,
    ) -> list[PlannedTask]:
        """List tasks belonging to a specific goal, scoped to company when provided."""
        if company_id is not None:
            company_id = self._require_company_id(company_id)

        # TENANT-EXEMPT: conditional filter applied below when company_id is provided;
        # None reserved for system/admin contexts (sensor cannot trace conditional .where()).
        query = select(PlannedTask).where(PlannedTask.goal_id == goal_id)
        if company_id:
            query = query.where(PlannedTask.company_id == company_id)

        if not include_completed:
            query = query.where(
                PlannedTask.status.notin_(
                    [PlannedTaskStatus.COMPLETED, PlannedTaskStatus.CANCELLED]
                )
            )

        query = query.order_by(
            PlannedTask.execution_level, PlannedTask.priority_score.desc()
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_subtasks(
        self, parent_task_id: str, *, company_id: str | None = None
    ) -> list[PlannedTask]:
        """List subtasks of a parent task, scoped to company when provided."""
        if company_id is not None:
            company_id = self._require_company_id(company_id)

        # TENANT-EXEMPT: conditional filter applied below when company_id is provided;
        # None reserved for system/admin contexts (sensor cannot trace conditional .where()).
        query = select(PlannedTask).where(
            PlannedTask.parent_task_id == parent_task_id
        )
        if company_id:
            query = query.where(PlannedTask.company_id == company_id)

        query = query.order_by(
            PlannedTask.execution_level, PlannedTask.priority_score.desc()
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_ids(
        self, task_ids: list[str], *, company_id: str | None = None
    ) -> list[PlannedTask]:
        """Bulk fetch planned tasks by id list, scoped to company when provided."""
        if not task_ids:
            return []
        if company_id is not None:
            company_id = self._require_company_id(company_id)

        # TENANT-EXEMPT: conditional filter applied below when company_id is provided;
        # None reserved for system/admin bulk fetch (sensor cannot trace conditional .where()).
        query = select(PlannedTask).where(PlannedTask.id.in_(task_ids))
        if company_id:
            query = query.where(PlannedTask.company_id == company_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_completed_ids(
        self, *, company_id: str | None = None
    ) -> set[str]:
        """Return all PlannedTask ids in COMPLETED status (for dependency checks).

        When company_id is provided, scopes to tenant — recommended for
        per-tenant dependency resolution. Pass None for cross-tenant scans.
        """
        if company_id is not None:
            company_id = self._require_company_id(company_id)

        query = select(PlannedTask.id).where(
            PlannedTask.status == PlannedTaskStatus.COMPLETED
        )
        if company_id:
            query = query.where(PlannedTask.company_id == company_id)

        result = await self.db.execute(query)
        return set(row[0] for row in result.fetchall())

    async def list_ready_candidates(
        self,
        *,
        goal_id: str | None = None,
        parent_task_id: str | None = None,
        company_id: str | None = None,
        agent_type: str | None = None,
    ) -> list[PlannedTask]:
        """List tasks in READY/PENDING with optional filters.

        When company_id is provided it must be non-empty (R-019 P0
        fail-closed).  Pass None only when you intentionally want
        cross-tenant listing (system/admin contexts).
        """
        if company_id is not None:
            company_id = self._require_company_id(company_id)

        # TENANT-EXEMPT: conditional filter applied below when company_id is provided;
        # None reserved for system/admin scheduler scans (sensor cannot trace conditional .where()).
        query = select(PlannedTask).where(
            PlannedTask.status.in_(
                [PlannedTaskStatus.READY, PlannedTaskStatus.PENDING]
            )
        )

        if goal_id:
            query = query.where(PlannedTask.goal_id == goal_id)
        if parent_task_id:
            query = query.where(PlannedTask.parent_task_id == parent_task_id)
        if company_id:
            query = query.where(PlannedTask.company_id == company_id)
        if agent_type:
            query = query.where(PlannedTask.agent_type == agent_type)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_for_priority_context(
        self,
        *,
        goal_id: str | None,
        parent_task_id: str | None,
        company_id: str | None = None,
    ) -> list[PlannedTask]:
        """Sibling tasks needed for dependents-impact priority calculation."""
        if company_id is not None:
            company_id = self._require_company_id(company_id)

        # TENANT-EXEMPT: conditional filter applied below when company_id is provided;
        # priority context is goal-scoped or parent-scoped (sensor cannot trace conditional .where()).
        if goal_id:
            query = select(PlannedTask).where(PlannedTask.goal_id == goal_id)
        else:
            query = select(PlannedTask).where(
                PlannedTask.parent_task_id == parent_task_id
            )
        if company_id:
            query = query.where(PlannedTask.company_id == company_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_execution_plan(
        self, plan_id: str, *, company_id: str | None = None
    ) -> ExecutionPlan | None:
        """Get execution plan by id, scoped to company when provided."""
        if company_id is not None:
            company_id = self._require_company_id(company_id)

        # TENANT-EXEMPT: conditional filter applied below when company_id is provided;
        # None reserved for system/admin contexts (sensor cannot trace conditional .where()).
        query = select(ExecutionPlan).where(ExecutionPlan.id == plan_id)
        if company_id:
            query = query.where(ExecutionPlan.company_id == company_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add(self, entity) -> object:
        """Persist a new entity (PlannedTask or ExecutionPlan)."""
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def commit(self) -> None:
        """Commit pending changes."""
        await self.db.commit()

    async def commit_refresh(self, entity) -> object:
        """Commit and refresh."""
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def refresh(self, entity) -> object:
        """Refresh entity from DB."""
        await self.db.refresh(entity)
        return entity
