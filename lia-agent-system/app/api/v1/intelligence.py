"""
Intelligence Layer API endpoints.
Provides data quality assessment, pattern insights, and wizard enhancements.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.shared.services.intelligence_layer_service import intelligence_layer_service
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError
from app.shared.types import WeDoBaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class DataQualityResponse(BaseModel):
    total_jobs: int = 0
    filled_outcomes: int = 0
    months_of_data: int = 0
    pattern_detection_ready: bool = False
    correlation_analysis_ready: bool = False
    personalization_ready: bool = False
    has_minimum_data: bool = False
    recommendations: list[str] = Field(default_factory=list)


class IntelligenceContextRequest(WeDoBaseModel):
    role: str | None = None
    seniority: str | None = None
    department: str | None = None


class PatternAdjustmentRequest(WeDoBaseModel):
    field: str
    value: Any
    seniority: str | None = None


class PatternAdjustmentResponse(BaseModel):
    original_value: Any
    adjusted_value: Any
    adjustments_applied: list[str] = Field(default_factory=list)
    confidence_adjustment: float = 0.0


class WizardSuggestionResponse(BaseModel):
    field: str
    suggestion_type: str
    suggested_value: Any
    reason: str
    confidence: float
    source: str


@router.get("/data-quality", response_model=None)
async def get_data_quality(
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    """
    Get data quality assessment for the Intelligence Layer.
    
    Returns information about whether there's enough data for pattern detection,
    correlation analysis, and personalization.
    """
    company_id = get_user_company_id(current_user)
    try:
        report = await intelligence_layer_service.assess_data_quality(db, company_id)
        return DataQualityResponse(
            total_jobs=report.total_jobs,
            filled_outcomes=report.filled_outcomes,
            months_of_data=report.months_of_data,
            pattern_detection_ready=report.pattern_detection_ready,
            correlation_analysis_ready=report.correlation_analysis_ready,
            personalization_ready=report.personalization_ready,
            has_minimum_data=report.has_minimum_data,
            recommendations=report.recommendations,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data quality: {e}")
        raise LIAError(message="Error assessing data quality")


@router.post("/context", response_model=None)
async def get_intelligence_context(
    request: IntelligenceContextRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    """
    Get full intelligence context for a job creation session.
    
    This includes correction patterns, success profiles, correlations,
    and time-to-fill predictions relevant to the specified context.
    """
    company_id = get_user_company_id(current_user)
    try:
        context = await intelligence_layer_service.build_intelligence_context(
            db=db,
            company_id=company_id,
            recruiter_id=str(current_user.id),
            role=request.role,
            seniority=request.seniority,
            department=request.department,
        )
        
        return {
            "company_id": context.company_id,
            "recruiter_id": context.recruiter_id,
            "role": context.role,
            "seniority": context.seniority,
            "department": context.department,
            "data_quality": {
                "total_jobs": context.data_quality.total_jobs if context.data_quality else 0,
                "pattern_detection_ready": context.data_quality.pattern_detection_ready if context.data_quality else False,
                "correlation_analysis_ready": context.data_quality.correlation_analysis_ready if context.data_quality else False,
            },
            "correction_patterns_count": len(context.correction_patterns),
            "has_success_profile": context.success_profile is not None,
            "correlations_count": len(context.correlations),
            "time_to_fill_prediction": context.time_to_fill_prediction,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting intelligence context: {e}")
        raise LIAError(message="Error building intelligence context")


@router.post("/adjust-field", response_model=None)
async def adjust_field_value(
    request: PatternAdjustmentRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    """
    Apply pattern-based adjustments to a field value.
    
    Uses historical correction patterns to suggest adjustments
    for fields like salary, seniority, etc.
    """
    company_id = get_user_company_id(current_user)
    try:
        context = await intelligence_layer_service.build_intelligence_context(
            db=db,
            company_id=company_id,
            recruiter_id=str(current_user.id),
            seniority=request.seniority,
        )
        
        adjusted_value, adjustments, confidence_adj = intelligence_layer_service.apply_pattern_adjustment(
            field=request.field,
            value=request.value,
            patterns=context.correction_patterns,
            seniority=request.seniority,
        )
        
        return PatternAdjustmentResponse(
            original_value=request.value,
            adjusted_value=adjusted_value,
            adjustments_applied=adjustments,
            confidence_adjustment=confidence_adj,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting field: {e}")
        raise LIAError(message="Error applying pattern adjustment")


@router.get("/wizard-enhancements", response_model=None)
async def get_wizard_enhancements(
    seniority: str | None = None,
    department: str | None = None,
    role: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),

company_id: str = Depends(require_company_id)):
    """
    Get all wizard enhancements for the current context.
    
    Combines suggestions from patterns, success profiles, and correlations.
    """
    company_id = get_user_company_id(current_user)
    try:
        enhancements = await intelligence_layer_service.get_wizard_enhancements(
            db=db,
            company_id=company_id,
            recruiter_id=str(current_user.id),
            seniority=seniority,
            department=department,
            role=role,
        )
        
        return {
            "suggestions": [
                {
                    "field": s["field"],
                    "type": s["type"],
                    "value": s.get("value"),
                    "reason": s.get("reason", ""),
                    "confidence": s.get("confidence", 0.0),
                }
                for s in enhancements.get("suggestions", [])
            ],
            "insights": enhancements.get("insights", []),
            "warnings": enhancements.get("warnings", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wizard enhancements: {e}")
        raise LIAError(message="Error generating wizard enhancements")


@router.get("/success-profile", response_model=None)
async def get_success_profile(
    seniority: str | None = None,
    department: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),

company_id: str = Depends(require_company_id)):
    """
    Get the success profile for a specific context.
    
    Shows typical characteristics of successful hires.
    """
    company_id = get_user_company_id(current_user)
    try:
        context = await intelligence_layer_service.build_intelligence_context(
            db=db,
            company_id=company_id,
            recruiter_id=str(current_user.id),
            seniority=seniority,
            department=department,
        )
        
        if not context.success_profile:
            return {"success_profile": None, "available": False}
        
        profile = context.success_profile
        return {
            "available": True,
            "success_profile": {
                "seniority": profile.seniority,
                "department": profile.department,
                "avg_time_to_fill_days": profile.avg_time_to_fill_days,
                "avg_salary": profile.avg_salary,
                "salary_range": {
                    "min": profile.salary_range_min,
                    "max": profile.salary_range_max,
                },
                "common_skills": profile.common_skills or [],
                "common_requirements": profile.common_requirements or [],
                "preferred_work_model": profile.preferred_work_model,
                "avg_satisfaction_score": profile.avg_satisfaction_score,
                "sample_size": profile.sample_size,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting success profile: {e}")
        raise LIAError(message="Error retrieving success profile")


@router.get("/correlations", response_model=None)
async def get_correlations(
    factor_field: str | None = None,
    outcome_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),

company_id: str = Depends(require_company_id)):
    """
    Get outcome correlations for the company.
    
    Shows which factors correlate with outcomes like time-to-fill and satisfaction.
    """
    company_id = get_user_company_id(current_user)
    try:
        context = await intelligence_layer_service.build_intelligence_context(
            db=db,
            company_id=company_id,
            recruiter_id=str(current_user.id),
        )
        
        correlations = context.correlations
        
        if factor_field:
            correlations = [c for c in correlations if c.factor_field == factor_field]
        if outcome_type:
            correlations = [c for c in correlations if c.outcome_type == outcome_type]
        
        return {
            "correlations": [
                {
                    "factor_field": c.factor_field,
                    "outcome_type": c.outcome_type,
                    "correlation_coefficient": c.correlation_coefficient,
                    "p_value": c.p_value,
                    "is_significant": c.is_significant,
                    "direction": c.direction,
                    "insight_text": c.insight_text,
                    "sample_size": c.sample_size,
                }
                for c in correlations
            ],
            "count": len(correlations),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting correlations: {e}")
        raise LIAError(message="Error retrieving correlations")
