"""Task Service - Business logic for task management.

This service handles:
- Creating tasks from agents
- Assigning tasks
- Completing tasks
- Querying pending tasks
- Task automation

Refactored per ADR-001: SQL access delegated to TaskRepository.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.agents.agent_types import AgentTask
from app.domains.automation.repositories.task_repository import TaskRepository
from lia_models.task import Task, TaskPriority, TaskStatus, TaskType

logger = logging.getLogger(__name__)


class TaskService:
    """
    Service for managing tasks in the LIA system.
    """

    async def create_task(
        self,
        db: AsyncSession,
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
        requires_confirmation: bool = False,
        company_id: str | None = None,
    ) -> Task:
        """Create a new task.

        WT-2022 P0.TASK gap fix: propagar company_id ao Task model.
        Endpoint POST /tasks/ recebe company_id no JWT mas service nao passava
        pro Task object - tasks ficavam company_id=NULL -> invisiveis no list
        filtrado por tenancy. Param opcional para compat com callers legados
        (warning emitido quando ausente).
        """
        if not company_id:
            logger.warning(
                "task_service.create_task chamado sem company_id - Task ficara "
                "company_id=NULL (multi-tenancy gap). Caller deve passar company_id "
                "do JWT/agent context. WT-2022 P0.TASK."
            )
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

        repo = TaskRepository(db)
        task = await repo.add(task)

        logger.info(f"Created task: {task.id} - {title} (priority: {priority.value})")

        return task

    async def create_from_agent_task(
        self,
        db: AsyncSession,
        agent_task: AgentTask,
        assigned_to_user_id: str | None = None,
        company_id: str | None = None,
    ) -> Task:
        """Create a database task from an AgentTask object.

        WT-2022 P0.TASK gap fix: propagar company_id (do agent_context ou
        runtime_context do caller) ao Task model via create_task.
        """
        return await self.create_task(
            db=db,
            title=agent_task.title,
            description=agent_task.description,
            priority=TaskPriority(agent_task.priority.value),
            created_by_agent=agent_task.created_by_agent.value if agent_task.created_by_agent else None,
            assigned_to_agent=agent_task.assigned_to_agent.value if agent_task.assigned_to_agent else None,
            assigned_to_user_id=assigned_to_user_id,
            due_date=agent_task.due_date,
            context=agent_task.context,
            company_id=company_id,
        )

    async def get_task(self, db: AsyncSession, task_id: str) -> Task | None:
        """Get a task by ID."""
        repo = TaskRepository(db)
        return await repo.get_by_id(task_id)

    async def update_task_status(
        self,
        db: AsyncSession,
        task_id: str,
        status: TaskStatus,
        result: dict[str, Any] | None = None,
        error_message: str | None = None
    ) -> Task | None:
        """Update task status."""
        repo = TaskRepository(db)
        task = await repo.get_by_id(task_id)
        if not task:
            return None

        task.status = status
        task.updated_at = datetime.utcnow()

        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
            task.result = result
        elif status == TaskStatus.FAILED:
            task.error_message = error_message

        await repo.commit_refresh(task)

        logger.info(f"Updated task {task_id} status to {status.value}")

        return task

    async def get_pending_tasks(
        self,
        db: AsyncSession,
        user_id: str | None = None,
        agent_type: str | None = None,
        priority: TaskPriority | None = None,
        limit: int = 50
    ) -> list[Task]:
        """Get pending tasks with optional filters."""
        repo = TaskRepository(db)
        return await repo.list_pending(
            user_id=user_id,
            agent_type=agent_type,
            priority=priority,
            limit=limit,
        )

    async def get_overdue_tasks(
        self,
        db: AsyncSession,
        user_id: str | None = None
    ) -> list[Task]:
        """Get all overdue tasks."""
        repo = TaskRepository(db)
        return await repo.list_overdue(user_id=user_id)

    async def get_tasks_due_today(
        self,
        db: AsyncSession,
        user_id: str | None = None
    ) -> list[Task]:
        """Get tasks due today."""
        repo = TaskRepository(db)
        return await repo.list_due_today(user_id=user_id)

    async def get_task_summary(
        self,
        db: AsyncSession,
        user_id: str | None = None
    ) -> dict[str, Any]:
        """Get summary of tasks for dashboard."""
        repo = TaskRepository(db)
        counts = await repo.get_summary_counts(user_id=user_id)
        counts["total_active"] = counts["pending"] + counts["in_progress"]
        return counts

    async def assign_task(
        self,
        db: AsyncSession,
        task_id: str,
        user_id: str | None = None,
        agent_type: str | None = None
    ) -> Task | None:
        """Assign a task to a user or agent."""
        repo = TaskRepository(db)
        task = await repo.get_by_id(task_id)
        if not task:
            return None

        if user_id:
            task.assigned_to_user_id = user_id
        if agent_type:
            task.assigned_to_agent = agent_type

        task.updated_at = datetime.utcnow()
        await repo.commit_refresh(task)

        return task

    async def cancel_task(
        self,
        db: AsyncSession,
        task_id: str,
        reason: str | None = None
    ) -> Task | None:
        """Cancel a task."""
        return await self.update_task_status(
            db=db,
            task_id=task_id,
            status=TaskStatus.CANCELLED,
            error_message=reason
        )

    async def confirm_task(
        self,
        db: AsyncSession,
        task_id: str,
        confirmed_by: str
    ) -> Task | None:
        """Confirm an automated task."""
        repo = TaskRepository(db)
        task = await repo.get_by_id(task_id)
        if not task:
            return None

        task.confirmed_by = confirmed_by
        task.confirmed_at = datetime.utcnow()
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.utcnow()
        await repo.commit_refresh(task)

        logger.info(f"Task {task_id} confirmed by {confirmed_by}")

        return task

    async def reject_task(
        self,
        db: AsyncSession,
        task_id: str,
        rejected_by: str,
        reason: str | None = None
    ) -> Task | None:
        """Reject a task."""
        repo = TaskRepository(db)
        task = await repo.get_by_id(task_id)
        if not task:
            return None

        task.rejected_by = rejected_by
        task.rejected_at = datetime.utcnow()
        task.rejection_reason = reason
        task.status = TaskStatus.CANCELLED
        task.updated_at = datetime.utcnow()
        await repo.commit_refresh(task)

        logger.info(f"Task {task_id} rejected by {rejected_by}: {reason}")

        return task

    async def send_reminder(
        self,
        db: AsyncSession,
        task_id: str
    ) -> Task | None:
        """Mark a task as having a reminder sent and increment counter."""
        repo = TaskRepository(db)
        task = await repo.get_by_id(task_id)
        if not task:
            return None

        task.reminder_sent = True
        task.reminder_count = (task.reminder_count or 0) + 1
        task.updated_at = datetime.utcnow()
        await repo.commit_refresh(task)

        logger.info(f"Reminder sent for task {task_id} (count: {task.reminder_count})")

        return task

    async def get_tasks_needing_reminder(
        self,
        db: AsyncSession,
        hours_before_due: int = 24
    ) -> list[Task]:
        """Query tasks that are due soon and need reminders."""
        repo = TaskRepository(db)
        return await repo.list_needing_reminder(hours_before_due=hours_before_due)

    async def check_and_send_reminders(
        self,
        db: AsyncSession,
        hours_before_due: int = 24
    ) -> list[Task]:
        """Find tasks due soon and mark them for reminder."""
        tasks = await self.get_tasks_needing_reminder(db, hours_before_due)
        reminded_tasks = []

        for task in tasks:
            updated_task = await self.send_reminder(db, task.id)
            if updated_task:
                reminded_tasks.append(updated_task)

        logger.info(f"Sent reminders for {len(reminded_tasks)} tasks")

        return reminded_tasks

    async def escalate_task(
        self,
        db: AsyncSession,
        task_id: str,
        escalate_to: str,
        reason: str | None = None
    ) -> Task | None:
        """Escalate a task to a higher level."""
        repo = TaskRepository(db)
        task = await repo.get_by_id(task_id)
        if not task:
            return None

        task.escalated_to = escalate_to
        task.escalated_at = datetime.utcnow()
        task.escalation_reason = reason
        task.escalation_level = min((task.escalation_level or 0) + 1, 3)
        task.updated_at = datetime.utcnow()
        await repo.commit_refresh(task)

        logger.info(f"Task {task_id} escalated to {escalate_to} (level {task.escalation_level}): {reason}")

        return task

    async def get_escalatable_tasks(
        self,
        db: AsyncSession,
        overdue_hours: int = 48
    ) -> list[Task]:
        """Query tasks that are overdue and should be escalated."""
        repo = TaskRepository(db)
        return await repo.list_escalatable(overdue_hours=overdue_hours)

    async def check_and_escalate_overdue(
        self,
        db: AsyncSession,
        overdue_hours: int = 48
    ) -> list[Task]:
        """Auto-escalate critical overdue tasks."""
        tasks = await self.get_escalatable_tasks(db, overdue_hours)
        escalated_tasks = []

        for task in tasks:
            escalation_level = (task.escalation_level or 0) + 1
            escalate_to_map = {
                1: "supervisor",
                2: "manager",
                3: "critical_alert"
            }
            escalate_to = escalate_to_map.get(escalation_level, "supervisor")

            hours_overdue = (datetime.utcnow() - task.due_date).total_seconds() / 3600
            reason = f"Auto-escalated: Task {hours_overdue:.1f} hours overdue with {task.priority.value} priority"

            updated_task = await self.escalate_task(db, task.id, escalate_to, reason)
            if updated_task:
                escalated_tasks.append(updated_task)

        logger.info(f"Auto-escalated {len(escalated_tasks)} overdue tasks")

        return escalated_tasks

    async def get_tasks_pending_confirmation(
        self,
        db: AsyncSession,
        user_id: str | None = None,
        limit: int = 50
    ) -> list[Task]:
        """Get tasks that require confirmation."""
        repo = TaskRepository(db)
        return await repo.list_pending_confirmation(user_id=user_id, limit=limit)


task_service = TaskService()
