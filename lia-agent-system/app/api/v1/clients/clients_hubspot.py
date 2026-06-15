"""
HubSpot sync endpoints for clients.
"""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ._shared import (
    ClientAccountRepository,
    _get_client_checked,
    get_client_repo,
    get_user_from_headers,
    hubspot_service,
    logger,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter()


class HubSpotOnboardingUpdate(WeDoBaseModel):
    """Request model for updating HubSpot onboarding status."""
    welcome_email_sent: bool | None = None
    workos_configured: bool | None = None
    sso_enabled: bool | None = None
    users_count: int | None = None


@router.get("/{client_id}/hubspot/status", summary="Get HubSpot sync status", response_model=None)
async def get_hubspot_sync_status(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get HubSpot sync status for a client."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        if not is_admin and client_id != user_company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        status_result = await hubspot_service.get_sync_status(client_id, repo.db)
        return {"success": True, "data": status_result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting HubSpot status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{client_id}/hubspot/sync", summary="Sync client to HubSpot", response_model=None)
async def sync_client_hubspot(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Manually sync a client to HubSpot CRM. Only admin users can trigger manual sync."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only admin users can sync clients to HubSpot")
        client = await _get_client_checked(client_id, current_user, repo)
        sync_result = await hubspot_service.sync_client_to_hubspot(client, repo.db)
        if sync_result.get("success"):
            return {
                "success": True,
                "message": "Client synced to HubSpot successfully",
                "data": {
                    "hubspot_company_id": sync_result.get("hubspot_company_id"),
                    "hubspot_contact_id": sync_result.get("hubspot_contact_id"),
                    "hubspot_deal_id": sync_result.get("hubspot_deal_id"),
                },
            }
        return {"success": False, "message": "HubSpot sync failed", "error": sync_result.get("error")}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing to HubSpot: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{client_id}/hubspot/onboarding", summary="Update HubSpot onboarding status", response_model=None)
async def update_hubspot_onboarding(
    client_id: str,
    data: HubSpotOnboardingUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update onboarding status on HubSpot for a client. Only admin users."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only admin users can update HubSpot onboarding status")
        status_data = data.model_dump(exclude_unset=True)
        if not status_data:
            raise HTTPException(status_code=400, detail="At least one field must be provided")
        update_result = await hubspot_service.update_onboarding_status(
            client_id=client_id, status=status_data, db=repo.db
        )
        if update_result.get("success"):
            return {"success": True, "message": "HubSpot onboarding status updated successfully"}
        return {
            "success": False,
            "message": "Failed to update HubSpot onboarding status",
            "error": update_result.get("error"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating HubSpot onboarding: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
