"""
LIA Field Toggles API endpoints.

Manages field toggle configurations for companies in the LIA wizard.
"""
import logging
import uuid as uuid_lib
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.core.database import get_db, get_tenant_db
from app.domains.cv_screening.services.lia_field_config_service import invalidate_lia_field_config_cache
from app.shared.services.tenant_context_service import invalidate_tenant_context_cache
from app.models.lia_field_toggles import DEFAULT_FIELD_TOGGLES, FIELD_FALLBACK_CONFIG, LiaFieldToggle
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["field-toggles"])


class FieldToggleResponse(BaseModel):
    """Response for a single field toggle."""
    field_key: str
    is_active: bool
    comment: str | None = None
    fallback_strategies: list[str] | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None


class FieldTogglesResponse(BaseModel):
    """Response containing all field toggles for a company."""
    company_id: str
    toggles: dict[str, bool]
    comments: dict[str, str | None]
    details: list[FieldToggleResponse]


class FieldToggleUpdate(WeDoBaseModel):
    """Update for a single field toggle."""
    is_active: bool
    comment: str | None = None


class FieldTogglesUpdate(WeDoBaseModel):
    """Request to update field toggles."""
    toggles: dict[str, bool]
    comments: dict[str, str] | None = None


class CompletenessCheckRequest(WeDoBaseModel):
    """Request for completeness check."""
    job_data: dict[str, Any]
    toggles: dict[str, bool] | None = None


class FieldSuggestionResponse(BaseModel):
    """Response for a field suggestion."""
    value: Any
    source: str
    confidence: float
    explanation: str


class CompletenessCheckResponse(BaseModel):
    """Response for completeness check."""
    filled_fields: list[str]
    missing_critical: list[str]
    missing_important: list[str]
    toggled_off: list[str]
    can_publish: bool
    completeness_score: int
    field_details: dict[str, dict[str, Any]]
    suggestions: dict[str, FieldSuggestionResponse]


@router.get("/{company_id}/field-toggles", response_model=FieldTogglesResponse)
async def get_field_toggles(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_demo), 
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get all field toggles for a company.
    Returns default toggles if none are configured.
    
    Toggle controls AI/LLM data consumption only:
    - is_active=True: AI agents consume this field's company data
    - is_active=False: AI uses fallback strategies (job history, benchmarks)
    
    Fields still appear in wizard UI regardless of toggle state.
    """
    try:
        company_uuid = uuid_lib.UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company_id format")
    
    result = await db.execute(
        select(LiaFieldToggle).where(LiaFieldToggle.company_id == company_uuid)  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
    )
    existing_toggles = result.scalars().all()
    
    if existing_toggles:
        toggles_dict = {t.field_key: t.is_active for t in existing_toggles}
        comments_dict = {t.field_key: t.comment for t in existing_toggles}
        details = [
            FieldToggleResponse(
                field_key=t.field_key,
                is_active=t.is_active,
                comment=t.comment,
                fallback_strategies=FIELD_FALLBACK_CONFIG.get(t.field_key, ["skip"]) if not t.is_active else None,
                updated_at=t.updated_at,
                updated_by=t.updated_by
            )
            for t in existing_toggles
        ]
    else:
        toggles_dict = {t["field_key"]: t["is_active"] for t in DEFAULT_FIELD_TOGGLES}
        comments_dict = {t["field_key"]: None for t in DEFAULT_FIELD_TOGGLES}
        details = [
            FieldToggleResponse(
                field_key=t["field_key"],
                is_active=t["is_active"],
                comment=None,
                fallback_strategies=FIELD_FALLBACK_CONFIG.get(t["field_key"], ["skip"]) if not t["is_active"] else None,
                updated_at=None,
                updated_by=None
            )
            for t in DEFAULT_FIELD_TOGGLES
        ]
    
    return FieldTogglesResponse(
        company_id=company_id,
        toggles=toggles_dict,
        comments=comments_dict,
        details=details
    )


@router.put("/{company_id}/field-toggles", response_model=FieldTogglesResponse)
async def update_field_toggles(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    update_data: FieldTogglesUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: dict = Depends(get_current_user_or_demo), 
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Update field toggles and comments for a company.
    Creates new toggles if they don't exist.
    
    Toggle controls AI/LLM data consumption:
    - When is_active=False, AI agents will use fallback strategies
    - Comments provide additional instructions for AI agents
    """
    try:
        company_uuid = uuid_lib.UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company_id format")
    
    user_email = current_user.get("email", "system")
    comments = update_data.comments or {}
    
    result = await db.execute(
        select(LiaFieldToggle).where(LiaFieldToggle.company_id == company_uuid)  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
    )
    existing_toggles = {t.field_key: t for t in result.scalars().all()}
    
    updated_toggles = []
    
    for field_key, is_active in update_data.toggles.items():
        comment = comments.get(field_key)
        
        if field_key in existing_toggles:
            toggle = existing_toggles[field_key]
            toggle.is_active = is_active
            toggle.comment = comment if comment is not None else toggle.comment
            toggle.updated_at = datetime.utcnow()
            toggle.updated_by = user_email
            updated_toggles.append(toggle)
        else:
            new_toggle = LiaFieldToggle(
                company_id=company_uuid,
                field_key=field_key,
                is_active=is_active,
                comment=comment,
                updated_by=user_email
            )
            db.add(new_toggle)
            updated_toggles.append(new_toggle)
    
    
    result = await db.execute(
        select(LiaFieldToggle).where(LiaFieldToggle.company_id == company_uuid)  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
    )
    all_toggles = result.scalars().all()
    
    toggles_dict = {t.field_key: t.is_active for t in all_toggles}
    comments_dict = {t.field_key: t.comment for t in all_toggles}
    details = [
        FieldToggleResponse(
            field_key=t.field_key,
            is_active=t.is_active,
            comment=t.comment,
            fallback_strategies=FIELD_FALLBACK_CONFIG.get(t.field_key, ["skip"]) if not t.is_active else None,
            updated_at=t.updated_at,
            updated_by=t.updated_by
        )
        for t in all_toggles
    ]
    
    invalidate_lia_field_config_cache(company_id)
    invalidate_tenant_context_cache(company_id)

    return FieldTogglesResponse(
        company_id=company_id,
        toggles=toggles_dict,
        comments=comments_dict,
        details=details
    )


