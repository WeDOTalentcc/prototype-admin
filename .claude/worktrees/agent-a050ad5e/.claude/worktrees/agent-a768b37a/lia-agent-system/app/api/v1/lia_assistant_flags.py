"""
LIA Assistant — Feature Flags endpoints.

Extracted from lia_assistant.py (Phase 5 decomposition).
All routes share prefix="/lia" to preserve existing /api/v1/lia/feature-flags/* URLs.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from datetime import datetime as dt
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia", tags=["lia-feature-flags"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FeatureFlagRequest(BaseModel):
    flag_key: str
    is_enabled: bool
    company_id: Optional[str] = None
    rollout_percentage: int = 100
    description: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_at: Optional[str] = None
    created_by: Optional[str] = None


class FeatureFlagResponse(BaseModel):
    success: bool
    flag_id: Optional[str] = None
    flag_key: Optional[str] = None
    is_enabled: Optional[bool] = None
    company_id: Optional[str] = None
    rollout_percentage: Optional[int] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/feature-flags/set", response_model=FeatureFlagResponse)
async def set_feature_flag(
    request: FeatureFlagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> FeatureFlagResponse:
    try:
        from app.services.feature_flag_service import feature_flag_service

        expires = None
        if request.expires_at:
            expires = dt.fromisoformat(request.expires_at)

        result = await feature_flag_service.set_flag(
            db=db,
            flag_key=request.flag_key,
            is_enabled=request.is_enabled,
            company_id=request.company_id,
            rollout_percentage=request.rollout_percentage,
            description=request.description,
            category=request.category,
            metadata=request.metadata,
            expires_at=expires,
            created_by=request.created_by
        )
        return FeatureFlagResponse(
            success=result.get("success", False),
            flag_id=result.get("flag_id"),
            flag_key=result.get("flag_key"),
            is_enabled=result.get("is_enabled"),
            company_id=result.get("company_id"),
            rollout_percentage=result.get("rollout_percentage"),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Error setting feature flag: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-flags")
async def get_feature_flags(
    company_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> Dict[str, Any]:
    try:
        from app.services.feature_flag_service import feature_flag_service

        flags = await feature_flag_service.get_all_flags(
            db=db,
            company_id=company_id,
            category=category
        )
        return {
            "flags": flags,
            "total": len(flags),
            "company_id": company_id,
            "category": category
        }
    except Exception as e:
        logger.error(f"Error getting feature flags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-flags/check/{flag_key}")
async def check_feature_flag(
    flag_key: str,
    company_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> Dict[str, Any]:
    try:
        from app.services.feature_flag_service import feature_flag_service

        is_enabled = await feature_flag_service.is_enabled(
            db=db,
            flag_key=flag_key,
            company_id=company_id
        )
        return {
            "flag_key": flag_key,
            "is_enabled": is_enabled,
            "company_id": company_id
        }
    except Exception as e:
        logger.error(f"Error checking feature flag: {e}")
        raise HTTPException(status_code=500, detail=str(e))
