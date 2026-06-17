"""
Feedback Learning Service - Learns from recruiter corrections and job outcomes.

This service enables LIA to improve suggestions over time by:
- Recording corrections made during the job creation wizard
- Tracking job outcomes (filled, cancelled, expired)
- Analyzing correction patterns to adjust future suggestions
- Identifying success patterns from completed hires

Example:
    If LIA suggests R$15k for "Dev Sênior" and recruiters consistently correct to R$18k+,
    the service learns to suggest R$18k for similar roles in the future.
"""
import json
import logging
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.repositories.feedback_repository import FeedbackRepository
from lia_models.feedback_learning import JobOutcome, JobOutcomeType, SuggestionFeedback, WizardFeedback

logger = logging.getLogger(__name__)


@dataclass
class CorrectionPattern:
    """Represents a pattern of corrections for a specific field."""
    field: str
    sample_size: int
    average_original: float | None
    average_corrected: float | None
    correction_direction: str
    correction_percentage: float
    confidence: str
    recommendation: str


@dataclass
class SuccessPattern:
    """Represents patterns from successful hires."""
    role: str
    seniority: str | None
    sample_size: int
    avg_time_to_fill: float
    avg_salary: float
    avg_candidates_screened: int
    common_skills: list[str]
    satisfaction_score: float
    confidence: str


@dataclass
class LearningAdjustment:
    """Adjustment to apply to a suggestion based on past learning."""
    field: str
    original_value: Any
    adjusted_value: Any
    adjustment_reason: str
    confidence: str
    based_on_samples: int


