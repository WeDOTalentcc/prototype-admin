"""TaskRepository — data access for Task model (automation domain).

ADR-001-EXEMPT: Task model has no company_id column (legacy non-tenant model).
All queries are tenant-broad by design; multi-tenancy is enforced at the
service layer via assigned_to_user_id / related_job_id filtering when
required by callers.

TENANT-EXEMPT applied per-query below: every `select(Task)` in this file is
explicitly tenant-broad because the model lacks a company_id column. The
sensor `scripts/check_query_has_tenant_filter.py` honors these inline markers.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.task import Task, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class TaskRepository:
    """Repository for Task entity. Encapsulates all SQL access for tasks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        # TENANT-EXEMPT: Task model has no company_id column (ADR-001-EXEMPT module-level)
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def list_pending(
        self,
        *,
        user_id: str | None = None,
        agent_type: str | None = None,
        priority: TaskPriority | None = None,
        limit: int = 50,
    ) -> list[Task]:
        """List pending/in-progress tasks with optional filters."""
        # TENANT-EXEMPT: Task model has no company_id column (ADR-001-EXEMPT module-level);
        # tenant scope established via user_id at service layer when required.
        query = select(Task).where(
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        )
        if user_id:
            query = query.where(Task.assigned_to_user_id == user_id)
        if agent_type:
            query = query.where(Task.assigned_to_agent == agent_type)
        if priority:
            query = query.where(Task.priority == priority)

        query = query.order_by(
            Task.priority.desc(),
            Task.due_date.asc().nullslast(),
            Task.created_at.desc(),
        ).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_overdue(self, *, user_id: str | None = None) -> list[Task]:
        """List overdue tasks (status pending/in-progress with due_date in past)."""
        # TENANT-EXEMPT: Task model has no company_id column (ADR-001-EXEMPT module-level)
        query = select(Task).where(
            and_(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.due_date < datetime.utcnow(),
            )
        )
        if user_id:
            query = query.where(Task.assigned_to_user_id == user_id)
        query = query.order_by(Task.due_date.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_due_today(self, *, user_id: str | None = None) -> list[Task]:
        """List tasks due today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # TENANT-EXEMPT: Task model has no company_id column (ADR-001-EXEMPT module-level)
        query = select(Task).where(
            and_(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.due_date >= today_start,
                Task.due_date < today_end,
            )
        )
        if user_id:
            query = query.where(Task.assigned_to_user_id == user_id)
        query = query.order_by(Task.due_date.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_summary_counts(
        self, *, user_id: str | None = None
    ) -> dict[str, int]:
        """Aggregate counts for dashboard summary."""
        base_query = select(func.count(Task.id))
        if user_id:
            base_query = base_query.where(Task.assigned_to_user_id == user_id)

        pending_query = base_query.where(Task.status == TaskStatus.PENDING)
        in_progress_query = base_query.where(Task.status == TaskStatus.IN_PROGRESS)
        completed_query = base_query.where(Task.status == TaskStatus.COMPLETED)
        overdue_query = base_query.where(
            and_(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.due_date < datetime.utcnow(),
            )
        )
        critical_query = base_query.where(
            and_(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.priority == TaskPriority.CRITICAL,
            )
        )

        return {
            "pending": (await self.db.execute(pending_query)).scalar() or 0,
            "in_progress": (await self.db.execute(in_progress_query)).scalar() or 0,
            "completed": (await self.db.execute(completed_query)).scalar() or 0,
            "overdue": (await self.db.execute(overdue_query)).scalar() or 0,
            "critical": (await self.db.execute(critical_query)).scalar() or 0,
        }

    async def list_needing_reminder(
        self, *, hours_before_due: int = 24
    ) -> list[Task]:
        """List tasks due within the reminder window where reminder not yet sent."""
        now = datetime.utcnow()
        reminder_threshold = now + timedelta(hours=hours_before_due)

        # TENANT-EXEMPT: Task model has no company_id column (ADR-001-EXEMPT module-level);
        # cron scanner runs cross-tenant by design — tenant scope reapplied at dispatch.
        query = (
            select(Task)
            .where(
                and_(
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                    Task.due_date.isnot(None),
                    Task.due_date <= reminder_threshold,
                    Task.due_date > now,
                    or_(not Task.reminder_sent, Task.reminder_sent.is_(None)),
                )
            )
            .order_by(Task.due_date.asc())
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_escalatable(
        self, *, overdue_hours: int = 48
    ) -> list[Task]:
        """List HIGH/CRITICAL tasks overdue beyond threshold and below max escalation."""
        escalation_threshold = datetime.utcnow() - timedelta(hours=overdue_hours)

        # TENANT-EXEMPT: Task model has no company_id column (ADR-001-EXEMPT module-level);
        # cron scanner runs cross-tenant by design — tenant scope reapplied at escalation dispatch.
        query = (
            select(Task)
            .where(
                and_(
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                    Task.due_date.isnot(None),
                    Task.due_date < escalation_threshold,
                    Task.priority.in_([TaskPriority.HIGH, TaskPriority.CRITICAL]),
                    Task.escalation_level < 3,
                )
            )
            .order_by(Task.priority.desc(), Task.due_date.asc())
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_pending_confirmation(
        self,
        *,
        user_id: str | None = None,
        limit: int = 50,
    ) -> list[Task]:
        """List tasks awaiting confirmation."""
        # TENANT-EXEMPT: Task model has no company_id column (ADR-001-EXEMPT module-level)
        query = select(Task).where(
            and_(
                Task.status == TaskStatus.PENDING,
                Task.requires_confirmation,
                Task.confirmed_at.is_(None),
                Task.rejected_at.is_(None),
            )
        )
        if user_id:
            query = query.where(Task.assigned_to_user_id == user_id)
        query = query.order_by(
            Task.priority.desc(),
            Task.due_date.asc().nullslast(),
            Task.created_at.desc(),
        ).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add(self, task: Task) -> Task:
        """Persist a new task."""
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def commit_refresh(self, task: Task) -> Task:
        """Commit pending changes on attached task."""
        await self.db.commit()
        await self.db.refresh(task)
        return task
