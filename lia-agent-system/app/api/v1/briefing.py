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
from app.services.briefing_service import briefing_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/briefing", tags=["briefing"])


@router.get("")
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
    """
    try:
        briefing = await briefing_service.generate_daily_briefing(user_id, db)
        return {
            "success": True,
            "data": briefing
        }
    except Exception as e:
        logger.error(f"Error generating briefing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
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
