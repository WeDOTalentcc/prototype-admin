"""
Tasks Repository - Database access layer for task management.
"""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus, TaskType


class TasksRepository:
    """Repository for task database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        *,
        company_id: str,  # WT-2022 P0.TASK fix: required tenant scoping
        title: str,
        description: str | None = None,
        task_type: TaskType = TaskType.GENERAL,
        priority: TaskPriority = TaskPriority.MEDIUM,
        created_by_agent: str | None = None,
        assigned_to_agent: str | None = None,
        assigned_to_user_id: str | None = None,
        related_job_id: str | None = None,
        related_candidate_id: str | None = None,
        due_date: datetime | None = None,
        context: dict[str, Any] | None = None,
        is_automated: bool = False,
        requires_confirmation: bool = False
    ) -> Task:
        """Create and persist a new task."""
        if not company_id:
            raise ValueError("company_id required for tenant scoping (WT-2022 P0.TASK)")
        task = Task(
            company_id=company_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            created_by_agent=created_by_agent,
            assigned_to_agent=assigned_to_agent,
            assigned_to_user_id=assigned_to_user_id,
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            due_date=due_date,
            context=context or {},
            is_automated=is_automated,
            requires_confirmation=requires_confirmation
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_active_task_for_job_and_type(
        self,
        *,
        company_id: str,  # WT-2022 P0.TASK fix: required tenant scoping
        job_id: str,
        task_type: TaskType,
    ) -> Task | None:
        """Return an active (PENDING/IN_PROGRESS) task for a job by type.

        Used by app/domains/sourcing/services/sourcing_pipeline_service.py
        (Sprint Q2 ADR-001 cross-domain cleanup) to dedupe sourcing tasks.
        """
        if not company_id:
            raise ValueError("company_id required for tenant scoping (WT-2022 P0.TASK)")
        result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.company_id == company_id,
                    Task.related_job_id == job_id,
                    Task.task_type == task_type,
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_task(self, task_id: str, *, company_id: str) -> Task | None:
        """Get a task by ID, scoped to company_id (WT-2022 P0.TASK fix)."""
        if not company_id:
            raise ValueError("company_id required for tenant scoping (WT-2022 P0.TASK)")
        result = await self.db.execute(
            select(Task).where(
                and_(Task.id == task_id, Task.company_id == company_id)
            )
        )
        return result.scalar_one_or_none()

    async def flush_and_refresh(self, task: Task) -> Task:
        """Flush pending changes and refresh the task instance."""
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def commit_and_refresh(self, task: Task) -> Task:
        """Commit and refresh the task instance."""
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_pending_tasks(
        self,
        *,
        company_id: str,  # WT-2022 P0.TASK fix: required tenant scoping
        user_id: str | None = None,
        agent_type: str | None = None,
        priority: TaskPriority | None = None,
        limit: int = 50
    ) -> list[Task]:
        """Get pending/in-progress tasks with optional filters."""
        if not company_id:
            raise ValueError("company_id required for tenant scoping (WT-2022 P0.TASK)")
        query = select(Task).where(
            and_(
                Task.company_id == company_id,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            )
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
            Task.created_at.desc()
        ).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_overdue_tasks(
        self, *, company_id: str, user_id: str | None = None
    ) -> list[Task]:
        """Get all overdue tasks (WT-2022 P0.TASK fix: tenant-scoped)."""
        if not company_id:
            raise ValueError("company_id required for tenant scoping (WT-2022 P0.TASK)")
        query = select(Task).where(
            and_(
                Task.company_id == company_id,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.due_date < datetime.utcnow()
            )
        )
        if user_id:
            query = query.where(Task.assigned_to_user_id == user_id)
        query = query.order_by(Task.due_date.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_tasks_due_today(
        self, *, company_id: str, user_id: str | None = None
    ) -> list[Task]:
        """Get tasks due today (WT-2022 P0.TASK fix: tenant-scoped)."""
        if not company_id:
            raise ValueError("company_id required for tenant scoping (WT-2022 P0.TASK)")
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        query = select(Task).where(
            and_(
                Task.company_id == company_id,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.due_date >= today_start,
                Task.due_date < today_end
            )
        )
        if user_id:
            query = query.where(Task.assigned_to_user_id == user_id)
        query = query.order_by(Task.due_date.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_task_summary(
        self, *, company_id: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """Get summary counts for dashboard (WT-2022 P0.TASK fix: tenant-scoped)."""
        if not company_id:
            raise ValueError("company_id required for tenant scoping (WT-2022 P0.TASK)")
        base_query = select(func.count(Task.id)).where(Task.company_id == company_id)
        if user_id:
            base_query = base_query.where(Task.assigned_to_user_id == user_id)

        pending_count = (await self.db.execute(
            base_query.where(Task.status == TaskStatus.PENDING)
        )).scalar() or 0
        in_progress_count = (await self.db.execute(
            base_query.where(Task.status == TaskStatus.IN_PROGRESS)
        )).scalar() or 0
        completed_count = (await self.db.execute(
            base_query.where(Task.status == TaskStatus.COMPLETED)
        )).scalar() or 0
        overdue_count = (await self.db.execute(
            base_query.where(
                and_(
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                    Task.due_date < datetime.utcnow()
                )
            )
        )).scalar() or 0
        critical_count = (await self.db.execute(
            base_query.where(
                and_(
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                    Task.priority == TaskPriority.CRITICAL
                )
            )
        )).scalar() or 0

        return {
            "pending": pending_count,
            "in_progress": in_progress_count,
            "completed": completed_count,
            "overdue": overdue_count,
            "critical": critical_count,
            "total_active": pending_count + in_progress_count
        }
