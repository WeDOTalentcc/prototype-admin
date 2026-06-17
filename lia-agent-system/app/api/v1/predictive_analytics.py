"""
Predictive Analytics API endpoints.

Provides endpoints for:
- Candidate hiring probability prediction
- Time to fill estimation
- Dropout risk assessment
- Pipeline forecasting
- Analytics dashboard
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.analytics.services.predictive_analytics_service import predictive_analytics_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.shared.errors import LIAError
from app.repositories.dependencies import get_job_vacancies_analytics_repo
from app.repositories.job_vacancies_analytics_repository import JobVacanciesAnalyticsRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics/predictions", tags=["predictive-analytics"])


class HiringProbabilityRequest(WeDoBaseModel):
    """Request for hiring probability prediction."""
    candidate_id: str
    job_id: str


class TimeToFillRequest(WeDoBaseModel):
    """Request for time to fill prediction."""
    job_id: str


class DropoutRiskRequest(WeDoBaseModel):
    """Request for dropout risk prediction."""
    candidate_id: str
    job_id: str


class PipelineForecastRequest(WeDoBaseModel):
    """Request for pipeline forecast."""
    job_id: str
    weeks_ahead: int = 4


@router.get("/dashboard", response_model=None)
async def get_predictions_dashboard(
    user_id: str | None = Query(None, description="Filter by user/recruiter"),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/hiring-probability", response_model=None)
async def predict_hiring_probability(
    request: HiringProbabilityRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting hiring probability: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/hiring-probability/{candidate_id}/{job_id}", response_model=None)
async def get_hiring_probability(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting hiring probability: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/time-to-fill", response_model=None)
async def predict_time_to_fill(
    request: TimeToFillRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting time to fill: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/time-to-fill/{job_id}", response_model=None)
async def get_time_to_fill(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting time to fill: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/dropout-risk", response_model=None)
async def predict_dropout_risk(
    request: DropoutRiskRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting dropout risk: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/dropout-risk/{candidate_id}/{job_id}", response_model=None)
async def get_dropout_risk(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting dropout risk: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/pipeline-forecast", response_model=None)
async def generate_pipeline_forecast(
    request: PipelineForecastRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating pipeline forecast: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/pipeline-forecast/{job_id}", response_model=None)
async def get_pipeline_forecast(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    weeks_ahead: int = Query(4, ge=1, le=12, description="Weeks to forecast"),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating pipeline forecast: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/health", response_model=None)
async def analytics_health(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
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



@router.get("/talent-pool/{job_id}", response_model=None)
async def get_talent_pool_insights(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
    repo: JobVacanciesAnalyticsRepository = Depends(get_job_vacancies_analytics_repo),
) -> dict:
    # multi-tenancy: gated via Depends(require_company_id) + job ownership check
    """Aggregated talent pool analytics for a specific job vacancy.

    Aggregates funnel metrics, hiring probability and pipeline prediction
    for the TalentPoolInsights modal in the frontend.
    """
    try:
        # 1. Multi-tenancy gate: confirm job belongs to company
        job = await repo.get_job_by_id_and_company(job_id, company_id)
        if not job:
            raise HTTPException(status_code=404, detail="Vaga nao encontrada ou sem permissao")

        # 2. Funnel metrics via existing repo methods (ADR-001 compliant — no inline SQL)
        stage_counts = await repo.get_stage_counts_for_vacancy(job_id)
        total_candidates = await repo.get_total_candidates_for_vacancy(job_id)

        screening_count = (
            stage_counts.get("screening", 0)
            + stage_counts.get("triagem", 0)
            + stage_counts.get("initial", 0)
        )
        interview_count = (
            stage_counts.get("interview", 0)
            + stage_counts.get("entrevista", 0)
            + stage_counts.get("interview_1", 0)
            + stage_counts.get("interview_2", 0)
        )
        offer_count = stage_counts.get("offer", 0) + stage_counts.get("proposta", 0)
        hired_count = stage_counts.get("hired", 0) + stage_counts.get("contratado", 0)
        rejected_count = (
            stage_counts.get("rejected", 0)
            + stage_counts.get("reprovado", 0)
            + stage_counts.get("recusado", 0)
        )

        conversion_rate = 0.0
        if total_candidates > 0:
            conversion_rate = round((hired_count / total_candidates) * 100, 1)

        avg_hours = await repo.get_avg_time_to_hire(job_id)
        avg_time_to_fill_days = round(avg_hours / 24, 1) if avg_hours is not None else None

        metrics = {
            "total_candidates": total_candidates,
            "in_screening": screening_count,
            "in_interview": interview_count,
            "in_offer": offer_count,
            "hired": hired_count,
            "rejected": rejected_count,
            "conversion_rate": conversion_rate,
            "avg_time_to_fill_days": avg_time_to_fill_days,
        }

        # 3. Top skills from top-scoring candidates (uses repo — no inline SQL)
        top_candidates = await repo.get_top_candidates_with_score(job_id, limit=20)
        skill_counter: dict = {}
        for _vc, candidate in top_candidates:
            all_skills = list(candidate.technical_skills or []) + list(candidate.soft_skills or [])
            for skill in all_skills:
                if skill:
                    k = skill.strip().lower()
                    skill_counter[k] = skill_counter.get(k, 0) + 1

        total_mentions = sum(skill_counter.values()) or 1
        top_skills = [
            {"skill": sk, "count": cnt, "percentage": round((cnt / total_mentions) * 100, 1)}
            for sk, cnt in sorted(skill_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # 4. Vacancy-level hiring probability (heuristic — no candidate_id required)
        if total_candidates == 0:
            hiring_probability = {"probability": 0.0, "confidence": "low"}
        else:
            advanced = interview_count + offer_count + hired_count
            raw_prob = min((advanced / total_candidates) * 100 + (hired_count * 20), 100.0)
            confidence = (
                "high" if total_candidates >= 10 else ("medium" if total_candidates >= 3 else "low")
            )
            hiring_probability = {"probability": round(raw_prob, 1), "confidence": confidence}

        # 5. Pipeline prediction via existing predictive_analytics_service
        try:
            forecast = await predictive_analytics_service.generate_pipeline_forecast(
                job_id, weeks_ahead=4, db=db
            )
            fill_prob = forecast.get("fill_probability", 0.0)
            estimated_days = None
            for i, w in enumerate(forecast.get("weekly_forecast", [])):
                if w.get("expected_hires", 0) > 0:
                    estimated_days = (i + 1) * 7
                    break
            pipeline_prediction = {
                "closure_probability": fill_prob,
                "estimated_days_to_close": estimated_days,
                "confidence_level": "medium" if total_candidates >= 5 else "low",
            }
        except Exception as fe:
            logger.warning(f"Pipeline forecast fallback for job {job_id}: {fe}")
            pipeline_prediction = {
                "closure_probability": 0.0,
                "estimated_days_to_close": None,
                "confidence_level": "low",
            }

        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "company_id": company_id,
                "metrics": metrics,
                "hiring_probability": hiring_probability,
                "pipeline_prediction": pipeline_prediction,
                "top_skills": top_skills,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating talent pool insights for job {job_id}: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


reorder_collection_before_item(router)
