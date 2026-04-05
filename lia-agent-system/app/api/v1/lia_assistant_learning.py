"""
LIA Assistant — Learning Hub endpoints.

Extracted from lia_assistant.py (Phase 5 decomposition).
All routes share prefix="/lia" to preserve existing /api/v1/lia/learning/* URLs.
"""
from typing import Dict, Any, List, Optional, Any
from enum import Enum
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.services.learning_hub_service import learning_hub_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia", tags=["lia-learning"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SkillConfirmationRequest(BaseModel):
    company_id: str
    skill_name: str
    skill_type: str = "technical"
    role: Optional[str] = None
    seniority: Optional[str] = None
    accepted: bool


class SkillConfirmationResponse(BaseModel):
    success: bool
    item_id: Optional[str] = None
    is_new: bool
    times_confirmed: int
    is_promoted: bool
    message: str


class ResponsibilityConfirmationRequest(BaseModel):
    company_id: str
    description: str
    category: Optional[str] = None
    role: Optional[str] = None
    seniority: Optional[str] = None
    accepted: bool


class ResponsibilityConfirmationResponse(BaseModel):
    success: bool
    item_id: Optional[str] = None
    is_new: bool
    times_confirmed: int
    is_promoted: bool
    message: str


class LearningContextRequest(BaseModel):
    company_id: str
    role: Optional[str] = None
    seniority: Optional[str] = None


class LearningContextResponse(BaseModel):
    company_skills: List[Dict[str, Any]]
    company_responsibilities: List[Dict[str, Any]]
    patterns: Dict[str, Any]
    success_rate: Dict[str, float]


class JobOutcomeType(str, Enum):
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REPOSTED = "reposted"


class JobOutcomeRequest(BaseModel):
    company_id: str
    job_id: UUID
    outcome: JobOutcomeType
    time_to_fill_days: Optional[int] = None
    salary_initial_min: Optional[float] = None
    salary_initial_max: Optional[float] = None
    salary_final: Optional[float] = None
    candidate_count_total: Optional[int] = None
    candidate_count_screened: Optional[int] = None
    candidate_count_interviewed: Optional[int] = None
    candidate_count_offered: Optional[int] = None
    satisfaction_score: Optional[float] = None
    role: Optional[str] = None
    seniority: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = None
    skills_used: Optional[List[str]] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None


class JobOutcomeResponse(BaseModel):
    success: bool
    outcome_id: Optional[str] = None
    outcome: Optional[str] = None
    patterns_updated: Optional[Dict[str, Any]] = None
    message: str
    error: Optional[str] = None


class OutcomeInsightsRequest(BaseModel):
    company_id: str
    role: Optional[str] = None
    seniority: Optional[str] = None


class OutcomeInsightsResponse(BaseModel):
    has_data: bool
    total_jobs: Optional[int] = None
    filled_jobs: Optional[int] = None
    fill_rate: Optional[float] = None
    avg_time_to_fill_days: Optional[float] = None
    salary_range: Optional[Dict[str, float]] = None
    top_skills: Optional[List[Dict[str, Any]]] = None
    filters_applied: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None


class StageFeedbackRequest(BaseModel):
    company_id: str
    stage_number: int
    field_name: str
    suggested_value: Optional[Any] = None
    accepted_value: Optional[Any] = None
    was_accepted: bool = True
    was_modified: bool = False
    job_id: Optional[str] = None
    stage_name: Optional[str] = None
    role: Optional[str] = None
    seniority: Optional[str] = None
    confidence_before: Optional[float] = None
    created_by: Optional[str] = None


class StageFeedbackResponse(BaseModel):
    success: bool
    feedback_id: Optional[str] = None
    stage: Optional[int] = None
    was_accepted: Optional[bool] = None
    was_modified: Optional[bool] = None
    error: Optional[str] = None


class LearningDashboardRequest(BaseModel):
    company_id: str


class LearningDashboardResponse(BaseModel):
    summary: Optional[Dict[str, Any]] = None
    stage_analytics: Optional[Dict[str, Any]] = None
    outcome_insights: Optional[Dict[str, Any]] = None
    success_rates: Optional[Dict[str, Any]] = None
    learning_health: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SkillsDeduplicatedRequest(BaseModel):
    company_id: str
    role: Optional[str] = None
    exclude_already_selected: Optional[List[str]] = None


class SkillsDeduplicatedResponse(BaseModel):
    skills: List[Dict[str, Any]]
    total: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/learning/confirm-skill", response_model=SkillConfirmationResponse)
async def confirm_skill(
    request: SkillConfirmationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> SkillConfirmationResponse:
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
    except Exception as e:
        logger.error(f"Error confirming skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/confirm-responsibility", response_model=ResponsibilityConfirmationResponse)
async def confirm_responsibility(
    request: ResponsibilityConfirmationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> ResponsibilityConfirmationResponse:
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
    except Exception as e:
        logger.error(f"Error confirming responsibility: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/context", response_model=LearningContextResponse)
async def get_learning_context(
    request: LearningContextRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> LearningContextResponse:
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
    except Exception as e:
        logger.error(f"Error getting learning context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/job-outcome", response_model=JobOutcomeResponse)
async def record_job_outcome(
    request: JobOutcomeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> JobOutcomeResponse:
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
    except Exception as e:
        logger.error(f"Error recording job outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/outcome-insights", response_model=OutcomeInsightsResponse)
async def get_outcome_insights(
    request: OutcomeInsightsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> OutcomeInsightsResponse:
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
    except Exception as e:
        logger.error(f"Error getting outcome insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/stage-feedback", response_model=StageFeedbackResponse)
async def record_stage_feedback(
    request: StageFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> StageFeedbackResponse:
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
    except Exception as e:
        logger.error(f"Error recording stage feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/dashboard", response_model=LearningDashboardResponse)
async def get_learning_dashboard(
    request: LearningDashboardRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> LearningDashboardResponse:
    try:
        dashboard = await learning_hub_service.get_learning_dashboard(
            db=db,
            company_id=request.company_id
        )
        return LearningDashboardResponse(
            summary=dashboard.get("summary"),
            stage_analytics=dashboard.get("stage_analytics"),
            outcome_insights=dashboard.get("outcome_insights"),
            success_rates=dashboard.get("success_rates"),
            learning_health=dashboard.get("learning_health"),
            error=dashboard.get("error")
        )
    except Exception as e:
        logger.error(f"Error getting learning dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/skills-deduplicated", response_model=SkillsDeduplicatedResponse)
async def get_skills_deduplicated(
    request: SkillsDeduplicatedRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> SkillsDeduplicatedResponse:
    try:
        skills = await learning_hub_service.get_skills_without_duplicates(
            db=db,
            company_id=current_user.company_id,
            role=request.role,
            exclude_already_selected=request.exclude_already_selected
        )
        return SkillsDeduplicatedResponse(skills=skills, total=len(skills))
    except Exception as e:
        logger.error(f"Error getting deduplicated skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))
