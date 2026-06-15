"""
LIA Assistant — Learning Hub endpoints.

Extracted from lia_assistant.py (Phase 5 decomposition).
All routes share prefix="/lia" to preserve existing /api/v1/lia/learning/* URLs.
"""
import logging
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.shared.services.learning_hub_service import learning_hub_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia", tags=["lia-learning"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SkillConfirmationRequest(WeDoBaseModel):
    skill_name: str
    skill_type: str = "technical"
    role: str | None = None
    seniority: str | None = None
    accepted: bool


class SkillConfirmationResponse(BaseModel):
    success: bool
    item_id: str | None = None
    is_new: bool
    times_confirmed: int
    is_promoted: bool
    message: str


class ResponsibilityConfirmationRequest(WeDoBaseModel):
    description: str
    category: str | None = None
    role: str | None = None
    seniority: str | None = None
    accepted: bool


class ResponsibilityConfirmationResponse(BaseModel):
    success: bool
    item_id: str | None = None
    is_new: bool
    times_confirmed: int
    is_promoted: bool
    message: str


class LearningContextRequest(WeDoBaseModel):
    role: str | None = None
    seniority: str | None = None


class LearningContextResponse(BaseModel):
    company_skills: list[dict[str, Any]]
    company_responsibilities: list[dict[str, Any]]
    patterns: dict[str, Any]
    success_rate: dict[str, float]


class JobOutcomeType(StrEnum):
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REPOSTED = "reposted"


class JobOutcomeRequest(WeDoBaseModel):
    job_id: UUID
    outcome: JobOutcomeType
    time_to_fill_days: int | None = None
    salary_initial_min: float | None = None
    salary_initial_max: float | None = None
    salary_final: float | None = None
    candidate_count_total: int | None = None
    candidate_count_screened: int | None = None
    candidate_count_interviewed: int | None = None
    candidate_count_offered: int | None = None
    satisfaction_score: float | None = None
    role: str | None = None
    seniority: str | None = None
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    skills_used: list[str] | None = None
    notes: str | None = None
    created_by: str | None = None


class JobOutcomeResponse(BaseModel):
    success: bool
    outcome_id: str | None = None
    outcome: str | None = None
    patterns_updated: dict[str, Any] | None = None
    message: str
    error: str | None = None


class OutcomeInsightsRequest(WeDoBaseModel):
    role: str | None = None
    seniority: str | None = None


class OutcomeInsightsResponse(BaseModel):
    has_data: bool
    total_jobs: int | None = None
    filled_jobs: int | None = None
    fill_rate: float | None = None
    avg_time_to_fill_days: float | None = None
    salary_range: dict[str, float] | None = None
    top_skills: list[dict[str, Any]] | None = None
    filters_applied: dict[str, Any] | None = None
    message: str | None = None
    error: str | None = None


class StageFeedbackRequest(WeDoBaseModel):
    stage_number: int
    field_name: str
    suggested_value: Any | None = None
    accepted_value: Any | None = None
    was_accepted: bool = True
    was_modified: bool = False
    job_id: str | None = None
    stage_name: str | None = None
    role: str | None = None
    seniority: str | None = None
    confidence_before: float | None = None
    created_by: str | None = None


class StageFeedbackResponse(BaseModel):
    success: bool
    feedback_id: str | None = None
    stage: int | None = None
    was_accepted: bool | None = None
    was_modified: bool | None = None
    error: str | None = None


class LearningDashboardRequest(WeDoBaseModel):
    pass


class LearningDashboardResponse(BaseModel):
    summary: dict[str, Any] | None = None
    stage_analytics: dict[str, Any] | None = None
    outcome_insights: dict[str, Any] | None = None
    success_rates: dict[str, Any] | None = None
    learning_health: dict[str, Any] | None = None
    error: str | None = None


class SkillsDeduplicatedRequest(WeDoBaseModel):
    role: str | None = None
    exclude_already_selected: list[str] | None = None


class SkillsDeduplicatedResponse(BaseModel):
    skills: list[dict[str, Any]]
    total: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/learning/confirm-skill", response_model=SkillConfirmationResponse)
