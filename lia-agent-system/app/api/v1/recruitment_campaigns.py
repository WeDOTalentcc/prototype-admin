"""
Recruitment Campaigns API endpoints.

Stub implementation — returns empty/placeholder data for frontend compatibility.
"""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Any
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruitment_campaigns", tags=["Recruitment Campaigns"])


@router.get("")
async def list_campaigns(
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user_or_demo),
):
    """List recruitment campaigns."""
    return {"data": [], "total": 0, "status_filter": status}


@router.post("", status_code=201)
async def create_campaign(
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user_or_demo),
):
    """Create a recruitment campaign (stub)."""
    return {"data": None, "message": "Recruitment campaigns module not yet implemented"}


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_or_demo),
):
    """Get a single recruitment campaign (stub)."""
    raise HTTPException(status_code=404, detail="Campaign not found")


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user_or_demo),
):
    """Update a recruitment campaign (stub)."""
    raise HTTPException(status_code=404, detail="Campaign not found")


@router.post("/{campaign_id}/advance-stage")
async def advance_stage(
    campaign_id: str,
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
):
    """Advance campaign stage (stub)."""
    raise HTTPException(status_code=404, detail="Campaign not found")


@router.post("/{campaign_id}/complete-stage")
async def complete_stage(
    campaign_id: str,
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
):
    """Complete campaign stage (stub)."""
    raise HTTPException(status_code=404, detail="Campaign not found")


@router.post("/{campaign_id}/add-checkpoint")
async def add_checkpoint(
    campaign_id: str,
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
):
    """Add checkpoint to campaign (stub)."""
    raise HTTPException(status_code=404, detail="Campaign not found")
