"""
Wizard Analytics API endpoints.

Provides REST endpoints for:
- Session tracking
- Performance metrics
- Dashboard data
"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.domains.analytics.services.wizard_analytics_service import wizard_analytics_service

router = APIRouter(prefix="/wizard-analytics", tags=["Wizard Analytics"])
logger = logging.getLogger(__name__)


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
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class SuggestionTrackRequest(BaseModel):
    """Request to track suggestion."""
    session_id: str
    suggestion_type: str
    accepted: bool


class CompleteSessionRequest(BaseModel):
    """Request to complete a session."""
    session_id: str
    job_id: Optional[str] = None


@router.post("/session/start")
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


@router.post("/session/stage")
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


@router.post("/session/field")
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


@router.post("/session/suggestion")
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


@router.post("/session/complete")
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


@router.get("/metrics/{company_id}")
async def get_company_metrics(
    company_id: str,
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


@router.get("/metrics/{company_id}/recruiter/{recruiter_id}")
async def get_recruiter_metrics(
    company_id: str,
    recruiter_id: str,
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


@router.get("/stages/{company_id}")
async def get_stage_breakdown(
    company_id: str,
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


@router.get("/suggestions/{company_id}")
async def get_suggestion_effectiveness(
    company_id: str,
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


@router.get("/kpis")
async def get_kpi_summary():
    """Get KPI summary for dashboard."""
    return wizard_analytics_service.get_kpi_summary()


@router.get("/dashboard/{company_id}")
async def get_dashboard_data(
    company_id: str,
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
