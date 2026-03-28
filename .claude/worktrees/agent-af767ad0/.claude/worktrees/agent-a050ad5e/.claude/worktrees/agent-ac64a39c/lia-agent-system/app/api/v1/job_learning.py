"""
Job Learning API endpoints.

Provides REST endpoints for:
- Wizard suggestions (salary, skills, behavioral, TTF)
- Similar jobs lookup
- Pattern-based recommendations
- Analytics and metrics
"""
import logging
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.services.job_pattern_service import job_pattern_service

router = APIRouter(prefix="/learning", tags=["Job Learning"])
logger = logging.getLogger(__name__)


class WizardSuggestionsRequest(BaseModel):
    """Request for wizard suggestions."""
    company_id: str
    job_title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    location: Optional[str] = None
    existing_skills: Optional[List[str]] = Field(default_factory=list)
    existing_behavioral: Optional[List[str]] = Field(default_factory=list)


class SalarySuggestionRequest(BaseModel):
    """Request for salary suggestion."""
    company_id: str
    job_title: str
    seniority: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None


class SkillsRecommendationRequest(BaseModel):
    """Request for skills recommendation."""
    company_id: str
    job_title: str
    existing_skills: Optional[List[str]] = Field(default_factory=list)
    department: Optional[str] = None
    seniority: Optional[str] = None
    limit: int = 10


class BehavioralRecommendationRequest(BaseModel):
    """Request for behavioral recommendation."""
    company_id: str
    job_title: str
    existing_behavioral: Optional[List[str]] = Field(default_factory=list)
    department: Optional[str] = None
    seniority: Optional[str] = None
    limit: int = 10


class TimeFillPredictionRequest(BaseModel):
    """Request for time-to-fill prediction."""
    company_id: str
    job_title: str
    seniority: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None


class JobOutcomeRequest(BaseModel):
    """Request to record job outcome."""
    company_id: str
    job_id: str
    outcome_status: str
    job_title: Optional[str] = None
    department: Optional[str] = None
    seniority: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    final_salary: Optional[float] = None
    skills: Optional[List[str]] = Field(default_factory=list)
    behavioral_competencies: Optional[List[str]] = Field(default_factory=list)
    time_to_fill_days: Optional[int] = None
    candidates_total: Optional[int] = None
    candidates_screened: Optional[int] = None
    candidates_interviewed: Optional[int] = None
    candidates_offered: Optional[int] = None
    hire_quality_score: Optional[float] = None
    wizard_time_seconds: Optional[int] = None
    fields_auto_filled: Optional[int] = None
    fields_edited: Optional[int] = None
    extra_data: Optional[dict] = Field(default_factory=dict)


class SimilarJobsRequest(BaseModel):
    """Request for similar jobs."""
    company_id: str
    job_title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    limit: int = 5


@router.post("/wizard-suggestions")
async def get_wizard_suggestions(request: WizardSuggestionsRequest):
    """
    Get all wizard suggestions in a single call.
    
    Returns salary, skills, behavioral, and TTF predictions based on
    historical patterns for similar jobs.
    """
    try:
        suggestions = await job_pattern_service.get_wizard_suggestions(
            company_id=request.company_id,
            job_title=request.job_title,
            department=request.department,
            seniority=request.seniority,
            location=request.location,
            existing_skills=request.existing_skills,
            existing_behavioral=request.existing_behavioral,
        )
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error getting wizard suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/salary-suggestion")
async def get_salary_suggestion(request: SalarySuggestionRequest):
    """
    Get salary suggestion based on historical data.
    
    Returns recommended salary range with confidence score.
    """
    try:
        suggestion = await job_pattern_service.get_salary_suggestion(
            company_id=request.company_id,
            job_title=request.job_title,
            seniority=request.seniority,
            location=request.location,
            department=request.department,
        )
        
        return suggestion
        
    except Exception as e:
        logger.error(f"Error getting salary suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skills-recommendation")
