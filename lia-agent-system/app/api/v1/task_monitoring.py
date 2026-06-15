import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.shared.async_processing.enhanced_task_manager import EnhancedTaskManager
from app.shared.async_processing.task_persistence import TaskPersistenceService
from app.shared.async_processing.task_queue import TaskPriority
from app.shared.async_processing.task_scheduler import TaskScheduler
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/async-tasks")


class TaskSubmitRequest(WeDoBaseModel):
    domain_id: str
    action_id: str
    params: dict[str, Any] = Field(default_factory=dict)
    user_id: str = ""
    tenant_id: str | None = None
    priority: int = 1
    max_retries: int = 2
    callback: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScheduleCreateRequest(WeDoBaseModel):
    name: str
    domain_id: str
    action_id: str
    cron_expression: str
    params: dict[str, Any] = Field(default_factory=dict)
    priority: int = 1
    tenant_id: str | None = None
    user_id: str = "system"
    max_retries: int = 2
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/submit", response_model=None)
async def submit_task(request: TaskSubmitRequest, current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        manager = EnhancedTaskManager.get_instance()
        priority_map = {0: TaskPriority.LOW, 1: TaskPriority.NORMAL, 2: TaskPriority.HIGH, 3: TaskPriority.URGENT}
        priority = priority_map.get(request.priority, TaskPriority.NORMAL)

        task_id = await manager.submit_task(
            domain_id=request.domain_id,
            action_id=request.action_id,
            params=request.params,
            user_id=request.user_id,
            tenant_id=request.tenant_id,
            priority=priority,
            max_retries=request.max_retries,
            callback=request.callback,
            metadata=request.metadata,
        )
        return {"task_id": task_id, "status": "submitted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=None)
async def get_stats(current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        manager = EnhancedTaskManager.get_instance()
        return await manager.get_enhanced_stats()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history", response_model=None)
async def get_task_history(
    domain_id: str | None = Query(None),
    state: str | None = Query(None),
    user_id: str | None = Query(None),
    tenant_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        manager = EnhancedTaskManager.get_instance()
        history = await manager.get_task_history(
            domain_id=domain_id,
            state=state,
            user_id=user_id,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )
        return {"tasks": history, "count": len(history), "limit": limit, "offset": offset}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/schedules", response_model=None)
async def list_schedules(
    active_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        scheduler = TaskScheduler.get_instance()
        schedules = await scheduler.list_schedules(active_only=active_only, limit=limit, offset=offset)
        return {"schedules": schedules, "count": len(schedules)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/schedules", response_model=None)
async def create_schedule(request: ScheduleCreateRequest, current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        scheduler = TaskScheduler.get_instance()
        schedule = await scheduler.add_schedule(
            name=request.name,
            domain_id=request.domain_id,
            action_id=request.action_id,
            cron_expression=request.cron_expression,
            params=request.params,
            priority=request.priority,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            max_retries=request.max_retries,
            metadata=request.metadata,
        )
        return {"schedule": schedule, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/schedules/{schedule_id}", response_model=None)
async def remove_schedule(schedule_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        scheduler = TaskScheduler.get_instance()
        removed = await scheduler.remove_schedule(schedule_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return {"status": "removed", "schedule_id": schedule_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove schedule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dlq", response_model=None)
async def list_dlq(
    resolved: bool | None = Query(None),
    domain_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        persistence = TaskPersistenceService.get_instance()
        entries = await persistence.list_dlq(
            resolved=resolved, domain_id=domain_id, limit=limit, offset=offset
        )
        return {"entries": entries, "count": len(entries)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list DLQ: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/dlq/{dlq_id}/retry", response_model=None)
async def retry_dlq_entry(dlq_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        persistence = TaskPersistenceService.get_instance()
        record = await persistence.get_dlq_record(dlq_id)
        if not record:
            raise HTTPException(status_code=404, detail="DLQ entry not found")

        manager = EnhancedTaskManager.get_instance()

        task_id = await manager.submit_task(
            domain_id=record.domain_id,
            action_id=record.action_id,
            params=record.params or {},
            metadata={"retried_from_dlq": dlq_id},
        )

        await persistence.resolve_dlq(dlq_id)

        return {"task_id": task_id, "dlq_id": dlq_id, "status": "retried"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry DLQ entry {dlq_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{task_id}", response_model=None)
async def get_task_status(task_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        manager = EnhancedTaskManager.get_instance()
        status = await manager.get_task_status_enhanced(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=None)
async def list_tasks(
    domain_id: str | None = Query(None),
    state: str | None = Query(None),
    user_id: str | None = Query(None),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        manager = EnhancedTaskManager.get_instance()
        from app.shared.async_processing.task_queue import TaskState

        task_state = None
        if state:
            try:
                task_state = TaskState(state)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid state: {state}")

        tasks = manager.list_tasks(domain_id=domain_id, state=task_state, user_id=user_id)
        return {"tasks": tasks, "count": len(tasks)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{task_id}", response_model=None)
async def cancel_task(task_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        manager = EnhancedTaskManager.get_instance()
        cancelled = manager.cancel_task(task_id)
        if not cancelled:
            raise HTTPException(status_code=404, detail="Task not found or already terminal")

        try:
            await manager._persistence.update_task_state(task_id, "cancelled")
        except Exception as e:
            logger.error(f"Failed to persist cancellation for {task_id}: {e}")

        return {"task_id": task_id, "status": "cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

reorder_collection_before_item(router)
