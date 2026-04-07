"""
LIA Assistant — Feature Flags endpoints.

Extracted from lia_assistant.py (Phase 5 decomposition).
All routes share prefix="/lia" to preserve existing /api/v1/lia/feature-flags/* URLs.
"""
import logging
from datetime import datetime as dt
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.shared.governance.feature_flag_service import FeatureFlagService, get_feature_flag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia", tags=["lia-feature-flags"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FeatureFlagRequest(BaseModel):
    flag_key: str
    is_enabled: bool
    company_id: str | None = None
    rollout_percentage: int = 100
    description: str | None = None
    category: str | None = None
    metadata: dict[str, Any] | None = None
    expires_at: str | None = None
    created_by: str | None = None


class FeatureFlagResponse(BaseModel):
    success: bool
    flag_id: str | None = None
    flag_key: str | None = None
    is_enabled: bool | None = None
    company_id: str | None = None
    rollout_percentage: int | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/feature-flags/set", response_model=FeatureFlagResponse)
async def set_feature_flag(
    request: FeatureFlagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    ff_svc: FeatureFlagService = Depends(get_feature_flag_service),
) -> FeatureFlagResponse:
    try:
        expires = None
        if request.expires_at:
            expires = dt.fromisoformat(request.expires_at)

        result = await ff_svc.set_flag(
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


@router.get("/feature-flags", response_model=None)
async def get_feature_flags(
    company_id: str | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    ff_svc: FeatureFlagService = Depends(get_feature_flag_service),
) -> dict[str, Any]:
    try:
        flags = await ff_svc.get_all_flags(
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


@router.get("/feature-flags/check/{flag_key}", response_model=None)
async def check_feature_flag(
    flag_key: str,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    ff_svc: FeatureFlagService = Depends(get_feature_flag_service),
) -> dict[str, Any]:
    try:
        is_enabled = await ff_svc.is_enabled(
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
