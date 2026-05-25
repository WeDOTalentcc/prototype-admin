"""
Briefing API endpoints.

Provides endpoints for:
- Getting daily briefing
- Refreshing briefing
"""
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from app.shared.observability.canary_metrics import (
    inc_briefing_generated,
    obs_briefing_duration,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.services.briefing_service import briefing_service
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/briefing", tags=["briefing"])


_EMPTY_BRIEFING = {
    "urgent_actions": [],
    "pipeline_summary": {},
    "today_schedule": [],
    "pending_tasks": [],
    "active_alerts": [],
    "insights": [],
}


@router.get("", response_model=None)
async def get_daily_briefing(
    request: Request,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get daily briefing for a user.

    Returns comprehensive briefing including:
    - Urgent actions
    - Pipeline summary
    - Today's schedule
    - Pending tasks
    - Active alerts
    - AI-powered insights

    Safety: para "default_user" (pre-auth / anonymous), retorna briefing vazio
    em vez de 500 — evita o card quebrar enquanto o auth context hidrata no FE.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    if not user_id or user_id == "default_user":
        logger.info(
            "briefing.anonymous_or_default_user",
            extra={"request_id": request_id, "user_id": user_id},
        )
        inc_briefing_generated(company_id or "", "empty_user")
        return {"success": True, "data": _EMPTY_BRIEFING}

    _t0 = time.perf_counter()
    try:
        briefing = await briefing_service.generate_daily_briefing(
            user_id, db, company_id=company_id  # WT-2022 P0.TASK
        )
        _elapsed = time.perf_counter() - _t0
        logger.info(
            "briefing.generated",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "duration_ms": round(_elapsed * 1000, 1),
                "urgent_count": briefing.get("summary", {}).get("urgent_count", 0),
                "alerts_active": briefing.get("summary", {}).get("alerts_active", 0),
            },
        )
        inc_briefing_generated(company_id or "", "success")
        obs_briefing_duration(company_id or "", _elapsed)
        return {
            "success": True,
            "data": briefing
        }
    except HTTPException:
        raise
    except Exception as e:
        _elapsed = time.perf_counter() - _t0
        logger.error(
            "briefing.generate_failed",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "duration_ms": round(_elapsed * 1000, 1),
                "error": e.__class__.__name__,
            },
            exc_info=True,
        )
        inc_briefing_generated(company_id or "", "error")
        obs_briefing_duration(company_id or "", _elapsed)
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao gerar briefing: {e.__class__.__name__}",
        )


@router.post("/refresh", response_model=None)
async def refresh_briefing(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Force refresh the daily briefing.
    """
    try:
        briefing = await briefing_service.generate_daily_briefing(
            user_id, db, company_id=company_id  # WT-2022 P0.TASK
        )
        return {
            "success": True,
            "data": briefing,
            "message": "Briefing atualizado com sucesso"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing briefing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
