"""
Intelligence Layer Service - Orchestrates pattern detection, correlation analysis, and knowledge.

This is the main entry point for the Intelligence Layer, coordinating:
- Pattern detection from corrections and outcomes
- Outcome correlations analysis
- Knowledge repository access
- Confidence adjustments based on patterns
- Suggestion generation for the wizard
"""
import logging
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.repositories.intelligence_repository import (
    IntelligenceRepository,
)
from lia_models.feedback_learning import JobOutcome, JobOutcomeType, WizardFeedback
from lia_models.intelligence_layer import (
    CorrectionPattern,
    IntelligenceInsight,
    OutcomeCorrelation,
    PatternCache,
    SuccessProfile,
)
from app.shared.services.confidence_policy_service import (
    ConfidencePolicyService,
    ConfidenceThresholds,
)
from app.shared.services.outcome_correlator_service import (
    OutcomeCorrelatorService,
    outcome_correlator_service,
)
from app.shared.services.pattern_detector_service import (
    PatternDetectorService,
    pattern_detector_service,
)

logger = logging.getLogger(__name__)


MIN_JOBS_FOR_PATTERNS = 50
MIN_JOBS_FOR_LITE_MODE = 10   # lite: sugestões básicas para clientes novos
MIN_OUTCOMES_FOR_CORRELATIONS = 30
MONTHS_FOR_DATA_QUALITY = 3


@dataclass
class DataQualityReport:
    """Report on data quality for intelligence features."""
    total_jobs: int = 0
    filled_outcomes: int = 0
    total_corrections: int = 0
    months_of_data: int = 0
    has_minimum_data: bool = False
    pattern_detection_ready: bool = False
    correlation_analysis_ready: bool = False
    personalization_ready: bool = False
    lite_mode_ready: bool = False   # sugestões básicas disponíveis com ≥10 vagas
    recommendations: list[str] = dataclass_field(default_factory=list)


@dataclass
class FieldSuggestion:
    """Suggestion for a field value from intelligence layer."""
    field: str
    value: Any
    confidence: float
    source: str
    action: str
    reasoning: str
    insights: list[str] = dataclass_field(default_factory=list)
    adjustments_applied: list[str] = dataclass_field(default_factory=list)


@dataclass
class IntelligenceContext:
    """Full intelligence context for a job creation session."""
    company_id: str
    recruiter_id: str | None = None
    role: str | None = None
    seniority: str | None = None
    department: str | None = None
    
    data_quality: DataQualityReport | None = None
    correction_patterns: list[CorrectionPattern] = dataclass_field(default_factory=list)
    success_profile: SuccessProfile | None = None
    correlations: list[OutcomeCorrelation] = dataclass_field(default_factory=list)
    
    suggestions: dict[str, FieldSuggestion] = dataclass_field(default_factory=dict)
    
    time_to_fill_prediction: dict[str, Any] | None = None
    
    generated_at: datetime = dataclass_field(default_factory=datetime.utcnow)


