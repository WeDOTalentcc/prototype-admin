"""
Tasks API - Endpoints for task management.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.domains.tasks.dependencies import get_tasks_repo
from app.domains.tasks.repositories.tasks_repository import TasksRepository
from app.domains.automation.services.task_service import task_service
from lia_models.task import TaskPriority, TaskStatus, TaskType
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
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


class TaskUpdate(BaseModel):
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
    repo: TasksRepository = Depends(get_tasks_repo)
):
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
        requires_confirmation=task_data.requires_confirmation
    )
    return task.to_dict()


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    user_id: str | None = None,
    agent_type: str | None = None,
    limit: int = Query(default=50, le=100),
    repo: TasksRepository = Depends(get_tasks_repo)
):
    """List tasks with optional filters."""
    tasks = await repo.get_pending_tasks(
        user_id=user_id,
        agent_type=agent_type,
        priority=priority,
        limit=limit
    )
    return [task.to_dict() for task in tasks]


@router.get("/summary", response_model=TaskSummaryResponse)
async def get_task_summary(
    user_id: str | None = None,
    repo: TasksRepository = Depends(get_tasks_repo)
):
    """Get task summary for dashboard."""
    summary = await repo.get_task_summary(user_id=user_id)
    return summary


@router.get("/today", response_model=list[TaskResponse])
async def get_tasks_due_today(
    user_id: str | None = None,
    repo: TasksRepository = Depends(get_tasks_repo)
):
    """Get tasks due today."""
    tasks = await repo.get_tasks_due_today(user_id=user_id)
    return [task.to_dict() for task in tasks]


@router.get("/overdue", response_model=list[TaskResponse])
async def get_overdue_tasks(
    user_id: str | None = None,
    repo: TasksRepository = Depends(get_tasks_repo)
):
    """Get overdue tasks."""
    tasks = await repo.get_overdue_tasks(user_id=user_id)
    return [task.to_dict() for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: _DualId,
    repo: TasksRepository = Depends(get_tasks_repo)
):
    """Get a specific task by ID."""
    task = await repo.get_task(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: _DualId,
    update_data: TaskUpdate,
    repo: TasksRepository = Depends(get_tasks_repo)
):
    """Update a task."""
    task = await repo.get_task(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

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
    task_id: _DualId,
    result: dict | None = None,
    repo: TasksRepository = Depends(get_tasks_repo)
):
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
    task_id: _DualId,
    reason: str | None = None,
    repo: TasksRepository = Depends(get_tasks_repo)
):
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
    task_id: _DualId,
    user_id: str | None = None,
    agent_type: str | None = None,
    repo: TasksRepository = Depends(get_tasks_repo)
):
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

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
