"""
ATS mapping CRUD endpoints.
"""
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ._shared import (
    ATSMappingCreate,
    assert_resource_ownership,
    get_current_active_user,
    get_user_company_id,
    require_admin_or_recruiter,
    get_ats_mapping_repo,
    ATSMappingRepository,
    User,
)
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recruitment Stages - ATS Mappings"])


@router.get("/ats-mappings", response_model=None)
async def list_ats_mappings(
    ats_type: str | None = Query(default=None, description="Filter by ATS type"),
    current_user: User = Depends(get_current_active_user),
    ats_repo: ATSMappingRepository = Depends(get_ats_mapping_repo),
company_id: str = Depends(require_company_id)):
    """List all ATS stage mappings for the authenticated user's company."""
    try:
        effective_company_id = get_user_company_id(current_user)

        mappings = await ats_repo.list_for_company(
            effective_company_id, ats_type=ats_type
        )

        return {
            "mappings": [m.to_dict() for m in mappings],
            "total": len(mappings)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing ATS mappings: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/ats-mappings", response_model=None)
async def create_ats_mapping(
    mapping: ATSMappingCreate,
    current_user: User = Depends(require_admin_or_recruiter),
    ats_repo: ATSMappingRepository = Depends(get_ats_mapping_repo),
company_id: str = Depends(require_company_id)):
    """Create a new ATS stage mapping for the authenticated user's company."""
    try:
        effective_company_id = get_user_company_id(current_user)

        new_mapping = await ats_repo.create({
            "company_id": effective_company_id,
            "wedotalent_stage_id": uuid.UUID(mapping.wedotalent_stage_id),
            "wedotalent_sub_status_id": uuid.UUID(mapping.wedotalent_sub_status_id) if mapping.wedotalent_sub_status_id else None,
            "ats_type": mapping.ats_type,
            "ats_stage_id": mapping.ats_stage_id,
            "ats_stage_name": mapping.ats_stage_name,
            "ats_stage_order": mapping.ats_stage_order,
            "mapping_direction": mapping.mapping_direction,
            "is_default_for_sync": mapping.is_default_for_sync,
            "priority": mapping.priority,
            "notes": mapping.notes,
        })

        return new_mapping.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ATS mapping: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.delete("/ats-mappings/{mapping_id}", response_model=None)
async def delete_ats_mapping(
    mapping_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(require_admin_or_recruiter),
    ats_repo: ATSMappingRepository = Depends(get_ats_mapping_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Delete an ATS mapping. Validates resource ownership."""
    try:
        existing = await ats_repo.get_by_id(uuid.UUID(mapping_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Mapping not found")

        assert_resource_ownership(existing, current_user, "ATS mapping")

        await ats_repo.soft_delete(uuid.UUID(mapping_id))

        return {"success": True, "deleted": mapping_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ATS mapping: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")
