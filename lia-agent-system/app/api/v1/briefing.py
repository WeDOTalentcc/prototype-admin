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
from app.auth.dependencies import get_current_user_or_demo, get_user_company_id

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
    current_user=Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily briefing for a user.

    Safety: para "default_user" (pre-auth / anonymous), retorna briefing vazio
    em vez de 500 — evita o card quebrar enquanto o auth context hidrata no FE.
    """
    if not user_id or user_id == "default_user":
        logger.info("briefing.anonymous_or_default_user — returning empty briefing")
        return {"success": True, "data": _EMPTY_BRIEFING}

    try:
        company_id = get_user_company_id(current_user)
        from app.domains.integrations_hub.services.rails_adapter import RailsAdapter
        _adapter = RailsAdapter(db=db)
        briefing = await _adapter.daily_summary(
            company_id=str(company_id or ""),
            user_id=str(user_id),
        )
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
    current_user=Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    Force refresh the daily briefing.
    """
    try:
        company_id = get_user_company_id(current_user)
        from app.domains.integrations_hub.services.rails_adapter import RailsAdapter
        _adapter = RailsAdapter(db=db)
        briefing = await _adapter.daily_summary(
            company_id=str(company_id or ""),
            user_id=str(user_id),
        )
        return {
            "success": True,
            "data": briefing,
            "message": "Briefing atualizado com sucesso"
        }
    except Exception as e:
        logger.error(f"Error refreshing briefing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
