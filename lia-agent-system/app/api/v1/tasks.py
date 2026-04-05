"""
Tasks API - Endpoints for task management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.domains.automation.services.task_service import task_service
from app.models.task import TaskPriority, TaskStatus, TaskType

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    """Request model for creating a task."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: Optional[TaskType] = TaskType.GENERAL
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    assigned_to_user_id: Optional[str] = None
    assigned_to_agent: Optional[str] = None
    related_job_id: Optional[str] = None
    related_candidate_id: Optional[str] = None
    due_date: Optional[datetime] = None
    context: Optional[dict] = None
    is_automated: bool = False
    requires_confirmation: bool = False


class TaskUpdate(BaseModel):
    """Request model for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    assigned_to_user_id: Optional[str] = None
    assigned_to_agent: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    """Response model for a task."""
    id: str
    title: str
    description: Optional[str]
    task_type: Optional[str]
    priority: Optional[str]
    status: Optional[str]
    created_by_agent: Optional[str]
    assigned_to_agent: Optional[str]
    assigned_to_user_id: Optional[str]
    related_job_id: Optional[str]
    related_candidate_id: Optional[str]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    context: Optional[dict]
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
    db: AsyncSession = Depends(get_db)
):
    """Create a new task."""
    task = await task_service.create_task(
        db=db,
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


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    user_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List tasks with optional filters."""
    tasks = await task_service.get_pending_tasks(
        db=db,
        user_id=user_id,
        agent_type=agent_type,
        priority=priority,
        limit=limit
    )
    return [task.to_dict() for task in tasks]


@router.get("/summary", response_model=TaskSummaryResponse)
async def get_task_summary(
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get task summary for dashboard."""
    summary = await task_service.get_task_summary(db=db, user_id=user_id)
    return summary


@router.get("/today", response_model=List[TaskResponse])
async def get_tasks_due_today(
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get tasks due today."""
    tasks = await task_service.get_tasks_due_today(db=db, user_id=user_id)
    return [task.to_dict() for task in tasks]


@router.get("/overdue", response_model=List[TaskResponse])
async def get_overdue_tasks(
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get overdue tasks."""
    tasks = await task_service.get_overdue_tasks(db=db, user_id=user_id)
    return [task.to_dict() for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific task by ID."""
    task = await task_service.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    update_data: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a task."""
    task = await task_service.get_task(db=db, task_id=task_id)
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
    
    await db.commit()
    await db.refresh(task)
    
    return task.to_dict()


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    result: Optional[dict] = None,
    db: AsyncSession = Depends(get_db)
):
    """Mark a task as completed."""
    task = await task_service.update_task_status(
        db=db,
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
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a task."""
    task = await task_service.cancel_task(
        db=db,
        task_id=task_id,
        reason=reason
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: str,
    user_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Assign a task to a user or agent."""
    if not user_id and not agent_type:
        raise HTTPException(
            status_code=400,
            detail="Must provide either user_id or agent_type"
        )
    
    task = await task_service.assign_task(
        db=db,
        task_id=task_id,
        user_id=user_id,
        agent_type=agent_type
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()