async def confirm_skill(
    request: SkillConfirmationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> SkillConfirmationResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        if request.accepted:
            result = await learning_hub_service.record_skill_confirmation(
                db=db,
                company_id=current_user.company_id,
                skill_name=request.skill_name,
                skill_type=request.skill_type,
                role=request.role,
                seniority=request.seniority
            )
            return SkillConfirmationResponse(
                success=result.success,
                item_id=result.item_id,
                is_new=result.is_new,
                times_confirmed=result.times_confirmed,
                is_promoted=result.is_promoted,
                message=result.message
            )
        else:
            success = await learning_hub_service.record_skill_rejection(
                db=db,
                company_id=current_user.company_id,
                skill_name=request.skill_name
            )
            return SkillConfirmationResponse(
                success=success,
                item_id=None,
                is_new=False,
                times_confirmed=0,
                is_promoted=False,
                message=f"Skill '{request.skill_name}' rejeitada" if success else "Erro ao rejeitar skill"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming skill: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/learning/confirm-responsibility", response_model=ResponsibilityConfirmationResponse)
async def confirm_responsibility(
    request: ResponsibilityConfirmationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> ResponsibilityConfirmationResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        if request.accepted:
            result = await learning_hub_service.record_responsibility_confirmation(
                db=db,
                company_id=current_user.company_id,
                description=request.description,
                category=request.category,
                role=request.role,
                seniority=request.seniority
            )
            return ResponsibilityConfirmationResponse(
                success=result.success,
                item_id=result.item_id,
                is_new=result.is_new,
                times_confirmed=result.times_confirmed,
                is_promoted=result.is_promoted,
                message=result.message
            )
        else:
            return ResponsibilityConfirmationResponse(
                success=True,
                item_id=None,
                is_new=False,
                times_confirmed=0,
                is_promoted=False,
                message="Responsabilidade rejeitada"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming responsibility: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/learning/context", response_model=LearningContextResponse)
async def get_learning_context(
    request: LearningContextRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> LearningContextResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        context = await learning_hub_service.get_learning_context(
            db=db,
            company_id=current_user.company_id,
            role=request.role,
            seniority=request.seniority
        )
        return LearningContextResponse(
            company_skills=context.company_skills,
            company_responsibilities=context.company_responsibilities,
            patterns=context.patterns,
            success_rate=context.success_rate
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning context: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/learning/job-outcome", response_model=JobOutcomeResponse)
async def record_job_outcome(
    request: JobOutcomeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> JobOutcomeResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        result = await learning_hub_service.record_job_outcome(
            db=db,
            company_id=current_user.company_id,
            job_id=request.job_id,
            outcome=request.outcome.value,
            time_to_fill_days=request.time_to_fill_days,
            salary_initial_min=request.salary_initial_min,
            salary_initial_max=request.salary_initial_max,
            salary_final=request.salary_final,
            candidate_count_total=request.candidate_count_total,
            candidate_count_screened=request.candidate_count_screened,
            candidate_count_interviewed=request.candidate_count_interviewed,
            candidate_count_offered=request.candidate_count_offered,
            satisfaction_score=request.satisfaction_score,
            role=request.role,
            seniority=request.seniority,
            department=request.department,
            location=request.location,
            work_model=request.work_model,
            skills_used=request.skills_used,
            notes=request.notes,
            created_by=request.created_by
        )
        return JobOutcomeResponse(
            success=result.get("success", False),
            outcome_id=result.get("outcome_id"),
            outcome=result.get("outcome"),
            patterns_updated=result.get("patterns_updated"),
            message=result.get("message", ""),
            error=result.get("error")
        )
    except ValueError as e:
        logger.error(f"Invalid job outcome value: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid outcome value: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording job outcome: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/learning/outcome-insights", response_model=OutcomeInsightsResponse)
async def get_outcome_insights(
    request: OutcomeInsightsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> OutcomeInsightsResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        insights = await learning_hub_service.get_outcome_insights(
            db=db,
            company_id=current_user.company_id,
            role=request.role,
            seniority=request.seniority
        )
        return OutcomeInsightsResponse(
            has_data=insights.get("has_data", False),
            total_jobs=insights.get("total_jobs"),
            filled_jobs=insights.get("filled_jobs"),
            fill_rate=insights.get("fill_rate"),
            avg_time_to_fill_days=insights.get("avg_time_to_fill_days"),
            salary_range=insights.get("salary_range"),
            top_skills=insights.get("top_skills"),
            filters_applied=insights.get("filters_applied"),
            message=insights.get("message"),
            error=insights.get("error")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting outcome insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/learning/stage-feedback", response_model=StageFeedbackResponse)
async def record_stage_feedback(
    request: StageFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> StageFeedbackResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        job_uuid = None
        if request.job_id:
            job_uuid = UUID(request.job_id)

        result = await learning_hub_service.record_stage_feedback(
            db=db,
            company_id=current_user.company_id,
            stage_number=request.stage_number,
            field_name=request.field_name,
            suggested_value=request.suggested_value,
            accepted_value=request.accepted_value,
            was_accepted=request.was_accepted,
            was_modified=request.was_modified,
            job_id=job_uuid,
            stage_name=request.stage_name,
            role=request.role,
            seniority=request.seniority,
            confidence_before=request.confidence_before,
            created_by=request.created_by
        )
        return StageFeedbackResponse(
            success=result.get("success", False),
            feedback_id=result.get("feedback_id"),
            stage=result.get("stage"),
            was_accepted=result.get("was_accepted"),
            was_modified=result.get("was_modified"),
            error=result.get("error")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording stage feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/learning/dashboard", response_model=LearningDashboardResponse)
async def get_learning_dashboard(
    request: LearningDashboardRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> LearningDashboardResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        dashboard = await learning_hub_service.get_learning_dashboard(
            db=db,
            company_id=company_id
        )
        return LearningDashboardResponse(
            summary=dashboard.get("summary"),
            stage_analytics=dashboard.get("stage_analytics"),
            outcome_insights=dashboard.get("outcome_insights"),
            success_rates=dashboard.get("success_rates"),
            learning_health=dashboard.get("learning_health"),
            error=dashboard.get("error")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/learning/skills-deduplicated", response_model=SkillsDeduplicatedResponse)
async def get_skills_deduplicated(
    request: SkillsDeduplicatedRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> SkillsDeduplicatedResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        skills = await learning_hub_service.get_skills_without_duplicates(
            db=db,
            company_id=current_user.company_id,
            role=request.role,
            exclude_already_selected=request.exclude_already_selected
        )
        return SkillsDeduplicatedResponse(skills=skills, total=len(skills))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deduplicated skills: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
