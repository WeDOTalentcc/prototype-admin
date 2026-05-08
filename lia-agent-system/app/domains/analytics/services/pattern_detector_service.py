"""
Pattern Detector Service - Detects correction and success patterns from historical data.

This service analyzes:
- Recruiter corrections during wizard flow to detect systematic patterns
- Success patterns from filled positions
- Temporal patterns (seasonal, day-of-week effects)

When sufficient data is available (50+ vagas, 30+ outcomes), patterns are detected
and cached for efficient retrieval during wizard execution.
"""
import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.repositories.intelligence_repository import (
    IntelligenceRepository,
)
from lia_models.feedback_learning import JobOutcome, JobOutcomeType, WizardFeedback
from lia_models.intelligence_layer import (
    CorrectionPattern,
    PatternCache,
    SuccessProfile,
)

logger = logging.getLogger(__name__)


# Minimum data requirements for pattern detection
MIN_CORRECTIONS_FOR_PATTERN = 10
MIN_OUTCOMES_FOR_SUCCESS_PROFILE = 20
MIN_SAMPLE_SIZE_HIGH_CONFIDENCE = 30
PATTERN_CACHE_HOURS = 24


@dataclass
class DetectedPattern:
    """Represents a detected pattern."""
    pattern_type: str
    field: str | None
    key: str
    data: dict[str, Any]
    sample_size: int
    confidence: float
    applies_to: str | None = None


