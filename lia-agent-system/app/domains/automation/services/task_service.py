"""
Task Service - Business logic for task management.

This service handles:
- Creating tasks from agents
- Assigning tasks
- Completing tasks
- Querying pending tasks
- Task automation
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentTask
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
        requires_confirmation: bool = False
    ) -> Task:
        """
        Create a new task.
        
        Args:
            db: Database session
            title: Task title
            description: Optional task description
            task_type: Type of task
            priority: Task priority
            created_by_agent: Agent that created the task
            assigned_to_agent: Agent assigned to handle the task
            assigned_to_user_id: User assigned to handle the task
            related_job_id: Related job vacancy ID
            related_candidate_id: Related candidate ID
            due_date: Optional due date
            context: Additional context data
            is_automated: Whether task can be auto-executed
            requires_confirmation: Whether task needs user confirmation
            
        Returns:
            Created Task instance
        """
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
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Created task: {task.id} - {title} (priority: {priority.value})")
        
        return task
    
    async def create_from_agent_task(
        self,
        db: AsyncSession,
        agent_task: AgentTask,
        assigned_to_user_id: str | None = None
    ) -> Task:
        """
        Create a database task from an AgentTask object.
        
        Args:
            db: Database session
            agent_task: AgentTask from an agent
            assigned_to_user_id: Optional user to assign
            
        Returns:
            Created Task instance
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
            context=agent_task.context
        )
    
    async def get_task(self, db: AsyncSession, task_id: str) -> Task | None:
        """Get a task by ID."""
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()
    
    async def update_task_status(
        self,
        db: AsyncSession,
        task_id: str,
        status: TaskStatus,
        result: dict[str, Any] | None = None,
        error_message: str | None = None
    ) -> Task | None:
        """
        Update task status.
        
        Args:
            db: Database session
            task_id: Task ID
            status: New status
            result: Optional result data
            error_message: Optional error message
            
        Returns:
            Updated Task or None if not found
        """
        task = await self.get_task(db, task_id)
        if not task:
            return None
        
        task.status = status
        task.updated_at = datetime.utcnow()
        
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
            task.result = result
        elif status == TaskStatus.FAILED:
            task.error_message = error_message
        
        await db.commit()
        await db.refresh(task)
        
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
        """
        Get pending tasks with optional filters.
        
        Args:
            db: Database session
            user_id: Filter by assigned user
            agent_type: Filter by assigned agent
            priority: Filter by priority
            limit: Maximum number of tasks to return
            
        Returns:
            List of pending tasks
        """
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
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_overdue_tasks(
        self,
        db: AsyncSession,
        user_id: str | None = None
    ) -> list[Task]:
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
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_tasks_due_today(
        self,
        db: AsyncSession,
        user_id: str | None = None
    ) -> list[Task]:
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
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_task_summary(
        self,
        db: AsyncSession,
        user_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get summary of tasks for dashboard.
        
        Args:
            db: Database session
            user_id: Optional user to filter by
            
        Returns:
            Dictionary with task counts and summary
        """
        base_query = select(func.count(Task.id))
        
        if user_id:
            base_query = base_query.where(Task.assigned_to_user_id == user_id)
        
        pending_query = base_query.where(Task.status == TaskStatus.PENDING)
        in_progress_query = base_query.where(Task.status == TaskStatus.IN_PROGRESS)
        completed_query = base_query.where(Task.status == TaskStatus.COMPLETED)
        
        overdue_query = base_query.where(
            and_(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.due_date < datetime.utcnow()
            )
        )
        
        critical_query = base_query.where(
            and_(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.priority == TaskPriority.CRITICAL
            )
        )
        
        pending_count = (await db.execute(pending_query)).scalar() or 0
        in_progress_count = (await db.execute(in_progress_query)).scalar() or 0
        completed_count = (await db.execute(completed_query)).scalar() or 0
        overdue_count = (await db.execute(overdue_query)).scalar() or 0
        critical_count = (await db.execute(critical_query)).scalar() or 0
        
        return {
            "pending": pending_count,
            "in_progress": in_progress_count,
            "completed": completed_count,
            "overdue": overdue_count,
            "critical": critical_count,
            "total_active": pending_count + in_progress_count
        }
    
    async def assign_task(
        self,
        db: AsyncSession,
        task_id: str,
        user_id: str | None = None,
        agent_type: str | None = None
    ) -> Task | None:
        """
        Assign a task to a user or agent.
        
        Args:
            db: Database session
            task_id: Task ID
            user_id: User to assign
            agent_type: Agent to assign
            
        Returns:
            Updated Task or None if not found
        """
        task = await self.get_task(db, task_id)
        if not task:
            return None
        
        if user_id:
            task.assigned_to_user_id = user_id
        if agent_type:
            task.assigned_to_agent = agent_type
        
        task.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(task)
        
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
        """
        Confirm an automated task.
        
        Args:
            db: Database session
            task_id: Task ID
            confirmed_by: User ID who confirmed the task
            
        Returns:
            Updated Task or None if not found
        """
        task = await self.get_task(db, task_id)
        if not task:
            return None
        
        task.confirmed_by = confirmed_by
        task.confirmed_at = datetime.utcnow()
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Task {task_id} confirmed by {confirmed_by}")
        
        return task
    
    async def reject_task(
        self,
        db: AsyncSession,
        task_id: str,
        rejected_by: str,
        reason: str | None = None
    ) -> Task | None:
        """
        Reject a task.
        
        Args:
            db: Database session
            task_id: Task ID
            rejected_by: User ID who rejected the task
            reason: Reason for rejection
            
        Returns:
            Updated Task or None if not found
        """
        task = await self.get_task(db, task_id)
        if not task:
            return None
        
        task.rejected_by = rejected_by
        task.rejected_at = datetime.utcnow()
        task.rejection_reason = reason
        task.status = TaskStatus.CANCELLED
        task.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Task {task_id} rejected by {rejected_by}: {reason}")
        
        return task
    
    async def send_reminder(
        self,
        db: AsyncSession,
        task_id: str
    ) -> Task | None:
        """
        Mark a task as having a reminder sent and increment counter.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            Updated Task or None if not found
        """
        task = await self.get_task(db, task_id)
        if not task:
            return None
        
        task.reminder_sent = True
        task.reminder_count = (task.reminder_count or 0) + 1
        task.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Reminder sent for task {task_id} (count: {task.reminder_count})")
        
        return task
    
    async def get_tasks_needing_reminder(
        self,
        db: AsyncSession,
        hours_before_due: int = 24
    ) -> list[Task]:
        """
        Query tasks that are due soon and need reminders.
        
        Args:
            db: Database session
            hours_before_due: Hours before due date to send reminder (default 24)
            
        Returns:
            List of tasks needing reminders
        """
        now = datetime.utcnow()
        reminder_threshold = now + timedelta(hours=hours_before_due)
        
        query = select(Task).where(
            and_(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.due_date.isnot(None),
                Task.due_date <= reminder_threshold,
                Task.due_date > now,
                or_(
                    not Task.reminder_sent,
                    Task.reminder_sent.is_(None)
                )
            )
        ).order_by(Task.due_date.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def check_and_send_reminders(
        self,
        db: AsyncSession,
        hours_before_due: int = 24
    ) -> list[Task]:
        """
        Find tasks due soon and mark them for reminder.
        
        Args:
            db: Database session
            hours_before_due: Hours before due date to trigger reminder
            
        Returns:
            List of tasks that were marked for reminder
        """
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
        """
        Escalate a task to a higher level.
        
        Args:
            db: Database session
            task_id: Task ID
            escalate_to: User/role to escalate to
            reason: Reason for escalation
            
        Returns:
            Updated Task or None if not found
        """
        task = await self.get_task(db, task_id)
        if not task:
            return None
        
        task.escalated_to = escalate_to
        task.escalated_at = datetime.utcnow()
        task.escalation_reason = reason
        task.escalation_level = min((task.escalation_level or 0) + 1, 3)
        task.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Task {task_id} escalated to {escalate_to} (level {task.escalation_level}): {reason}")
        
        return task
    
    async def get_escalatable_tasks(
        self,
        db: AsyncSession,
        overdue_hours: int = 48
    ) -> list[Task]:
        """
        Query tasks that are overdue and should be escalated.
        Only HIGH and CRITICAL priority tasks are considered.
        
        Args:
            db: Database session
            overdue_hours: Hours after due date to trigger escalation (default 48)
            
        Returns:
            List of tasks that should be escalated
        """
        escalation_threshold = datetime.utcnow() - timedelta(hours=overdue_hours)
        
        query = select(Task).where(
            and_(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.due_date.isnot(None),
                Task.due_date < escalation_threshold,
                Task.priority.in_([TaskPriority.HIGH, TaskPriority.CRITICAL]),
                Task.escalation_level < 3
            )
        ).order_by(Task.priority.desc(), Task.due_date.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def check_and_escalate_overdue(
        self,
        db: AsyncSession,
        overdue_hours: int = 48
    ) -> list[Task]:
        """
        Auto-escalate critical overdue tasks.
        
        Args:
            db: Database session
            overdue_hours: Hours after due date to trigger escalation
            
        Returns:
            List of tasks that were escalated
        """
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
        """
        Get tasks that require confirmation.
        
        Args:
            db: Database session
            user_id: Optional user to filter by
            limit: Maximum number of tasks to return
            
        Returns:
            List of tasks pending confirmation
        """
        query = select(Task).where(
            and_(
                Task.status == TaskStatus.PENDING,
                Task.requires_confirmation,
                Task.confirmed_at.is_(None),
                Task.rejected_at.is_(None)
            )
        )
        
        if user_id:
            query = query.where(Task.assigned_to_user_id == user_id)
        
        query = query.order_by(
            Task.priority.desc(),
            Task.due_date.asc().nullslast(),
            Task.created_at.desc()
        ).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Chat tool surface (registered in app/domains/automation/tools/__init__.py)
    # ------------------------------------------------------------------
    async def list_tasks(
        self,
        db=None,
        company_id: str | None = None,
        status: str | None = None,
        **kwargs,
    ):
        """List tasks for the chat surface; defaults to pending."""
        if db is None:
            return {"success": True, "tasks": [], "count": 0, "filter": status or "pending"}
        if status == "overdue":
            tasks = await self.get_overdue_tasks(db, company_id=company_id)
        elif status == "today":
            tasks = await self.get_tasks_due_today(db, company_id=company_id)
        else:
            tasks = await self.get_pending_tasks(db, company_id=company_id)
        return {
            "success": True,
            "count": len(tasks),
            "filter": status or "pending",
            "tasks": [getattr(t, "id", None) for t in tasks],
        }

    async def complete_task(
        self,
        db=None,
        task_id: str = "",
        completed_by: str | None = None,
        **kwargs,
    ):
        """Mark a task as completed (thin wrapper over update_task_status)."""
        from lia_models.task import TaskStatus  # local import: avoid cycles
        return await self.update_task_status(
            db=db,
            task_id=task_id,
            new_status=TaskStatus.COMPLETED if hasattr(TaskStatus, "COMPLETED") else "completed",
            updated_by=completed_by,
        )


task_service = TaskService()
