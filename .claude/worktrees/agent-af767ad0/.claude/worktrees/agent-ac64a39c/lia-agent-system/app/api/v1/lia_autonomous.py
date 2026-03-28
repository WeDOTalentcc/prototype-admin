"""
LIA Autonomous Agent & Proactive Actions endpoints — extracted from lia_assistant.py (Sprint E).
Router is included by lia_assistant.router, so all routes resolve under /lia/autonomous/...
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging

from app.services.autonomous_agent_service import autonomous_agent_service

logger = logging.getLogger(__name__)

autonomous_router = APIRouter()

DEFAULT_COMPANY_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


# ── Schemas ──────────────────────────────────────────────────────────────────

class CreateJobRequest(BaseModel):
    """Request model for creating a background job."""
    job_type: str
    name: str
    config: dict = {}
    schedule: Optional[str] = None
    description: Optional[str] = None
    company_id: str = DEFAULT_COMPANY_UUID


class CreateActionRequest(BaseModel):
    """Request model for creating a proactive action."""
    action_type: str
    title: str
    description: str
    suggested_action: dict = {}
    priority: str = "normal"
    related_job_id: Optional[str] = None
    related_candidate_id: Optional[str] = None
    trigger_reason: Optional[str] = None
    auto_executable: bool = False
    expires_in_hours: Optional[int] = 24
    company_id: str = DEFAULT_COMPANY_UUID


# ── Background Jobs ────────────────────────────────────────────────────────────

@autonomous_router.post("/autonomous/jobs")
async def create_background_job(request: CreateJobRequest) -> dict:
    """Create a new background job (screening, sourcing, report_generation, etc.)."""
    try:
        job = await autonomous_agent_service.create_job(
            company_id=request.company_id,
            job_type=request.job_type,
            name=request.name,
            config=request.config,
            schedule=request.schedule,
            description=request.description,
            created_by="api"
        )
        return {"success": True, "job": job.to_dict()}
    except Exception as e:
        logger.error(f"Failed to create background job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@autonomous_router.get("/autonomous/jobs")
async def list_jobs(
    company_id: str = Query(DEFAULT_COMPANY_UUID, description="Company ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of jobs to return")
) -> dict:
    """List background jobs with optional filters."""
    try:
        jobs = await autonomous_agent_service.list_jobs(
            company_id=company_id, status=status, job_type=job_type, limit=limit
        )
        return {"success": True, "jobs": [job.to_dict() for job in jobs], "count": len(jobs)}
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@autonomous_router.get("/autonomous/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict:
    """Get the status and details of a specific background job."""
    try:
        job = await autonomous_agent_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"success": True, "job": job.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@autonomous_router.post("/autonomous/jobs/{job_id}/execute")
async def trigger_job_execution(job_id: str) -> dict:
    """Trigger immediate execution of a background job (async, poll for progress)."""
    try:
        return await autonomous_agent_service.execute_job(job_id)
    except Exception as e:
        logger.error(f"Failed to execute job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@autonomous_router.delete("/autonomous/jobs/{job_id}")
async def cancel_job(job_id: str) -> dict:
    """Cancel a pending or scheduled background job."""
    try:
        result = await autonomous_agent_service.cancel_job(job_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to cancel job"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@autonomous_router.post("/autonomous/jobs/check-scheduled")
async def check_scheduled_jobs() -> dict:
    """Check for scheduled jobs ready to run and execute them (typically called by cron)."""
    try:
        executed_ids = await autonomous_agent_service.check_and_execute_scheduled_jobs()
        return {"success": True, "executed_jobs": executed_ids, "count": len(executed_ids)}
    except Exception as e:
        logger.error(f"Failed to check scheduled jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Proactive Actions ──────────────────────────────────────────────────────────

@autonomous_router.post("/autonomous/actions")
async def create_proactive_action(request: CreateActionRequest) -> dict:
    """Create a new proactive action suggestion (suggestion, notification, auto_action)."""
    try:
        action = await autonomous_agent_service.create_proactive_action(
            company_id=request.company_id,
            action_type=request.action_type,
            title=request.title,
            description=request.description,
            suggested_action=request.suggested_action,
            priority=request.priority,
            related_job_id=request.related_job_id,
            related_candidate_id=request.related_candidate_id,
            trigger_reason=request.trigger_reason,
            auto_executable=request.auto_executable,
            expires_in_hours=request.expires_in_hours
        )
        return {"success": True, "action": action.to_dict()}
    except Exception as e:
        logger.error(f"Failed to create proactive action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@autonomous_router.get("/autonomous/actions")
async def get_proactive_actions(
    company_id: str = Query(DEFAULT_COMPANY_UUID, description="Company ID"),
    status: str = Query("pending", description="Filter by status"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of actions to return")
) -> dict:
    """Get proactive actions for a company."""
    try:
        if status == "pending":
            actions = await autonomous_agent_service.get_pending_actions(company_id=company_id, limit=limit)
        else:
            actions = await autonomous_agent_service.get_actions_by_status(company_id=company_id, status=status, limit=limit)
        return {"success": True, "actions": [a.to_dict() for a in actions], "count": len(actions)}
    except Exception as e:
        logger.error(f"Failed to get proactive actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@autonomous_router.post("/autonomous/actions/{action_id}/accept")
async def accept_proactive_action(
    action_id: str,
    user_id: str = Query("default_user", description="User ID accepting the action")
) -> dict:
    """Accept a proactive action; if auto-executable it runs immediately."""
    try:
        result = await autonomous_agent_service.accept_action(action_id, user_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to accept action"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to accept action {action_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@autonomous_router.post("/autonomous/actions/{action_id}/reject")
async def reject_proactive_action(
    action_id: str,
    user_id: str = Query("default_user", description="User ID rejecting the action")
) -> dict:
    """Reject a proactive action."""
    try:
        result = await autonomous_agent_service.reject_action(action_id, user_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to reject action"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject action {action_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
