"""
ML Predictions API endpoints.

Provides REST API access to ML predictions for:
- Time to fill prediction
- Salary optimization
- Skill success prediction
- Hiring insights
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.ml import OutcomePredictor, get_model_registry
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ML Predictions"])


class TimeToFillRequest(WeDoBaseModel):
    """Request for time to fill prediction."""
    job_data: dict
    company_data: dict | None = None


class TimeToFillResponse(BaseModel):
    """Response for time to fill prediction."""
    predicted_days: int
    range_min: int
    range_max: int
    confidence: float
    confidence_level: str
    comparison_to_market: str
    explanation: str
    factors: list[dict]
    model_version: str


class SalaryPredictionRequest(WeDoBaseModel):
    """Request for salary prediction."""
    job_data: dict
    market_benchmark: float | None = None


class SalaryPredictionResponse(BaseModel):
    """Response for salary prediction."""
    suggested_min: float
    suggested_max: float
    market_percentile: int
    competitive_analysis: str
    confidence: float
    confidence_level: str
    explanation: str
    factors: list[dict]


class SkillSuccessRequest(WeDoBaseModel):
    """Request for skill success prediction."""
    skill_name: str
    role: str | None = None


class SkillSuccessResponse(BaseModel):
    """Response for skill success prediction."""
    skill_name: str
    success_probability: float
    historical_hires_with_skill: int
    recommendation: str
    confidence: float
    confidence_level: str


class HiringInsightsRequest(WeDoBaseModel):
    """Request for hiring insights."""
    role: str | None = None


class HiringInsightsResponse(BaseModel):
    """Response for hiring insights."""
    summary: dict
    recommendations: list[dict]
    top_successful_skills: list[dict]
    confidence: float


@router.post("/predict/time-to-fill", response_model=TimeToFillResponse)
async def predict_time_to_fill(
    request: TimeToFillRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Predict time to fill for a job vacancy.

    Uses historical data and job features to estimate
    the number of days to fill the position.
    """
    predictor = OutcomePredictor()

    try:
        prediction = await predictor.predict_time_to_fill(
            db=db,
            job_data=request.job_data,
            company_id=company_id,
            company_data=request.company_data
        )

        registry = get_model_registry()
        await registry.ensure_loaded(db)
        default_model = registry.get_default_model("time_to_fill_predictor")
        if default_model:
            registry.record_prediction(
                model_id=default_model.model_id,
                predicted_value=prediction.predicted_days
            )
            await registry.flush_pending(db)
        
        return TimeToFillResponse(
            predicted_days=prediction.predicted_days,
            range_min=prediction.range_min,
            range_max=prediction.range_max,
            confidence=prediction.confidence,
            confidence_level=prediction.confidence_level,
            comparison_to_market=prediction.comparison_to_market,
            explanation=prediction.explanation,
            factors=prediction.factors,
            model_version=prediction.model_version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict/salary", response_model=SalaryPredictionResponse)
async def predict_optimal_salary(
    request: SalaryPredictionRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Predict optimal salary range for a job vacancy.

    Considers role, seniority, company history, and
    market benchmarks to suggest competitive salary ranges.
    """
    # FairnessGuard: checar linguagem discriminatória no job_data antes de predizer
    _job_text = " ".join(str(v) for v in request.job_data.values() if isinstance(v, str))
    if _job_text.strip():
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg_result = FairnessGuard().check(_job_text[:1000])
            if _fg_result.is_blocked:
                logger.warning(
                    "[ml/predict/salary] FairnessGuard blocked company=%s: %s",
                    company_id, _fg_result.blocked_terms,
                )
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Dados da vaga contêm critérios discriminatórios. "
                        f"{_fg_result.educational_message or 'Remova critérios protegidos antes de solicitar previsão salarial.'}"
                    ),
                )
            if _fg_result.soft_warnings:
                logger.warning(
                    "[ml/predict/salary] FairnessGuard warnings company=%s: %s",
                    company_id, _fg_result.soft_warnings,
                )
        except HTTPException:
            raise
        except Exception:
            pass  # fail-safe

    predictor = OutcomePredictor()

    # Audit: registrar solicitação de previsão salarial
    logger.info(
        "[ml/predict/salary] request company=%s job_title=%s",
        company_id,
        request.job_data.get("title", "unknown"),
    )

    try:
        prediction = await predictor.predict_optimal_salary(
            db=db,
            job_data=request.job_data,
            company_id=company_id,
            market_benchmark=request.market_benchmark
        )
        
        registry = get_model_registry()
        await registry.ensure_loaded(db)
        default_model = registry.get_default_model("salary_predictor")
        if default_model:
            registry.record_prediction(
                model_id=default_model.model_id,
                predicted_value=prediction.predicted_value
            )
            await registry.flush_pending(db)
        
        return SalaryPredictionResponse(
            suggested_min=prediction.suggested_min,
            suggested_max=prediction.suggested_max,
            market_percentile=prediction.market_percentile,
            competitive_analysis=prediction.competitive_analysis,
            confidence=prediction.confidence,
            confidence_level=prediction.confidence_level,
            explanation=prediction.explanation,
            factors=prediction.factors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict/skill-success", response_model=SkillSuccessResponse)
async def predict_skill_success(
    request: SkillSuccessRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Predict success likelihood for a skill.
    
    Analyzes historical confirmation data to estimate
    how likely a skill is to lead to successful hires.
    """
    predictor = OutcomePredictor()
    
    try:
        prediction = await predictor.predict_skill_success(
            db=db,
            skill_name=request.skill_name,
            company_id=company_id,
            role=request.role
        )
        
        registry = get_model_registry()
        await registry.ensure_loaded(db)
        default_model = registry.get_default_model("skill_success_predictor")
        if default_model:
            registry.record_prediction(
                model_id=default_model.model_id,
                predicted_value=prediction.success_probability
            )
            await registry.flush_pending(db)
        
        return SkillSuccessResponse(
            skill_name=prediction.skill_name,
            success_probability=prediction.success_probability,
            historical_hires_with_skill=prediction.historical_hires_with_skill,
            recommendation=prediction.recommendation,
            confidence=prediction.confidence,
            confidence_level=prediction.confidence_level
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/insights/hiring", response_model=HiringInsightsResponse)
async def get_hiring_insights(
    request: HiringInsightsRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get comprehensive hiring insights for a company.
    
    Aggregates predictions and historical data to provide
    actionable recommendations for improving hiring.
    """
    predictor = OutcomePredictor()
    
    try:
        insights = await predictor.get_hiring_insights(
            db=db,
            company_id=company_id,
            role=request.role
        )
        
        return HiringInsightsResponse(
            summary=insights["summary"],
            recommendations=insights["recommendations"],
            top_successful_skills=insights["top_successful_skills"],
            confidence=insights["confidence"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights failed: {str(e)}")


@router.get("/models", response_model=None)
async def list_models(
    model_name: str | None = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List registered ML models.

    Returns metadata about available models including
    version, performance metrics, and status.
    """
    registry = get_model_registry()
    await registry.ensure_loaded(db)
    models = registry.list_models(model_name=model_name, active_only=active_only)
    
    return {
        "models": [m.to_dict() for m in models],
        "count": len(models)
    }


@router.get("/models/{model_id}/performance", response_model=None)
async def get_model_performance(
    model_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get performance metrics for a specific model.
    """
    registry = get_model_registry()
    await registry.ensure_loaded(db)
    performance = registry.get_performance(model_id)
    
    if not performance:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "model_id": model_id,
        "predictions_count": performance.predictions_count,
        "accuracy": performance.accuracy,
        "mean_error": performance.mean_error,
        "last_evaluated": performance.last_evaluated.isoformat() if performance.last_evaluated else None
    }


@router.post("/models/compare", response_model=None)
async def compare_models(
    model_ids: list[str],
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Compare performance of multiple models.
    """
    registry = get_model_registry()
    await registry.ensure_loaded(db)
    comparison = registry.compare_models(model_ids)
    
    return {
        "comparison": comparison,
        "recommendation": _get_model_recommendation(comparison)
    }


def _get_model_recommendation(comparison: dict) -> str:
    """Generate recommendation based on comparison."""
    if not comparison:
        return "No models to compare"
    
    best_accuracy = 0
    best_model = None
    
    for model_id, metrics in comparison.items():
        if metrics.get("predictions_count", 0) >= 10:
            accuracy = metrics.get("accuracy", 0)
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model = model_id
    
    if best_model:
        return f"Recommend {best_model} with {best_accuracy:.1%} accuracy"
    
    return "Not enough data to make recommendation"

reorder_collection_before_item(router)