@router.post("/{company_id}/check-completeness", response_model=CompletenessCheckResponse)
async def check_job_completeness(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: CompletenessCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_demo), 
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Check completeness of job data and get suggestions for missing fields.
    """
    from app.models.company import CompanyProfile
    from app.models.job_vacancy import JobVacancy
    from app.shared.services.config_completeness_service import config_completeness_service
    
    try:
        company_uuid = uuid_lib.UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company_id format")
    
    toggles = request.toggles
    if toggles is None:
        result = await db.execute(
            select(LiaFieldToggle).where(LiaFieldToggle.company_id == company_uuid)  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
        )
        existing_toggles = result.scalars().all()
        if existing_toggles:
            toggles = {t.field_key: t.is_active for t in existing_toggles}
        else:
            toggles = {t["field_key"]: t["is_active"] for t in DEFAULT_FIELD_TOGGLES}
    
    company_result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.id == company_uuid)  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
    )
    company_profile = company_result.scalar_one_or_none()
    company_config = {}
    if company_profile:
        company_config = {
            "work_model": company_profile.additional_data.get("work_model") if company_profile.additional_data else None,
            "employment_types": company_profile.additional_data.get("employment_types") if company_profile.additional_data else None,
            "seniority_levels": company_profile.additional_data.get("seniority_levels") if company_profile.additional_data else None,
        }
    
    jobs_result = await db.execute(
        select(JobVacancy)  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
        .where(JobVacancy.company_id == company_id)
        .order_by(JobVacancy.created_at.desc())
        .limit(10)
    )
    previous_jobs = [
        {
            "seniority_level": j.seniority_level,
            "department": j.department,
            "salary_range": j.salary_range,
            "benefits": j.benefits,
            "behavioral_competencies": j.behavioral_competencies,
            "technical_requirements": j.technical_requirements,
            "work_model": j.work_model,
            "employment_type": j.employment_type,
            "description": j.description,
        }
        for j in jobs_result.scalars().all()
    ]
    
    completeness_result = config_completeness_service.check_completeness(
        job_data=request.job_data,
        company_config=company_config,
        toggles=toggles
    )
    
    all_missing = completeness_result.missing_critical + completeness_result.missing_important
    suggestions_data = config_completeness_service.get_all_suggestions(
        missing_fields=all_missing,
        job_data=request.job_data,
        company_config=company_config,
        previous_jobs=previous_jobs
    )
    
    suggestions = {
        field_key: FieldSuggestionResponse(
            value=suggestion.value,
            source=suggestion.source.value,
            confidence=suggestion.confidence,
            explanation=suggestion.explanation
        )
        for field_key, suggestion in suggestions_data.items()
    }
    
    return CompletenessCheckResponse(
        filled_fields=completeness_result.filled_fields,
        missing_critical=completeness_result.missing_critical,
        missing_important=completeness_result.missing_important,
        toggled_off=completeness_result.toggled_off,
        can_publish=completeness_result.can_publish,
        completeness_score=completeness_result.completeness_score,
        field_details=completeness_result.field_details,
        suggestions=suggestions
    )


@router.post("/{company_id}/field-toggles/seed", response_model=None)
async def seed_default_toggles(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_tenant_db),
    current_user: dict = Depends(get_current_user_or_demo), 
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Seed default field toggles for a company.
    Only creates toggles that don't already exist.
    """
    try:
        company_uuid = uuid_lib.UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company_id format")
    
    result = await db.execute(
        select(LiaFieldToggle).where(LiaFieldToggle.company_id == company_uuid)  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
    )
    existing_keys = {t.field_key for t in result.scalars().all()}
    
    created_count = 0
    for toggle_def in DEFAULT_FIELD_TOGGLES:
        if toggle_def["field_key"] not in existing_keys:
            new_toggle = LiaFieldToggle(
                company_id=company_uuid,
                field_key=toggle_def["field_key"],
                is_active=toggle_def["is_active"],
                updated_by="system"
            )
            db.add(new_toggle)
            created_count += 1
    
    
    return {
        "message": f"Created {created_count} default toggles",
        "company_id": company_id
    }