class IntelligenceLayerService:
    """
    Main service for the Intelligence Layer.
    
    Orchestrates all intelligence features:
    - Data quality assessment
    - Pattern detection
    - Correlation analysis
    - Suggestion generation with adjustments
    - Insight logging
    """
    
    def __init__(
        self,
        pattern_detector: PatternDetectorService | None = None,
        outcome_correlator: OutcomeCorrelatorService | None = None,
        confidence_service: ConfidencePolicyService | None = None
    ):
        self.pattern_detector = pattern_detector or pattern_detector_service
        self.outcome_correlator = outcome_correlator or outcome_correlator_service
        self.confidence_service = confidence_service or ConfidencePolicyService()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def assess_data_quality(
        self,
        db: AsyncSession,
        company_id: str
    ) -> DataQualityReport:
        """
        Assess data quality for a company.
        
        Determines what intelligence features are available based on
        the amount and quality of historical data.
        """
        try:
            jobs_query = select(func.count()).select_from(JobOutcome).where(
                JobOutcome.company_id == company_id
            )
            jobs_result = await db.execute(jobs_query)
            total_jobs = jobs_result.scalar() or 0
            
            filled_query = select(func.count()).select_from(JobOutcome).where(
                and_(
                    JobOutcome.company_id == company_id,
                    JobOutcome.outcome == JobOutcomeType.FILLED
                )
            )
            filled_result = await db.execute(filled_query)
            filled_outcomes = filled_result.scalar() or 0
            
            corrections_query = select(func.count()).select_from(WizardFeedback).where(
                WizardFeedback.company_id == company_id
            )
            corrections_result = await db.execute(corrections_query)
            total_corrections = corrections_result.scalar() or 0
            
            oldest_query = select(func.min(JobOutcome.created_at)).where(
                JobOutcome.company_id == company_id
            )
            oldest_result = await db.execute(oldest_query)
            oldest_date = oldest_result.scalar()
            
            if oldest_date:
                months_of_data = (datetime.utcnow() - oldest_date).days // 30
            else:
                months_of_data = 0
            
            report = DataQualityReport(
                total_jobs=total_jobs,
                filled_outcomes=filled_outcomes,
                total_corrections=total_corrections,
                months_of_data=months_of_data,
            )
            
            report.lite_mode_ready = total_jobs >= MIN_JOBS_FOR_LITE_MODE
            report.pattern_detection_ready = (
                total_jobs >= MIN_JOBS_FOR_PATTERNS and
                total_corrections >= 10
            )
            report.correlation_analysis_ready = (
                filled_outcomes >= MIN_OUTCOMES_FOR_CORRELATIONS and
                months_of_data >= MONTHS_FOR_DATA_QUALITY
            )
            report.has_minimum_data = (
                report.pattern_detection_ready or
                report.correlation_analysis_ready or
                report.lite_mode_ready
            )
            report.personalization_ready = total_corrections >= 10

            if not report.pattern_detection_ready or not report.correlation_analysis_ready:
                needed_jobs = max(0, MIN_JOBS_FOR_PATTERNS - total_jobs)
                needed_outcomes = max(0, MIN_OUTCOMES_FOR_CORRELATIONS - filled_outcomes)

                if not report.lite_mode_ready:
                    jobs_for_lite = max(0, MIN_JOBS_FOR_LITE_MODE - total_jobs)
                    report.recommendations.append(
                        f"Crie mais {jobs_for_lite} vaga(s) para ativar sugestões inteligentes básicas (modo lite)"
                    )
                elif needed_jobs > 0:
                    report.recommendations.append(
                        f"Sugestões lite ativas — crie mais {needed_jobs} vagas para detecção completa de padrões"
                    )
                if needed_outcomes > 0:
                    report.recommendations.append(
                        f"Registre mais {needed_outcomes} contratações para análise de correlações"
                    )
                if months_of_data < MONTHS_FOR_DATA_QUALITY:
                    report.recommendations.append(
                        f"Aguarde mais {MONTHS_FOR_DATA_QUALITY - months_of_data} meses para insights de correlação"
                    )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error assessing data quality: {e}")
            return DataQualityReport()
    
    async def build_intelligence_context(
        self,
        db: AsyncSession,
        company_id: str,
        recruiter_id: str | None = None,
        role: str | None = None,
        seniority: str | None = None,
        department: str | None = None
    ) -> IntelligenceContext:
        """
        Build full intelligence context for a job creation session.
        
        Gathers all relevant patterns, correlations, and predictions
        for the specified context.
        """
        context = IntelligenceContext(
            company_id=company_id,
            recruiter_id=recruiter_id,
            role=role,
            seniority=seniority,
            department=department,
        )
        
        try:
            context.data_quality = await self.assess_data_quality(db, company_id)
            
            if context.data_quality.pattern_detection_ready:
                _repo = IntelligenceRepository(db)
                context.correction_patterns = await _repo.list_active_correction_patterns(
                    company_id, seniority=seniority
                )

                patterns_need_refresh = await self._is_cache_expired(
                    db, company_id, "correction_patterns"
                )
                if not context.correction_patterns or patterns_need_refresh:
                    await self._ensure_patterns_detected(db, company_id)
                    context.correction_patterns = await _repo.list_active_correction_patterns(
                        company_id, seniority=seniority
                    )
            
            if context.data_quality.correlation_analysis_ready:
                _repo2 = IntelligenceRepository(db)
                context.success_profile = await _repo2.find_top_success_profile(
                    company_id, seniority=seniority
                )

                context.correlations = await _repo2.list_outcome_correlations(company_id)

                correlations_need_refresh = await self._is_cache_expired(
                    db, company_id, "outcome_correlations"
                )
                if not context.success_profile or not context.correlations or correlations_need_refresh:
                    await self._ensure_correlations_analyzed(db, company_id)
                    if not context.success_profile or correlations_need_refresh:
                        context.success_profile = await _repo2.find_top_success_profile(
                            company_id, seniority=seniority
                        )
                    if not context.correlations or correlations_need_refresh:
                        context.correlations = await _repo2.list_outcome_correlations(
                            company_id
                        )

                context.time_to_fill_prediction = await self.outcome_correlator.predict_time_to_fill(
                    db, company_id, seniority=seniority
                )

            elif context.data_quality.lite_mode_ready:
                # Lite mode: predição TTF via benchmarks de mercado (sem correlações históricas)
                try:
                    context.time_to_fill_prediction = await self.outcome_correlator.predict_time_to_fill(
                        db, company_id, seniority=seniority
                    )
                    if context.time_to_fill_prediction:
                        context.time_to_fill_prediction["_lite_mode"] = True
                except Exception as e:
                    self.logger.debug(f"Lite mode TTF prediction skipped: {e}")

            return context
            
        except Exception as e:
            self.logger.error(f"Error building intelligence context: {e}")
            return context
    
    async def _is_cache_expired(
        self,
        db: AsyncSession,
        company_id: str,
        pattern_type: str
    ) -> bool:
        """
        Check if cache for a pattern type is expired or doesn't exist.
        
        Returns True if cache is expired or missing, False if valid cache exists.
        """
        try:
            repo = IntelligenceRepository(db)
            cache = await repo.find_active_cache(company_id, pattern_type)
            return cache is None
        except Exception as e:
            self.logger.error(f"Error checking cache expiry: {e}")
            return True
    
    async def _ensure_patterns_detected(
        self,
        db: AsyncSession,
        company_id: str
    ) -> None:
        """
        Ensure patterns are detected and persisted if data is sufficient.
        
        Uses PatternCache with 24h TTL to avoid redundant calculations.
        Deactivates old patterns and replaces cache entry on refresh.
        """
        try:
            from sqlalchemy import delete, update
            
            await db.execute(
                update(CorrectionPattern)
                .where(CorrectionPattern.company_id == company_id)
                .values(is_active=False)
            )
            
            await db.execute(
                delete(SuccessProfile)
                .where(SuccessProfile.company_id == company_id)
            )
            
            detected_patterns = await self.pattern_detector.detect_correction_patterns(
                db, company_id
            )
            if detected_patterns:
                await self.pattern_detector.save_correction_patterns(
                    db, company_id, detected_patterns
                )
            
            success_profiles = await self.pattern_detector.detect_success_profiles(
                db, company_id
            )
            if success_profiles:
                for profile in success_profiles:
                    db.add(profile)
            
            await db.execute(
                delete(PatternCache)
                .where(
                    and_(
                        PatternCache.company_id == company_id,
                        PatternCache.pattern_type == "correction_patterns"
                    )
                )
            )
            
            cache_entry = PatternCache(
                company_id=company_id,
                pattern_type="correction_patterns",
                cache_key=f"patterns_{company_id}",
                cached_data={"pattern_count": len(detected_patterns) if detected_patterns else 0},
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(cache_entry)
            
            await db.flush()
            self.logger.info(f"Detected and cached {len(detected_patterns) if detected_patterns else 0} patterns for {company_id}")
        except Exception as e:
            self.logger.error(f"Error ensuring patterns detected: {e}")
    
    async def _ensure_correlations_analyzed(
        self,
        db: AsyncSession,
        company_id: str
    ) -> None:
        """
        Ensure correlations are analyzed and persisted if data is sufficient.
        
        Uses PatternCache with 24h TTL to avoid redundant calculations.
        Deletes old correlations and success profiles before refresh.
        """
        try:
            from sqlalchemy import delete
            
            await db.execute(
                delete(OutcomeCorrelation)
                .where(OutcomeCorrelation.company_id == company_id)
            )
            
            await db.execute(
                delete(SuccessProfile)
                .where(SuccessProfile.company_id == company_id)
            )
            
            correlations = await self.outcome_correlator.analyze_correlations(
                db, company_id
            )
            if correlations:
                await self.outcome_correlator.save_correlations(
                    db, company_id, correlations
                )
            
            success_profiles = await self.pattern_detector.detect_success_profiles(
                db, company_id
            )
            if success_profiles:
                for profile in success_profiles:
                    db.add(profile)
            
            await db.execute(
                delete(PatternCache)
                .where(
                    and_(
                        PatternCache.company_id == company_id,
                        PatternCache.pattern_type == "outcome_correlations"
                    )
                )
            )
            
            cache_entry = PatternCache(
                company_id=company_id,
                pattern_type="outcome_correlations",
                cache_key=f"correlations_{company_id}",
                cached_data={"correlation_count": len(correlations) if correlations else 0},
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(cache_entry)
            
            await db.flush()
            self.logger.info(f"Analyzed and cached {len(correlations) if correlations else 0} correlations for {company_id}")
        except Exception as e:
            self.logger.error(f"Error ensuring correlations analyzed: {e}")
    
    def apply_pattern_adjustment(
        self,
        field: str,
        value: Any,
        patterns: list[CorrectionPattern],
        seniority: str | None = None
    ) -> tuple[Any, list[str], float]:
        """
        Apply pattern-based adjustments to a field value.
        
        Returns:
            Tuple of (adjusted_value, adjustments_applied, confidence_adjustment)
        """
        adjustments = []
        adjusted_value = value
        confidence_boost = 0.0
        
        relevant_patterns = [
            p for p in patterns
            if p.field == field and (
                p.seniority is None or  # type: ignore[union-attr]
                (seniority and str(p.seniority).lower() == seniority.lower())  # type: ignore[union-attr]
            )
        ]
        
        for pattern in relevant_patterns:
            if pattern.confidence < 0.6:  # type: ignore[union-attr]
                continue
            
            if field in ["salary_range", "salary_min", "salary_max"]:
                if isinstance(value, dict):
                    adjustment = float(pattern.avg_adjustment)  # type: ignore[union-attr]
                    adjusted_value = {
                        "min": round(value.get("min", 0) * adjustment, 2),
                        "max": round(value.get("max", 0) * adjustment, 2)
                    }
                    adjustments.append(
                        f"Ajustado por padrão de correção: {(adjustment - 1) * 100:.0f}%"
                    )
                    confidence_boost = min(0.1, float(pattern.confidence) * 0.1)  # type: ignore[union-attr]
                elif isinstance(value, (int, float)):
                    adjustment = float(pattern.avg_adjustment)  # type: ignore[union-attr]
                    adjusted_value = round(value * adjustment, 2)
                    adjustments.append(
                        f"Ajustado por padrão de correção: {(adjustment - 1) * 100:.0f}%"
                    )
                    confidence_boost = min(0.1, float(pattern.confidence) * 0.1)  # type: ignore[union-attr]
        
        return adjusted_value, adjustments, confidence_boost
    
    def generate_field_suggestion(
        self,
        field: str,
        base_value: Any,
        base_confidence: float,
        source: str,
        context: IntelligenceContext,
        custom_thresholds: ConfidenceThresholds | None = None
    ) -> FieldSuggestion:
        """
        Generate a field suggestion with intelligence adjustments.
        
        Applies:
        - Pattern-based adjustments
        - Success profile insights
        - Correlation-based recommendations
        """
        adjusted_value, adjustments, confidence_boost = self.apply_pattern_adjustment(
            field,
            base_value,
            context.correction_patterns,
            context.seniority
        )
        
        final_confidence = min(0.95, base_confidence + confidence_boost)
        
        insights = []
        
        if context.success_profile and field == "salary_range":
            avg_salary = context.success_profile.avg_salary  # type: ignore[union-attr]
            if avg_salary:
                insights.append(
                    f"Média salarial de contratações bem-sucedidas: R$ {avg_salary:,.0f}"
                )
        
        if context.success_profile and field == "skills":
            must_have = context.success_profile.must_have_skills  # type: ignore[union-attr]
            if must_have:
                insights.append(
                    f"Skills mais comuns em contratações: {', '.join(must_have[:5])}"
                )
        
        for corr in context.correlations:
            if corr.recommendation:  # type: ignore[union-attr]
                insights.append(str(corr.recommendation))
        
        thresholds = custom_thresholds or ConfidenceThresholds()
        action = self.confidence_service.get_action_for_confidence(
            final_confidence, thresholds
        )
        
        reasoning = self._generate_reasoning(
            field, source, adjustments, base_confidence, final_confidence
        )
        
        return FieldSuggestion(
            field=field,
            value=adjusted_value,
            confidence=final_confidence,
            source=source,
            action=action.value,
            reasoning=reasoning,
            insights=insights,
            adjustments_applied=adjustments,
        )
    
    def _generate_reasoning(
        self,
        field: str,
        source: str,
        adjustments: list[str],
        base_confidence: float,
        final_confidence: float
    ) -> str:
        """Generate human-readable reasoning for a suggestion."""
        parts = [f"Baseado em: {source}"]
        
        if adjustments:
            parts.append(f"Ajustes: {', '.join(adjustments)}")
        
        if final_confidence > base_confidence:
            parts.append(
                f"Confiança ajustada de {base_confidence:.0%} para {final_confidence:.0%}"
            )
        
        return " | ".join(parts)
    
    async def log_insight(
        self,
        db: AsyncSession,
        company_id: str,
        insight_type: str,
        field: str | None = None,
        job_id: UUID | None = None,
        recruiter_id: str | None = None,
        original_value: Any = None,
        suggested_value: Any = None,
        confidence: float = 0.0,
        source: str | None = None,
        reasoning: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> IntelligenceInsight:
        """Log an intelligence insight for tracking and improvement."""
        insight = IntelligenceInsight(
            company_id=company_id,
            job_id=job_id,
            recruiter_id=recruiter_id,
            insight_type=insight_type,
            field=field,
            original_value=original_value,
            suggested_value=suggested_value,
            confidence=confidence,
            source=source,
            reasoning=reasoning,
            insight_metadata=metadata or {},
        )
        
        db.add(insight)
        await db.flush()
        
        return insight
    
    async def record_insight_outcome(
        self,
        db: AsyncSession,
        insight_id: UUID,
        was_applied: bool,
        was_accepted: bool,
        final_value: Any = None
    ) -> None:
        """Record the outcome of an insight (was it applied and accepted?)."""
        repo = IntelligenceRepository(db)
        insight = await repo.find_insight_by_id(insight_id)
        
        if insight:
            insight.was_applied = was_applied  # type: ignore[union-attr]
            insight.was_accepted = was_accepted  # type: ignore[union-attr]
            insight.final_value = final_value  # type: ignore[union-attr]
            await db.flush()
    
    async def refresh_patterns(
        self,
        db: AsyncSession,
        company_id: str
    ) -> dict[str, Any]:
        """
        Refresh all patterns for a company.
        
        Recalculates correction patterns and success profiles
        from current data.
        """
        results = {
            "correction_patterns": 0,
            "success_profiles": 0,
            "correlations": 0,
            "errors": []
        }
        
        try:
            detected_patterns = await self.pattern_detector.detect_correction_patterns(
                db, company_id
            )
            if detected_patterns:
                saved = await self.pattern_detector.save_correction_patterns(
                    db, company_id, detected_patterns
                )
                results["correction_patterns"] = len(saved)
            
            success_profiles = await self.pattern_detector.detect_success_profiles(
                db, company_id
            )
            if success_profiles:
                for profile in success_profiles:
                    db.add(profile)
                results["success_profiles"] = len(success_profiles)
            
            correlations = await self.outcome_correlator.analyze_correlations(
                db, company_id
            )
            if correlations:
                saved_corr = await self.outcome_correlator.save_correlations(
                    db, company_id, correlations
                )
                results["correlations"] = len(saved_corr)
            
            await db.flush()
            
        except Exception as e:
            self.logger.error(f"Error refreshing patterns: {e}")
            results["errors"].append(str(e))
        
        return results
    
    async def get_wizard_enhancements(
        self,
        db: AsyncSession,
        company_id: str,
        recruiter_id: str | None = None,
        role: str | None = None,
        seniority: str | None = None
    ) -> dict[str, Any]:
        """
        Get all enhancements for the job creation wizard.
        
        Returns a complete package of intelligence-driven improvements
        for the wizard experience.
        """
        context = await self.build_intelligence_context(
            db, company_id, recruiter_id, role, seniority
        )
        
        enhancements = {
            "data_quality": {
                "has_minimum_data": context.data_quality.has_minimum_data if context.data_quality else False,
                "pattern_detection_ready": context.data_quality.pattern_detection_ready if context.data_quality else False,
                "correlation_analysis_ready": context.data_quality.correlation_analysis_ready if context.data_quality else False,
                "recommendations": context.data_quality.recommendations if context.data_quality else [],
            },
            "patterns": {
                "count": len(context.correction_patterns),
                "fields_with_patterns": list(set(
                    str(p.field) for p in context.correction_patterns  # type: ignore[union-attr]
                )),
            },
            "predictions": {},
            "insights": [],
            "success_profile": None,
        }
        
        if context.time_to_fill_prediction:
            enhancements["predictions"]["time_to_fill"] = context.time_to_fill_prediction
        
        if context.success_profile:
            enhancements["success_profile"] = {
                "avg_time_to_fill": context.success_profile.avg_time_to_fill,  # type: ignore[union-attr]
                "avg_salary": context.success_profile.avg_salary,  # type: ignore[union-attr]
                "satisfaction_avg": context.success_profile.satisfaction_avg,  # type: ignore[union-attr]
                "must_have_skills": context.success_profile.must_have_skills,  # type: ignore[union-attr]
                "sample_size": context.success_profile.sample_size,  # type: ignore[union-attr]
            }
        
        for corr in context.correlations:
            if corr.recommendation:  # type: ignore[union-attr]
                enhancements["insights"].append({
                    "type": "correlation",
                    "factor": str(corr.factor),  # type: ignore[union-attr]
                    "outcome": str(corr.outcome_metric),  # type: ignore[union-attr]
                    "recommendation": str(corr.recommendation),  # type: ignore[union-attr]
                })
        
        return enhancements


intelligence_layer_service = IntelligenceLayerService()
