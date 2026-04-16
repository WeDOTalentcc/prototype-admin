"""
Tasks Repository - Database access layer for task management.
"""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.task import Task, TaskPriority, TaskStatus, TaskType


class TasksRepository:
    """Repository for task database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
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
        task = Task(
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

    async def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        result = await self.db.execute(select(Task).where(Task.id == task_id))
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
        user_id: str | None = None,
        agent_type: str | None = None,
        priority: TaskPriority | None = None,
        limit: int = 50
    ) -> list[Task]:
        """Get pending/in-progress tasks with optional filters."""
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
            Task.created_at.desc()
        ).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_overdue_tasks(self, user_id: str | None = None) -> list[Task]:
        """Get all overdue tasks."""
        query = select(Task).where(
            and_(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.due_date < datetime.utcnow()
            )
        )
        if user_id:
            query = query.where(Task.assigned_to_user_id == user_id)
        query = query.order_by(Task.due_date.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_tasks_due_today(self, user_id: str | None = None) -> list[Task]:
        """Get tasks due today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        query = select(Task).where(
            and_(
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

    async def get_task_summary(self, user_id: str | None = None) -> dict[str, Any]:
        """Get summary counts for dashboard."""
        base_query = select(func.count(Task.id))
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