class JobContextRequest(WeDoBaseModel):
    """Job context for better field resolution."""
    title: str | None = None
    seniority: str | None = None
    department: str | None = None


class FieldContextResponse(BaseModel):
    """Context for a single field."""
    field_key: str
    value: Any | None = None
    source: str
    source_explanation: str
    confidence: float
    is_toggle_active: bool
    recruiter_comment: str | None = None


class AgentContextResponse(BaseModel):
    """Complete context response for AI agents."""
    company_id: str
    context_prompt: str
    data_quality_score: float
    active_field_count: int
    inactive_field_count: int
    field_contexts: dict[str, FieldContextResponse]


@router.post("/{company_id}/agent-context", response_model=AgentContextResponse)
async def get_agent_context(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    job_context: JobContextRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_demo), 
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get AI agent context for job creation wizard.
    
    This endpoint provides:
    - Context prompt respecting toggle states
    - Fallback values for inactive fields (from job history, benchmarks)
    - Data source attribution for transparency
    - Data quality score
    
    Toggle behavior:
    - is_active=True: Uses company configuration data
    - is_active=False: Uses fallback strategies (job history, benchmarks)
    
    AI agents should call this endpoint before making suggestions.
    """
    from app.shared.services.lia_field_config_service import LiaFieldConfigService
    
    service = LiaFieldConfigService(db)
    
    job_ctx = None
    if job_context:
        job_ctx = {
            "title": job_context.title,
            "seniority": job_context.seniority,
            "department": job_context.department
        }
    
    result = await service.get_field_config(company_id, job_ctx)
    
    field_contexts = {
        key: FieldContextResponse(
            field_key=ctx.field_key,
            value=ctx.value,
            source=ctx.source.value,
            source_explanation=ctx.source_explanation,
            confidence=ctx.confidence,
            is_toggle_active=ctx.is_toggle_active,
            recruiter_comment=ctx.recruiter_comment
        )
        for key, ctx in result.field_contexts.items()
    }
    
    return AgentContextResponse(
        company_id=company_id,
        context_prompt=result.context_prompt,
        data_quality_score=result.data_quality_score,
        active_field_count=len(result.active_fields),
        inactive_field_count=len(result.inactive_fields),
        field_contexts=field_contexts
    )


class EmptyFieldAction(BaseModel):
    """Action for an empty field notification."""
    action: str
    label: str
    description: str


class EmptyFieldNotification(BaseModel):
    """Notification for a field with active toggle but empty value."""
    field_key: str
    field_label: str
    impact_description: str
    has_fallback: bool
    fallback_strategies: list[str]
    times_reminded: int
    actions: list[EmptyFieldAction]


class EmptyFieldsResponse(BaseModel):
    """Response with all empty active field notifications."""
    company_id: str
    user_id: str
    notifications: list[EmptyFieldNotification]
    total_empty_fields: int


class ReminderPreferenceUpdate(WeDoBaseModel):
    """Update for reminder preference."""
    action: str


class ReminderPreferenceResponse(BaseModel):
    """Response for reminder preference update."""
    field_key: str
    action: str
    remind_me: bool
    snooze_until: str | None = None
    times_reminded: int
    times_filled_with_lia: int


class FieldSuggestionRequest(WeDoBaseModel):
    """Request for field value suggestion."""
    job_context: JobContextRequest | None = None


class FieldValueSuggestion(BaseModel):
    """Suggested value for an empty field."""
    field_key: str
    field_label: str
    suggested_value: Any | None = None
    source: str
    source_icon: str
    source_explanation: str
    confidence: float
    formatted_value: str


@router.get("/{company_id}/empty-fields", response_model=EmptyFieldsResponse)
async def get_empty_field_notifications(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_or_demo), 
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get notifications for fields with active toggles but empty company config.
    
    This endpoint detects fields where:
    - The toggle is active (recruiter wants AI to use company data)
    - But the company config value is empty/null
    
    Returns notifications with impact description and available actions:
    - fill_now: LIA helps fill the field with suggestions
    - remind_later: Snooze for 7 days
    - dont_remind: Stop reminding for this field
    
    Respects user preferences (snooze, dont_remind).
    """
    from app.shared.services.lia_field_config_service import LiaFieldConfigService
    
    user_id = str(current_user.id)
    
    service = LiaFieldConfigService(db)
    notifications = await service.detect_empty_active_fields(company_id, user_id)
    
    return EmptyFieldsResponse(
        company_id=company_id,
        user_id=user_id,
        notifications=[
            EmptyFieldNotification(
                field_key=n["field_key"],
                field_label=n["field_label"],
                impact_description=n["impact_description"],
                has_fallback=n["has_fallback"],
                fallback_strategies=n["fallback_strategies"],
                times_reminded=n["times_reminded"],
                actions=[
                    EmptyFieldAction(
                        action=a["action"],
                        label=a["label"],
                        description=a["description"]
                    )
                    for a in n["actions"]
                ]
            )
            for n in notifications
        ],
        total_empty_fields=len(notifications)
    )


