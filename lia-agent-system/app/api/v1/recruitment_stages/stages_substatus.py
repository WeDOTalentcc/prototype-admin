"""
Sub-status CRUD endpoints.
"""
import uuid
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from ._shared import (
    SubStatusCreate,
    assert_resource_ownership,
    get_current_active_user,
    require_admin_or_recruiter,
    get_stage_repo,
    get_sub_status_repo,
    get_user_company_id,
    RecruitmentStageRepository,
    SubStatusRepository,
    User,
)
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recruitment Stages - Sub-statuses"])


@router.get("/stages/{stage_id}/sub-statuses", response_model=None)
async def list_stage_sub_statuses(
    stage_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    include_inactive: bool = Query(default=False, description="Include inactive sub-statuses (for settings view)"),
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List sub-statuses for a specific stage. Use include_inactive=true in settings to show full catalog."""
    try:
        stage = await stage_repo.get_by_id(uuid.UUID(stage_id))
        if not stage:
            raise HTTPException(status_code=404, detail="Stage not found")

        assert_resource_ownership(stage, current_user, "stage")

        sub_statuses = await sub_status_repo.list_for_stage(
            stage.id, include_inactive=include_inactive
        )

        return {
            "stage_id": stage_id,
            "sub_statuses": [s.to_dict() for s in sub_statuses],
            "total": len(sub_statuses)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sub-statuses: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/stages/{stage_id}/sub-statuses", response_model=None)
async def create_sub_status(
    stage_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    sub_status: SubStatusCreate,
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    """Create a new sub-status for a stage. Validates stage ownership."""
    try:
        effective_company_id = get_user_company_id(current_user)

        stage = await stage_repo.get_by_id(uuid.UUID(stage_id))
        if not stage:
            raise HTTPException(status_code=404, detail="Stage not found")

        assert_resource_ownership(stage, current_user, "stage")

        new_sub = await sub_status_repo.create({
            "stage_id": uuid.UUID(stage_id),
            "company_id": effective_company_id,
            **sub_status.model_dump()
        })

        return new_sub.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sub-status: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.put("/sub-statuses/{sub_status_id}", response_model=None)
async def update_sub_status(
    sub_status_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    sub_status: SubStatusCreate,
    current_user: User = Depends(require_admin_or_recruiter),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update a sub-status. Validates resource ownership."""
    try:
        existing = await sub_status_repo.get_by_id(uuid.UUID(sub_status_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Sub-status not found")

        assert_resource_ownership(existing, current_user, "sub-status")

        updated = await sub_status_repo.update(
            uuid.UUID(sub_status_id),
            sub_status.model_dump(exclude_unset=True)
        )

        return updated.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sub-status: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.patch("/sub-statuses/{sub_status_id}", response_model=None)
async def patch_sub_status(
    sub_status_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: dict = Body(...),
    current_user: User = Depends(require_admin_or_recruiter),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Partially update a sub-status (e.g., toggle is_active or is_default). All fields optional."""
    try:
        existing = await sub_status_repo.get_by_id(uuid.UUID(sub_status_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Sub-status not found")

        assert_resource_ownership(existing, current_user, "sub-status")

        allowed = {"is_active", "is_default", "is_waiting", "waiting_for", "sla_hours", "color", "icon"}
        updated = await sub_status_repo.patch(uuid.UUID(sub_status_id), allowed, payload)

        return updated.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching sub-status: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.delete("/sub-statuses/{sub_status_id}", response_model=None)
async def delete_sub_status(
    sub_status_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(require_admin_or_recruiter),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Delete a sub-status (soft delete). Validates resource ownership."""
    try:
        existing = await sub_status_repo.get_by_id(uuid.UUID(sub_status_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Sub-status not found")

        assert_resource_ownership(existing, current_user, "sub-status")

        await sub_status_repo.soft_delete(uuid.UUID(sub_status_id))

        return {"success": True, "deleted": sub_status_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sub-status: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")
