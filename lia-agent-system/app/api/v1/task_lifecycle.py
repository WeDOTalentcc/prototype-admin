"""
Task Lifecycle API - Endpoints for task confirmation, reminders, and escalation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.automation.services.task_service import task_service
from app.models.task import Task
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/task-lifecycle", tags=["task-lifecycle"])


def _task_to_lifecycle_response(task: Task) -> dict:
    """
    Convert a Task model to a TaskLifecycleResponse-compatible dictionary.
    Ensures proper serialization of enums and datetime fields.
    """
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status.value if task.status else None,
        "priority": task.priority.value if task.priority else None,
        "confirmed_by": task.confirmed_by,
        "confirmed_at": task.confirmed_at.isoformat() if task.confirmed_at else None,
        "rejected_by": task.rejected_by,
        "rejected_at": task.rejected_at.isoformat() if task.rejected_at else None,
        "rejection_reason": task.rejection_reason,
        "escalated_to": task.escalated_to,
        "escalated_at": task.escalated_at.isoformat() if task.escalated_at else None,
        "escalation_reason": task.escalation_reason,
        "escalation_level": task.escalation_level or 0,
        "reminder_sent": task.reminder_sent or False,
        "reminder_count": task.reminder_count or 0,
    }


class TaskConfirmRequest(WeDoBaseModel):
    """Request model for confirming a task."""
    confirmed_by: str = Field(..., description="User ID who confirmed the task")


class TaskRejectRequest(WeDoBaseModel):
    """Request model for rejecting a task."""
    rejected_by: str = Field(..., description="User ID who rejected the task")
    reason: str | None = Field(None, description="Reason for rejection")


class TaskEscalateRequest(WeDoBaseModel):
    """Request model for escalating a task."""
    escalate_to: str = Field(..., description="User/role to escalate to")
    reason: str | None = Field(None, description="Reason for escalation")


class CheckRemindersRequest(WeDoBaseModel):
    """Request model for checking reminders."""
    hours_before_due: int = Field(default=24, ge=1, le=168, description="Hours before due date to send reminder")


class CheckEscalationsRequest(WeDoBaseModel):
    """Request model for checking escalations."""
    overdue_hours: int = Field(default=48, ge=1, le=720, description="Hours after due date to trigger escalation")


class TaskLifecycleResponse(BaseModel):
    """Response model for a task lifecycle operation."""
    id: str
    title: str
    status: str | None
    priority: str | None
    confirmed_by: str | None = None
    confirmed_at: str | None = None
    rejected_by: str | None = None
    rejected_at: str | None = None
    rejection_reason: str | None = None
    escalated_to: str | None = None
    escalated_at: str | None = None
    escalation_reason: str | None = None
    escalation_level: int = 0
    reminder_sent: bool = False
    reminder_count: int = 0
    
    class Config:
        from_attributes = True


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""
    processed_count: int
    tasks: list[TaskLifecycleResponse]


@router.post("/{task_id}/confirm", response_model=TaskLifecycleResponse)
async def confirm_task(
    task_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: TaskConfirmRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Confirm a task that requires confirmation.
    
    This marks the task as confirmed and sets its status to IN_PROGRESS.
    """
    task = await task_service.confirm_task(
        db=db,
        task_id=task_id,
        confirmed_by=request.confirmed_by
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_lifecycle_response(task)


@router.post("/{task_id}/reject", response_model=TaskLifecycleResponse)
async def reject_task(
    task_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: TaskRejectRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Reject a task.
    
    This marks the task as rejected and sets its status to CANCELLED.
    """
    task = await task_service.reject_task(
        db=db,
        task_id=task_id,
        rejected_by=request.rejected_by,
        reason=request.reason
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_lifecycle_response(task)


@router.post("/{task_id}/escalate", response_model=TaskLifecycleResponse)
async def escalate_task(
    task_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: TaskEscalateRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Escalate a task to a higher level.
    
    Escalation levels:
    - 0: No escalation
    - 1: Supervisor
    - 2: Manager
    - 3: Critical (highest)
    """
    task = await task_service.escalate_task(
        db=db,
        task_id=task_id,
        escalate_to=request.escalate_to,
        reason=request.reason
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_lifecycle_response(task)


@router.post("/{task_id}/reminder", response_model=TaskLifecycleResponse)
async def send_task_reminder(
    task_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Mark a reminder as sent for a task and increment the reminder counter.
    """
    task = await task_service.send_reminder(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_lifecycle_response(task)


@router.post("/check-reminders", response_model=BulkOperationResponse)
async def check_and_send_reminders(
    request: CheckRemindersRequest = CheckRemindersRequest(),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Check for tasks due soon and mark them for reminder.
    
    Default: Tasks due within 24 hours will be flagged.
    """
    tasks = await task_service.check_and_send_reminders(
        db=db,
        hours_before_due=request.hours_before_due
    )
    return BulkOperationResponse(
        processed_count=len(tasks),
        tasks=[_task_to_lifecycle_response(task) for task in tasks]
    )


@router.post("/check-escalations", response_model=BulkOperationResponse)
async def check_and_escalate_overdue(
    request: CheckEscalationsRequest = CheckEscalationsRequest(),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Check for overdue tasks and auto-escalate them.
    
    Default: HIGH/CRITICAL priority tasks overdue by 48+ hours will be escalated.
    """
    tasks = await task_service.check_and_escalate_overdue(
        db=db,
        overdue_hours=request.overdue_hours
    )
    return BulkOperationResponse(
        processed_count=len(tasks),
        tasks=[_task_to_lifecycle_response(task) for task in tasks]
    )


@router.get("/pending-confirmation", response_model=list[TaskLifecycleResponse])
async def get_tasks_pending_confirmation(
    user_id: str | None = None,
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List tasks that are pending confirmation.
    
    These are automated tasks that require user approval before proceeding.
    """
    tasks = await task_service.get_tasks_pending_confirmation(
        db=db,
        user_id=user_id,
        limit=limit
    )
    return [_task_to_lifecycle_response(task) for task in tasks]


@router.get("/needing-reminder", response_model=list[TaskLifecycleResponse])
async def get_tasks_needing_reminder(
    hours_before_due: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List tasks that are due soon and haven't received a reminder yet.
    """
    tasks = await task_service.get_tasks_needing_reminder(
        db=db,
        hours_before_due=hours_before_due
    )
    return [_task_to_lifecycle_response(task) for task in tasks]


@router.get("/escalatable", response_model=list[TaskLifecycleResponse])
async def get_escalatable_tasks(
    overdue_hours: int = Query(default=48, ge=1, le=720),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List HIGH/CRITICAL priority tasks that are overdue and can be escalated.
    """
    tasks = await task_service.get_escalatable_tasks(
        db=db,
        overdue_hours=overdue_hours
    )
    return [_task_to_lifecycle_response(task) for task in tasks]

reorder_collection_before_item(router)
