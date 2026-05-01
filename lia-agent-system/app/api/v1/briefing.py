"""
Briefing API endpoints.

Provides endpoints for:
- Getting daily briefing
- Refreshing briefing
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.services.briefing_service import briefing_service

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
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
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
    if not user_id or user_id == "default_user":
        logger.info("briefing.anonymous_or_default_user — returning empty briefing")
        return {"success": True, "data": _EMPTY_BRIEFING}

    try:
        briefing = await briefing_service.generate_daily_briefing(user_id, db)
        return {
            "success": True,
            "data": briefing
        }
    except Exception as e:
        logger.error("briefing.generate_failed user_id=%s error=%s", user_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao gerar briefing: {e.__class__.__name__}",
        )


@router.post("/refresh", response_model=None)
async def refresh_briefing(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """
    Force refresh the daily briefing.
    """
    try:
        briefing = await briefing_service.generate_daily_briefing(user_id, db)
        return {
            "success": True,
            "data": briefing,
            "message": "Briefing atualizado com sucesso"
        }
    except Exception as e:
        logger.error(f"Error refreshing briefing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
