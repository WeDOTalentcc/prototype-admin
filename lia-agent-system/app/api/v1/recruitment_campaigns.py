"""
Recruitment Campaigns API endpoints.

Module not yet implemented — returns explicit 501 responses so consumers
know the feature is pending rather than silently receiving empty data.
"""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruitment_campaigns", tags=["Recruitment Campaigns"])

_NOT_IMPLEMENTED = {
    "status": "not_implemented",
    "message": "Recruitment campaigns module is not yet available. This feature is under development and will be connected to the Rails ATS integration.",
    "documentation": "https://docs.wedotalent.cc/roadmap#recruitment-campaigns",
}


@router.get("")
async def list_campaigns(
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user_or_demo),
):
    return {
        **_NOT_IMPLEMENTED,
        "data": [],
        "total": 0,
        "status_filter": status,
    }


@router.post("", status_code=501)
async def create_campaign(
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
):
    from app.services.quota_enforcement import enforce_quota
    await enforce_quota("campaigns", current_user.company_id, db)
    return _NOT_IMPLEMENTED


@router.get("/{campaign_id}", status_code=501)
async def get_campaign(
    campaign_id: _DualId,
    current_user: User = Depends(get_current_user_or_demo),
):
    return _NOT_IMPLEMENTED


@router.patch("/{campaign_id}", status_code=501)
async def update_campaign(
    campaign_id: _DualId,
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user_or_demo),
):
    return _NOT_IMPLEMENTED


@router.post("/{campaign_id}/advance-stage", status_code=501)
async def advance_stage(
    campaign_id: _DualId,
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
):
    return _NOT_IMPLEMENTED


@router.post("/{campaign_id}/complete-stage", status_code=501)
async def complete_stage(
    campaign_id: _DualId,
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
):
    return _NOT_IMPLEMENTED


@router.post("/{campaign_id}/add-checkpoint", status_code=501)
async def add_checkpoint(
    campaign_id: _DualId,
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
):
    return _NOT_IMPLEMENTED

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
