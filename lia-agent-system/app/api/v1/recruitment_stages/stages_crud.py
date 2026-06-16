"""Recruitment stages CRUD endpoints — multi-tenant."""
from app.middleware.request_id import get_correlation_id
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ._shared import (
    VALID_ACTION_BEHAVIORS,
    STANDARD_STAGE_CATALOG,
    InferBehaviorRequest,
    StageCreate,
    StageUpdate,
    StageConfigUpdate,
    InlineStageEdit,
    StageReorderRequest,
    assert_resource_ownership,
    get_current_active_user,
    get_user_company_id,
    require_admin_or_recruiter,
    get_stage_repo,
    get_sub_status_repo,
    RecruitmentStageRepository,
    SubStatusRepository,
    User,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.compliance.audit_service import AuditService  # P1-W1-05
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recruitment Stages - CRUD"])


@router.get("/stages", response_model=None)
async def list_stages(
    include_inactive: bool = Query(default=False),
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    """
    List all recruitment stages for the authenticated user's company.
    Returns stages with their sub-statuses.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        stages = await stage_repo.list_for_company(
            effective_company_id, include_inactive=include_inactive
        )

        stages_with_substatus = []
        for stage in stages:
            stage_dict = stage.to_dict()
            sub_statuses = await sub_status_repo.list_for_stage(stage.id)
            stage_dict["sub_statuses"] = [s.to_dict() for s in sub_statuses]
            stages_with_substatus.append(stage_dict)

        return {
            "stages": stages_with_substatus,
            "total": len(stages_with_substatus)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing stages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stages", response_model=None)
async def create_stage(
    stage: StageCreate,
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    """Create a new recruitment stage for the authenticated user's company."""
    try:
        effective_company_id = get_user_company_id(current_user)

        existing = await stage_repo.get_by_name(effective_company_id, stage.name)
        if existing:
            raise HTTPException(status_code=400, detail=f"Stage '{stage.name}' already exists")

        if stage.action_behavior not in VALID_ACTION_BEHAVIORS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action_behavior: '{stage.action_behavior}'. Must be one of: {VALID_ACTION_BEHAVIORS}"
            )

        new_stage = await stage_repo.create({
            "company_id": effective_company_id,
            **stage.model_dump()
        })

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created stage: {stage.name} for company {effective_company_id}")
        try:
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=effective_company_id, action_type="pipeline_stage_created", actor=str(getattr(current_user, "id", "system")), target_id=str(new_stage.id), target_type="recruitment_stage", metadata={"stage_name": stage.name, "action_behavior": stage.action_behavior})  # P1-W1-05
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return new_stage.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/stages/{stage_id}", response_model=None)
async def update_stage(
    stage_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    stage: StageUpdate,
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update an existing recruitment stage. Validates resource ownership."""
    try:
        existing = await stage_repo.get_by_id(uuid.UUID(stage_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Stage not found")

        assert_resource_ownership(existing, current_user, "stage")

        if stage.action_behavior is not None and stage.action_behavior not in VALID_ACTION_BEHAVIORS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action_behavior: '{stage.action_behavior}'. Must be one of: {VALID_ACTION_BEHAVIORS}"
            )

        update_data = stage.model_dump(exclude_unset=True)
        updated = await stage_repo.update(uuid.UUID(stage_id), update_data)

        try:
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=str(getattr(current_user, "company_id", "")), action_type="pipeline_stage_updated", actor=str(getattr(current_user, "id", "system")), target_id=stage_id, target_type="recruitment_stage", metadata={"updates": list(update_data.keys())})  # P1-W1-05
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return updated.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/stages/{stage_id}", response_model=None)
async def delete_stage(
    stage_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    hard_delete: bool = Query(default=False),
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Delete a recruitment stage. Validates resource ownership.
    By default, soft-deletes (sets is_active=False).
    """
    try:
        existing = await stage_repo.get_by_id(uuid.UUID(stage_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Stage not found")

        assert_resource_ownership(existing, current_user, "stage")

        if existing.is_system:  # type: ignore[truthy-bool]
            raise HTTPException(status_code=400, detail="Cannot delete system stages")

        if hard_delete:
            await stage_repo.delete(uuid.UUID(stage_id))
        else:
            await stage_repo.soft_delete(uuid.UUID(stage_id))

        try:
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=str(getattr(current_user, "company_id", "")), action_type="pipeline_stage_deleted", actor=str(getattr(current_user, "id", "system")), target_id=stage_id, target_type="recruitment_stage", metadata={"hard_delete": hard_delete})  # P1-W1-05
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return {"success": True, "deleted": stage_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/stages/{stage_id}/config", response_model=None)
async def update_stage_config(
    stage_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    config: StageConfigUpdate,
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update stage configuration (action_behavior, default_channel, SLA)."""
    try:
        existing = await stage_repo.get_by_id(uuid.UUID(stage_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Stage not found")

        assert_resource_ownership(existing, current_user, "stage")

        updates = {}
        if config.action_behavior is not None:
            if config.action_behavior not in VALID_ACTION_BEHAVIORS + ["passive"]:
                raise HTTPException(status_code=400, detail=f"Invalid action_behavior: {config.action_behavior}")
            updates["action_behavior"] = config.action_behavior
        if config.default_channel is not None:
            valid_channels = ["email", "whatsapp", "email_whatsapp"]
            if config.default_channel not in valid_channels:
                raise HTTPException(status_code=400, detail=f"Invalid channel: {config.default_channel}")
            updates["default_channel"] = config.default_channel
        if config.sla_hours is not None:
            updates["sla_hours"] = config.sla_hours

        if updates:
            await stage_repo.update_fields_uuid(uuid.UUID(stage_id), updates)
            existing = await stage_repo.get_by_id(uuid.UUID(stage_id))

        return {"success": True, "stage": existing.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/catalog", response_model=None)
async def get_stage_catalog(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get the standard stage catalog for adding new columns."""
    return {"catalog": STANDARD_STAGE_CATALOG, "total": len(STANDARD_STAGE_CATALOG)}


@router.get("/stage-catalog", summary="Get standard stage catalog", response_model=None)
async def get_standard_stage_catalog(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Returns the standard stage catalog with all available pipeline columns.

    Each entry includes:
    - Stage metadata (name, display_name, icon, color)
    - action_behavior (determines what happens on transition)
    - stage_category (system/catalog/custom)
    - default_sub_statuses for the stage
    - Whether it's removable, system-required, initial, or final

    Used by:
    - Menu Configurações to show available stages
    - Pipeline customization in job settings
    - "+" button in Kanban to add new columns
    """
    return {
        "catalog": STANDARD_STAGE_CATALOG,
        "action_behaviors": VALID_ACTION_BEHAVIORS,
        "total": len(STANDARD_STAGE_CATALOG),
    }


@router.get("/defaults", response_model=None)
async def get_defaults(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get default stage configurations.
    Useful for reference and setting up new companies.
    """
    from app.models.recruitment_stages import (
        DEFAULT_RECRUITMENT_STAGES,
        DEFAULT_SUB_STATUSES,
        GUPY_STAGE_MAPPINGS,
        PANDAPE_STAGE_MAPPINGS,
    )
    return {
        "stages": DEFAULT_RECRUITMENT_STAGES,
        "sub_statuses": DEFAULT_SUB_STATUSES,
        "ats_mappings": {
            "gupy": GUPY_STAGE_MAPPINGS,
            "pandape": PANDAPE_STAGE_MAPPINGS
        }
    }


@router.patch("/stages/{stage_id}/inline-edit", response_model=None)
async def inline_edit_stage(
    stage_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: InlineStageEdit,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        stage = await stage_repo.get_by_id_str(stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Stage not found")

        # Onda 4.2b-P0-6 (2026-05-23): cross-tenant ownership check.
        # Antes user empresa A podia editar stage da empresa B.
        if str(getattr(stage, 'company_id', '')) != str(company_id):
            raise HTTPException(status_code=404, detail="Stage not found")

        is_system = bool(stage.is_initial or stage.is_final)  # type: ignore[truthy-bool]
        stage_category = getattr(stage, 'stage_category', 'custom') or 'custom'  # type: ignore[truthy-bool]

        if is_system or stage_category == 'system':
            raise HTTPException(
                status_code=403,
                detail="System stages cannot be edited inline"
            )

        updates = {}
        if payload.display_name is not None:
            updates["display_name"] = payload.display_name
        if payload.is_active is not None:
            updates["is_active"] = payload.is_active
        if payload.sla_hours is not None:
            updates["sla_hours"] = payload.sla_hours
        if payload.stage_order is not None:
            updates["stage_order"] = payload.stage_order

        if not updates:
            return {"success": True, "message": "No changes provided"}

        await stage_repo.update_fields(stage_id, updates)

        try:
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=str(company_id), action_type="pipeline_stage_updated", actor=str(getattr(current_user, "id", "system")), target_id=stage_id, target_type="recruitment_stage", metadata={"inline_edit": True, "updates": list(updates.keys())})  # P1-W1-05
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return {
            "success": True,
            "stage_id": stage_id,
            "updates": updates,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inline editing stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/stages/{stage_id}/remove", response_model=None)
async def remove_custom_stage(
    stage_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        stage = await stage_repo.get_by_id_str(stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Stage not found")

        # Onda 4.2b-P0-7 (2026-05-23): cross-tenant ownership check.
        # Antes user empresa A podia DELETAR (hard) stage da empresa B.
        if str(getattr(stage, 'company_id', '')) != str(company_id):
            raise HTTPException(status_code=404, detail="Stage not found")

        is_system = bool(stage.is_initial or stage.is_final)  # type: ignore[truthy-bool]
        stage_category = getattr(stage, 'stage_category', 'custom') or 'custom'  # type: ignore[truthy-bool]

        if is_system or stage_category == 'system':
            raise HTTPException(status_code=403, detail="System stages cannot be removed")

        if stage_category == 'default':
            raise HTTPException(status_code=403, detail="Default stages cannot be removed, only deactivated")

        await stage_repo.hard_delete_by_id_str(stage_id)

        try:
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=str(company_id), action_type="pipeline_stage_deleted", actor=str(getattr(current_user, "id", "system")), target_id=stage_id, target_type="recruitment_stage", metadata={"hard_delete": True, "custom_remove": True})  # P1-W1-05
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return {"success": True, "stage_id": stage_id, "removed": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stages/reorder", response_model=None)
async def reorder_stages(
    payload: StageReorderRequest,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        # Onda 4.2b-P0-8 (2026-05-23): pre-validar que todos os stage_ids
        # pertencem a empresa do user antes de reordenar. Antes user empresa A
        # podia reordenar stages da empresa B passando os UUIDs.
        company_stages = await stage_repo.list_for_company(company_id)
        company_stage_ids = {str(s.id) for s in company_stages}
        rogue_ids = [
            item.stage_id for item in payload.stages
            if str(item.stage_id) not in company_stage_ids
        ]
        if rogue_ids:
            raise HTTPException(
                status_code=403,
                detail=f"Stage IDs not in your tenant: {rogue_ids[:3]}",
            )

        items = [{"stage_id": item.stage_id, "new_order": item.new_order} for item in payload.stages]
        await stage_repo.reorder(items)
        try:
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=str(company_id), action_type="pipeline_stages_reordered", actor=str(getattr(current_user, "id", "system")), target_type="recruitment_stage", metadata={"reordered_count": len(payload.stages)})  # P1-W1-05
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return {"success": True, "reordered": len(payload.stages)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering stages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stages/infer-behavior", response_model=None)
async def infer_stage_behavior(
    request: InferBehaviorRequest,
    method: str = Query(default="auto", pattern="^(keyword|llm|auto)$"),
    current_user: User = Depends(get_current_active_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Infer action_behavior for a custom stage name."""
    try:
        if method == "keyword":
            from app.domains.communication.services.infer_behavior_service import infer_behavior
            result = infer_behavior(request.stage_name)
        elif method == "llm":
            from app.domains.communication.services.infer_behavior_service import infer_behavior_llm
            result = await infer_behavior_llm(request.stage_name, request.description)
        else:
            from app.domains.communication.services.infer_behavior_service import infer_behavior_auto

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# See: app/domains/integrations_hub/services/rails_adapter.py
            result = await infer_behavior_auto(request.stage_name, request.description)

        return result
    except Exception as e:
        # pii-logs ok: stage_name é identificador de etapa do pipeline (não PII de pessoa)
        logger.error(f"Error inferring behavior for stage \"{request.stage_name}\": {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Falha ao inferir comportamento do estágio. Tente novamente ou selecione manualmente."
        )