class PatternDetectorService:
    """
    Detects patterns from correction and outcome data.
    
    Features:
    - Correction pattern detection (salary adjustments, seniority corrections)
    - Success profile generation (what characteristics lead to successful hires)
    - Pattern caching for efficient retrieval
    - Confidence calculation based on sample size and consistency
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _calculate_confidence(
        self,
        sample_size: int,
        std_deviation: float | None = None,
        mean_value: float | None = None
    ) -> float:
        """
        Calculate confidence score based on sample size and consistency.
        
        Uses coefficient of variation (CV = std_dev / mean) when available
        to adjust confidence based on data consistency.
        """
        if sample_size < 5:
            return 0.3
        elif sample_size < 10:
            base = 0.5
        elif sample_size < 20:
            base = 0.7
        elif sample_size < 50:
            base = 0.8
        else:
            base = 0.9
        
        if std_deviation is not None and mean_value is not None and mean_value > 0 and sample_size > 5:
            cv = std_deviation / mean_value
            if cv < 0.1:
                base = min(base + 0.05, 0.95)
            elif cv > 0.5:
                base = max(base - 0.10, 0.3)
        
        return round(base, 2)
    
    async def detect_correction_patterns(
        self,
        db: AsyncSession,
        company_id: str,
        field: str | None = None,
        seniority: str | None = None,
        role_pattern: str | None = None,
        months_back: int = 12
    ) -> list[DetectedPattern]:
        """
        Detect patterns in recruiter corrections.
        
        Args:
            db: Database session
            company_id: Company to analyze
            field: Optional specific field to analyze
            seniority: Optional seniority filter
            role_pattern: Optional role pattern filter
            months_back: How many months of data to consider
            
        Returns:
            List of detected patterns
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            repo = IntelligenceRepository(db)
            feedbacks = await repo.list_wizard_feedback_filtered(
                company_id=company_id,
                cutoff_date=cutoff_date,
                field=field,
                seniority=seniority,
                role_pattern=role_pattern,
            )
            
            if len(feedbacks) < MIN_CORRECTIONS_FOR_PATTERN:
                self.logger.info(
                    f"Insufficient correction data for {company_id}: {len(feedbacks)} < {MIN_CORRECTIONS_FOR_PATTERN}"
                )
                return []
            
            patterns = []
            
            field_groups: dict[str, list[WizardFeedback]] = {}
            for fb in feedbacks:
                field_key = fb.field_corrected
                if field_key not in field_groups:
                    field_groups[field_key] = []
                field_groups[field_key].append(fb)
            
            for field_name, field_feedbacks in field_groups.items():
                if len(field_feedbacks) < MIN_CORRECTIONS_FOR_PATTERN:
                    continue
                
                if field_name in ["salary_range", "salary_min", "salary_max"]:
                    salary_patterns = self._detect_salary_patterns(field_feedbacks, field_name)
                    patterns.extend(salary_patterns)
                elif field_name == "seniority":
                    seniority_patterns = self._detect_seniority_patterns(field_feedbacks)
                    patterns.extend(seniority_patterns)
                else:
                    generic_patterns = self._detect_generic_patterns(field_feedbacks, field_name)
                    patterns.extend(generic_patterns)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting correction patterns: {e}")
            return []
    
    def _detect_salary_patterns(
        self,
        feedbacks: list[WizardFeedback],
        field_name: str
    ) -> list[DetectedPattern]:
        """Detect patterns in salary corrections."""
        patterns = []
        
        adjustments = []
        seniority_adjustments: dict[str, list[float]] = {}
        
        for fb in feedbacks:
            orig = fb.original_value
            corr = fb.corrected_value
            
            if isinstance(orig, dict) and isinstance(corr, dict):
                orig_mid = (orig.get("min", 0) + orig.get("max", 0)) / 2
                corr_mid = (corr.get("min", 0) + corr.get("max", 0)) / 2
            elif isinstance(orig, (int, float)) and isinstance(corr, (int, float)):
                orig_mid = float(orig)
                corr_mid = float(corr)
            else:
                continue
            
            if orig_mid > 0:
                adjustment = corr_mid / orig_mid
                adjustments.append(adjustment)
                
                sen = str(fb.seniority).lower() if fb.seniority else "unknown"
                if sen not in seniority_adjustments:
                    seniority_adjustments[sen] = []
                seniority_adjustments[sen].append(adjustment)
        
        if adjustments:
            avg_adjustment = statistics.mean(adjustments)
            std_dev = statistics.stdev(adjustments) if len(adjustments) > 1 else 0
            
            if abs(avg_adjustment - 1.0) > 0.05:
                direction = "increase" if avg_adjustment > 1.0 else "decrease"
                patterns.append(DetectedPattern(
                    pattern_type="salary_correction",
                    field=field_name,
                    key="salary_correction_overall",
                    data={
                        "direction": direction,
                        "avg_adjustment": round(avg_adjustment, 3),
                        "adjustment_percentage": round((avg_adjustment - 1.0) * 100, 1),
                        "min_adjustment": round(min(adjustments), 3),
                        "max_adjustment": round(max(adjustments), 3),
                        "std_deviation": round(std_dev, 3),
                    },
                    sample_size=len(adjustments),
                    confidence=self._calculate_confidence(len(adjustments), std_dev, avg_adjustment)
                ))
        
        for seniority, sen_adjustments in seniority_adjustments.items():
            if len(sen_adjustments) >= 5:
                avg = statistics.mean(sen_adjustments)
                std = statistics.stdev(sen_adjustments) if len(sen_adjustments) > 1 else 0
                
                if abs(avg - 1.0) > 0.05:
                    patterns.append(DetectedPattern(
                        pattern_type="salary_correction",
                        field=field_name,
                        key=f"salary_correction_seniority_{seniority}",
                        data={
                            "seniority": seniority,
                            "direction": "increase" if avg > 1.0 else "decrease",
                            "avg_adjustment": round(avg, 3),
                            "adjustment_percentage": round((avg - 1.0) * 100, 1),
                            "std_deviation": round(std, 3),
                        },
                        sample_size=len(sen_adjustments),
                        confidence=self._calculate_confidence(len(sen_adjustments), std, avg),
                        applies_to=seniority
                    ))
        
        return patterns
    
    def _detect_seniority_patterns(
        self,
        feedbacks: list[WizardFeedback]
    ) -> list[DetectedPattern]:
        """Detect patterns in seniority corrections."""
        patterns = []
        
        transitions: dict[str, int] = {}
        for fb in feedbacks:
            orig = str(fb.original_value).lower() if fb.original_value else "unknown"
            corr = str(fb.corrected_value).lower() if fb.corrected_value else "unknown"
            
            if orig != corr:
                key = f"{orig}->{corr}"
                transitions[key] = transitions.get(key, 0) + 1
        
        total = sum(transitions.values())
        for transition, count in transitions.items():
            if count >= 5 and count / total >= 0.2:
                from_val, to_val = transition.split("->")
                patterns.append(DetectedPattern(
                    pattern_type="seniority_correction",
                    field="seniority",
                    key=f"seniority_transition_{transition}",
                    data={
                        "from_value": from_val,
                        "to_value": to_val,
                        "count": count,
                        "percentage": round((count / total) * 100, 1),
                    },
                    sample_size=count,
                    confidence=self._calculate_confidence(count)
                ))
        
        return patterns
    
    def _detect_generic_patterns(
        self,
        feedbacks: list[WizardFeedback],
        field_name: str
    ) -> list[DetectedPattern]:
        """Detect patterns for generic fields."""
        patterns = []
        
        value_counts: dict[str, int] = {}
        for fb in feedbacks:
            corr = str(fb.corrected_value) if fb.corrected_value else "none"
            value_counts[corr] = value_counts.get(corr, 0) + 1
        
        total = sum(value_counts.values())
        dominant_values = [
            (val, count) for val, count in value_counts.items()
            if count / total >= 0.3
        ]
        
        if dominant_values:
            patterns.append(DetectedPattern(
                pattern_type="value_preference",
                field=field_name,
                key=f"value_preference_{field_name}",
                data={
                    "dominant_values": [
                        {"value": val, "percentage": round((count / total) * 100, 1)}
                        for val, count in sorted(dominant_values, key=lambda x: -x[1])
                    ]
                },
                sample_size=total,
                confidence=self._calculate_confidence(total)
            ))
        
        return patterns
    
    async def detect_success_profiles(
        self,
        db: AsyncSession,
        company_id: str,
        seniority: str | None = None,
        role_pattern: str | None = None,
        months_back: int = 12
    ) -> list[SuccessProfile]:
        """
        Detect success profiles from filled positions.
        
        Args:
            db: Database session
            company_id: Company to analyze
            seniority: Optional seniority filter
            role_pattern: Optional role pattern filter
            months_back: How many months of data to consider
            
        Returns:
            List of detected success profiles
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            
            conditions = [
                JobOutcome.company_id == company_id,
                JobOutcome.outcome == JobOutcomeType.FILLED,
                JobOutcome.created_at >= cutoff_date
            ]
            
            if seniority:
                conditions.append(func.lower(JobOutcome.seniority) == seniority.lower())
            if role_pattern:
                conditions.append(JobOutcome.role.ilike(f"%{role_pattern}%"))
            
            repo = IntelligenceRepository(db)
            outcomes = await repo.list_filled_outcomes_filtered(
                company_id=company_id,
                cutoff_date=cutoff_date,
                seniority=seniority,
                role_pattern=role_pattern,
            )
            
            if len(outcomes) < MIN_OUTCOMES_FOR_SUCCESS_PROFILE:
                self.logger.info(
                    f"Insufficient outcome data for {company_id}: {len(outcomes)} < {MIN_OUTCOMES_FOR_SUCCESS_PROFILE}"
                )
                return []
            
            profiles = []
            
            seniority_groups: dict[str, list[JobOutcome]] = {}
            for outcome in outcomes:
                sen = str(outcome.seniority).lower() if outcome.seniority else "unknown"
                if sen not in seniority_groups:
                    seniority_groups[sen] = []
                seniority_groups[sen].append(outcome)
            
            for sen, sen_outcomes in seniority_groups.items():
                if len(sen_outcomes) >= 10:
                    profile = self._build_success_profile(sen_outcomes, sen, company_id)
                    if profile:
                        profiles.append(profile)
            
            all_profile = self._build_success_profile(outcomes, None, company_id)
            if all_profile:
                profiles.append(all_profile)
            
            return profiles
            
        except Exception as e:
            self.logger.error(f"Error detecting success profiles: {e}")
            return []
    
    def _build_success_profile(
        self,
        outcomes: list[JobOutcome],
        seniority: str | None,
        company_id: str
    ) -> SuccessProfile | None:
        """Build a success profile from outcomes."""
        if not outcomes:
            return None
        
        time_to_fill = [o.time_to_fill_days for o in outcomes if o.time_to_fill_days]
        salaries = [o.salary_final for o in outcomes if o.salary_final]
        satisfaction = [o.satisfaction_score for o in outcomes if o.satisfaction_score]
        [o.candidate_count_screened for o in outcomes if o.candidate_count_screened]
        [o.candidate_count_interviewed for o in outcomes if o.candidate_count_interviewed]
        
        all_skills: list[str] = []
        for o in outcomes:
            if o.skills_used:
                all_skills.extend(o.skills_used)
        
        skill_counts: dict[str, int] = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        common_skills = sorted(skill_counts.items(), key=lambda x: -x[1])[:10]
        must_have = [s[0] for s in common_skills if s[1] >= len(outcomes) * 0.5]
        
        profile = SuccessProfile(
            company_id=company_id,
            seniority=seniority,
            avg_time_to_fill_days=int(statistics.mean(time_to_fill)) if time_to_fill else None,
            avg_salary=round(statistics.mean(salaries), 2) if salaries else None,
            salary_range_min=round(min(salaries), 2) if salaries else None,
            salary_range_max=round(max(salaries), 2) if salaries else None,
            avg_satisfaction_score=round(statistics.mean(satisfaction), 2) if satisfaction else None,
            common_skills=[{"skill": s[0], "frequency": s[1]} for s in common_skills],
            common_requirements=must_have,
            sample_size=len(outcomes),
        )
        
        return profile
    
    async def cache_patterns(
        self,
        db: AsyncSession,
        company_id: str,
        patterns: list[DetectedPattern],
        pattern_type: str
    ) -> None:
        """Cache detected patterns for efficient retrieval."""
        try:
            for pattern in patterns:
                await db.execute(
                    text("""
                        DELETE FROM pattern_cache 
                        WHERE company_id = :company_id 
                        AND pattern_type = :pattern_type 
                        AND pattern_key = :pattern_key
                    """),
                    {
                        "company_id": company_id,
                        "pattern_type": pattern_type,
                        "pattern_key": pattern.key
                    }
                )
            
            for pattern in patterns:
                cache_entry = PatternCache(
                    company_id=company_id,
                    pattern_type=pattern_type,
                    pattern_key=pattern.key,
                    pattern_data=pattern.data,
                    sample_size=pattern.sample_size,
                    confidence=pattern.confidence,
                    calculated_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=PATTERN_CACHE_HOURS)
                )
                db.add(cache_entry)
            
            await db.flush()
            self.logger.info(f"Cached {len(patterns)} patterns for {company_id}")
            
        except Exception as e:
            self.logger.error(f"Error caching patterns: {e}")
    
    async def get_cached_patterns(
        self,
        db: AsyncSession,
        company_id: str,
        pattern_type: str | None = None,
        pattern_key: str | None = None
    ) -> list[PatternCache]:
        """Retrieve cached patterns."""
        try:
            conditions = [
                PatternCache.company_id == company_id,
                PatternCache.expires_at > datetime.utcnow()
            ]
            
            if pattern_type:
                conditions.append(PatternCache.pattern_type == pattern_type)
            if pattern_key:
                conditions.append(PatternCache.pattern_key == pattern_key)
            
            repo = IntelligenceRepository(db)
            return await repo.list_active_pattern_caches(
                company_id=company_id,
                pattern_type=pattern_type,
                pattern_key=pattern_key,
            )
            
        except Exception as e:
            self.logger.error(f"Error getting cached patterns: {e}")
            return []
    
    async def save_correction_patterns(
        self,
        db: AsyncSession,
        company_id: str,
        patterns: list[DetectedPattern]
    ) -> list[CorrectionPattern]:
        """Save detected correction patterns to database."""
        saved = []
        try:
            for pattern in patterns:
                data = pattern.data
                
                _repo4 = IntelligenceRepository(db)
                existing_pattern = await _repo4.find_correction_pattern_by_field(
                    company_id=company_id,
                    field=pattern.field,
                    seniority=data.get("seniority"),
                )
                
                if existing_pattern:
                    existing_pattern.adjustment_direction = data.get("direction", "unknown")
                    existing_pattern.adjustment_magnitude = data.get("avg_adjustment", 1.0)
                    existing_pattern.pattern_type = pattern.pattern_type
                    existing_pattern.occurrence_count = data.get("count", pattern.sample_size)
                    existing_pattern.original_value_pattern = data.get("from_value")
                    existing_pattern.corrected_value_pattern = data.get("to_value")
                    existing_pattern.sample_size = pattern.sample_size
                    existing_pattern.confidence = pattern.confidence
                    existing_pattern.updated_at = datetime.utcnow()
                    saved.append(existing_pattern)
                else:
                    new_pattern = CorrectionPattern(
                        company_id=company_id,
                        field=pattern.field,
                        pattern_type=pattern.pattern_type,
                        seniority=data.get("seniority"),
                        adjustment_direction=data.get("direction", "unknown"),
                        adjustment_magnitude=data.get("avg_adjustment", 1.0),
                        original_value_pattern=data.get("from_value"),
                        corrected_value_pattern=data.get("to_value"),
                        occurrence_count=data.get("count", pattern.sample_size),
                        sample_size=pattern.sample_size,
                        confidence=pattern.confidence,
                    )
                    db.add(new_pattern)
                    saved.append(new_pattern)
            
            await db.flush()
            return saved
            
        except Exception as e:
            self.logger.error(f"Error saving correction patterns: {e}")
            return []


pattern_detector_service = PatternDetectorService()
