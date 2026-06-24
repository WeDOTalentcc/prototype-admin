"""
Client automation endpoints: list, create, update, delete, toggle.
"""
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ._shared import (
    ClientAccount,
    ClientAccountRepository,
    _get_client_checked,
    get_client_repo,
    get_user_from_headers,
    logger,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.shared.errors import LIAError

router = APIRouter()


# DUPLICATE_OF_INTENT: app/api/v1/recruitment_journey.py:98 — clients-domain automation create (simpler trigger/action shape); canonical is recruitment_journey (Sprint Q.4: M-bucket pending domain reconciliation)
class AutomationCreate(WeDoBaseModel):
    """Request model for creating an automation."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    trigger: str = Field(..., description="Trigger type: screening_reminder, interview_completed, offer_sent, etc")
    action: str = Field(..., description="Action type: send_email, send_whatsapp, send_notification, webhook")
    is_active: bool = Field(default=True)
    config: dict[str, Any] | None = Field(None)


# DUPLICATE_OF_INTENT: app/api/v1/recruitment_journey.py:108 — clients-domain automation update (couples with AutomationCreate above)
class AutomationUpdate(WeDoBaseModel):
    """Request model for updating an automation."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    trigger: str | None = None
    action: str | None = None
    is_active: bool | None = None
    config: dict[str, Any] | None = None


async def _get_client_for_automations(
    client_id: str, current_user: dict[str, Any], repo: ClientAccountRepository
) -> ClientAccount:
    return await _get_client_checked(client_id, current_user, repo)


@router.get("/{client_id}/automations", summary="List client automations", response_model=None)
async def list_client_automations(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all automations for a specific client."""
    try:
        client = await _get_client_for_automations(client_id, current_user, repo)
        settings = client.settings or {}
        automations = settings.get("automations", [])
        logger.info(f"Listed {len(automations)} automations for client {client_id}")
        return {"success": True, "data": {"automations": automations, "total": len(automations)}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing automations: {str(e)}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/{client_id}/automations", status_code=201, summary="Create automation", response_model=None)
async def create_client_automation(
    client_id: str,
    data: AutomationCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new automation for a client."""
    try:
        client = await _get_client_for_automations(client_id, current_user, repo)
        settings = client.settings or {}
        automations = settings.get("automations", [])
        now = datetime.utcnow()
        new_automation = {
            "id": str(uuid.uuid4()), "name": data.name, "description": data.description or "",
            "trigger": data.trigger, "action": data.action, "is_active": data.is_active,
            "trigger_count": 0, "config": data.config or {},
            "created_at": now.isoformat(), "updated_at": now.isoformat(),
        }
        automations.append(new_automation)
        settings["automations"] = automations
        client.settings = settings
        await repo.save(client)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created automation '{data.name}' for client {client_id}")
        return {"success": True, "message": "Automation created successfully", "data": new_automation}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating automation: {str(e)}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.put("/{client_id}/automations/{automation_id}", summary="Update automation", response_model=None)
async def update_client_automation(
    client_id: str,
    automation_id: str,
    data: AutomationUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update an existing automation."""
    try:
        client = await _get_client_for_automations(client_id, current_user, repo)
        settings = client.settings or {}
        automations = settings.get("automations", [])
        automation_index = next((i for i, a in enumerate(automations) if a.get("id") == automation_id), None)
        if automation_index is None:
            raise HTTPException(status_code=404, detail=f"Automation not found: {automation_id}")
        automation = automations[automation_index]
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            automation[field] = value
        automation["updated_at"] = datetime.utcnow().isoformat()
        automations[automation_index] = automation
        settings["automations"] = automations
        client.settings = settings
        await repo.save(client)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Updated automation '{automation.get('name')}' for client {client_id}")
        return {"success": True, "message": "Automation updated successfully", "data": automation}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating automation: {str(e)}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.delete("/{client_id}/automations/{automation_id}", summary="Delete automation", response_model=None)
async def delete_client_automation(
    client_id: str,
    automation_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Delete an automation."""
    try:
        client = await _get_client_for_automations(client_id, current_user, repo)
        settings = client.settings or {}
        automations = settings.get("automations", [])
        original_count = len(automations)
        automations = [a for a in automations if a.get("id") != automation_id]
        if len(automations) == original_count:
            raise HTTPException(status_code=404, detail=f"Automation not found: {automation_id}")
        settings["automations"] = automations
        client.settings = settings
        await repo.save(client)
        logger.info(f"Deleted automation {automation_id} for client {client_id}")
        return {"success": True, "message": "Automation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting automation: {str(e)}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.patch("/{client_id}/automations/{automation_id}/toggle", summary="Toggle automation active state", response_model=None)
async def toggle_client_automation(
    client_id: str,
    automation_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Toggle the is_active state of an automation."""
    try:
        client = await _get_client_for_automations(client_id, current_user, repo)
        settings = client.settings or {}
        automations = settings.get("automations", [])
        automation_index = next((i for i, a in enumerate(automations) if a.get("id") == automation_id), None)
        if automation_index is None:
            raise HTTPException(status_code=404, detail=f"Automation not found: {automation_id}")
        automation = automations[automation_index]
        automation["is_active"] = not automation.get("is_active", False)
        automation["updated_at"] = datetime.utcnow().isoformat()
        automations[automation_index] = automation
        settings["automations"] = automations
        client.settings = settings
        await repo.save(client)
        status_text = "activated" if automation["is_active"] else "deactivated"
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Automation '{automation.get('name')}' {status_text} for client {client_id}")
        return {"success": True, "message": f"Automation {status_text} successfully", "data": automation}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling automation: {str(e)}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")