@router.post("/{company_id}/empty-fields/{field_key}/action", response_model=ReminderPreferenceResponse)
async def update_empty_field_preference(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    field_key: str,
    update: ReminderPreferenceUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user_or_demo), 
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Update recruiter's preference for an empty field reminder.
    
    Actions:
    - fill_now: Increments times_filled_with_lia, clears snooze
    - remind_later: Sets snooze for 7 days
    - dont_remind: Disables reminders for this field permanently
    - dismissed: Snoozes for 24 hours
    """
    from app.shared.services.lia_field_config_service import LiaFieldConfigService
    
    valid_actions = ["fill_now", "remind_later", "dont_remind", "dismissed"]
    if update.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Must be one of: {valid_actions}"
        )
    
    user_id = str(current_user.id)
    
    service = LiaFieldConfigService(db)
    result = await service.update_reminder_preference(
        company_id=company_id,
        user_id=user_id,
        field_key=field_key,
        action=update.action
    )
    
    return ReminderPreferenceResponse(
        field_key=result["field_key"],
        action=result["action"],
        remind_me=result["remind_me"],
        snooze_until=result["snooze_until"],
        times_reminded=result["times_reminded"],
        times_filled_with_lia=result["times_filled_with_lia"]
    )


@router.post("/{company_id}/empty-fields/{field_key}/suggest", response_model=FieldValueSuggestion)
async def suggest_field_value(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    field_key: str,
    request: FieldSuggestionRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_demo), 
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get AI suggestion for an empty field value.
    
    Uses fallback strategies (job history, market benchmarks) to suggest
    a value that the recruiter can use to fill the company config.
    
    Called when recruiter chooses "Preencher Agora" action.
    """
    from app.shared.services.lia_field_config_service import LiaFieldConfigService

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# See: app/domains/integrations_hub/services/rails_adapter.py
    
    job_ctx = None
    if request and request.job_context:
        job_ctx = {
            "title": request.job_context.title,
            "seniority": request.job_context.seniority,
            "department": request.job_context.department
        }
    
    service = LiaFieldConfigService(db)
    result = await service.suggest_field_value(
        company_id=company_id,
        field_key=field_key,
        job_context=job_ctx
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return FieldValueSuggestion(
        field_key=result["field_key"],
        field_label=result["field_label"],
        suggested_value=result["suggested_value"],
        source=result["source"],
        source_icon=result["source_icon"],
        source_explanation=result["source_explanation"],
        confidence=result["confidence"],
        formatted_value=result["formatted_value"]
    )

reorder_collection_before_item(router)
