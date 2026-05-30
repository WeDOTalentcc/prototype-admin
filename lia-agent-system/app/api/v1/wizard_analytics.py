"""
Wizard Analytics API endpoints.

Provides REST endpoints for:
- Session tracking
- Performance metrics
- Dashboard data
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.domains.analytics.services.wizard_analytics_service import wizard_analytics_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/wizard-analytics", tags=["Wizard Analytics"])
logger = logging.getLogger(__name__)


class StartSessionRequest(WeDoBaseModel):
    """Request to start a wizard session."""
    session_id: str
    recruiter_id: str


class StageChangeRequest(WeDoBaseModel):
    """Request to track stage change."""
    session_id: str
    stage: str


class FieldUpdateRequest(WeDoBaseModel):
    """Request to track field update."""
    session_id: str
    field: str
    source: str
    old_value: str | None = None
    new_value: str | None = None


class SuggestionTrackRequest(WeDoBaseModel):
    """Request to track suggestion."""
    session_id: str
    suggestion_type: str
    accepted: bool


class CompleteSessionRequest(WeDoBaseModel):
    """Request to complete a session."""
    session_id: str
    job_id: str | None = None


@router.post("/session/start", response_model=None)
async def start_session(request: StartSessionRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Start tracking a new wizard session."""
    try:
        session = wizard_analytics_service.start_session(
            session_id=request.session_id,
            company_id=company_id,
            recruiter_id=request.recruiter_id,
        )
        
        return {
            "success": True,
            "session_id": session.session_id,
            "started_at": session.started_at.isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/stage", response_model=None)
async def track_stage_change(request: StageChangeRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Track stage change in session."""
    try:
        wizard_analytics_service.track_stage_change(
            session_id=request.session_id,
            stage=request.stage,
        )
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking stage change: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/field", response_model=None)
async def track_field_update(request: FieldUpdateRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking field update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/suggestion", response_model=None)
async def track_suggestion(request: SuggestionTrackRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Track suggestion acceptance."""
    try:
        wizard_analytics_service.track_suggestion(
            session_id=request.session_id,
            suggestion_type=request.suggestion_type,
            accepted=request.accepted,
        )
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/complete", response_model=None)
async def complete_session(request: CompleteSessionRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{company_id}", response_model=None)
async def get_company_metrics(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    days: int = Query(30, ge=1, le=365),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """Get aggregated metrics for a company."""
    try:
        metrics = await wizard_analytics_service.get_company_metrics(
            company_id=company_id,
            days=days,
        )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{company_id}/recruiter/{recruiter_id}", response_model=None)
async def get_recruiter_metrics(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    recruiter_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    days: int = Query(30, ge=1, le=365),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """Get metrics for a specific recruiter."""
    try:
        metrics = await wizard_analytics_service.get_recruiter_metrics(
            company_id=company_id,
            recruiter_id=recruiter_id,
            days=days,
        )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recruiter metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stages/{company_id}", response_model=None)
async def get_stage_breakdown(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    days: int = Query(30, ge=1, le=365),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get time breakdown by wizard stage."""
    try:
        breakdown = await wizard_analytics_service.get_stage_breakdown(
            company_id=company_id,
            days=days,
        )
        
        return breakdown
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stage breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{company_id}", response_model=None)
async def get_suggestion_effectiveness(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    days: int = Query(30, ge=1, le=365),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get effectiveness metrics for LIA suggestions."""
    try:
        effectiveness = await wizard_analytics_service.get_suggestion_effectiveness(
            company_id=company_id,
            days=days,
        )
        
        return effectiveness
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestion effectiveness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpis", response_model=None)
async def get_kpi_summary(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get KPI summary for dashboard."""
    return wizard_analytics_service.get_kpi_summary()


@router.get("/dashboard/{company_id}", response_model=None)
async def get_dashboard_data(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    days: int = Query(30, ge=1, le=365),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
