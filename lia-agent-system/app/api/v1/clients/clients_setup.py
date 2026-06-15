"""
Client setup endpoints: get setup status, update setup section progress.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ._shared import (
    ClientAccountRepository,
    _get_client_checked,
    get_client_repo,
    get_user_from_headers,
    logger,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter()

DEFAULT_SETUP_SECTIONS = [
    {"id": "company-profile", "title": "Perfil da Empresa", "description": "Informações básicas, logo, missão e valores", "status": "pending", "progress": 0, "updated_at": None},
    {"id": "benefits", "title": "Benefícios", "description": "Pacote de benefícios oferecidos", "status": "pending", "progress": 0, "updated_at": None},
    {"id": "culture", "title": "Cultura & EVP", "description": "Proposta de valor ao empregado", "status": "pending", "progress": 0, "updated_at": None},
    {"id": "departments", "title": "Departamentos", "description": "Estrutura organizacional", "status": "pending", "progress": 0, "updated_at": None},
    {"id": "documents", "title": "Documentos", "description": "Templates e documentação padrão", "status": "pending", "progress": 0, "updated_at": None},
]

VALID_SECTION_IDS = ["company-profile", "benefits", "culture", "departments", "documents"]
VALID_SECTION_STATUSES = ["complete", "partial", "pending"]


class SetupSectionUpdate(WeDoBaseModel):
    """Request model for updating a setup section."""
    status: str | None = Field(None, description="Section status: complete, partial, pending")
    progress: int | None = Field(None, ge=0, le=100)


@router.get("/{client_id}/setup", summary="Get client setup status", response_model=None)
async def get_client_setup(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get setup status for a specific client."""
    try:
        client = await _get_client_checked(client_id, current_user, repo)
        settings = client.settings or {}
        setup_sections = settings.get("setup_sections") or [s.copy() for s in DEFAULT_SETUP_SECTIONS]
        return {"success": True, "data": {"client_id": str(client.id), "sections": setup_sections}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client setup: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{client_id}/setup/{section_id}", summary="Update setup section progress", response_model=None)
async def update_client_setup_section(
    client_id: str,
    section_id: str,
    data: SetupSectionUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update progress for a specific setup section."""
    try:
        if section_id not in VALID_SECTION_IDS:
            raise HTTPException(status_code=400, detail=f"Invalid section ID. Must be one of: {', '.join(VALID_SECTION_IDS)}")
        if data.status and data.status not in VALID_SECTION_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_SECTION_STATUSES)}")

        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        try:
            client_uuid = UUID(client_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid client ID format")
        client = await repo.get_by_id(client_uuid)
        if not client:
            raise HTTPException(status_code=404, detail=f"Client not found: {client_id}")
        if not is_admin and str(client.id) != user_company_id:
            raise HTTPException(status_code=403, detail="Access denied to update this client")

        settings = client.settings or {}
        setup_sections = settings.get("setup_sections") or [s.copy() for s in DEFAULT_SETUP_SECTIONS]
        section_index = next((i for i, s in enumerate(setup_sections) if s.get("id") == section_id), None)
        if section_index is None:
            raise HTTPException(status_code=404, detail=f"Section not found: {section_id}")

        section = setup_sections[section_index]
        now = datetime.utcnow()
        if data.status is not None:
            section["status"] = data.status
        if data.progress is not None:
            section["progress"] = data.progress
            if data.progress == 100:
                section["status"] = "complete"
            elif data.progress > 0:
                section["status"] = "partial"
            else:
                section["status"] = "pending"
        section["updated_at"] = now.isoformat()
        setup_sections[section_index] = section
        settings["setup_sections"] = setup_sections
        client.settings = settings
        await repo.save(client)
        logger.info(f"Updated setup section '{section_id}' for client {client_id}: progress={section['progress']}%, status={section['status']}")
        return {
            "success": True, "message": "Setup section updated successfully",
            "data": {"section": section, "all_sections": setup_sections},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating setup section: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