async def get_skills_recommendation(request: SkillsRecommendationRequest):
    """
    Get skill recommendations based on similar jobs.
    
    Returns recommended skills with relevance scores.
    """
    try:
        recommendation = await job_pattern_service.get_skills_recommendation(
            company_id=request.company_id,
            job_title=request.job_title,
            existing_skills=request.existing_skills,
            department=request.department,
            seniority=request.seniority,
            limit=request.limit,
        )
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Error getting skills recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/behavioral-recommendation")
async def get_behavioral_recommendation(request: BehavioralRecommendationRequest):
    """
    Get behavioral competency recommendations.
    """
    try:
        recommendation = await job_pattern_service.get_behavioral_recommendation(
            company_id=request.company_id,
            job_title=request.job_title,
            existing_behavioral=request.existing_behavioral,
            department=request.department,
            seniority=request.seniority,
            limit=request.limit,
        )
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Error getting behavioral recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/time-to-fill")
async def predict_time_to_fill(request: TimeFillPredictionRequest):
    """
    Predict time-to-fill based on similar jobs.
    
    Returns estimated days with confidence and factors.
    """
    try:
        prediction = await job_pattern_service.predict_time_to_fill(
            company_id=request.company_id,
            job_title=request.job_title,
            seniority=request.seniority,
            location=request.location,
            salary_min=request.salary_min,
            salary_max=request.salary_max,
        )
        
        return prediction
        
    except Exception as e:
        logger.error(f"Error predicting time-to-fill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/success-profile")
async def get_success_profile(request: SimilarJobsRequest):
    """
    Get success profile based on successful hires.
    
    Returns ideal candidate profile with skills and competencies.
    """
    try:
        profile = await job_pattern_service.get_success_profile(
            company_id=request.company_id,
            job_title=request.job_title,
            department=request.department,
        )
        
        return profile
        
    except Exception as e:
        logger.error(f"Error getting success profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar-jobs")
async def find_similar_jobs(request: SimilarJobsRequest):
    """
    Find similar job patterns for reference.
    
    Returns list of similar jobs with their patterns.
    """
    try:
        patterns = await job_pattern_service.find_similar_patterns(
            company_id=request.company_id,
            job_title=request.job_title,
            department=request.department,
            seniority=request.seniority,
            limit=request.limit,
        )
        
        return {
            "patterns": [p.to_dict() for p in patterns],
            "count": len(patterns),
        }
        
    except Exception as e:
        logger.error(f"Error finding similar jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-outcome")
async def record_job_outcome(request: JobOutcomeRequest):
    """
    Record a job outcome for learning.
    
    Called when a job is filled, closed, or cancelled.
    Updates patterns for future recommendations.
    """
    try:
        outcome = await job_pattern_service.record_job_outcome(
            company_id=request.company_id,
            job_id=request.job_id,
            outcome_data=request.model_dump(),
        )
        
        return {
            "success": True,
            "outcome_id": str(outcome.id),
            "message": "Outcome recorded and patterns updated",
        }
        
    except Exception as e:
        logger.error(f"Error recording job outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{company_id}")
async def list_patterns(
    company_id: str,
    pattern_type: Optional[str] = Query(None),
    min_samples: int = Query(3),
    limit: int = Query(20),
):
    """
    List job patterns for a company.
    
    Returns patterns ordered by confidence and sample count.
    """
    try:
        from sqlalchemy import select, and_
        from app.core.database import AsyncSessionLocal
        from app.models.job_pattern import JobPattern
        
        async with AsyncSessionLocal() as db:
            conditions = [
                JobPattern.company_id == UUID(company_id),
                JobPattern.is_active == True,
                JobPattern.sample_count >= min_samples,
            ]
            
            if pattern_type:
                conditions.append(JobPattern.pattern_type == pattern_type)
            
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
            
    except Exception as e:
        logger.error(f"Error listing patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))
