"""
Job Learning API endpoints.

Provides REST endpoints for:
- Wizard suggestions (salary, skills, behavioral, TTF)
- Similar jobs lookup
- Pattern-based recommendations
- Analytics and metrics
"""
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.domains.job_management.services.job_pattern_service import job_pattern_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/learning", tags=["Job Learning"])
logger = logging.getLogger(__name__)


class WizardSuggestionsRequest(WeDoBaseModel):
    """Request for wizard suggestions."""
    job_title: str
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    existing_skills: list[str] | None = Field(default_factory=list)
    existing_behavioral: list[str] | None = Field(default_factory=list)


class SalarySuggestionRequest(WeDoBaseModel):
    """Request for salary suggestion."""
    job_title: str
    seniority: str | None = None
    location: str | None = None
    department: str | None = None


class SkillsRecommendationRequest(WeDoBaseModel):
    """Request for skills recommendation."""
    job_title: str
    existing_skills: list[str] | None = Field(default_factory=list)
    department: str | None = None
    seniority: str | None = None
    limit: int = 10


class BehavioralRecommendationRequest(WeDoBaseModel):
    """Request for behavioral recommendation."""
    job_title: str
    existing_behavioral: list[str] | None = Field(default_factory=list)
    department: str | None = None
    seniority: str | None = None
    limit: int = 10


class TimeFillPredictionRequest(WeDoBaseModel):
    """Request for time-to-fill prediction."""
    job_title: str
    seniority: str | None = None
    location: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None


class JobOutcomeRequest(WeDoBaseModel):
    """Request to record job outcome."""
    job_id: str
    outcome_status: str
    job_title: str | None = None
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    work_model: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    final_salary: float | None = None
    skills: list[str] | None = Field(default_factory=list)
    behavioral_competencies: list[str] | None = Field(default_factory=list)
    time_to_fill_days: int | None = None
    candidates_total: int | None = None
    candidates_screened: int | None = None
    candidates_interviewed: int | None = None
    candidates_offered: int | None = None
    hire_quality_score: float | None = None
    wizard_time_seconds: int | None = None
    fields_auto_filled: int | None = None
    fields_edited: int | None = None
    extra_data: dict | None = Field(default_factory=dict)


class SimilarJobsRequest(WeDoBaseModel):
    """Request for similar jobs."""
    job_title: str
    department: str | None = None
    seniority: str | None = None
    limit: int = 5


@router.post("/wizard-suggestions", response_model=None)
# TODO(phase2): extract to repository — job learning pattern storage
async def get_wizard_suggestions(request: WizardSuggestionsRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get all wizard suggestions in a single call.
    
    Returns salary, skills, behavioral, and TTF predictions based on
    historical patterns for similar jobs.
    """
    try:
        suggestions = await job_pattern_service.get_wizard_suggestions(
            company_id=company_id,
            job_title=request.job_title,
            department=request.department,
            seniority=request.seniority,
            location=request.location,
            existing_skills=request.existing_skills,
            existing_behavioral=request.existing_behavioral,
        )
        
        return suggestions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wizard suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/salary-suggestion", response_model=None)
async def get_salary_suggestion(request: SalarySuggestionRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get salary suggestion based on historical data.
    
    Returns recommended salary range with confidence score.
    """
    try:
        suggestion = await job_pattern_service.get_salary_suggestion(
            company_id=company_id,
            job_title=request.job_title,
            seniority=request.seniority,
            location=request.location,
            department=request.department,
        )
        
        return suggestion
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting salary suggestion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/skills-recommendation", response_model=None)
async def get_skills_recommendation(request: SkillsRecommendationRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get skill recommendations based on similar jobs.
    
    Returns recommended skills with relevance scores.
    """
    try:
        recommendation = await job_pattern_service.get_skills_recommendation(
            company_id=company_id,
            job_title=request.job_title,
            existing_skills=request.existing_skills,
            department=request.department,
            seniority=request.seniority,
            limit=request.limit,
        )
        
        return recommendation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skills recommendation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/behavioral-recommendation", response_model=None)
async def get_behavioral_recommendation(request: BehavioralRecommendationRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get behavioral competency recommendations.
    """
    try:
        recommendation = await job_pattern_service.get_behavioral_recommendation(
            company_id=company_id,
            job_title=request.job_title,
            existing_behavioral=request.existing_behavioral,
            department=request.department,
            seniority=request.seniority,
            limit=request.limit,
        )
        
        return recommendation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting behavioral recommendation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/time-to-fill", response_model=None)
async def predict_time_to_fill(request: TimeFillPredictionRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Predict time-to-fill based on similar jobs.
    
    Returns estimated days with confidence and factors.
    """
    try:
        prediction = await job_pattern_service.predict_time_to_fill(
            company_id=company_id,
            job_title=request.job_title,
            seniority=request.seniority,
            location=request.location,
            salary_min=request.salary_min,
            salary_max=request.salary_max,
        )
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting time-to-fill: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/success-profile", response_model=None)
async def get_success_profile(request: SimilarJobsRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get success profile based on successful hires.
    
    Returns ideal candidate profile with skills and competencies.
    """
    try:
        profile = await job_pattern_service.get_success_profile(
            company_id=company_id,
            job_title=request.job_title,
            department=request.department,
        )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting success profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/similar-jobs", response_model=None)
async def find_similar_jobs(request: SimilarJobsRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Find similar job patterns for reference.
    
    Returns list of similar jobs with their patterns.
    """
    try:
        patterns = await job_pattern_service.find_similar_patterns(
            company_id=company_id,
            job_title=request.job_title,
            department=request.department,
            seniority=request.seniority,
            limit=request.limit,
        )
        
        return {
            "patterns": [p.to_dict() for p in patterns],
            "count": len(patterns),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar jobs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/record-outcome", response_model=None)
async def record_job_outcome(request: JobOutcomeRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Record a job outcome for learning.
    
    Called when a job is filled, closed, or cancelled.
    Updates patterns for future recommendations.
    """
    try:
        outcome = await job_pattern_service.record_job_outcome(
            company_id=company_id,
            job_id=request.job_id,
            outcome_data=request.model_dump(),
        )
        
        return {
            "success": True,
            "outcome_id": str(outcome.id),
            "message": "Outcome recorded and patterns updated",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording job outcome: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/patterns/{company_id}", response_model=None)
async def list_patterns(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    pattern_type: str | None = Query(None),
    min_samples: int = Query(3),
    limit: int = Query(20),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    List job patterns for a company.
    
    Returns patterns ordered by confidence and sample count.
    """
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.job_pattern import JobPattern
        
        async with AsyncSessionLocal() as db:
            conditions = [
                JobPattern.company_id == UUID(company_id),
                JobPattern.is_active,
                JobPattern.sample_count >= min_samples,
            ]
            
            if pattern_type:
                conditions.append(JobPattern.pattern_type == pattern_type)
            
            # TENANT-EXEMPT: conditions list built dynamically above with
            # JobPattern.company_id == UUID(company_id) as first filter (sensor AST
            # cannot follow indirection); endpoint gated via Depends(require_company_id)
            result = await db.execute(
                select(JobPattern)
                .where(and_(*conditions))
                .order_by(
                    JobPattern.confidence.desc(),
                    JobPattern.sample_count.desc()
                )
                .limit(limit)
            )
            
            patterns = result.scalars().all()
            
            return {
                "patterns": [p.to_dict() for p in patterns],
                "count": len(patterns),
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing patterns: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

reorder_collection_before_item(router)
