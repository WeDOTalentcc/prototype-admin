"""
Activity Feed API Endpoints

Handles activity feed retrieval for the recruitment system.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.domains.analytics.services.activity_service import ActivityService, get_activity_service
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=None)
async def list_activities(
    activity_type: str | None = Query(None, description="Filter by activity type (voice_screening, email_sent, etc.)"),
    priority: str | None = Query(None, description="Filter by priority (urgent, normal, low)"),
    category: str | None = Query(None, description="Filter by category (screening, hiring, communication, testing)"),
    candidate_id: str | None = Query(None, description="Filter by candidate ID (shows activities related to this candidate)"),
    limit: int = Query(50, ge=1, le=200, description="Max number of results (default: 50, max: 200)"),
    offset: int = Query(0, ge=0, description="Offset for pagination (default: 0)"),
    activity_svc: ActivityService = Depends(get_activity_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List activities with optional filters.
    
    Used in:
    - Painel de Controle → Tab "Histórico" (general feed, no candidate_id)
    - Candidate Preview → Tab "Atividades" (filtered by candidate_id)
    
    Examples:
    - GET /activities?limit=20 (general feed)
    - GET /activities?candidate_id=cand_123 (candidate-specific feed)
    - GET /activities?priority=urgent (urgent items only, for badge)
    - GET /activities?activity_type=voice_screening&limit=10 (voice screenings only)
    """
    try:
        result = await activity_svc.list_activities(
            activity_type=activity_type,
            priority=priority,
            category=category,
            candidate_id=candidate_id,
            limit=limit,
            offset=offset,
        )
        
        logger.info(f"📋 Listed {len(result['activities'])} activities (total: {result['total']})")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error listing activities: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list activities: {str(e)}"
        )


@router.get("/urgent/count", response_model=None)
async def get_urgent_count(
    user_id: str | None = Query(None, description="Optional user_id to filter visible activities"),
    activity_svc: ActivityService = Depends(get_activity_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get count of urgent activities.
    
    Used for header notification badge.
    Returns number of urgent unread activities.
    """
    try:
        count = await activity_svc.get_urgent_count(user_id=user_id)
        
        logger.info(f"🔔 {count} urgent activities")
        
        return {
            "count": count,
            "has_urgent": count > 0
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting urgent count: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get urgent count: {str(e)}"
        )


@router.get("/{activity_id}", response_model=None)
async def get_activity(
    activity_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    activity_svc: ActivityService = Depends(get_activity_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get a single activity by ID.
    
    Returns full activity details.
    """
    try:
        activity = await activity_svc.get_activity_by_id(activity_id)
        
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity not found: {activity_id}"
            )
        
        logger.info(f"📋 Retrieved activity: {activity.title}")
        
        return activity.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting activity: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity: {str(e)}"
        )

reorder_collection_before_item(router)
