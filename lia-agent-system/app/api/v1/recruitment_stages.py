"""
Recruitment Stages API - Manage pipeline stages, sub-statuses, and ATS mappings.

Admin > Jornada de Recrutamento

SECURITY: All endpoints require authentication via JWT token.
Company scoping is enforced server-side based on authenticated user context.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from app.auth.dependencies import (
    assert_resource_ownership,
    get_current_active_user,
    get_current_user_or_demo,
    get_user_company_id,
    require_admin_or_recruiter,
)
from app.auth.models import User
from app.core.config import settings
from app.domains.communication.services.return_event_service import (
    RETURN_EVENT_CONFIG,
    ReturnEventService,
)
from app.domains.recruiter_assistant.services.pipeline_stage_service import TransitionError, pipeline_stage_service
from app.domains.recruitment.dependencies import (
    get_ats_mapping_repo,
    get_screening_question_repo,
    get_stage_repo,
    get_sub_status_repo,
)
from app.domains.recruitment.repositories.ats_mapping_repository import ATSMappingRepository
from app.domains.recruitment.repositories.recruitment_stage_repository import RecruitmentStageRepository
from app.domains.recruitment.repositories.screening_question_repository import ScreeningQuestionRepository
from app.domains.recruitment.repositories.sub_status_repository import SubStatusRepository
from app.models.recruitment_stages import (
    CANONICAL_SUB_STATUSES,
    DEFAULT_RECRUITMENT_STAGES,
    DEFAULT_SUB_STATUSES,
    GUPY_STAGE_MAPPINGS,
    PANDAPE_STAGE_MAPPINGS,
    STANDARD_STAGE_CATALOG,
    RecruitmentStage,
    ScreeningQuestion,
)

logger = logging.getLogger(__name__)

VALID_ACTION_BEHAVIORS = [
    "intake", "screening", "scheduling", "evaluation", "verification",
    "offer", "passive", "conclusion_hired", "conclusion_rejected", "conclusion_declined"
]

router = APIRouter()


class StageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    stage_order: int = Field(default=0, ge=0)
    color: str | None = Field(default="#6B7280", max_length=20)
    icon: str | None = Field(default="circle", max_length=50)
    stage_type: str = Field(default="active")
    is_initial: bool = False
    is_final: bool = False
    is_rejection: bool = False
    is_hired: bool = False
    allowed_transitions: list[str] = Field(default_factory=list)
    sla_hours: int | None = None
    action_behavior: str = Field(default="passive", description="Action behavior type for this stage")


class StageConfigUpdate(BaseModel):
    action_behavior: str | None = Field(None, description="Tipo de ação (screening, scheduling, evaluation, verification, offer, passive, etc.)")
    default_channel: str | None = Field(None, description="Canal padrão (email, whatsapp, email_whatsapp)")
    sla_hours: int | None = Field(None, description="SLA em horas")


class StageUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    stage_order: int | None = None
    color: str | None = None
    icon: str | None = None
    allowed_transitions: list[str] | None = None
    sla_hours: int | None = None
    is_active: bool | None = None
    action_behavior: str | None = None


class SubStatusCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    sub_status_order: int = Field(default=0, ge=0)
    color: str | None = None
    icon: str | None = None
    is_default: bool = False
    is_waiting: bool = False
    waiting_for: str | None = None
    sla_hours: int | None = None
    is_active: bool | None = None


class ATSMappingCreate(BaseModel):
    ats_type: str = Field(..., description="gupy, pandape, merge")
    ats_stage_id: str | None = None
    ats_stage_name: str = Field(..., min_length=1, max_length=255)
    ats_stage_order: int | None = None
    wedotalent_stage_id: str
    wedotalent_sub_status_id: str | None = None
    mapping_direction: str = Field(default="both", description="import, export, both")
    is_default_for_sync: bool = False
    priority: int = Field(default=0, ge=0)
    notes: str | None = None


class TransitionRequest(BaseModel):
    vacancy_candidate_id: str
    to_stage: str
    to_sub_status: str | None = None
    triggered_by: str = "user"
    triggered_by_user_id: str | None = None
    source_agent: str | None = None
    reason: str | None = None
    notes: str | None = None
    force: bool = False


class InlineStageEdit(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None
    sla_hours: int | None = Field(None, ge=0)
    stage_order: int | None = Field(None, ge=0)


class StageReorderItem(BaseModel):
    stage_id: str
    new_order: int


class StageReorderRequest(BaseModel):
    stages: list[StageReorderItem]


class ChatMessageItem(BaseModel):
    role: str = "user"
    content: str = ""
    timestamp: float | None = None


class InterpretContextRequest(BaseModel):
    candidate_id: str
    candidate_name: str | None = None
    job_title: str | None = None
    job_id: str | None = None
    from_stage: str
    to_stage: str
    action_behavior: str
    prompt: str | None = None
    company_id: str | None = None
    message_history: list[ChatMessageItem] | None = None
    conversation_id: str | None = Field(None, description="Conversation ID for multi-turn context persistence")


class TaskItem(BaseModel):
    type: str = ""
    description: str = ""
    data_type: str | None = None
    status: str = "scheduled"


class LearnedSuggestion(BaseModel):
    key: str = ""
    value: str = ""
    frequency: int = 0
    source: str = "recruiter_history"


class InterpretContextResponse(BaseModel):
    suggested_sub_status: str
    suggested_action: str
    action_label: str
    urgency: str
    lia_message: str | None = None
    extracted_preferences: dict | None = None
    ai_powered: bool = False
    confidence: float | None = None
    tasks: list[TaskItem] | None = None
    out_of_scope: bool = False
    candidate_info: dict | None = None
    learned_suggestions: list[LearnedSuggestion] | None = None
    fairness_result: dict | None = None
    layer: int = 1
    conversation_id: str | None = None


@router.get("/stages", response_model=None)
async def list_stages(
    include_inactive: bool = Query(default=False),
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
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
    except Exception as e:
        logger.error(f"Error listing stages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stages", response_model=None)
async def create_stage(
    stage: StageCreate,
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
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

        logger.info(f"Created stage: {stage.name} for company {effective_company_id}")
        return new_stage.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/stages/{stage_id}", response_model=None)
async def update_stage(
    stage_id: str,
    stage: StageUpdate,
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
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

        return updated.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stages/{stage_id}", response_model=None)
async def delete_stage(
    stage_id: str,
    hard_delete: bool = Query(default=False),
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
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

        return {"success": True, "deleted": stage_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/stages/{stage_id}/config", response_model=None)
async def update_stage_config(
    stage_id: str,
    config: StageConfigUpdate,
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalog", response_model=None)
async def get_stage_catalog():
    """Get the standard stage catalog for adding new columns."""
    return {"catalog": STANDARD_STAGE_CATALOG, "total": len(STANDARD_STAGE_CATALOG)}


@router.patch("/stages/{stage_id}/inline-edit", response_model=None)
async def inline_edit_stage(
    stage_id: str,
    payload: InlineStageEdit,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    try:
        stage = await stage_repo.get_by_id_str(stage_id)
        if not stage:
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

        return {
            "success": True,
            "stage_id": stage_id,
            "updates": updates,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inline editing stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stages/{stage_id}/remove", response_model=None)
async def remove_custom_stage(
    stage_id: str,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    try:
        stage = await stage_repo.get_by_id_str(stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Stage not found")

        is_system = bool(stage.is_initial or stage.is_final)  # type: ignore[truthy-bool]
        stage_category = getattr(stage, 'stage_category', 'custom') or 'custom'  # type: ignore[truthy-bool]

        if is_system or stage_category == 'system':
            raise HTTPException(status_code=403, detail="System stages cannot be removed")

        if stage_category == 'default':
            raise HTTPException(status_code=403, detail="Default stages cannot be removed, only deactivated")

        await stage_repo.hard_delete_by_id_str(stage_id)

        return {"success": True, "stage_id": stage_id, "removed": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stages/reorder", response_model=None)
async def reorder_stages(
    payload: StageReorderRequest,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    try:
        items = [{"stage_id": item.stage_id, "new_order": item.new_order} for item in payload.stages]
        await stage_repo.reorder(items)
        return {"success": True, "reordered": len(payload.stages)}
    except Exception as e:
        logger.error(f"Error reordering stages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stages/{stage_id}/sub-statuses", response_model=None)
async def list_stage_sub_statuses(
    stage_id: str,
    include_inactive: bool = Query(default=False, description="Include inactive sub-statuses (for settings view)"),
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stages/{stage_id}/sub-statuses", response_model=None)
async def create_sub_status(
    stage_id: str,
    sub_status: SubStatusCreate,
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
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
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sub-statuses/{sub_status_id}", response_model=None)
async def update_sub_status(
    sub_status_id: str,
    sub_status: SubStatusCreate,
    current_user: User = Depends(require_admin_or_recruiter),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
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
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sub-statuses/{sub_status_id}", response_model=None)
async def patch_sub_status(
    sub_status_id: str,
    payload: dict = Body(...),
    current_user: User = Depends(require_admin_or_recruiter),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
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
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sub-statuses/{sub_status_id}", response_model=None)
async def delete_sub_status(
    sub_status_id: str,
    current_user: User = Depends(require_admin_or_recruiter),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
    """Delete a sub-status (soft delete). Validates resource ownership."""
    try:
        existing = await sub_status_repo.get_by_id(uuid.UUID(sub_status_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Sub-status not found")

        assert_resource_ownership(existing, current_user, "sub-status")

        await sub_status_repo.soft_delete(uuid.UUID(sub_status_id))

        return {"success": True, "deleted": sub_status_id}
    except Exception as e:
        logger.error(f"Error deleting sub-status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ats-mappings", response_model=None)
async def list_ats_mappings(
    ats_type: str | None = Query(default=None, description="Filter by ATS type"),
    current_user: User = Depends(get_current_active_user),
    ats_repo: ATSMappingRepository = Depends(get_ats_mapping_repo),
):
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
    except Exception as e:
        logger.error(f"Error listing ATS mappings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ats-mappings", response_model=None)
async def create_ats_mapping(
    mapping: ATSMappingCreate,
    current_user: User = Depends(require_admin_or_recruiter),
    ats_repo: ATSMappingRepository = Depends(get_ats_mapping_repo),
):
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
    except Exception as e:
        logger.error(f"Error creating ATS mapping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ats-mappings/{mapping_id}", response_model=None)
async def delete_ats_mapping(
    mapping_id: str,
    current_user: User = Depends(require_admin_or_recruiter),
    ats_repo: ATSMappingRepository = Depends(get_ats_mapping_repo),
):
    """Delete an ATS mapping. Validates resource ownership."""
    try:
        existing = await ats_repo.get_by_id(uuid.UUID(mapping_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Mapping not found")

        assert_resource_ownership(existing, current_user, "ATS mapping")

        await ats_repo.soft_delete(uuid.UUID(mapping_id))

        return {"success": True, "deleted": mapping_id}
    except Exception as e:
        logger.error(f"Error deleting ATS mapping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize", response_model=None)
async def initialize_company_stages(
    ats_type: str | None = Query(default=None, description="Also initialize ATS mappings"),
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    ats_repo: ATSMappingRepository = Depends(get_ats_mapping_repo),
):
    """
    Initialize default stages and sub-statuses for the authenticated user's company.
    Optionally also initializes ATS mappings for Gupy or Pandapé.
    """
    try:


        effective_company_id = get_user_company_id(current_user)

        # pipeline_stage_service.initialize_company_stages needs a raw db session
        stages = await pipeline_stage_service.initialize_company_stages(
            company_id=effective_company_id,
            db=stage_repo.db
        )

        ats_mappings_created = 0
        if ats_type and stages:
            stage_name_to_id = {}
            all_stages = await stage_repo.list_for_company(effective_company_id, include_inactive=True)
            for s in all_stages:
                stage_name_to_id[s.name] = s.id

            mappings_config = []
            if ats_type == "gupy":
                mappings_config = GUPY_STAGE_MAPPINGS
            elif ats_type == "pandape":
                mappings_config = PANDAPE_STAGE_MAPPINGS

            for mapping in mappings_config:
                wedo_stage = mapping.get("wedotalent_stage")
                if wedo_stage in stage_name_to_id:
                    await ats_repo.create_no_commit({
                        "company_id": effective_company_id,
                        "ats_type": ats_type,
                        "ats_stage_name": mapping["ats_stage_name"],
                        "wedotalent_stage_id": stage_name_to_id[wedo_stage],
                        "is_default_for_sync": mapping.get("is_default_for_sync", False),
                    })
                    ats_mappings_created += 1

            await ats_repo.commit()

        return {
            "success": True,
            "stages_created": len(stages),
            "ats_mappings_created": ats_mappings_created
        }
    except Exception as e:
        logger.error(f"Error initializing stages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-canonical-sub-statuses", response_model=None)
async def sync_canonical_sub_statuses(
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
    """
    Idempotent sync: inserts any CANONICAL_SUB_STATUSES entries missing from
    the company's existing stages. Safe to run multiple times.
    Call once after deploys that expand CANONICAL_SUB_STATUSES.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        stages = await stage_repo.list_for_company(effective_company_id)

        inserted_total = 0
        for stage in stages:
            canonical = CANONICAL_SUB_STATUSES.get(stage.name, [])
            if not canonical:
                continue

            existing_names = await sub_status_repo.get_existing_names_for_stage(stage.id)
            next_order = await sub_status_repo.get_max_order_for_stage(stage.id)

            for sub_data in canonical:
                if sub_data["name"] not in existing_names:
                    await sub_status_repo.create_no_commit({
                        "stage_id": stage.id,
                        "company_id": effective_company_id,
                        "sub_status_order": next_order,
                        "name": sub_data["name"],
                        "display_name": sub_data["display_name"],
                        "is_default": sub_data.get("is_default", False),
                        "is_waiting": sub_data.get("is_waiting", False),
                        "waiting_for": sub_data.get("waiting_for"),
                    })
                    next_order += 1
                    inserted_total += 1

        await sub_status_repo.commit()
        logger.info(
            "[sync_canonical] company=%s inserted=%d sub-statuses",
            effective_company_id, inserted_total
        )
        return {"success": True, "inserted": inserted_total}

    except Exception as e:
        logger.error("[sync_canonical] error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transition", response_model=None)
