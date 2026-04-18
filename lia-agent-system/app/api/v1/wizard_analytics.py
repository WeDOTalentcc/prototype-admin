"""
Wizard Analytics API endpoints.

Provides REST endpoints for:
- Session tracking
- Performance metrics
- Dashboard data
"""
import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.domains.analytics.services.wizard_analytics_service import wizard_analytics_service

# Task #458 — Same routing-shadowing blindagem as /job-vacancies (Task #455):
# every ``{*_id}`` path parameter is constrained to UUID-or-digit, and a
# collection-before-item reorder is enforced at the bottom of the module.
router = APIRouter(prefix="/wizard-analytics", tags=["Wizard Analytics"])
logger = logging.getLogger(__name__)

_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]


class StartSessionRequest(BaseModel):
    """Request to start a wizard session."""
    session_id: str
    company_id: str
    recruiter_id: str


class StageChangeRequest(BaseModel):
    """Request to track stage change."""
    session_id: str
    stage: str


class FieldUpdateRequest(BaseModel):
    """Request to track field update."""
    session_id: str
    field: str
    source: str
    old_value: str | None = None
    new_value: str | None = None


class SuggestionTrackRequest(BaseModel):
    """Request to track suggestion."""
    session_id: str
    suggestion_type: str
    accepted: bool


class CompleteSessionRequest(BaseModel):
    """Request to complete a session."""
    session_id: str
    job_id: str | None = None


@router.post("/session/start", response_model=None)
async def start_session(request: StartSessionRequest):
    """Start tracking a new wizard session."""
    try:
        session = wizard_analytics_service.start_session(
            session_id=request.session_id,
            company_id=request.company_id,
            recruiter_id=request.recruiter_id,
        )
        
        return {
            "success": True,
            "session_id": session.session_id,
            "started_at": session.started_at.isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/stage", response_model=None)
async def track_stage_change(request: StageChangeRequest):
    """Track stage change in session."""
    try:
        wizard_analytics_service.track_stage_change(
            session_id=request.session_id,
            stage=request.stage,
        )
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error tracking stage change: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/field", response_model=None)
async def track_field_update(request: FieldUpdateRequest):
    """Track field update in session."""
    try:
        wizard_analytics_service.track_field_update(
            session_id=request.session_id,
            field=request.field,
            source=request.source,
            old_value=request.old_value,
            new_value=request.new_value,
        )
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error tracking field update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/suggestion", response_model=None)
async def track_suggestion(request: SuggestionTrackRequest):
    """Track suggestion acceptance."""
    try:
        wizard_analytics_service.track_suggestion(
            session_id=request.session_id,
            suggestion_type=request.suggestion_type,
            accepted=request.accepted,
        )
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error tracking suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/complete", response_model=None)
async def complete_session(request: CompleteSessionRequest):
    """Complete session and get metrics."""
    try:
        metrics = await wizard_analytics_service.complete_session(
            session_id=request.session_id,
            job_id=request.job_id,
        )
        
        if metrics is None:
            return {"success": False, "message": "Session not found"}
        
        return {
            "success": True,
            "metrics": metrics,
        }
        
    except Exception as e:
        logger.error(f"Error completing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{company_id}", response_model=None)
async def get_company_metrics(
    company_id: _DualId,
    days: int = Query(30, ge=1, le=365),
):
    """Get aggregated metrics for a company."""
    try:
        metrics = await wizard_analytics_service.get_company_metrics(
            company_id=company_id,
            days=days,
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting company metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{company_id}/recruiter/{recruiter_id}", response_model=None)
async def get_recruiter_metrics(
    company_id: _DualId,
    recruiter_id: _DualId,
    days: int = Query(30, ge=1, le=365),
):
    """Get metrics for a specific recruiter."""
    try:
        metrics = await wizard_analytics_service.get_recruiter_metrics(
            company_id=company_id,
            recruiter_id=recruiter_id,
            days=days,
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting recruiter metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stages/{company_id}", response_model=None)
async def get_stage_breakdown(
    company_id: _DualId,
    days: int = Query(30, ge=1, le=365),
):
    """Get time breakdown by wizard stage."""
    try:
        breakdown = await wizard_analytics_service.get_stage_breakdown(
            company_id=company_id,
            days=days,
        )
        
        return breakdown
        
    except Exception as e:
        logger.error(f"Error getting stage breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{company_id}", response_model=None)
async def get_suggestion_effectiveness(
    company_id: _DualId,
    days: int = Query(30, ge=1, le=365),
):
    """Get effectiveness metrics for LIA suggestions."""
    try:
        effectiveness = await wizard_analytics_service.get_suggestion_effectiveness(
            company_id=company_id,
            days=days,
        )
        
        return effectiveness
        
    except Exception as e:
        logger.error(f"Error getting suggestion effectiveness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpis", response_model=None)
async def get_kpi_summary():
    """Get KPI summary for dashboard."""
    return wizard_analytics_service.get_kpi_summary()


@router.get("/dashboard/{company_id}", response_model=None)
async def get_dashboard_data(
    company_id: _DualId,
    days: int = Query(30, ge=1, le=365),
):
    """Get all dashboard data in a single call."""
    try:
        metrics = await wizard_analytics_service.get_company_metrics(
            company_id=company_id,
            days=days,
        )
        
        stages = await wizard_analytics_service.get_stage_breakdown(
            company_id=company_id,
            days=days,
        )
        
        suggestions = await wizard_analytics_service.get_suggestion_effectiveness(
            company_id=company_id,
            days=days,
        )
        
        kpis = wizard_analytics_service.get_kpi_summary()
        
        return {
            "metrics": metrics,
            "stages": stages,
            "suggestions": suggestions,
            "kpis": kpis,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Routing invariant (Task #458) — collection-scoped routes before item routes.
# ---------------------------------------------------------------------------
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder

_reorder(router)
