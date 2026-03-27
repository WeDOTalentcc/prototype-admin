"""
Predictive Analytics API endpoints.

Provides endpoints for:
- Candidate hiring probability prediction
- Time to fill estimation
- Dropout risk assessment
- Pipeline forecasting
- Analytics dashboard
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.services.predictive_analytics_service import predictive_analytics_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics/predictions", tags=["predictive-analytics"])


class HiringProbabilityRequest(BaseModel):
    """Request for hiring probability prediction."""
    candidate_id: str
    job_id: str


class TimeToFillRequest(BaseModel):
    """Request for time to fill prediction."""
    job_id: str


class DropoutRiskRequest(BaseModel):
    """Request for dropout risk prediction."""
    candidate_id: str
    job_id: str


class PipelineForecastRequest(BaseModel):
    """Request for pipeline forecast."""
    job_id: str
    weeks_ahead: int = 4


@router.get("/dashboard")
async def get_predictions_dashboard(
    user_id: Optional[str] = Query(None, description="Filter by user/recruiter"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive predictive analytics dashboard.
    
    Returns:
    - Summary of all predictions
    - High-risk candidates
    - Jobs at risk of delays
    - Quick win opportunities
    - Pipeline health overview
    """
    try:
        dashboard = await predictive_analytics_service.get_analytics_dashboard(user_id, db)
        return {
            "success": True,
            "data": dashboard
        }
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hiring-probability")
async def predict_hiring_probability(
    request: HiringProbabilityRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Predict probability of hiring a candidate for a specific job.
    
    Factors considered:
    - WSI Score
    - Experience match
    - Skills match
    - Interview performance
    - Response patterns
    - Cultural fit
    
    Returns probability (0-100), confidence level, and factor breakdown.
    """
    try:
        prediction = await predictive_analytics_service.predict_hiring_probability(
            request.candidate_id,
            request.job_id,
            db
        )
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        logger.error(f"Error predicting hiring probability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hiring-probability/{candidate_id}/{job_id}")
async def get_hiring_probability(
    candidate_id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get hiring probability prediction via GET request.
    """
    try:
        prediction = await predictive_analytics_service.predict_hiring_probability(
            candidate_id,
            job_id,
            db
        )
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        logger.error(f"Error predicting hiring probability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/time-to-fill")
async def predict_time_to_fill(
    request: TimeToFillRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Predict time to fill a job vacancy.
    
    Factors considered:
    - Job seniority level
    - Skills rarity
    - Salary competitiveness
    - Current pipeline strength
    - Market conditions
    
    Returns predicted days, date range, and recommendations.
    """
    try:
        prediction = await predictive_analytics_service.predict_time_to_fill(
            request.job_id,
            db
        )
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        logger.error(f"Error predicting time to fill: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/time-to-fill/{job_id}")
async def get_time_to_fill(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get time to fill prediction via GET request.
    """
    try:
        prediction = await predictive_analytics_service.predict_time_to_fill(
            job_id,
            db
        )
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        logger.error(f"Error predicting time to fill: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dropout-risk")
async def predict_dropout_risk(
    request: DropoutRiskRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Predict risk of candidate dropping out of the process.
    
    Factors considered:
    - Time in current stage
    - Communication frequency
    - Response patterns
    - Competing offers signals
    
    Returns risk percentage, level, and prevention actions.
    """
    try:
        prediction = await predictive_analytics_service.predict_dropout_risk(
            request.candidate_id,
            request.job_id,
            db
        )
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        logger.error(f"Error predicting dropout risk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dropout-risk/{candidate_id}/{job_id}")
async def get_dropout_risk(
    candidate_id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get dropout risk prediction via GET request.
    """
    try:
        prediction = await predictive_analytics_service.predict_dropout_risk(
            candidate_id,
            job_id,
            db
        )
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        logger.error(f"Error predicting dropout risk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline-forecast")
async def generate_pipeline_forecast(
    request: PipelineForecastRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate pipeline forecast for a job.
    
    Predicts:
    - Weekly hiring projections
    - Stage progression
    - Bottleneck identification
    - Fill probability
    
    Returns weekly forecast and recommendations.
    """
    try:
        forecast = await predictive_analytics_service.generate_pipeline_forecast(
            request.job_id,
            request.weeks_ahead,
            db
        )
        return {
            "success": True,
            "data": forecast
        }
    except Exception as e:
        logger.error(f"Error generating pipeline forecast: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline-forecast/{job_id}")
async def get_pipeline_forecast(
    job_id: str,
    weeks_ahead: int = Query(4, ge=1, le=12, description="Weeks to forecast"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get pipeline forecast via GET request.
    """
    try:
        forecast = await predictive_analytics_service.generate_pipeline_forecast(
            job_id,
            weeks_ahead,
            db
        )
        return {
            "success": True,
            "data": forecast
        }
    except Exception as e:
        logger.error(f"Error generating pipeline forecast: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def analytics_health():
    """Health check for predictive analytics service."""
    return {
        "status": "healthy",
        "service": "predictive-analytics",
        "available_predictions": [
            "hiring_probability",
            "time_to_fill",
            "dropout_risk",
            "pipeline_forecast"
        ]
    }