async def transition_candidate(
    request: TransitionRequest,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    """
    Transition a candidate to a new stage/sub-status.

    This is the main endpoint for moving candidates through the pipeline.
    Validates transition, records history, and triggers ATS sync.
    Uses the authenticated user's company for validation.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        result = await pipeline_stage_service.transition_candidate(
            vacancy_candidate_id=request.vacancy_candidate_id,
            to_stage=request.to_stage,
            to_sub_status=request.to_sub_status,
            triggered_by=request.triggered_by,
            triggered_by_user_id=request.triggered_by_user_id or str(current_user.id),
            source_agent=request.source_agent,
            reason=request.reason,
            notes=request.notes,
            context={"company_id": effective_company_id},
            force=request.force,
            db=stage_repo.db
        )
        return result
    except TransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error transitioning candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidate/{vacancy_candidate_id}/info", response_model=None)
async def get_candidate_stage_info(
    vacancy_candidate_id: str,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    """
    Get current stage/sub-status info for a candidate.
    Uses the authenticated user's company for access control.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        info = await pipeline_stage_service.get_candidate_stage_info(
            vacancy_candidate_id=vacancy_candidate_id,
            company_id=effective_company_id,
            db=stage_repo.db
        )
        if not info:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidate/{vacancy_candidate_id}/history", response_model=None)