class FeedbackLearningService:
    """
    Service for learning from recruiter feedback and job outcomes.
    
    Features:
    - Record corrections during wizard flow
    - Track job outcomes
    - Analyze correction patterns
    - Identify success patterns
    - Apply learnings to future suggestions
    """
    
    HIGH_CONFIDENCE_THRESHOLD = 10
    MEDIUM_CONFIDENCE_THRESHOLD = 5
    MONTHS_FOR_ANALYSIS = 12
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _calculate_confidence(self, sample_size: int) -> str:
        """Calculate confidence level based on sample size."""
        if sample_size >= self.HIGH_CONFIDENCE_THRESHOLD:
            return "high"
        elif sample_size >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return "medium"
        elif sample_size > 0:
            return "low"
        return "none"
    
    async def record_correction(
        self,
        db: AsyncSession,
        company_id: str,
        job_id: UUID,
        field: str,
        original_value: Any,
        corrected_value: Any,
        stage: str | None = None,
        role: str | None = None,
        seniority: str | None = None,
        department: str | None = None,
        location: str | None = None,
        correction_reason: str | None = None,
        created_by: str | None = None
    ) -> WizardFeedback:
        """
        Record a correction made by a recruiter during the wizard flow.
        
        Args:
            db: Database session
            company_id: Company ID
            job_id: Job vacancy ID
            field: Field that was corrected (e.g., "salary_range", "seniority")
            original_value: LIA's original suggestion
            corrected_value: Recruiter's correction
            stage: Wizard stage where correction was made
            role: Job role/title for context
            seniority: Seniority level for context
            department: Department for context
            location: Location for context
            correction_reason: Optional reason provided by recruiter
            created_by: User who made the correction
        
        Returns:
            Created WizardFeedback record
        """
        try:
            feedback = WizardFeedback(
                company_id=company_id,
                job_id=job_id,
                field_corrected=field,
                original_value=original_value,
                corrected_value=corrected_value,
                stage=stage,
                role=role,
                seniority=seniority,
                department=department,
                location=location,
                correction_reason=correction_reason,
                created_by=created_by
            )
            
            db.add(feedback)
            await db.flush()
            
            self.logger.info(
                f"Recorded correction for field '{field}' on job {job_id}: "
                f"{original_value} -> {corrected_value}"
            )
            
            return feedback
            
        except Exception as e:
            self.logger.error(f"Error recording correction: {e}")
            raise
    
    async def record_outcome(
        self,
        db: AsyncSession,
        company_id: str,
        job_id: UUID,
        outcome: JobOutcomeType,
        time_to_fill_days: int | None = None,
        salary_initial_min: float | None = None,
        salary_initial_max: float | None = None,
        salary_final: float | None = None,
        candidate_count_total: int | None = None,
        candidate_count_screened: int | None = None,
        candidate_count_interviewed: int | None = None,
        candidate_count_offered: int | None = None,
        satisfaction_score: float | None = None,
        role: str | None = None,
        seniority: str | None = None,
        department: str | None = None,
        location: str | None = None,
        work_model: str | None = None,
        skills_used: list[str] | None = None,
        notes: str | None = None,
        created_by: str | None = None
    ) -> JobOutcome:
        """
        Record the final outcome of a job vacancy.
        
        Args:
            db: Database session
            company_id: Company ID
            job_id: Job vacancy ID
            outcome: Final outcome (filled, cancelled, expired)
            time_to_fill_days: Days from opening to closing
            salary_initial_min: Initial minimum salary offered
            salary_initial_max: Initial maximum salary offered
            salary_final: Final salary of hired candidate
            candidate_count_*: Funnel metrics
            satisfaction_score: Hiring manager satisfaction (1-5)
            role: Job role/title
            seniority: Seniority level
            department: Department
            location: Location
            work_model: Work model (remote, hybrid, onsite)
            skills_used: Skills that were most relevant
            notes: Additional notes
            created_by: User who recorded outcome
        
        Returns:
            Created JobOutcome record
        """
        try:
            job_outcome = JobOutcome(
                company_id=company_id,
                job_id=job_id,
                outcome=outcome,
                time_to_fill_days=time_to_fill_days,
                salary_initial_min=salary_initial_min,
                salary_initial_max=salary_initial_max,
                salary_final=salary_final,
                candidate_count_total=candidate_count_total,
                candidate_count_screened=candidate_count_screened,
                candidate_count_interviewed=candidate_count_interviewed,
                candidate_count_offered=candidate_count_offered,
                satisfaction_score=satisfaction_score,
                role=role,
                seniority=seniority,
                department=department,
                location=location,
                work_model=work_model,
                skills_used=skills_used or [],
                notes=notes,
                closed_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(job_outcome)
            await db.flush()
            
            self.logger.info(
                f"Recorded outcome '{outcome.value}' for job {job_id}"
            )
            
            return job_outcome
            
        except Exception as e:
            self.logger.error(f"Error recording outcome: {e}")
            raise
    
    async def record_feedback(
        self,
        db: AsyncSession,
        company_id: str,
        field_name: str,
        suggested_value: Any,
        accepted: bool,
        actual_value: Any = None,
        context: dict[str, Any] | None = None
    ) -> SuggestionFeedback | None:
        """
        Record user feedback on a suggestion for learning.
        
        This method captures whether the user accepted or rejected a suggestion made by LIA
        during the wizard flow, enabling the system to improve future suggestions.
        
        Args:
            db: Database session
            company_id: Company ID
            field_name: Name of the field (e.g., "salary_range", "seniority", "skills")
            suggested_value: The value LIA suggested
            accepted: Whether the user accepted (True) or rejected (False) the suggestion
            actual_value: If rejected, the actual value the user provided
            context: Additional context (job_title, department, seniority, etc.)
        
        Returns:
            Created SuggestionFeedback record or None if error
        
        Example:
            If LIA suggests salary_range = {"min": 5000, "max": 6000} but user rejects
            and sets it to {"min": 6000, "max": 7500}, this tracks both the suggestion
            and the user's preference for learning purposes.
        """
        try:
            # Create feedback record
            feedback = SuggestionFeedback(
                company_id=company_id,
                field_name=field_name,
                suggested_value=suggested_value,
                actual_value=actual_value,
                accepted=1 if accepted else 0,
                context=context or {}
            )
            
            # Persist to database
            db.add(feedback)
            await db.flush()
            
            # Log feedback action
            feedback_action = "accepted" if accepted else "rejected"
            context_str = json.dumps(context) if context else ""
            
            self.logger.info(
                f"Feedback persisted to database - "
                f"Company: {company_id}, "
                f"Field: '{field_name}', "
                f"Action: {feedback_action}, "
                f"Suggested: {suggested_value}, "
                f"Actual: {actual_value}, "
                f"Context: {context_str}"
            )
            

            # T-10 Fase 1 MIRROR (ADR-032): also persist em InteractionFeedback
            # Desbloqueia training_data_service (RLHF/DPO pipeline) que antes era starving.
            # Fail-open: mirror falha NAO interrompe SuggestionFeedback canonical.
            try:
                from app.domains.analytics.services.feedback_service import FeedbackService
                from uuid import uuid4
                _fs = FeedbackService()
                _ctx = context or {}
                await _fs.record_feedback(
                    session_id=_ctx.get("session_id") or str(uuid4()),
                    company_id=company_id,
                    user_id=_ctx.get("user_id", "system"),
                    feedback_type="rating",
                    feedback_value={
                        "rating": 1 if accepted else 0,
                        "feedback_text": f"field={field_name} suggested={suggested_value} actual={actual_value}",
                        "category": "wizard_suggestion",
                    },
                    message_context={
                        "user_message": f"suggest {field_name}",
                        "lia_response": str(suggested_value),
                        "intent": "wizard_suggestion",
                        "stage": _ctx.get("stage"),
                        "tools_used": [field_name],
                    },
                    db=db,
                )
            except Exception as _mirror_exc:
                self.logger.warning(
                    "[T-10 mirror] InteractionFeedback mirror falhou - training data pipeline pode degradar: %s",
                    _mirror_exc, exc_info=True,
                )

            return feedback
            
        except Exception as e:
            self.logger.error(f"Failed to persist feedback: {e}")
            await db.rollback()
            # Don't raise - feedback recording should not block the main flow
            return None
    
    async def get_correction_patterns(
        self,
        db: AsyncSession,
        company_id: str,
        field: str,
        role: str | None = None,
        seniority: str | None = None,
        months_back: int = 12
    ) -> dict[str, Any]:
        """
        Analyze patterns in recruiter corrections for a specific field.
        
        Args:
            db: Database session
            company_id: Company ID
            field: Field to analyze (e.g., "salary_range")
            role: Optional role filter
            seniority: Optional seniority filter
            months_back: How many months of data to analyze
        
        Returns:
            Dictionary with correction patterns and statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            
            repo = FeedbackRepository(db)
            feedbacks = await repo.list_wizard_feedback_corrections(
                company_id=company_id,
                field=field,
                cutoff_date=cutoff_date,
                role=role,
                seniority=seniority,
            )
            
            if not feedbacks:
                return {
                    "field": field,
                    "sample_size": 0,
                    "patterns": [],
                    "confidence": "none",
                    "recommendation": None
                }
            
            patterns = self._analyze_field_corrections(feedbacks, field)
            
            return {
                "field": field,
                "sample_size": len(feedbacks),
                "patterns": patterns,
                "confidence": self._calculate_confidence(len(feedbacks)),
                "recommendation": self._generate_recommendation(patterns, field)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting correction patterns: {e}")
            return {
                "field": field,
                "sample_size": 0,
                "patterns": [],
                "confidence": "none",
                "error": str(e)
            }
    
    def _analyze_field_corrections(
        self,
        feedbacks: Sequence[WizardFeedback],
        field: str
    ) -> list[dict[str, Any]]:
        """Analyze corrections for a specific field type."""
        
        if field == "salary_range":
            return self._analyze_salary_corrections(feedbacks)
        elif field == "seniority":
            return self._analyze_categorical_corrections(feedbacks)
        else:
            return self._analyze_generic_corrections(feedbacks)
    
    def _analyze_salary_corrections(
        self,
        feedbacks: Sequence[WizardFeedback]
    ) -> list[dict[str, Any]]:
        """Analyze salary-related corrections."""
        patterns = []
        
        original_values = []
        corrected_values = []
        
        for fb in feedbacks:
            orig = fb.original_value
            corr = fb.corrected_value
            
            if isinstance(orig, dict) and isinstance(corr, dict):
                orig_mid = (orig.get("min", 0) + orig.get("max", 0)) / 2
                corr_mid = (corr.get("min", 0) + corr.get("max", 0)) / 2
                
                if orig_mid > 0 and corr_mid > 0:
                    original_values.append(orig_mid)
                    corrected_values.append(corr_mid)
            elif isinstance(orig, (int, float)) and isinstance(corr, (int, float)):
                original_values.append(float(orig))
                corrected_values.append(float(corr))
        
        if original_values and corrected_values:
            avg_original = statistics.mean(original_values)
            avg_corrected = statistics.mean(corrected_values)
            
            diff_pct = ((avg_corrected - avg_original) / avg_original) * 100 if avg_original > 0 else 0
            
            if diff_pct > 5:
                direction = "increase"
            elif diff_pct < -5:
                direction = "decrease"
            else:
                direction = "stable"
            
            patterns.append({
                "type": "salary_adjustment",
                "average_original": round(avg_original, 2),
                "average_corrected": round(avg_corrected, 2),
                "adjustment_percentage": round(diff_pct, 2),
                "direction": direction,
                "sample_size": len(original_values)
            })
        
        seniority_patterns: dict[str, dict[str, list[float]]] = {}
        for fb in feedbacks:
            fb_seniority = fb.seniority
            seniority = str(fb_seniority) if fb_seniority is not None else "unknown"
            if seniority not in seniority_patterns:
                seniority_patterns[seniority] = {"original": [], "corrected": []}
            
            orig = fb.original_value
            corr = fb.corrected_value
            
            if isinstance(orig, dict) and isinstance(corr, dict):
                orig_mid = (orig.get("min", 0) + orig.get("max", 0)) / 2
                corr_mid = (corr.get("min", 0) + corr.get("max", 0)) / 2
                if orig_mid > 0 and corr_mid > 0:
                    seniority_patterns[seniority]["original"].append(orig_mid)
                    seniority_patterns[seniority]["corrected"].append(corr_mid)
        
        for seniority, data in seniority_patterns.items():
            if data["original"] and data["corrected"]:
                avg_orig = statistics.mean(data["original"])
                avg_corr = statistics.mean(data["corrected"])
                diff = ((avg_corr - avg_orig) / avg_orig) * 100 if avg_orig > 0 else 0
                
                patterns.append({
                    "type": "salary_by_seniority",
                    "seniority": seniority,
                    "average_original": round(avg_orig, 2),
                    "average_corrected": round(avg_corr, 2),
                    "adjustment_percentage": round(diff, 2),
                    "sample_size": len(data["original"])
                })
        
        return patterns
    
    def _analyze_categorical_corrections(
        self,
        feedbacks: Sequence[WizardFeedback]
    ) -> list[dict[str, Any]]:
        """Analyze categorical field corrections (e.g., seniority level)."""
        transitions = {}
        
        for fb in feedbacks:
            fb_orig = fb.original_value
            fb_corr = fb.corrected_value
            orig = str(fb_orig) if fb_orig is not None else "none"
            corr = str(fb_corr) if fb_corr is not None else "none"
            
            key = f"{orig} -> {corr}"
            transitions[key] = transitions.get(key, 0) + 1
        
        patterns = []
        for transition, count in sorted(transitions.items(), key=lambda x: -x[1]):
            orig, corr = transition.split(" -> ")
            patterns.append({
                "type": "categorical_transition",
                "from_value": orig,
                "to_value": corr,
                "count": count,
                "percentage": round((count / len(feedbacks)) * 100, 2)
            })
        
        return patterns
    
    def _analyze_generic_corrections(
        self,
        feedbacks: Sequence[WizardFeedback]
    ) -> list[dict[str, Any]]:
        """Analyze generic field corrections."""
        return [{
            "type": "generic",
            "total_corrections": len(feedbacks),
            "unique_original_values": len(set(str(f.original_value) for f in feedbacks)),
            "unique_corrected_values": len(set(str(f.corrected_value) for f in feedbacks))
        }]
    
    def _generate_recommendation(
        self,
        patterns: list[dict[str, Any]],
        field: str
    ) -> str | None:
        """Generate a recommendation based on correction patterns."""
        if not patterns:
            return None
        
        for pattern in patterns:
            if pattern.get("type") == "salary_adjustment":
                direction = pattern.get("direction")
                pct = pattern.get("adjustment_percentage", 0)
                
                if direction == "increase" and abs(pct) > 10:
                    return f"Consider increasing salary suggestions by approximately {abs(pct):.0f}%"
                elif direction == "decrease" and abs(pct) > 10:
                    return f"Consider decreasing salary suggestions by approximately {abs(pct):.0f}%"
        
        return None
    
    async def get_success_patterns(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
        months_back: int = 12
    ) -> dict[str, Any]:
        """
        Analyze patterns from successful hires.
        
        Args:
            db: Database session
            company_id: Company ID
            role: Optional role filter
            seniority: Optional seniority filter
            months_back: How many months of data to analyze
        
        Returns:
            Dictionary with success patterns and metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            
            conditions = [
                JobOutcome.company_id == company_id,
                JobOutcome.outcome == JobOutcomeType.FILLED,
                JobOutcome.created_at >= cutoff_date
            ]
            
            repo = FeedbackRepository(db)
            outcomes = cast(list[JobOutcome], await repo.list_outcomes_for_role_analysis(
                company_id=company_id,
                role=role,
                seniority=seniority,
            ))
            
            if not outcomes:
                return {
                    "role": role,
                    "seniority": seniority,
                    "sample_size": 0,
                    "patterns": {},
                    "confidence": "none"
                }
            
            time_to_fill: list[int] = []
            salaries: list[float] = []
            satisfaction: list[float] = []
            candidates_screened: list[int] = []
            all_skills: list[str] = []
            
            for o in outcomes:
                if o.time_to_fill_days is not None:
                    time_to_fill.append(int(o.time_to_fill_days))  # type: ignore[arg-type]
                if o.salary_final is not None:
                    salaries.append(float(o.salary_final))  # type: ignore[arg-type]
                if o.satisfaction_score is not None:
                    satisfaction.append(float(o.satisfaction_score))  # type: ignore[arg-type]
                if o.candidate_count_screened is not None:
                    candidates_screened.append(int(o.candidate_count_screened))  # type: ignore[arg-type]
                if o.skills_used is not None:
                    all_skills.extend([str(s) for s in o.skills_used])  # type: ignore[union-attr]
            
            skill_counts = {}
            for skill in all_skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            common_skills = sorted(skill_counts.items(), key=lambda x: -x[1])[:10]
            
            patterns = {
                "time_to_fill": {
                    "average": round(statistics.mean(time_to_fill), 1) if time_to_fill else None,
                    "median": round(statistics.median(time_to_fill), 1) if time_to_fill else None,
                    "min": min(time_to_fill) if time_to_fill else None,
                    "max": max(time_to_fill) if time_to_fill else None,
                    "sample_size": len(time_to_fill)
                },
                "salary": {
                    "average": round(statistics.mean(salaries), 2) if salaries else None,
                    "median": round(statistics.median(salaries), 2) if salaries else None,
                    "min": min(salaries) if salaries else None,
                    "max": max(salaries) if salaries else None,
                    "sample_size": len(salaries)
                },
                "satisfaction": {
                    "average": round(statistics.mean(satisfaction), 2) if satisfaction else None,
                    "sample_size": len(satisfaction)
                },
                "funnel": {
                    "avg_candidates_screened": round(statistics.mean(candidates_screened), 1) if candidates_screened else None,
                    "sample_size": len(candidates_screened)
                },
                "common_skills": [
                    {"skill": skill, "count": count}
                    for skill, count in common_skills
                ]
            }
            
            return {
                "role": role,
                "seniority": seniority,
                "sample_size": len(outcomes),
                "patterns": patterns,
                "confidence": self._calculate_confidence(len(outcomes))
            }
            
        except Exception as e:
            self.logger.error(f"Error getting success patterns: {e}")
            return {
                "role": role,
                "seniority": seniority,
                "sample_size": 0,
                "patterns": {},
                "confidence": "none",
                "error": str(e)
            }
    
    async def apply_learning(
        self,
        db: AsyncSession,
        company_id: str,
        suggestion: dict[str, Any],
        role: str | None = None,
        seniority: str | None = None
    ) -> dict[str, Any]:
        """
        Adjust a suggestion based on past corrections and success patterns.
        
        Args:
            db: Database session
            company_id: Company ID
            suggestion: Original suggestion to adjust
            role: Role context
            seniority: Seniority context
        
        Returns:
            Adjusted suggestion with learning applied
        """
        try:
            adjusted = suggestion.copy()
            adjustments_made = []
            
            if "salary_range" in suggestion:
                salary_patterns = await self.get_correction_patterns(
                    db, company_id, "salary_range", role, seniority
                )
                
                if salary_patterns.get("sample_size", 0) >= self.MEDIUM_CONFIDENCE_THRESHOLD:
                    for pattern in salary_patterns.get("patterns", []):
                        if pattern.get("type") == "salary_adjustment":
                            pct = pattern.get("adjustment_percentage", 0)
                            
                            if abs(pct) > 10:
                                multiplier = 1 + (pct / 100)
                                
                                orig_salary = suggestion["salary_range"]
                                if isinstance(orig_salary, dict):
                                    adjusted["salary_range"] = {
                                        "min": round(orig_salary.get("min", 0) * multiplier, 2),
                                        "max": round(orig_salary.get("max", 0) * multiplier, 2),
                                        "currency": orig_salary.get("currency", "BRL")
                                    }
                                    
                                    adjustments_made.append({
                                        "field": "salary_range",
                                        "original": orig_salary,
                                        "adjusted": adjusted["salary_range"],
                                        "reason": f"Based on {salary_patterns['sample_size']} past corrections showing {pct:.0f}% adjustment",
                                        "confidence": salary_patterns["confidence"]
                                    })
                                break
            
            success_patterns = await self.get_success_patterns(
                db, company_id, role, seniority
            )
            
            if success_patterns.get("confidence") in ["high", "medium"]:
                patterns = success_patterns.get("patterns", {})
                
                if "skills" not in suggestion and patterns.get("common_skills"):
                    top_skills = [s["skill"] for s in patterns["common_skills"][:5]]
                    adjusted["suggested_skills"] = top_skills
                    adjustments_made.append({
                        "field": "suggested_skills",
                        "original": None,
                        "adjusted": top_skills,
                        "reason": f"Based on {success_patterns['sample_size']} successful hires",
                        "confidence": success_patterns["confidence"]
                    })
                
                if patterns.get("time_to_fill", {}).get("average"):
                    adjusted["expected_time_to_fill_days"] = patterns["time_to_fill"]["average"]
            
            return {
                "original": suggestion,
                "adjusted": adjusted,
                "adjustments": adjustments_made,
                "learning_applied": len(adjustments_made) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Error applying learning: {e}")
            return {
                "original": suggestion,
                "adjusted": suggestion,
                "adjustments": [],
                "learning_applied": False,
                "error": str(e)
            }
    
    async def get_learning_summary(
        self,
        db: AsyncSession,
        company_id: str,
        months_back: int = 12
    ) -> dict[str, Any]:
        """
        Get a summary of all learning data for a company.
        
        Args:
            db: Database session
            company_id: Company ID
            months_back: How many months of data to analyze
        
        Returns:
            Summary of corrections and outcomes
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            
            feedback_query = select(func.count(WizardFeedback.id)).where(
                and_(
                    WizardFeedback.company_id == company_id,
                    WizardFeedback.created_at >= cutoff_date
                )
            )
            feedback_result = await db.execute(feedback_query)
            total_corrections = feedback_result.scalar() or 0
            
            field_query = select(
                WizardFeedback.field_corrected,
                func.count(WizardFeedback.id).label("count")
            ).where(
                and_(
                    WizardFeedback.company_id == company_id,
                    WizardFeedback.created_at >= cutoff_date
                )
            ).group_by(WizardFeedback.field_corrected)
            
            field_result = await db.execute(field_query)
            corrections_by_field = {row[0]: row[1] for row in field_result.fetchall()}
            
            outcome_query = select(
                JobOutcome.outcome,
                func.count(JobOutcome.id).label("count")
            ).where(
                and_(
                    JobOutcome.company_id == company_id,
                    JobOutcome.created_at >= cutoff_date
                )
            ).group_by(JobOutcome.outcome)
            
            outcome_result = await db.execute(outcome_query)
            outcomes_by_type = {row[0].value: row[1] for row in outcome_result.fetchall()}
            
            return {
                "period_months": months_back,
                "total_corrections": total_corrections,
                "corrections_by_field": corrections_by_field,
                "outcomes_by_type": outcomes_by_type,
                "total_outcomes": sum(outcomes_by_type.values()),
                "fill_rate": round(
                    (outcomes_by_type.get("filled", 0) / sum(outcomes_by_type.values()) * 100)
                    if outcomes_by_type else 0,
                    2
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error getting learning summary: {e}")
            return {
                "period_months": months_back,
                "total_corrections": 0,
                "corrections_by_field": {},
                "outcomes_by_type": {},
                "total_outcomes": 0,
                "fill_rate": 0,
                "error": str(e)
            }


feedback_learning_service = FeedbackLearningService()


def get_feedback_learning_service() -> "FeedbackLearningService":
    return feedback_learning_service
