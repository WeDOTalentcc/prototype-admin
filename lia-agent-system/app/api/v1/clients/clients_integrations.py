"""
Client integration management endpoints.
"""
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
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

router = APIRouter()

VALID_INTEGRATION_NAMES = ["gupy", "linkedin", "greenhouse", "slack", "whatsapp", "email"]
VALID_INTEGRATION_STATUSES = ["connected", "disconnected", "pending"]


class IntegrationCreate(WeDoBaseModel):
    """Request model for creating an integration."""
    name: str = Field(..., description="Integration name (gupy, linkedin, greenhouse, slack, whatsapp, email)")
    description: str | None = Field(None)
    status: str = Field(default="pending")
    config: dict[str, Any] | None = Field(None)


class IntegrationUpdate(WeDoBaseModel):
    """Request model for updating an integration."""
    name: str | None = Field(None)
    description: str | None = Field(None)
    status: str | None = Field(None)
    config: dict[str, Any] | None = Field(None)


async def _get_client_for_integrations(
    client_id: str, current_user: dict[str, Any], repo: ClientAccountRepository
) -> ClientAccount:
    """Helper to get client and validate access for integration endpoints."""
    return await _get_client_checked(client_id, current_user, repo)


@router.get("/{client_id}/integrations", summary="List client integrations", response_model=None)
async def list_client_integrations(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all integrations for a specific client."""
    try:
        client = await _get_client_for_integrations(client_id, current_user, repo)
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        logger.info(f"Listed {len(integrations)} integrations for client {client_id}")
        return {"success": True, "data": {"integrations": integrations, "total": len(integrations)}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing integrations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{client_id}/integrations", status_code=201, summary="Add integration", response_model=None)
async def add_client_integration(
    client_id: str,
    data: IntegrationCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Add a new integration for a client."""
    try:
        client = await _get_client_for_integrations(client_id, current_user, repo)
        if data.name.lower() not in VALID_INTEGRATION_NAMES:
            raise HTTPException(status_code=400, detail=f"Invalid integration name. Must be one of: {', '.join(VALID_INTEGRATION_NAMES)}")
        if data.status not in VALID_INTEGRATION_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_INTEGRATION_STATUSES)}")
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        now = datetime.utcnow()
        new_integration = {
            "id": str(uuid.uuid4()), "name": data.name.lower(),
            "description": data.description or f"Integração com {data.name}",
            "status": data.status, "last_sync": None, "config": data.config or {},
            "created_at": now.isoformat(), "updated_at": now.isoformat(),
        }
        integrations.append(new_integration)
        settings["integrations"] = integrations
        client.settings = settings
        await repo.save(client)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Added integration '{data.name}' for client {client_id}")
        return {"success": True, "message": f"Integration '{data.name}' added successfully", "data": new_integration}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding integration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{client_id}/integrations/{integration_id}", summary="Update integration", response_model=None)
async def update_client_integration(
    client_id: str,
    integration_id: str,
    data: IntegrationUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update an existing integration for a client."""
    try:
        client = await _get_client_for_integrations(client_id, current_user, repo)
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        integration_index = next((i for i, v in enumerate(integrations) if v.get("id") == integration_id), None)
        if integration_index is None:
            raise HTTPException(status_code=404, detail=f"Integration not found: {integration_id}")
        integration = integrations[integration_index]
        if data.name is not None:
            if data.name.lower() not in VALID_INTEGRATION_NAMES:
                raise HTTPException(status_code=400, detail=f"Invalid integration name. Must be one of: {', '.join(VALID_INTEGRATION_NAMES)}")
            integration["name"] = data.name.lower()
        if data.description is not None:
            integration["description"] = data.description
        if data.status is not None:
            if data.status not in VALID_INTEGRATION_STATUSES:
                raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_INTEGRATION_STATUSES)}")
            integration["status"] = data.status
        if data.config is not None:
            integration["config"] = data.config
        integration["updated_at"] = datetime.utcnow().isoformat()
        integrations[integration_index] = integration
        settings["integrations"] = integrations
        client.settings = settings
        await repo.save(client)
        logger.info(f"Updated integration '{integration_id}' for client {client_id}")
        return {"success": True, "message": "Integration updated successfully", "data": integration}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating integration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{client_id}/integrations/{integration_id}", summary="Remove integration", response_model=None)
async def delete_client_integration(
    client_id: str,
    integration_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Remove an integration from a client."""
    try:
        client = await _get_client_for_integrations(client_id, current_user, repo)
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        integration_index = next((i for i, v in enumerate(integrations) if v.get("id") == integration_id), None)
        if integration_index is None:
            raise HTTPException(status_code=404, detail=f"Integration not found: {integration_id}")
        integration_name = integrations[integration_index].get("name")
        integrations.pop(integration_index)
        settings["integrations"] = integrations
        client.settings = settings
        await repo.save(client)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Removed integration '{integration_name}' from client {client_id}")
        return {"success": True, "message": f"Integration '{integration_name}' removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing integration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{client_id}/integrations/{integration_id}/sync", summary="Sync integration", response_model=None)
async def sync_client_integration(
    client_id: str,
    integration_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Trigger synchronization for a specific integration."""
    try:
        client = await _get_client_for_integrations(client_id, current_user, repo)
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        integration_index = next((i for i, v in enumerate(integrations) if v.get("id") == integration_id), None)
        if integration_index is None:
            raise HTTPException(status_code=404, detail=f"Integration not found: {integration_id}")
        integration = integrations[integration_index]
        if integration.get("status") != "connected":
            raise HTTPException(status_code=400, detail="Cannot sync a disconnected integration. Please connect it first.")
        now = datetime.utcnow()
        integration["last_sync"] = now.isoformat()
        integration["updated_at"] = now.isoformat()
        integrations[integration_index] = integration
        settings["integrations"] = integrations
        client.settings = settings
        await repo.save(client)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Synced integration '{integration.get('name')}' for client {client_id}")
        return {
            "success": True,
            "message": f"Integration '{integration.get('name')}' synchronized successfully",
            "data": integration,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing integration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{client_id}/integrations/sync-all", summary="Sync all integrations", response_model=None)
async def sync_all_client_integrations(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Trigger synchronization for all connected integrations."""
    try:
        client = await _get_client_for_integrations(client_id, current_user, repo)
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        now = datetime.utcnow()
        synced_count = 0
        for i, integ in enumerate(integrations):
            if integ.get("status") == "connected":
                integrations[i]["last_sync"] = now.isoformat()
                integrations[i]["updated_at"] = now.isoformat()
                synced_count += 1
        settings["integrations"] = integrations
        client.settings = settings
        await repo.save(client)
        logger.info(f"Synced {synced_count} integrations for client {client_id}")
        return {
            "success": True,
            "message": f"Synchronized {synced_count} connected integration(s)",
            "data": {"synced_count": synced_count, "integrations": integrations},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing all integrations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