async def get_candidate_history(
    vacancy_candidate_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    """
    Get stage transition history for a candidate.
    Uses the authenticated user's company for access control.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        history = await pipeline_stage_service.get_candidate_history(
            vacancy_candidate_id=vacancy_candidate_id,
            company_id=effective_company_id,
            limit=limit,
            db=stage_repo.db
        )
        return {
            "history": history,
            "total": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting candidate history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defaults", response_model=None)
async def get_defaults():
    """
    Get default stage configurations.
    Useful for reference and setting up new companies.
    """
    return {
        "stages": DEFAULT_RECRUITMENT_STAGES,
        "sub_statuses": DEFAULT_SUB_STATUSES,
        "ats_mappings": {
            "gupy": GUPY_STAGE_MAPPINGS,
            "pandape": PANDAPE_STAGE_MAPPINGS
        }
    }


@router.get("/stage-catalog", summary="Get standard stage catalog", response_model=None)
async def get_standard_stage_catalog():
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


class CompanyPipelineStageItem(BaseModel):
    id: str | None = None
    catalog_id: str | None = None
    name: str | None = None
    display_name: str | None = None
    stage_order: int
    color: str | None = None
    icon: str | None = None
    sla_hours: int | None = None
    is_active: bool = True
    action_behavior: str | None = None
    default_channel: str | None = None


class CompanyPipelineUpdate(BaseModel):
    stages: list[CompanyPipelineStageItem]


async def _get_company_pipeline(
    company_id: str,
    stage_repo: RecruitmentStageRepository,
    sub_status_repo: SubStatusRepository,
):
    stages = await stage_repo.list_for_company(company_id)

    if not stages:
        stages = await pipeline_stage_service.initialize_company_stages(
            company_id=company_id, db=stage_repo.db
        )
        if not stages:
            return []
        stages = await stage_repo.list_for_company(company_id)

    pipeline = []
    for stage in stages:
        stage_dict = stage.to_dict()
        sub_statuses = await sub_status_repo.list_for_stage(stage.id)
        stage_dict["sub_statuses"] = [s.to_dict() for s in sub_statuses]
        pipeline.append(stage_dict)
    return pipeline


@router.get("/company-pipeline", response_model=None)
async def get_company_pipeline(
    current_user: User = Depends(get_current_user_or_demo),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
    try:
        effective_company_id = get_user_company_id(current_user)
        pipeline = await _get_company_pipeline(effective_company_id, stage_repo, sub_status_repo)
        return {"pipeline": pipeline, "total": len(pipeline)}
    except Exception as e:
        logger.error(f"Error getting company pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/company-pipeline", response_model=None)
async def update_company_pipeline(
    payload: CompanyPipelineUpdate,
    current_user: User = Depends(get_current_user_or_demo),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
    try:
        effective_company_id = get_user_company_id(current_user)

        all_stages = await stage_repo.list_for_company(effective_company_id, include_inactive=True)
        existing_stages = {str(s.id): s for s in all_stages}

        catalog_by_id = {c["id"]: c for c in STANDARD_STAGE_CATALOG}
        incoming_ids = set()

        for item in payload.stages:
            if item.id and item.id in existing_stages:
                stage = existing_stages[item.id]
                incoming_ids.add(item.id)
                updates: dict = {"stage_order": item.stage_order, "is_active": item.is_active}
                if item.display_name is not None:
                    updates["display_name"] = item.display_name
                if item.sla_hours is not None:
                    updates["sla_hours"] = item.sla_hours
                if item.color is not None:
                    updates["color"] = item.color
                if item.icon is not None:
                    updates["icon"] = item.icon
                if item.action_behavior is not None:
                    updates["action_behavior"] = item.action_behavior
                if item.default_channel is not None:
                    updates["default_channel"] = item.default_channel
                await stage_repo.update_fields_uuid(stage.id, updates)
            elif item.catalog_id and item.catalog_id in catalog_by_id:
                catalog_entry = catalog_by_id[item.catalog_id]
                new_stage = RecruitmentStage(
                    company_id=effective_company_id,
                    name=catalog_entry["name"],
                    display_name=item.display_name or catalog_entry["display_name"],
                    stage_order=item.stage_order,
                    color=item.color or catalog_entry.get("color", "#6B7280"),
                    icon=item.icon or catalog_entry.get("icon", "circle"),
                    stage_type="active" if not catalog_entry.get("is_final") else "final",
                    is_initial=catalog_entry.get("is_initial", False),
                    is_final=catalog_entry.get("is_final", False),
                    is_system=catalog_entry.get("is_system", False),
                    stage_category=catalog_entry.get("stage_category", "custom"),
                    action_behavior=item.action_behavior or catalog_entry.get("action_behavior", "passive"),
                    sla_hours=item.sla_hours,
                    is_active=item.is_active,
                )
                stage_repo.db.add(new_stage)
                await stage_repo.db.flush()

                sub_status_defs = DEFAULT_SUB_STATUSES.get(catalog_entry["name"], [])
                for idx, sub_def in enumerate(sub_status_defs):
                    await sub_status_repo.create_no_commit({
                        "stage_id": new_stage.id,
                        "company_id": effective_company_id,
                        "name": sub_def["name"],
                        "display_name": sub_def["display_name"],
                        "sub_status_order": idx,
                        "is_default": sub_def.get("is_default", False),
                        "is_waiting": sub_def.get("is_waiting", False),
                        "waiting_for": sub_def.get("waiting_for"),
                    })

        for stage_id, stage in existing_stages.items():
            if stage_id not in incoming_ids:
                if not stage.is_system:  # type: ignore[truthy-bool]
                    await stage_repo.update_fields_uuid(
                        stage.id, {"is_active": False}
                    )

        await stage_repo.db.commit()

        pipeline = await _get_company_pipeline(effective_company_id, stage_repo, sub_status_repo)
        return {"pipeline": pipeline, "total": len(pipeline)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class JobPipelineStageItem(BaseModel):
    stage_name: str
    stage_order: int
    is_active: bool = True
    sla_hours: int | None = None
    display_name: str | None = None
    color: str | None = None
    icon: str | None = None


class JobPipelineUpdate(BaseModel):
    stages: list[JobPipelineStageItem]


@router.get("/jobs/{job_id}/pipeline", response_model=None)
async def get_job_pipeline(
    job_id: str,
    current_user: User = Depends(get_current_user_or_demo),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
    try:
        from app.models.job_vacancy import JobVacancy

        effective_company_id = get_user_company_id(current_user)

        job = await stage_repo.db.get(JobVacancy, uuid.UUID(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if str(job.company_id) != effective_company_id:
            raise HTTPException(status_code=403, detail="Access denied")

        pipeline_config = getattr(job, "pipeline_config", None)

        if pipeline_config:
            config_map = {item["stage_name"]: item for item in pipeline_config}
            company_pipeline = await _get_company_pipeline(effective_company_id, stage_repo, sub_status_repo)
            customized = []
            for stage in company_pipeline:
                override = config_map.get(stage["name"])
                if override:
                    stage["stage_order"] = override.get("stage_order", stage["stage_order"])
                    stage["is_active"] = override.get("is_active", stage["is_active"])
                    if override.get("sla_hours") is not None:
                        stage["sla_hours"] = override["sla_hours"]
                    if override.get("display_name"):
                        stage["display_name"] = override["display_name"]
                    if override.get("color"):
                        stage["color"] = override["color"]
                    if override.get("icon"):
                        stage["icon"] = override["icon"]
                    customized.append(stage)
                else:
                    customized.append(stage)
            customized.sort(key=lambda s: s["stage_order"])
            return {
                "pipeline": customized,
                "total": len(customized),
                "is_inherited": False,
                "source": "custom",
            }
        else:
            company_pipeline = await _get_company_pipeline(effective_company_id, stage_repo, sub_status_repo)
            return {
                "pipeline": company_pipeline,
                "total": len(company_pipeline),
                "is_inherited": True,
                "source": "company",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/jobs/{job_id}/pipeline", response_model=None)
async def update_job_pipeline(
    job_id: str,
    payload: JobPipelineUpdate,
    current_user: User = Depends(get_current_user_or_demo),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
):
    try:
        from app.models.job_vacancy import JobVacancy

        effective_company_id = get_user_company_id(current_user)

        job = await stage_repo.db.get(JobVacancy, uuid.UUID(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if str(job.company_id) != effective_company_id:
            raise HTTPException(status_code=403, detail="Access denied")

        config = [
            {
                "stage_name": s.stage_name,
                "stage_order": s.stage_order,
                "is_active": s.is_active,
                "sla_hours": s.sla_hours,
                "display_name": s.display_name,
                "color": s.color,
                "icon": s.icon,
            }
            for s in payload.stages
        ]

        job.pipeline_config = config  # type: ignore[assignment]
        job.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await stage_repo.db.commit()
        await stage_repo.db.refresh(job)

        config_map = {item["stage_name"]: item for item in config}
        company_pipeline = await _get_company_pipeline(effective_company_id, stage_repo, sub_status_repo)
        customized = []
        for stage in company_pipeline:
            override = config_map.get(stage["name"])
            if override:
                stage["stage_order"] = override.get("stage_order", stage["stage_order"])
                stage["is_active"] = override.get("is_active", stage["is_active"])
                if override.get("sla_hours") is not None:
                    stage["sla_hours"] = override["sla_hours"]
                if override.get("display_name"):
                    stage["display_name"] = override["display_name"]
                if override.get("color"):
                    stage["color"] = override["color"]
                if override.get("icon"):
                    stage["icon"] = override["icon"]
            customized.append(stage)
        customized.sort(key=lambda s: s["stage_order"])

        return {
            "pipeline": customized,
            "total": len(customized),
            "is_inherited": False,
            "source": "custom",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


STAGE_DISPLAY_NAMES = {s["name"]: s["display_name"] for s in DEFAULT_RECRUITMENT_STAGES}

ACTION_BEHAVIOR_LABELS = {
    "intake": "Adicionar ao Funil",
    "screening": "Iniciar Triagem",
    "scheduling": "Agendar Entrevista",
    "evaluation": "Enviar Avaliação",
    "verification": "Solicitar Referências",
    "offer": "Enviar Proposta",
    "passive": "Mover Candidato",
    "conclusion_hired": "Confirmar Contratação",
    "conclusion_rejected": "Confirmar Reprovação",
    "conclusion_declined": "Registrar Recusa",
}

import re


def _extract_scheduling_preferences(text: str) -> dict:
    preferences = {}
    days = re.findall(
        r'\b(segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo|hoje|amanhã|amanha)\b',
        text.lower()
    )
    if days:
        preferences["date"] = days[0]
    times = re.findall(r'\b(\d{1,2}[h:]\d{0,2})\b', text.lower())
    if times:
        preferences["time"] = times[0]
    return preferences


def _determine_suggested_action(action_behavior: str, prompt: str | None) -> str:
    if prompt:
        prompt_lower = prompt.lower()
        auto_keywords = ["automático", "automatico", "lia", "auto", "agendar", "enviar"]
        manual_keywords = ["manual", "eu mesmo", "eu mesma", "não enviar", "nao enviar", "só mover", "so mover"]
        if any(kw in prompt_lower for kw in manual_keywords):
            return "manual"
        if any(kw in prompt_lower for kw in auto_keywords):
            return "lia_auto"
    if action_behavior in ("scheduling", "screening", "offer"):
        return "lia_auto"
    if action_behavior in ("passive", "intake"):
        return "just_move"
    return "manual"


def _get_default_sub_status(to_stage: str) -> str:
    subs = DEFAULT_SUB_STATUSES.get(to_stage, [])
    for s in subs:
        if s.get("is_default"):
            return s["name"]
    return subs[0]["name"] if subs else "novo"


def _determine_urgency(action_behavior: str) -> str:
    if action_behavior in ("conclusion_rejected", "conclusion_hired", "conclusion_declined"):
        return "high"
    if action_behavior in ("passive",):
        return "low"
    return "normal"


def _build_lia_message(
    to_stage: str,
    action_behavior: str,
    candidate_name: str | None,
    preferences: dict,
    suggested_action: str,
) -> str:
    display = STAGE_DISPLAY_NAMES.get(to_stage, to_stage)
    name = candidate_name or "o candidato"

    if action_behavior == "scheduling" and preferences:
        parts = []
        if "date" in preferences:
            parts.append(f"dia {preferences['date']}")
        if "time" in preferences:
            parts.append(f"às {preferences['time']}")
        if "format" in preferences:
            parts.append(f"({preferences['format']})")
        time_str = " ".join(parts)
        if time_str:
            return f"Entendido! Vou enviar o convite de entrevista para {time_str}. Ao confirmar, {name} receberá o convite por e-mail."
        return f"Vou enviar o convite de agendamento para {name}. Ao confirmar, o candidato será notificado."

    if action_behavior == "scheduling":
        return f"Vou enviar o convite de agendamento para {name}. Ao confirmar, o candidato será notificado por e-mail."

    if action_behavior == "screening":
        return f"Vou iniciar a triagem WSI com {name}. Ao confirmar, o candidato receberá as perguntas por e-mail."
    if action_behavior == "evaluation":
        return f"Vou enviar o teste técnico para {name}. Ao confirmar, o candidato receberá o link de avaliação."
    if action_behavior == "verification":
        return f"Vou solicitar os documentos necessários a {name}. Ao confirmar, o candidato receberá a solicitação."
    if action_behavior == "offer":
        return f"Vou preparar a proposta para {name}. Ao confirmar, o candidato será notificado."
    if action_behavior == "conclusion_hired":
        return f"Confirmando contratação de {name}! Ao confirmar, o processo será finalizado."
    if action_behavior == "conclusion_rejected":
        return f"Registrando reprovação de {name}. Ao confirmar, o candidato receberá o feedback."
    if action_behavior == "conclusion_declined":
        return f"Registrando recusa de proposta de {name}."

    if suggested_action == "just_move":
        return f"Movendo {name} para {display}"

    return f"Movendo {name} para {display}"


@router.post("/transition/interpret-context", response_model=InterpretContextResponse)
async def interpret_transition_context(
    request: InterpretContextRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """
    Interpret a candidate stage transition context.
    Layer 3: PipelineTransitionAgent (ReAct loop with tools) — primary.
    Layer 2: Uses LLM single-shot when Layer 3 fails.
    Layer 1: Rule-based logic as final fallback.
    """
    try:
        if request.prompt and request.prompt.strip():
            # --- Layer 3: ReAct Agent ---
            try:
                from lia_agents_core.agent_interface import AgentInput

                from app.domains.pipeline.agents.pipeline_transition_agent import get_pipeline_transition_agent

                conversation_history = []
                if request.message_history:
                    conversation_history = [
                        {"role": m.role, "content": m.content}
                        for m in request.message_history
                    ]

                company_id = request.company_id or get_user_company_id(current_user)
                user_id = str(getattr(current_user, "id", "")) or ""

                conv_id = request.conversation_id or str(uuid.uuid4())

                agent_input = AgentInput(
                    message=request.prompt,
                    context={
                        "action_behavior": request.action_behavior,
                        "candidate_id": request.candidate_id,
                        "candidate_name": request.candidate_name or "",
                        "job_id": request.job_id or "",
                        "job_title": request.job_title or "",
                        "from_stage": request.from_stage,
                        "to_stage": request.to_stage,
                        "company_id": company_id,
                    },
                    session_id=conv_id,
                    company_id=company_id,
                    user_id=user_id,
                    conversation_history=conversation_history,
                )

                agent = get_pipeline_transition_agent()
                agent_output = await agent.process(agent_input)

                if agent_output and agent_output.message and not agent_output.error:
                    state = agent_output.state_updates or {}

                    suggested_sub = state.get("suggested_sub_status")
                    if not suggested_sub:
                        suggested_sub = _get_default_sub_status(request.to_stage)

                    tasks_raw = state.get("tasks") or []
                    tasks = [TaskItem(**t) for t in tasks_raw] if tasks_raw else None

                    learned_raw = state.get("learned_suggestions") or []
                    learned = [LearnedSuggestion(**s) for s in learned_raw] if learned_raw else None

                    return InterpretContextResponse(
                        suggested_sub_status=suggested_sub,
                        suggested_action=state.get("suggested_action", "lia_auto"),
                        action_label=ACTION_BEHAVIOR_LABELS.get(request.action_behavior, "Mover Candidato"),
                        urgency=_determine_urgency(request.action_behavior),
                        lia_message=agent_output.message,
                        extracted_preferences=state.get("extracted_preferences") or None,
                        ai_powered=True,
                        confidence=agent_output.confidence,
                        tasks=tasks,
                        out_of_scope=state.get("out_of_scope", False),
                        candidate_info=state.get("candidate_info"),
                        learned_suggestions=learned,
                        fairness_result=state.get("fairness_result"),
                        layer=3,
                        conversation_id=conv_id,
                    )

                logger.warning("[INTERPRET] Layer 3 returned empty/error response")
                return InterpretContextResponse(
                    suggested_sub_status=_get_default_sub_status(request.to_stage),
                    suggested_action="lia_auto",
                    action_label=ACTION_BEHAVIOR_LABELS.get(request.action_behavior, "Mover Candidato"),
                    urgency=_determine_urgency(request.action_behavior),
                    lia_message="Não consegui processar sua mensagem agora. Por favor, tente novamente.",
                    ai_powered=False,
                    layer=1,
                    conversation_id=conv_id,
                )

            except Exception as agent_err:
                logger.warning(f"[INTERPRET] ReAct agent failed: {agent_err}")
                return InterpretContextResponse(
                    suggested_sub_status=_get_default_sub_status(request.to_stage),
                    suggested_action=_determine_suggested_action(request.action_behavior, request.prompt),
                    action_label=ACTION_BEHAVIOR_LABELS.get(request.action_behavior, "Mover Candidato"),
                    urgency=_determine_urgency(request.action_behavior),
                    lia_message="Estou com dificuldade em processar agora. Você pode prosseguir com a movimentação manualmente.",
                    ai_powered=False,
                    layer=1,
                    conversation_id=conv_id if 'conv_id' in locals() else None,
                )

        # No prompt — rule-based defaults only (UI didn't open chat)
        return InterpretContextResponse(
            suggested_sub_status=_get_default_sub_status(request.to_stage),
            suggested_action=_determine_suggested_action(request.action_behavior, request.prompt),
            action_label=ACTION_BEHAVIOR_LABELS.get(request.action_behavior, "Mover Candidato"),
            urgency=_determine_urgency(request.action_behavior),
            ai_powered=False,
            layer=1,
        )
    except Exception as e:
        logger.error(f"Error interpreting transition context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


DEFAULT_SCREENING_QUESTIONS = [
    {"id": "1", "question": "Você tem interesse real nesta vaga?", "question_type": "yesno", "is_required": True, "order": 1, "is_default": True, "options": []},
    {"id": "2", "question": "Qual sua disponibilidade para início?", "question_type": "text", "is_required": True, "order": 2, "is_default": True, "options": []},
    {"id": "3", "question": "Qual sua pretensão salarial?", "question_type": "text", "is_required": True, "order": 3, "is_default": True, "options": []},
    {"id": "4", "question": "Quantos anos de experiência você tem na área?", "question_type": "text", "is_required": True, "order": 4, "is_default": True, "options": []},
    {"id": "5", "question": "Você aceita trabalhar no modelo híbrido/presencial?", "question_type": "yesno", "is_required": True, "order": 5, "is_default": True, "options": []},
    {"id": "6", "question": "Você está em algum outro processo seletivo?", "question_type": "yesno", "is_required": False, "order": 6, "is_default": True, "options": []}
]


class ScreeningQuestionCreate(BaseModel):
    question: str = Field(..., min_length=1)
    question_type: str = Field(default="text")
    is_required: bool = True
    order: int = Field(default=0, ge=0)
    is_default: bool = False
    options: list[str] = Field(default_factory=list)


class ScreeningQuestionUpdate(BaseModel):
    id: str | None = None
    question: str | None = None
    question_type: str | None = None
    is_required: bool | None = None
    order: int | None = None
    is_default: bool | None = None
    options: list[str] | None = None


screening_questions_router = APIRouter(prefix="/screening-questions", tags=["screening-questions"])


async def initialize_default_questions(
    company_id: str,
    sq_repo: ScreeningQuestionRepository,
) -> list[ScreeningQuestion]:
    """Initialize default screening questions for a company if none exist."""
    existing = await sq_repo.list_all_for_company(company_id)

    if not existing:
        for q in DEFAULT_SCREENING_QUESTIONS:
            await sq_repo.create_no_commit({
                "company_id": company_id,
                "question": q["question"],
                "question_type": q["question_type"],
                "is_required": q["is_required"],
                "order": q["order"],
                "is_default": q["is_default"],
                "options": q.get("options", []),
            })
        await sq_repo.commit()
        return await sq_repo.list_for_company(company_id)

    return existing


@screening_questions_router.get("")
async def list_screening_questions(
    current_user: User = Depends(get_current_active_user),
    sq_repo: ScreeningQuestionRepository = Depends(get_screening_question_repo),
):
    """
    List all screening questions for the authenticated user's company.
    Initializes default questions if none exist.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        await initialize_default_questions(effective_company_id, sq_repo)
        questions = await sq_repo.list_for_company(effective_company_id)

        return [q.to_dict() for q in questions]
    except Exception as e:
        logger.error(f"Error listing screening questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@screening_questions_router.post("")
async def create_screening_question(
    question: ScreeningQuestionCreate,
    current_user: User = Depends(require_admin_or_recruiter),
    sq_repo: ScreeningQuestionRepository = Depends(get_screening_question_repo),
):
    """
    Create a new screening question for the authenticated user's company.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        next_order = await sq_repo.get_last_order(effective_company_id)

        new_question = await sq_repo.create({
            "company_id": effective_company_id,
            "question": question.question,
            "question_type": question.question_type,
            "is_required": question.is_required,
            "order": question.order if question.order > 0 else next_order,
            "is_default": False,
            "options": question.options,
        })

        logger.info(f"Created screening question: {question.question[:50]} for company {effective_company_id}")
        return {
            "success": True,
            "message": "Screening question created",
            "data": new_question.to_dict()
        }
    except Exception as e:
        logger.error(f"Error creating screening question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@screening_questions_router.put("")
async def update_screening_questions(
    questions: list[dict] = Body(...),
    current_user: User = Depends(require_admin_or_recruiter),
    sq_repo: ScreeningQuestionRepository = Depends(get_screening_question_repo),
):
    """
    Update screening questions (bulk update).
    Syncs the database with the provided list of questions.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        existing_list = await sq_repo.list_all_for_company(effective_company_id)
        existing_questions = {str(q.id): q for q in existing_list}

        incoming_ids = set()
        updated_questions = []

        for idx, q_data in enumerate(questions):
            q_id = q_data.get("id", "")

            if q_id in existing_questions:
                existing = existing_questions[q_id]
                existing.question = q_data.get("question", existing.question)
                existing.question_type = q_data.get("question_type", existing.question_type)
                existing.is_required = q_data.get("is_required", existing.is_required)
                existing.order = q_data.get("order", idx + 1)
                existing.options = q_data.get("options", existing.options)
                existing.updated_at = datetime.utcnow()  # type: ignore[assignment]
                incoming_ids.add(q_id)
                updated_questions.append(existing)
            elif q_id.startswith("q-") or not q_id:
                new_question = await sq_repo.create_no_commit({
                    "company_id": effective_company_id,
                    "question": q_data.get("question", ""),
                    "question_type": q_data.get("question_type", "text"),
                    "is_required": q_data.get("is_required", True),
                    "order": q_data.get("order", idx + 1),
                    "is_default": q_data.get("is_default", False),
                    "options": q_data.get("options", []),
                })
                updated_questions.append(new_question)
            else:
                try:
                    existing_uuid = existing_questions.get(q_id)
                    if existing_uuid:
                        existing_uuid.question = q_data.get("question", existing_uuid.question)
                        existing_uuid.question_type = q_data.get("question_type", existing_uuid.question_type)
                        existing_uuid.is_required = q_data.get("is_required", existing_uuid.is_required)
                        existing_uuid.order = q_data.get("order", idx + 1)
                        existing_uuid.options = q_data.get("options", existing_uuid.options)
                        existing_uuid.updated_at = datetime.utcnow()  # type: ignore[assignment]
                        incoming_ids.add(q_id)
                        updated_questions.append(existing_uuid)
                except Exception:
                    pass

        for q_id, existing in existing_questions.items():
            if q_id not in incoming_ids:
                await sq_repo.soft_delete_no_commit(existing)

        await sq_repo.commit()

        for q in updated_questions:
            await sq_repo.refresh(q)

        logger.info(f"Updated {len(questions)} screening questions for company {effective_company_id}")
        return {
            "success": True,
            "message": "Screening questions updated",
            "data": [q.to_dict() for q in updated_questions if q.is_active]
        }
    except Exception as e:
        logger.error(f"Error updating screening questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@screening_questions_router.put("/{question_id}")
async def update_screening_question(
    question_id: str,
    question: ScreeningQuestionUpdate,
    current_user: User = Depends(require_admin_or_recruiter),
    sq_repo: ScreeningQuestionRepository = Depends(get_screening_question_repo),
):
    """
    Update a single screening question.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        try:
            q_uuid = uuid.UUID(question_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question ID format")

        existing = await sq_repo.get_by_id(q_uuid)
        if not existing:
            raise HTTPException(status_code=404, detail="Question not found")

        if existing.company_id != effective_company_id:  # type: ignore[truthy-bool]
            raise HTTPException(status_code=403, detail="Access denied")

        update_data = question.model_dump(exclude_unset=True)
        updated = await sq_repo.update(q_uuid, update_data)

        return {
            "success": True,
            "message": "Screening question updated",
            "data": updated.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating screening question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@screening_questions_router.delete("/{question_id}")
async def delete_screening_question(
    question_id: str,
    current_user: User = Depends(require_admin_or_recruiter),
    sq_repo: ScreeningQuestionRepository = Depends(get_screening_question_repo),
):
    """
    Delete a screening question (soft delete).
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        try:
            q_uuid = uuid.UUID(question_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question ID format")

        existing = await sq_repo.get_by_id(q_uuid)
        if not existing:
            raise HTTPException(status_code=404, detail="Question not found")

        if existing.company_id != effective_company_id:  # type: ignore[truthy-bool]
            raise HTTPException(status_code=403, detail="Access denied")

        await sq_repo.soft_delete(q_uuid)

        logger.info(f"Deleted screening question: {question_id}")
        return {
            "success": True,
            "message": "Screening question deleted",
            "deleted_id": question_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting screening question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class DispatchResult(BaseModel):
    success: bool
    channel: str | None = None
    message_id: str | None = None
    template_name: str | None = None
    recipient: str | None = None
    mock: bool = False
    error: str | None = None
    ai_personalized: bool = False


class TransitionExecuteRequest(BaseModel):
    vacancy_candidate_id: str
    to_stage: str
    from_stage: str | None = None
    vacancy_id: str | None = None
    sub_status: str | None = None
    action: str | None = "just_move"
    prompt: str | None = None
    channel: str | None = "email"
    action_behavior: str | None = None
    extracted_preferences: dict[str, Any] | None = None


class TransitionExecuteResponse(BaseModel):
    success: bool
    message: str
    candidate_id: str
    new_stage: str
    new_sub_status: str | None = None
    dispatch_results: list[DispatchResult] | None = None
    predicted_sub_status: str | None = None
    prediction_confidence: float | None = None


@router.post("/transition/execute", response_model=TransitionExecuteResponse)
async def execute_transition(
    request: TransitionExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    """Execute a candidate stage transition with optional auto-dispatch."""
    try:
        from sqlalchemy import update as sa_update

        from app.models.candidate import VacancyCandidate

        values = {"stage": request.to_stage}
        if request.sub_status:
            values["status"] = request.sub_status

        predicted_sub_status = None
        prediction = None
        if not request.sub_status and settings.ENABLE_LLM_SUBSTATUS_PREDICTION:
            try:
                from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator
                from app.domains.automation.services.stage_transition_automation import SubStatusPredictor

                aggregator = CandidateContextAggregator(stage_repo.db)
                candidate_context = await aggregator.aggregate(request.vacancy_candidate_id)

                prediction = SubStatusPredictor.predict(
                    candidate_context=candidate_context,
                    from_stage=request.from_stage or "",
                    to_stage=request.to_stage,
                )

                if prediction and prediction.get("confidence", 0) >= 0.6:
                    predicted_sub_status = prediction.get("predicted_substatus") or ""  # type: ignore[arg-type]
                    values["status"] = predicted_sub_status
                    logger.info(
                        f"[PIPELINE] Predicted sub-status: {predicted_sub_status} "
                        f"(confidence: {prediction.get('confidence')}, "
                        f"reasoning: {prediction.get('reasoning')})"
                    )
            except Exception as pred_err:
                logger.warning(f"[PIPELINE] SubStatus prediction failed (fallback to no sub-status): {pred_err}")

        stmt = (
            sa_update(VacancyCandidate)
            .where(VacancyCandidate.id == request.vacancy_candidate_id)
            .values(**values)
        )
        await stage_repo.db.execute(stmt)
        await stage_repo.db.commit()

        try:
            from app.domains.automation.services.stage_automation_engine import (
                AutomationEvent,
                StageAutomationEngine,
                TriggerType,
            )

            automation_payload = {
                    "from_stage": request.from_stage or "",
                    "to_stage": request.to_stage,
                    "action_behavior": request.action_behavior or "",
                    "sub_status": request.sub_status or "",
                    "prompt": request.prompt or "",
                    "action": request.action or "",
                    "triggered_by": str(getattr(current_user, 'id', 'system')),
                }
            if request.extracted_preferences:
                automation_payload["extracted_preferences"] = request.extracted_preferences

            event = AutomationEvent(
                trigger_type=TriggerType.STAGE_CHANGED,
                candidate_id=request.vacancy_candidate_id,
                vacancy_id=request.vacancy_id or "",
                company_id=getattr(current_user, 'company_id', '') or 'admin_company',
                payload=automation_payload,
            )
            engine = StageAutomationEngine()
            asyncio.create_task(engine.process_event(event, stage_repo.db))
            logger.info(f"[PIPELINE] Emitted STAGE_CHANGED event for {request.vacancy_candidate_id}")
        except Exception as event_err:
            logger.warning(f"[PIPELINE] Failed to emit STAGE_CHANGED event: {event_err}")

        dispatch_results = []

        resolved_action_behavior = request.action_behavior
        if request.action == "lia_auto" and not resolved_action_behavior:
            try:
                from sqlalchemy import select as sa_select

                from app.models.recruitment_stages import RecruitmentStage as _RS
                stage_result = await stage_repo.db.execute(
                    sa_select(_RS).where(_RS.name == request.to_stage)
                )
                dest_stage = stage_result.scalar_one_or_none()
                if dest_stage:
                    resolved_action_behavior = dest_stage.action_behavior
                    logger.info(f"Resolved action_behavior '{resolved_action_behavior}' from stage '{request.to_stage}'")
            except Exception as stage_err:
                logger.warning(f"Could not resolve action_behavior from stage: {stage_err}")

        if request.action == "lia_auto" and resolved_action_behavior:  # type: ignore[truthy-bool]
            try:
                from app.domains.communication.services.transition_dispatch_service import TransitionDispatchService
                dispatch_service = TransitionDispatchService(stage_repo.db)

                company_id = getattr(current_user, 'company_id', None) or 'admin_company'
                triggered_by = getattr(current_user, 'id', None) or 'system'

                personalized_content = None
                if request.prompt and settings.ENABLE_LLM_DISPATCH_PERSONALIZATION:
                    try:
                        from app.domains.automation.services.candidate_context_aggregator import (
                            CandidateContextAggregator,
                        )
                        from app.domains.automation.services.stage_transition_automation import MessageGenerator

                        aggregator = CandidateContextAggregator(stage_repo.db)
                        candidate_context = await aggregator.aggregate(request.vacancy_candidate_id)
                        job_context = candidate_context.get("job", {})

                        msg_type = "feedback_construtivo" if request.to_stage == "rejected" else "aprovacao"

                        msg_result = await MessageGenerator.generate(
                            candidate_context=candidate_context,
                            to_stage=request.to_stage,
                            substatus=request.sub_status or predicted_sub_status or "",
                            job_context=job_context,
                            message_type=msg_type,
                            channel=request.channel or "email",
                        )

                        if msg_result and msg_result.get("body"):
                            personalized_content = msg_result["body"]
                            logger.info("[PIPELINE] AI-generated personalized message for dispatch")
                    except Exception as msg_err:
                        logger.warning(f"[PIPELINE] AI message generation failed, using template: {msg_err}")

                extra_vars: dict[str, Any] = {}
                if request.prompt:
                    extra_vars["prompt"] = request.prompt
                if request.extracted_preferences and request.action in ("lia_auto", None):
                    prefs = {k: str(v) for k, v in request.extracted_preferences.items() if v is not None and str(v).strip()}
                    extra_vars.update(prefs)
                    pref_map = {
                        "date": "interview_date",
                        "time": "interview_time",
                        "interviewer": "interviewer_name",
                        "location": "interview_location",
                        "format": "interview_format",
                        "duration": "interview_duration",
                    }
                    for src_key, dest_key in pref_map.items():
                        if src_key in prefs:
                            extra_vars[dest_key] = prefs[src_key]

                result = await dispatch_service.dispatch_for_transition(
                    vacancy_candidate_id=request.vacancy_candidate_id,
                    to_stage=request.to_stage,
                    action_behavior=str(resolved_action_behavior),  # type: ignore[arg-type]
                    channel=request.channel or "email",
                    company_id=str(company_id),
                    triggered_by=str(triggered_by),
                    extra_variables=extra_vars if extra_vars else None,
                    personalized_content=personalized_content,
                )
                dispatch_results.append(DispatchResult(**result))
            except Exception as dispatch_error:
                logger.error(f"Dispatch error during transition: {dispatch_error}", exc_info=True)
                dispatch_results.append(DispatchResult(
                    success=False,
                    channel=request.channel or "email",
                    error=str(dispatch_error)
                ))

        return TransitionExecuteResponse(
            success=True,
            message=f"Candidato movido para {request.to_stage}",
            candidate_id=request.vacancy_candidate_id,
            new_stage=request.to_stage,
            new_sub_status=request.sub_status or predicted_sub_status,
            dispatch_results=dispatch_results if dispatch_results else None,
            predicted_sub_status=predicted_sub_status,
            prediction_confidence=prediction.get("confidence") if predicted_sub_status and prediction else None,
        )
    except Exception as e:
        return TransitionExecuteResponse(
            success=False,
            message=str(e),
            candidate_id=request.vacancy_candidate_id,
            new_stage=request.to_stage,
        )


class ReturnEventRequest(BaseModel):
    vacancy_candidate_id: str = Field(..., description="ID do VacancyCandidate")
    event_type: str = Field(..., description="Tipo do evento de retorno (screening_complete, interview_confirmed, etc.)")
    metadata: dict | None = Field(default=None, description="Dados adicionais do evento (score, notas, etc.)")
    triggered_by: str | None = Field(default=None, description="Quem disparou o evento (system, webhook, candidate)")


class ReturnEventResponse(BaseModel):
    success: bool
    event_type: str
    new_sub_status: str | None = None
    new_stage: str | None = None
    activity_id: str | None = None
    notification_sent: bool = False
    auto_moved: bool = False
    error: str | None = None


class BulkReturnEventRequest(BaseModel):
    events: list[ReturnEventRequest] = Field(..., description="Lista de eventos de retorno para processar em lote")


@router.get("/transition/return-event/stream", response_model=None)
async def stream_return_events(
    job_id: str | None = None,
    company_id: str | None = None,
    current_user: User = Depends(get_current_active_user),
):
    from sqlalchemy import and_ as sa_and
    from sqlalchemy import select as sa_select

    from app.core.database import async_session_factory
    from app.models.activity_feed import ActivityFeed

    effective_company_id = company_id or get_user_company_id(current_user)

    async def event_generator():
        last_check = datetime.utcnow()
        while True:
            try:
                async with async_session_factory() as session:
                    filters = [
                        ActivityFeed.activity_type.like("return_event_%"),
                        ActivityFeed.created_at > last_check,
                        ActivityFeed.is_visible,
                    ]

                    if effective_company_id:
                        filters.append(
                            ActivityFeed.extra_data["company_id"].as_string() == effective_company_id
                        )

                    if job_id:
                        filters.append(
                            ActivityFeed.extra_data["job_id"].as_string() == job_id
                        )

                    query = sa_select(ActivityFeed).where(sa_and(*filters))
                    query = query.order_by(ActivityFeed.created_at.desc()).limit(20)

                    result = await session.execute(query)
                    activities = result.scalars().all()

                    if activities:
                        last_check = datetime.utcnow()
                        for activity in activities:
                            extra = activity.extra_data or {} if hasattr(activity, 'extra_data') else {}
                            event = {
                                "id": str(activity.id),
                                "event_type": extra.get("event_type", activity.activity_type.replace("return_event_", "")),
                                "vacancy_candidate_id": extra.get("vacancy_candidate_id", ""),
                                "candidate_name": getattr(activity, 'actor_name', '') or "",
                                "new_sub_status": extra.get("sub_status", ""),
                                "new_stage": extra.get("new_stage"),
                                "auto_moved": extra.get("new_stage") is not None,
                                "notification_type": extra.get("notification_type", "info"),
                                "title": getattr(activity, 'title', '') or "",
                                "description": getattr(activity, 'description', '') or "",
                                "action_label": getattr(activity, 'action_label', 'Ver Candidato') or "Ver Candidato",
                                "action_url": getattr(activity, 'action_url', '') or "",
                                "category": getattr(activity, 'category', '') or "",
                                "timestamp": activity.created_at.isoformat() if hasattr(activity, 'created_at') and activity.created_at else "",
                            }
                            yield f"data: {json.dumps(event)}\n\n"
                    else:
                        yield ": keepalive\n\n"
            except Exception as e:
                logger.error(f"SSE error: {e}")
                yield ": error\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/transition/return-event", response_model=ReturnEventResponse)
async def process_return_event(
    request: ReturnEventRequest,
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    """
    Process a candidate return event.

    Used when a candidate completes an action (screening, interview confirmation,
    test submission, document upload, offer response) to update their sub-status,
    optionally auto-move to a new stage, and notify the recruiter.

    Valid event_types:
    - screening_complete, screening_expired
    - interview_confirmed, interview_declined, interview_completed, interview_no_show
    - test_submitted, test_expired
    - documents_received
    - offer_accepted, offer_declined

    Auto-move rules:
    - offer_accepted → moves candidate to "hired" stage
    - offer_declined → moves candidate to "offer_declined" stage
    - All other events → only update sub-status (no stage change)
    """
    try:
        service = ReturnEventService(stage_repo.db)
        result = await service.process_event(
            vacancy_candidate_id=request.vacancy_candidate_id,
            event_type=request.event_type,
            metadata=request.metadata,
            triggered_by=request.triggered_by,
        )

        auto_moved = result.get("new_stage") is not None and result.get("success", False)

        logger.info(
            f"Return event processed: type={request.event_type}, "
            f"candidate={request.vacancy_candidate_id}, "
            f"success={result.get('success')}, auto_moved={auto_moved}"
        )

        return ReturnEventResponse(
            success=result.get("success", False),
            event_type=result.get("event_type", request.event_type),
            new_sub_status=result.get("new_sub_status"),
            new_stage=result.get("new_stage"),
            activity_id=result.get("activity_id"),
            notification_sent=result.get("notification_sent", False),
            auto_moved=auto_moved,
            error=result.get("error"),
        )
    except Exception as e:
        logger.error(f"Error processing return event: {e}", exc_info=True)
        return ReturnEventResponse(
            success=False,
            event_type=request.event_type,
            error=str(e),
        )


@router.post("/transition/return-event/bulk", response_model=None)
async def process_bulk_return_events(
    request: BulkReturnEventRequest,
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    """
    Process multiple return events in batch.
    Useful for webhook payloads that report multiple candidate completions at once.
    """
    results = []
    service = ReturnEventService(stage_repo.db)

    for event in request.events:
        try:
            result = await service.process_event(
                vacancy_candidate_id=event.vacancy_candidate_id,
                event_type=event.event_type,
                metadata=event.metadata,
                triggered_by=event.triggered_by,
            )
            results.append({
                "vacancy_candidate_id": event.vacancy_candidate_id,
                "event_type": event.event_type,
                **result,
            })
        except Exception as e:
            results.append({
                "vacancy_candidate_id": event.vacancy_candidate_id,
                "event_type": event.event_type,
                "success": False,
                "error": str(e),
            })

    success_count = sum(1 for r in results if r.get("success"))
    logger.info(f"Bulk return events processed: {success_count}/{len(results)} successful")

    return {
        "total": len(results),
        "success_count": success_count,
        "failure_count": len(results) - success_count,
        "results": results,
    }


@router.get("/transition/return-event/recent", response_model=None)
async def get_recent_return_events(
    since: str | None = Query(None, description="ISO timestamp to fetch events since"),
    job_id: str | None = Query(None),
    company_id: str | None = Query(None, description="Company ID for scoping"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    """Get recent return events for polling/real-time updates."""
    try:
        from sqlalchemy import select as sa_select

        from app.models.activity_feed import ActivityFeed

        query = sa_select(ActivityFeed).where(
            ActivityFeed.activity_type.like("return_event_%")  # type: ignore[union-attr]
        )

        if since:
            from datetime import datetime as dt
            try:
                since_dt = dt.fromisoformat(since.replace('Z', '+00:00'))
                query = query.where(ActivityFeed.created_at > since_dt)  # type: ignore[operator]
            except ValueError:
                pass

        effective_company_id = company_id or get_user_company_id(current_user)
        if effective_company_id:
            pass

        query = query.order_by(ActivityFeed.created_at.desc()).limit(limit)  # type: ignore[union-attr]

        result = await stage_repo.db.execute(query)
        activities = result.scalars().all()

        events = []
        for activity in activities:
            extra = activity.extra_data or {} if hasattr(activity, 'extra_data') else {}
            events.append({
                "id": str(activity.id),
                "event_type": extra.get("event_type", activity.activity_type.replace("return_event_", "")),
                "vacancy_candidate_id": extra.get("vacancy_candidate_id", ""),
                "candidate_name": getattr(activity, 'actor_name', '') or "",
                "new_sub_status": extra.get("sub_status", ""),
                "new_stage": extra.get("new_stage"),
                "auto_moved": extra.get("new_stage") is not None,
                "notification_type": extra.get("notification_type", "info"),
                "title": getattr(activity, 'title', '') or "",
                "description": getattr(activity, 'description', '') or "",
                "action_label": getattr(activity, 'action_label', 'Ver Candidato') or "Ver Candidato",
                "action_url": getattr(activity, 'action_url', '') or "",
                "category": getattr(activity, 'category', '') or "",
                "timestamp": activity.created_at.isoformat() if hasattr(activity, 'created_at') and activity.created_at else "",
            })

        return {
            "events": events,
            "total": len(events),
            "since": since,
        }
    except Exception as e:
        logger.error(f"Error fetching recent return events: {e}", exc_info=True)
        return {"events": [], "total": 0, "since": since, "error": str(e)}


@router.get("/transition/return-event/types", response_model=None)
async def list_return_event_types():
    """
    List all supported return event types with their configurations.
    Useful for frontend to know which events are available and their effects.
    """
    event_types = []
    for event_type, config in RETURN_EVENT_CONFIG.items():
        event_types.append({
            "event_type": event_type,
            "sub_status": config["sub_status"],
            "auto_moves_to_stage": config.get("stage"),
            "category": config.get("category"),
            "priority": config.get("priority", "normal"),
            "description": config.get("description_template", "").replace("{candidate_name}", "[candidato]"),
        })

    return {
        "event_types": event_types,
        "total": len(event_types),
    }


@router.get("/pipeline/job/{job_id}/inheritance-status", response_model=None)
async def get_pipeline_inheritance_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    """Check if a job's pipeline is customized or inherited from company default."""
    try:
        from sqlalchemy import select as sa_select

        from app.models.job_vacancy import JobVacancy

        result = await stage_repo.db.execute(
            sa_select(JobVacancy).where(JobVacancy.id == job_id)
        )
        job = result.scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "job_id": str(job.id),
            "is_customized": bool(getattr(job, 'is_pipeline_customized', False)),  # type: ignore[truthy-bool]
            "pipeline_config": job.pipeline_config if hasattr(job, 'pipeline_config') else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking pipeline inheritance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/job/{job_id}/copy-from-company", response_model=None)
async def copy_company_pipeline_to_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    """Copy company's default pipeline configuration to a job (reset to default)."""
    try:
        from sqlalchemy import select as sa_select
        from sqlalchemy import update as sa_update

        from app.models.job_vacancy import JobVacancy

        job_result = await stage_repo.db.execute(
            sa_select(JobVacancy).where(JobVacancy.id == job_id)
        )
        job = job_result.scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        effective_user_company = get_user_company_id(current_user)
        if str(job.company_id) != effective_user_company:
            raise HTTPException(status_code=403, detail="Access denied")

        company_id = str(job.company_id)  # type: ignore[truthy-bool]

        company_stages = await stage_repo.list_for_company(company_id)

        pipeline_config = []
        for stage in company_stages:
            pipeline_config.append({
                "stage_id": str(stage.id),
                "name": stage.name,  # type: ignore[truthy-bool]
                "display_name": stage.display_name,  # type: ignore[truthy-bool]
                "stage_order": stage.stage_order,
                "action_behavior": stage.action_behavior or "passive",  # type: ignore[truthy-bool]
                "color": stage.color or "#6B7280",  # type: ignore[truthy-bool]
                "icon": stage.icon or "circle",  # type: ignore[truthy-bool]
                "stage_type": stage.stage_type or "active",  # type: ignore[truthy-bool]
                "is_system": bool(stage.is_initial or stage.is_final),  # type: ignore[truthy-bool]
                "sla_hours": stage.sla_hours,
                "default_channel": getattr(stage, 'default_channel', 'email') or "email",
            })

        stmt = (
            sa_update(JobVacancy)
            .where(JobVacancy.id == job_id)
            .values(
                pipeline_config=pipeline_config,
                is_pipeline_customized=False,
                updated_at=datetime.utcnow(),
            )
        )
        await stage_repo.db.execute(stmt)
        await stage_repo.db.commit()

        return {
            "success": True,
            "job_id": str(job.id),
            "is_customized": False,
            "stages_copied": len(pipeline_config),
            "pipeline_config": pipeline_config,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error copying company pipeline to job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/job/{job_id}/mark-customized", response_model=None)
async def mark_pipeline_customized(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
):
    """Mark a job's pipeline as customized (no longer inherits from company)."""
    try:
        from sqlalchemy import update as sa_update

        from app.models.job_vacancy import JobVacancy

        stmt = (
            sa_update(JobVacancy)
            .where(JobVacancy.id == job_id)
            .values(
                is_pipeline_customized=True,
                updated_at=datetime.utcnow(),
            )
        )
        result = await stage_repo.db.execute(stmt)
        await stage_repo.db.commit()

        row_count = getattr(result, 'rowcount', 0)  # type: ignore[union-attr]
        if row_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")

        return {"success": True, "job_id": job_id, "is_customized": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking pipeline as customized: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class InferBehaviorRequest(BaseModel):
    stage_name: str = Field(..., min_length=1, max_length=200, description="Nome da etapa customizada")
    description: str | None = None

class InferBehaviorResponse(BaseModel):
    suggested_behavior: str
    confidence: float
    alternatives: list[dict] = []
    method: str = "keyword"

@router.post("/stages/infer-behavior", response_model=None)
async def infer_stage_behavior(
    request: InferBehaviorRequest,
    method: str = Query(default="auto", regex="^(keyword|llm|auto)$"),
    current_user: User = Depends(get_current_active_user),
):
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
            result = await infer_behavior_auto(request.stage_name, request.description)

        return result
    except Exception as e:
        logger.error(f"Error inferring behavior: {e}", exc_info=True)
        return {"suggested_behavior": "passive", "confidence": 0.5, "alternatives": [], "method": "error_fallback"}
