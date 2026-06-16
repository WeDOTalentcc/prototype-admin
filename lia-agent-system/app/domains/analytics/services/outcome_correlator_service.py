"""
Outcome Correlator Service - Analyzes correlations between job characteristics and outcomes.

This service discovers relationships like:
- "Higher salary offers correlate with faster time-to-fill"
- "Remote positions in tech fill 30% faster"
- "Jobs with 3+ screening questions have better satisfaction scores"

Uses statistical analysis to identify actionable correlations
that can improve future job creation decisions.
"""
import logging
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.repositories.intelligence_repository import (
    IntelligenceRepository,
)
from lia_models.feedback_learning import JobOutcome, JobOutcomeType
from lia_models.intelligence_layer import OutcomeCorrelation

logger = logging.getLogger(__name__)


MIN_SAMPLE_SIZE = 20
SIGNIFICANCE_THRESHOLD = 0.05
CORRELATION_THRESHOLD = 0.3


@dataclass
class CorrelationResult:
    """Result of a correlation analysis."""
    factor: str
    outcome: str
    correlation: float
    significance: float
    direction: str
    recommendation: str | None
    sample_size: int
    factor_stats: dict[str, Any]
    outcome_stats: dict[str, Any]


class OutcomeCorrelatorService:
    """
    Analyzes correlations between job characteristics and outcomes.
    
    Features:
    - Correlation discovery between factors and outcomes
    - Significance testing for reliable insights
    - Actionable recommendation generation
    - Cached correlations for efficient retrieval
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.outcome_metrics = [
            "time_to_fill_days",
            "satisfaction_score",
            "candidate_count_total",
            "candidate_count_interviewed",
        ]
        
        self.analyzable_factors = [
            "salary_percentile",
            "work_model",
            "seniority",
            "has_screening_questions",
            "pipeline_length",
        ]
    
    def _pearson_correlation(
        self,
        x: list[float],
        y: list[float]
    ) -> tuple[float, float]:
        """Calculate Pearson correlation coefficient and p-value approximation."""
        n = len(x)
        if n < 3:
            return 0.0, 1.0
        
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        
        std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
        
        if std_x == 0 or std_y == 0:
            return 0.0, 1.0
        
        r = numerator / (std_x * std_y)
        
        if abs(r) >= 1.0:
            return r, 0.0
        
        t = r * math.sqrt((n - 2) / (1 - r**2))
        p_approx = 2.0 / (1.0 + math.exp(0.8 * abs(t)))
        
        return r, p_approx
    
    async def analyze_correlations(
        self,
        db: AsyncSession,
        company_id: str,
        months_back: int = 12
    ) -> list[CorrelationResult]:
        """
        Analyze all correlations for a company.
        
        Args:
            db: Database session
            company_id: Company to analyze
            months_back: How many months of data to consider
            
        Returns:
            List of significant correlations discovered
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            repo = IntelligenceRepository(db)
            outcomes = await repo.list_filled_outcomes_since(company_id, cutoff_date)
            
            if len(outcomes) < MIN_SAMPLE_SIZE:
                self.logger.info(
                    f"Insufficient data for correlation analysis: {len(outcomes)} < {MIN_SAMPLE_SIZE}"
                )
                return []
            
            correlations = []
            
            salary_ttf = await self._analyze_salary_time_to_fill(outcomes)
            if salary_ttf:
                correlations.append(salary_ttf)
            
            work_model_corr = await self._analyze_work_model_outcomes(outcomes)
            correlations.extend(work_model_corr)
            
            seniority_corr = await self._analyze_seniority_outcomes(outcomes)
            correlations.extend(seniority_corr)
            
            return correlations
            
        except Exception as e:
            self.logger.error(f"Error analyzing correlations: {e}")
            return []
    
    async def _analyze_salary_time_to_fill(
        self,
        outcomes: list[JobOutcome]
    ) -> CorrelationResult | None:
        """Analyze correlation between salary and time to fill."""
        salary_values = []
        ttf_values = []
        
        for o in outcomes:
            if o.salary_final and o.time_to_fill_days:
                salary_values.append(float(o.salary_final))
                ttf_values.append(float(o.time_to_fill_days))
        
        if len(salary_values) < MIN_SAMPLE_SIZE:
            return None
        
        correlation, p_value = self._pearson_correlation(salary_values, ttf_values)
        
        if abs(correlation) < CORRELATION_THRESHOLD or p_value > SIGNIFICANCE_THRESHOLD:
            return None
        
        direction = "negative" if correlation < 0 else "positive"
        
        if correlation < -0.3:
            recommendation = "Higher salary offers tend to reduce time-to-fill. Consider competitive compensation for faster hiring."
        elif correlation > 0.3:
            recommendation = "Time-to-fill increases with salary level, likely due to more selective hiring for senior roles."
        else:
            recommendation = None
        
        return CorrelationResult(
            factor="salary_final",
            outcome="time_to_fill_days",
            correlation=round(correlation, 3),
            significance=round(1 - p_value, 3),
            direction=direction,
            recommendation=recommendation,
            sample_size=len(salary_values),
            factor_stats={
                "mean": round(statistics.mean(salary_values), 2),
                "median": round(statistics.median(salary_values), 2),
                "min": round(min(salary_values), 2),
                "max": round(max(salary_values), 2),
            },
            outcome_stats={
                "mean": round(statistics.mean(ttf_values), 2),
                "median": round(statistics.median(ttf_values), 2),
                "min": round(min(ttf_values), 2),
                "max": round(max(ttf_values), 2),
            }
        )
    
    async def _analyze_work_model_outcomes(
        self,
        outcomes: list[JobOutcome]
    ) -> list[CorrelationResult]:
        """Analyze how work model affects outcomes."""
        correlations = []
        
        by_work_model: dict[str, list[JobOutcome]] = {}
        for o in outcomes:
            model = str(o.work_model).lower() if o.work_model else "unknown"
            if model not in by_work_model:
                by_work_model[model] = []
            by_work_model[model].append(o)
        
        if len(by_work_model) < 2:
            return []
        
        for metric in ["time_to_fill_days", "satisfaction_score"]:
            model_averages: dict[str, float] = {}
            
            for model, model_outcomes in by_work_model.items():
                values = [getattr(o, metric) for o in model_outcomes if getattr(o, metric)]
                if len(values) >= 5:
                    model_averages[model] = statistics.mean(values)
            
            if len(model_averages) >= 2:
                sorted_models = sorted(model_averages.items(), key=lambda x: x[1])
                best = sorted_models[0]
                worst = sorted_models[-1]
                
                if worst[1] > 0:
                    difference = (worst[1] - best[1]) / worst[1]
                    
                    if abs(difference) > 0.15:
                        if metric == "time_to_fill_days":
                            recommendation = f"{best[0].title()} positions fill {abs(difference)*100:.0f}% faster on average."
                        else:
                            recommendation = f"{best[0].title()} positions have higher satisfaction scores."
                        
                        correlations.append(CorrelationResult(
                            factor="work_model",
                            outcome=metric,
                            correlation=round(difference, 3),
                            significance=0.9,
                            direction="varies_by_category",
                            recommendation=recommendation,
                            sample_size=len(outcomes),
                            factor_stats=model_averages,
                            outcome_stats={"best": best[0], "worst": worst[0]}
                        ))
        
        return correlations
    
    async def _analyze_seniority_outcomes(
        self,
        outcomes: list[JobOutcome]
    ) -> list[CorrelationResult]:
        """Analyze how seniority affects outcomes."""
        correlations = []
        
        by_seniority: dict[str, list[JobOutcome]] = {}
        for o in outcomes:
            sen = str(o.seniority).lower() if o.seniority else "unknown"
            if sen not in by_seniority:
                by_seniority[sen] = []
            by_seniority[sen].append(o)
        
        if len(by_seniority) < 2:
            return []
        
        seniority_order = ["estagiario", "junior", "pleno", "senior", "specialist", "lead", "manager", "director"]
        
        for metric in ["time_to_fill_days", "satisfaction_score"]:
            seniority_averages: dict[str, tuple[float, int]] = {}
            
            for sen, sen_outcomes in by_seniority.items():
                values = [getattr(o, metric) for o in sen_outcomes if getattr(o, metric)]
                if len(values) >= 5:
                    seniority_averages[sen] = (statistics.mean(values), len(values))
            
            if len(seniority_averages) >= 2:
                ordered = []
                for sen_level in seniority_order:
                    if sen_level in seniority_averages:
                        ordered.append((sen_level, seniority_averages[sen_level][0]))
                
                if len(ordered) >= 2:
                    positions = list(range(len(ordered)))
                    values = [v[1] for v in ordered]
                    
                    corr, p_value = self._pearson_correlation(
                        [float(p) for p in positions],
                        values
                    )
                    
                    if abs(corr) > CORRELATION_THRESHOLD:
                        if metric == "time_to_fill_days":
                            if corr > 0:
                                rec = "Senior positions take longer to fill. Plan for extended timelines."
                            else:
                                rec = "Junior positions take longer to fill. Consider employer branding for entry-level roles."
                        else:
                            rec = "Satisfaction varies by seniority level. Adjust expectations accordingly."
                        
                        correlations.append(CorrelationResult(
                            factor="seniority",
                            outcome=metric,
                            correlation=round(corr, 3),
                            significance=round(1 - p_value, 3),
                            direction="positive" if corr > 0 else "negative",
                            recommendation=rec,
                            sample_size=sum(v[1] for v in seniority_averages.values()),
                            factor_stats={k: v[0] for k, v in seniority_averages.items()},
                            outcome_stats={"trend": "increasing" if corr > 0 else "decreasing"}
                        ))
        
        return correlations
    
    async def save_correlations(
        self,
        db: AsyncSession,
        company_id: str,
        correlations: list[CorrelationResult]
    ) -> list[OutcomeCorrelation]:
        """Save discovered correlations to database."""
        saved = []
        try:
            for corr in correlations:
                _repo = IntelligenceRepository(db)
                existing_corr = await _repo.find_correlation(
                    company_id, corr.factor, corr.outcome
                )
                
                if existing_corr:
                    existing_corr.correlation = corr.correlation
                    existing_corr.significance = corr.significance
                    existing_corr.direction = corr.direction
                    existing_corr.recommendation = corr.recommendation
                    existing_corr.sample_size = corr.sample_size
                    existing_corr.factor_values = corr.factor_stats
                    existing_corr.outcome_values = corr.outcome_stats
                    existing_corr.updated_at = datetime.utcnow()
                    saved.append(existing_corr)
                else:
                    new_corr = OutcomeCorrelation(
                        company_id=company_id,
                        factor=corr.factor,
                        outcome_metric=corr.outcome,
                        correlation=corr.correlation,
                        significance=corr.significance,
                        direction=corr.direction,
                        recommendation=corr.recommendation,
                        sample_size=corr.sample_size,
                        factor_values=corr.factor_stats,
                        outcome_values=corr.outcome_stats,
                    )
                    db.add(new_corr)
                    saved.append(new_corr)
            
            await db.flush()
            return saved
            
        except Exception as e:
            self.logger.error(f"Error saving correlations: {e}")
            return []
    
    async def get_correlations(
        self,
        db: AsyncSession,
        company_id: str,
        factor: str | None = None,
        outcome_metric: str | None = None
    ) -> list[OutcomeCorrelation]:
        """Retrieve stored correlations."""
        try:
            repo = IntelligenceRepository(db)
            return await repo.list_correlations_filtered(
                company_id=company_id,
                factor=factor,
                outcome_metric=outcome_metric,
            )
            
        except Exception as e:
            self.logger.error(f"Error getting correlations: {e}")
            return []
    
    async def predict_time_to_fill(
        self,
        db: AsyncSession,
        company_id: str,
        seniority: str | None = None,
        work_model: str | None = None,
        salary: float | None = None
    ) -> dict[str, Any]:
        """
        Predict time to fill based on job characteristics.
        
        Uses historical data to estimate how long a position will take to fill.
        """
        try:
            repo = IntelligenceRepository(db)
            outcomes = await repo.list_filled_with_time_to_fill(company_id)
            
            if len(outcomes) < 10:
                return {
                    "prediction": None,
                    "confidence": "low",
                    "message": "Insufficient historical data for prediction"
                }
            
            relevant = outcomes
            
            if seniority:
                seniority_match = [o for o in relevant if o.seniority and seniority.lower() in o.seniority.lower()]
                if len(seniority_match) >= 5:
                    relevant = seniority_match
            
            if work_model:
                work_model_match = [o for o in relevant if o.work_model and work_model.lower() in o.work_model.lower()]
                if len(work_model_match) >= 5:
                    relevant = work_model_match
            
            ttf_values = [o.time_to_fill_days for o in relevant if o.time_to_fill_days]
            
            if not ttf_values:
                return {
                    "prediction": None,
                    "confidence": "low",
                    "message": "No matching historical data"
                }
            
            prediction = int(statistics.median(ttf_values))
            std_dev = statistics.stdev(ttf_values) if len(ttf_values) > 1 else 0
            
            if len(relevant) >= 20:
                confidence = "high"
            elif len(relevant) >= 10:
                confidence = "medium"
            else:
                confidence = "low"
            
            return {
                "prediction": prediction,
                "confidence": confidence,
                "range": {
                    "min": max(1, prediction - int(std_dev)),
                    "max": prediction + int(std_dev)
                },
                "sample_size": len(relevant),
                "factors_considered": {
                    "seniority": seniority,
                    "work_model": work_model
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting time to fill: {e}")
            return {
                "prediction": None,
                "confidence": "low",
                "error": str(e)
            }


outcome_correlator_service = OutcomeCorrelatorService()
