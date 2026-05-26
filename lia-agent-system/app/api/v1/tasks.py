"""
Tasks API - Endpoints for task management.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.domains.tasks.dependencies import get_tasks_repo
from app.domains.tasks.repositories.tasks_repository import TasksRepository
from app.domains.automation.services.task_service import task_service
from app.models.task import TaskPriority, TaskStatus, TaskType
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.shared.rbac.mutation_gate import assert_mutation_allowed
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(WeDoBaseModel):
    """Request model for creating a task."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    task_type: TaskType | None = TaskType.GENERAL
    priority: TaskPriority | None = TaskPriority.MEDIUM
    assigned_to_user_id: str | None = None
    assigned_to_agent: str | None = None
    related_job_id: str | None = None
    related_candidate_id: str | None = None
    due_date: datetime | None = None
    context: dict | None = None
    is_automated: bool = False
    requires_confirmation: bool = False


class TaskUpdate(WeDoBaseModel):
    """Request model for updating a task."""
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    assigned_to_user_id: str | None = None
    assigned_to_agent: str | None = None
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    """Response model for a task."""
    id: str
    title: str
    description: str | None
    task_type: str | None
    priority: str | None
    status: str | None
    created_by_agent: str | None
    assigned_to_agent: str | None
    assigned_to_user_id: str | None
    related_job_id: str | None
    related_candidate_id: str | None
    due_date: datetime | None
    completed_at: datetime | None
    context: dict | None
    is_automated: bool
    requires_confirmation: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskSummaryResponse(BaseModel):
    """Response model for task summary."""
    pending: int
    in_progress: int
    completed: int
    overdue: int
    critical: int
    total_active: int


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    repo: TasksRepository = Depends(get_tasks_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new task."""
    task = await task_service.create_task(
        db=repo.db,
        title=task_data.title,
        description=task_data.description,
        task_type=task_data.task_type or TaskType.GENERAL,
        priority=task_data.priority or TaskPriority.MEDIUM,
        assigned_to_user_id=task_data.assigned_to_user_id,
        assigned_to_agent=task_data.assigned_to_agent,
        related_job_id=task_data.related_job_id,
        related_candidate_id=task_data.related_candidate_id,
        due_date=task_data.due_date,
        context=task_data.context,
        is_automated=task_data.is_automated,
        requires_confirmation=task_data.requires_confirmation,
        company_id=company_id,  # WT-2022 P0.TASK: propaga JWT company_id
    )
    return task.to_dict()




# ---------------------------------------------------------------------------
# Sprint 6.2 RBAC — manager hierarchy filter for tasks
# Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
# ---------------------------------------------------------------------------
async def _filter_tasks_by_visible_scope(tasks: list, current_user) -> list:
    """Visible scope filter (1-level manager hierarchy).

    Task visible if:
      - admin (bypass)
      - legacy user (no dept + no subordinates) — soft-launch compat
      - assigned_to_user_id is self
      - assigned_to_user_id in subordinate_user_ids (manager sees team)
      - assigned_to_user_id is None (unassigned tasks visible to all in tenant)
    """
    if not tasks:
        return tasks
    try:
        from app.shared.rbac.visible_scope import compute_visible_scope
        scope = await compute_visible_scope(current_user)
    except Exception:
        return tasks  # non-blocking fallback

    if scope.is_admin:
        return tasks
    if scope.own_dept_id is None and not scope.has_subordinates:
        return tasks  # legacy soft-launch bypass

    allowed = set(scope.subordinate_user_ids)
    if scope.user_id:
        allowed.add(scope.user_id)

    visible = []
    for t in tasks:
        assignee = getattr(t, "assigned_to_user_id", None)
        if assignee is None:
            visible.append(t)  # unassigned tasks visible (could be reassigned)
            continue
        if str(assignee) in allowed:
            visible.append(t)
    return visible

@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    user_id: str | None = None,
    agent_type: str | None = None,
    limit: int = Query(default=50, le=100),
    repo: TasksRepository = Depends(get_tasks_repo),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List tasks with optional filters."""
    tasks = await repo.get_pending_tasks(
        user_id=user_id,
        agent_type=agent_type,
        priority=priority,
        limit=limit
    )
    # Sprint 6.2 RBAC visible scope filter
    tasks = await _filter_tasks_by_visible_scope(tasks, current_user)
    return [task.to_dict() for task in tasks]


@router.get("/summary", response_model=TaskSummaryResponse)
async def get_task_summary(
    user_id: str | None = None,
    repo: TasksRepository = Depends(get_tasks_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get task summary for dashboard."""
    summary = await repo.get_task_summary(user_id=user_id)
    return summary


@router.get("/today", response_model=list[TaskResponse])
async def get_tasks_due_today(
    user_id: str | None = None,
    repo: TasksRepository = Depends(get_tasks_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get tasks due today."""
    tasks = await repo.get_tasks_due_today(user_id=user_id)
    tasks = await _filter_tasks_by_visible_scope(tasks, current_user)
    return [task.to_dict() for task in tasks]


@router.get("/overdue", response_model=list[TaskResponse])
async def get_overdue_tasks(
    user_id: str | None = None,
    repo: TasksRepository = Depends(get_tasks_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get overdue tasks."""
    tasks = await repo.get_overdue_tasks(user_id=user_id)
    tasks = await _filter_tasks_by_visible_scope(tasks, current_user)
    return [task.to_dict() for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    repo: TasksRepository = Depends(get_tasks_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get a specific task by ID."""
    task = await repo.get_task(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task.to_dict()


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    update_data: TaskUpdate,
    repo: TasksRepository = Depends(get_tasks_repo),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update a task."""
    task = await repo.get_task(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        await assert_mutation_allowed(task, current_user, resource_label="tarefa")

    if update_data.title:
        task.title = update_data.title
    if update_data.description is not None:
        task.description = update_data.description
    if update_data.priority:
        task.priority = update_data.priority
    if update_data.status:
        task.status = update_data.status
        if update_data.status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
    if update_data.assigned_to_user_id is not None:
        task.assigned_to_user_id = update_data.assigned_to_user_id
    if update_data.assigned_to_agent is not None:
        task.assigned_to_agent = update_data.assigned_to_agent
    if update_data.due_date is not None:
        task.due_date = update_data.due_date

    task.updated_at = datetime.utcnow()

    task = await repo.flush_and_refresh(task)

    return task.to_dict()


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    result: dict | None = None,
    repo: TasksRepository = Depends(get_tasks_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Mark a task as completed."""
    task = await task_service.update_task_status(
        db=repo.db,
        task_id=task_id,
        status=TaskStatus.COMPLETED,
        result=result
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    reason: str | None = None,
    repo: TasksRepository = Depends(get_tasks_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Cancel a task."""
    task = await task_service.cancel_task(
        db=repo.db,
        task_id=task_id,
        reason=reason
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: str,
    user_id: str | None = None,
    agent_type: str | None = None,
    repo: TasksRepository = Depends(get_tasks_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Assign a task to a user or agent."""
    if not user_id and not agent_type:
        raise HTTPException(
            status_code=400,
            detail="Must provide either user_id or agent_type"
        )

    task = await task_service.assign_task(
        db=repo.db,
        task_id=task_id,
        user_id=user_id,
        agent_type=agent_type
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()
