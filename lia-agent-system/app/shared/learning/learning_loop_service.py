"""
Learning Loop Service - Captures feedback and generates learning patterns.

Provides continuous improvement through:
1. CAPTURE: Silently records all suggestions and their outcomes
2. ANALYZE: Detects patterns from accumulated feedback
3. APPLY: Uses patterns to improve future suggestions

The learning loop operates invisibly - it captures data without
requiring explicit UI feedback from users. Learning happens through
observing what users accept, modify, or reject.
"""
import json
import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, StrEnum
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.tracing import trace_span

logger = logging.getLogger(__name__)


class FeedbackOutcome(StrEnum):
    """Possible outcomes for a suggestion."""
    ACCEPTED = "accepted"
    MODIFIED = "modified"
    REJECTED = "rejected"
    IGNORED = "ignored"


class PatternType(StrEnum):
    """Types of learnable patterns."""
    SALARY_PREFERENCE = "salary_preference"
    SKILL_PREFERENCE = "skill_preference"
    BENEFIT_PREFERENCE = "benefit_preference"
    WORK_MODEL_PREFERENCE = "work_model_preference"
    SCREENING_PREFERENCE = "screening_preference"
    JD_STYLE_PREFERENCE = "jd_style_preference"
    SOURCE_TRUST = "source_trust"


@dataclass
class FeedbackCapture:
    """Data structure for capturing feedback."""
    company_id: str
    field_name: str
    suggested_value: Any
    final_value: Any
    outcome: FeedbackOutcome
    session_id: str | None = None
    job_id: str | None = None
    stage: str | None = None
    role: str | None = None
    seniority: str | None = None
    department: str | None = None
    location: str | None = None
    source: str | None = None
    source_confidence: float | None = None
    response_time_ms: int | None = None


@dataclass
class LearnedPattern:
    """A pattern extracted from feedback data."""
    pattern_type: PatternType
    pattern_key: str
    pattern_value: Any
    sample_size: int
    acceptance_rate: float
    confidence: str
    confidence_score: float
    filters: dict[str, str | None]


class LearningLoopService:
    """
    Core learning service that captures feedback and generates patterns.
    
    Key responsibilities:
    1. Record every suggestion and its outcome (silent capture)
    2. Detect patterns from accumulated feedback
    3. Provide patterns for future suggestion improvement
    4. Track confidence levels based on sample sizes
    """
    
    CONFIDENCE_THRESHOLDS = {
        "high": 20,
        "medium": 10,
        "low": 5
    }
    
    ACCEPTANCE_THRESHOLDS = {
        "promote": 0.75,
        "demote": 0.25
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _determine_outcome(
        self,
        suggested_value: Any,
        final_value: Any,
        explicitly_rejected: bool = False
    ) -> FeedbackOutcome:
        """Determine the outcome based on suggested vs final values."""
        if explicitly_rejected:
            return FeedbackOutcome.REJECTED
        
        if final_value is None:
            return FeedbackOutcome.IGNORED
        
        if self._values_match(suggested_value, final_value):
            return FeedbackOutcome.ACCEPTED
        
        return FeedbackOutcome.MODIFIED
    
    def _values_match(self, suggested: Any, final: Any) -> bool:
        """Check if two values are equivalent."""
        if suggested is None and final is None:
            return True
        if suggested is None or final is None:
            return False
        
        if isinstance(suggested, dict) and isinstance(final, dict):
            return json.dumps(suggested, sort_keys=True) == json.dumps(final, sort_keys=True)
        
        if isinstance(suggested, list) and isinstance(final, list):
            return set(map(str, suggested)) == set(map(str, final))
        
        return str(suggested).lower().strip() == str(final).lower().strip()
    
    def _calculate_modification_delta(
        self,
        suggested_value: Any,
        final_value: Any,
        field_name: str
    ) -> dict[str, Any] | None:
        """Calculate the difference between suggested and final values."""
        if suggested_value is None or final_value is None:
            return None
        
        delta = {}
        
        if field_name in ["salary_min", "salary_max", "salary"]:
            if isinstance(suggested_value, dict) and isinstance(final_value, dict):
                sug_min = suggested_value.get("min", 0)
                sug_max = suggested_value.get("max", 0)
                fin_min = final_value.get("min", 0)
                fin_max = final_value.get("max", 0)
                
                if sug_min and fin_min:
                    delta["min_change_pct"] = ((fin_min - sug_min) / sug_min) * 100
                if sug_max and fin_max:
                    delta["max_change_pct"] = ((fin_max - sug_max) / sug_max) * 100
                
                delta["direction"] = "increased" if fin_min > sug_min else "decreased"
        
        elif field_name in ["skills", "technical_skills", "behavioral_skills"]:
            if isinstance(suggested_value, list) and isinstance(final_value, list):
                sug_set = set(map(str, suggested_value))
                fin_set = set(map(str, final_value))
                
                delta["added"] = list(fin_set - sug_set)
                delta["removed"] = list(sug_set - fin_set)
                delta["kept"] = list(sug_set & fin_set)
        
        elif field_name == "benefits":
            if isinstance(suggested_value, list) and isinstance(final_value, list):
                sug_names = {b.get("name") if isinstance(b, dict) else b for b in suggested_value}
                fin_names = {b.get("name") if isinstance(b, dict) else b for b in final_value}
                
                delta["added"] = list(fin_names - sug_names)
                delta["removed"] = list(sug_names - fin_names)
        
        return delta if delta else None
    
    def _calculate_confidence(self, sample_size: int, acceptance_rate: float) -> tuple[str, float]:
        """Calculate confidence level based on sample size and acceptance rate."""
        if sample_size >= self.CONFIDENCE_THRESHOLDS["high"]:
            base_conf = "high"
            base_score = 0.9
        elif sample_size >= self.CONFIDENCE_THRESHOLDS["medium"]:
            base_conf = "medium"
            base_score = 0.7
        elif sample_size >= self.CONFIDENCE_THRESHOLDS["low"]:
            base_conf = "low"
            base_score = 0.5
        else:
            base_conf = "very_low"
            base_score = 0.3
        
        if acceptance_rate < 0.5:
            base_score *= 0.8
            if base_conf == "high":
                base_conf = "medium"
        elif acceptance_rate > 0.8:
            base_score *= 1.1
            base_score = min(1.0, base_score)
        
        return base_conf, base_score
    
    async def capture_feedback(
        self,
        db: AsyncSession,
        capture: FeedbackCapture
    ) -> str:
        """
        Silently capture feedback event.
        
        This is called whenever a field is finalized to record
        what was suggested vs what was actually used.
        
        Returns the feedback event ID.
        """
        try:
            from app.models.intelligent_cache import FeedbackEvent
            
            modification_delta = None
            if capture.outcome == FeedbackOutcome.MODIFIED:
                modification_delta = self._calculate_modification_delta(
                    capture.suggested_value,
                    capture.final_value,
                    capture.field_name
                )
            
            event = FeedbackEvent(
                company_id=capture.company_id,
                session_id=capture.session_id,
                job_id=capture.job_id,
                event_type="wizard_suggestion",
                field_name=capture.field_name,
                stage=capture.stage,
                suggested_value=capture.suggested_value,
                final_value=capture.final_value,
                outcome=capture.outcome.value,
                modification_delta=modification_delta,
                role=capture.role,
                seniority=capture.seniority,
                department=capture.department,
                location=capture.location,
                source=capture.source,
                source_confidence=capture.source_confidence,
                response_time_ms=capture.response_time_ms,
                processed_for_learning=False
            )
            
            db.add(event)
            await db.commit()
            
            self.logger.debug(
                f"Captured feedback: {capture.field_name} -> {capture.outcome.value}"
            )

            # Conectar ao model drift quando há feedbacks negativos
            try:
                if capture.outcome in (FeedbackOutcome.REJECTED, FeedbackOutcome.IGNORED):
                    import asyncio

                    from app.shared.services.model_drift_service import ModelDriftService
                    asyncio.create_task(
                        ModelDriftService().check_drift_trigger(
                            company_id=capture.company_id,
                            trigger_type="learning_feedback",
                        )
                    )
            except Exception as _drift_exc:
                logger.debug("[LearningLoop] drift trigger skipped: %s", _drift_exc)

            return str(event.id)

        except Exception as e:
            self.logger.error(f"Error capturing feedback: {e}")
            await db.rollback()
            raise
    
    async def capture_from_wizard_update(
        self,
        db: AsyncSession,
        company_id: str,
        session_id: str,
        job_id: str | None,
        field_name: str,
        suggested_value: Any,
        final_value: Any,
        stage: str | None = None,
        context: dict[str, Any] | None = None,
        source: str | None = None,
        source_confidence: float | None = None,
        explicitly_rejected: bool = False
    ) -> str:
        """
        Convenience method for capturing feedback from wizard updates.
        
        Called automatically when fields are updated in the wizard.
        """
        outcome = self._determine_outcome(suggested_value, final_value, explicitly_rejected)
        
        ctx = context or {}
        
        capture = FeedbackCapture(
            company_id=company_id,
            field_name=field_name,
            suggested_value=suggested_value,
            final_value=final_value,
            outcome=outcome,
            session_id=session_id,
            job_id=job_id,
            stage=stage,
            role=ctx.get("role") or ctx.get("title"),
            seniority=ctx.get("seniority"),
            department=ctx.get("department"),
            location=ctx.get("location"),
            source=source,
            source_confidence=source_confidence
        )
        
        return await self.capture_feedback(db, capture)
    
    @trace_span("learning.process_feedback", attributes={"component": "learning_loop"})
    async def process_unprocessed_feedback(
        self,
        db: AsyncSession,
        company_id: str,
        batch_size: int = 100
    ) -> int:
        """
        Process unprocessed feedback events to update learning patterns.
        
        This is typically called periodically by a background job.
        Returns the number of events processed.
        """
        try:
            from app.models.intelligent_cache import FeedbackEvent
            
            result = await db.execute(
                select(FeedbackEvent)
                .where(
                    and_(
                        FeedbackEvent.company_id == company_id,
                        not FeedbackEvent.processed_for_learning
                    )
                )
                .order_by(FeedbackEvent.created_at)
                .limit(batch_size)
            )
            events = result.scalars().all()
            
            if not events:
                return 0
            
            patterns_to_update: dict[str, dict] = {}
            
            for event in events:
                pattern_key = self._generate_pattern_key(event)
                
                if pattern_key not in patterns_to_update:
                    patterns_to_update[pattern_key] = {
                        "pattern_type": self._get_pattern_type(event.field_name),
                        "accepted": 0,
                        "total": 0,
                        "values": [],
                        "role": event.role,
                        "seniority": event.seniority,
                        "department": event.department,
                        "location": event.location
                    }
                
                patterns_to_update[pattern_key]["total"] += 1
                if event.outcome in ["accepted", "modified"]:
                    patterns_to_update[pattern_key]["accepted"] += 1
                    if event.final_value:
                        patterns_to_update[pattern_key]["values"].append(event.final_value)
                
                event.processed_for_learning = True
            
            # F1-02: FairnessGuard — bloqueia padrões discriminatórios antes de persistir
            import os as _os
            if _os.getenv("FAIRNESS_LEARNING_CHECK_ENABLED", "true").lower() != "false":
                try:
                    from app.shared.compliance.fairness_guard import FairnessGuard as _FG
                    _validation = _FG().validate_learning_batch(patterns_to_update)
                    if not _validation.is_clean:
                        for _bk in _validation.blocked_patterns:
                            patterns_to_update.pop(_bk, None)
                            self.logger.warning(
                                "[LearningLoop] FairnessGuard bloqueou padrão: %s", _bk
                            )
                        # Audit trail (fail-safe)
                        try:
                            from app.shared.compliance.audit_service import audit_service
                            await audit_service.log_decision(
                                db=db,
                                company_id=company_id,
                                agent_name="learning_loop",
                                decision_type="fairness_check",
                                action="block_learning_pattern",
                                decision="blocked",
                                reasoning=_validation.warnings,
                                criteria_used=["fairness_guard_layer1", "fairness_guard_layer2"],
                                criteria_ignored=_validation.blocked_patterns,
                            )
                        except Exception as _ae:
                            self.logger.debug(
                                "[LearningLoop] audit log falhou (fail-safe): %s", _ae
                            )
                except Exception as _fge:
                    self.logger.debug(
                        "[LearningLoop] FairnessGuard check falhou (fail-open): %s", _fge
                    )

            # Z2-01: snapshot ANTES de aplicar — permite rollback em caso de viés posterior
            try:
                from app.shared.learning.learning_snapshot_service import (
                    learning_snapshot_service as _snap_svc,
                )
                await _snap_svc.save_snapshot(company_id, db)
            except Exception as _snap_exc:
                self.logger.debug(
                    "[LearningLoop] snapshot falhou (fail-safe): %s", _snap_exc
                )

            for pattern_key, data in patterns_to_update.items():
                await self._update_pattern(db, company_id, pattern_key, data)

            await db.commit()
            
            self.logger.info(
                f"Processed {len(events)} feedback events into {len(patterns_to_update)} patterns"
            )
            
            return len(events)
            
        except Exception as e:
            self.logger.error(f"Error processing feedback: {e}")
            await db.rollback()
            raise
    
    def _generate_pattern_key(self, event) -> str:
        """Generate a unique key for pattern grouping."""
        parts = [
            event.field_name,
            event.role or "any_role",
            event.seniority or "any_seniority"
        ]
        return ":".join(parts)
    
    def _get_pattern_type(self, field_name: str) -> str:
        """Map field name to pattern type."""
        field_to_pattern = {
            "salary_min": PatternType.SALARY_PREFERENCE.value,
            "salary_max": PatternType.SALARY_PREFERENCE.value,
            "salary": PatternType.SALARY_PREFERENCE.value,
            "salary_range": PatternType.SALARY_PREFERENCE.value,
            "skills": PatternType.SKILL_PREFERENCE.value,
            "technical_skills": PatternType.SKILL_PREFERENCE.value,
            "behavioral_skills": PatternType.SKILL_PREFERENCE.value,
            "benefits": PatternType.BENEFIT_PREFERENCE.value,
            "work_model": PatternType.WORK_MODEL_PREFERENCE.value,
            "screening_questions": PatternType.SCREENING_PREFERENCE.value,
            "job_summary": PatternType.JD_STYLE_PREFERENCE.value,
        }
        return field_to_pattern.get(field_name, "general_preference")
    
    async def _update_pattern(
        self,
        db: AsyncSession,
        company_id: str,
        pattern_key: str,
        data: dict
    ) -> None:
        """Update or create a learning pattern."""
        from app.models.intelligent_cache import LearningPattern
        
        result = await db.execute(
            select(LearningPattern)
            .where(
                and_(
                    LearningPattern.company_id == company_id,
                    LearningPattern.pattern_key == pattern_key
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            new_sample_size = existing.sample_size + data["total"]
            total_accepted = int(existing.acceptance_rate * existing.sample_size) + data["accepted"]
            new_acceptance_rate = total_accepted / new_sample_size if new_sample_size > 0 else 0
            
            confidence, confidence_score = self._calculate_confidence(
                new_sample_size, new_acceptance_rate
            )
            
            pattern_value = self._aggregate_pattern_value(
                existing.pattern_value,
                data["values"],
                data["pattern_type"]
            )
            
            existing.sample_size = new_sample_size
            existing.acceptance_rate = new_acceptance_rate
            existing.confidence = confidence
            existing.confidence_score = confidence_score
            existing.pattern_value = pattern_value
            existing.updated_at = datetime.utcnow()
        else:
            acceptance_rate = data["accepted"] / data["total"] if data["total"] > 0 else 0
            confidence, confidence_score = self._calculate_confidence(
                data["total"], acceptance_rate
            )
            
            pattern_value = self._aggregate_pattern_value(
                None, data["values"], data["pattern_type"]
            )
            
            pattern = LearningPattern(
                company_id=company_id,
                pattern_type=data["pattern_type"],
                pattern_key=pattern_key,
                pattern_value=pattern_value,
                sample_size=data["total"],
                acceptance_rate=acceptance_rate,
                confidence=confidence,
                confidence_score=confidence_score,
                role_filter=data.get("role"),
                seniority_filter=data.get("seniority"),
                department_filter=data.get("department"),
                location_filter=data.get("location"),
                is_active=True
            )
            db.add(pattern)
    
    def _aggregate_pattern_value(
        self,
        existing_value: dict | None,
        new_values: list[Any],
        pattern_type: str
    ) -> dict[str, Any]:
        """Aggregate values into a pattern value structure."""
        result = existing_value or {}
        
        if pattern_type == PatternType.SALARY_PREFERENCE.value:
            all_mins = result.get("min_values", [])
            all_maxs = result.get("max_values", [])
            
            for val in new_values:
                if isinstance(val, dict):
                    if val.get("min"):
                        all_mins.append(val["min"])
                    if val.get("max"):
                        all_maxs.append(val["max"])
            
            result["min_values"] = all_mins[-50:]
            result["max_values"] = all_maxs[-50:]
            
            if all_mins:
                result["avg_min"] = statistics.mean(all_mins)
                result["median_min"] = statistics.median(all_mins)
            if all_maxs:
                result["avg_max"] = statistics.mean(all_maxs)
                result["median_max"] = statistics.median(all_maxs)
        
        elif pattern_type in [PatternType.SKILL_PREFERENCE.value, PatternType.BENEFIT_PREFERENCE.value]:
            item_counts = result.get("item_counts", {})
            
            for val in new_values:
                items = val if isinstance(val, list) else [val]
                for item in items:
                    item_name = item.get("name") if isinstance(item, dict) else str(item)
                    item_counts[item_name] = item_counts.get(item_name, 0) + 1
            
            result["item_counts"] = item_counts
            sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
            result["top_items"] = [item[0] for item in sorted_items[:20]]
        
        else:
            result["recent_values"] = (result.get("recent_values", []) + new_values)[-20:]
        
        result["last_updated"] = datetime.utcnow().isoformat()
        return result
    
    async def get_patterns_for_context(
        self,
        db: AsyncSession,
        company_id: str,
        field_name: str,
        role: str | None = None,
        seniority: str | None = None,
        department: str | None = None,
        location: str | None = None,
        min_confidence: float = 0.5
    ) -> list[LearnedPattern]:
        """
        Retrieve applicable learning patterns for a given context.
        
        Returns patterns sorted by specificity and confidence.
        """
        try:
            from app.models.intelligent_cache import LearningPattern
            
            pattern_type = self._get_pattern_type(field_name)
            
            conditions = [
                LearningPattern.company_id == company_id,
                LearningPattern.pattern_type == pattern_type,
                LearningPattern.is_active,
                LearningPattern.confidence_score >= min_confidence
            ]
            
            result = await db.execute(
                select(LearningPattern)
                .where(and_(*conditions))
                .order_by(LearningPattern.confidence_score.desc())
            )
            patterns = result.scalars().all()
            
            applicable = []
            for p in patterns:
                if role and p.role_filter and p.role_filter.lower() != role.lower():
                    continue
                if seniority and p.seniority_filter and p.seniority_filter.lower() != seniority.lower():
                    continue
                
                specificity = sum([
                    1 if p.role_filter else 0,
                    1 if p.seniority_filter else 0,
                    1 if p.department_filter else 0,
                    1 if p.location_filter else 0
                ])
                
                applicable.append((p, specificity))
            
            applicable.sort(key=lambda x: (x[1], x[0].confidence_score), reverse=True)
            
            return [
                LearnedPattern(
                    pattern_type=PatternType(p.pattern_type) if p.pattern_type in [e.value for e in PatternType] else PatternType.SALARY_PREFERENCE,
                    pattern_key=p.pattern_key,
                    pattern_value=p.pattern_value,
                    sample_size=p.sample_size,
                    acceptance_rate=p.acceptance_rate,
                    confidence=p.confidence,
                    confidence_score=p.confidence_score,
                    filters={
                        "role": p.role_filter,
                        "seniority": p.seniority_filter,
                        "department": p.department_filter,
                        "location": p.location_filter
                    }
                )
                for p, _ in applicable
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting patterns: {e}")
            return []
    
    async def get_salary_adjustment(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None
    ) -> dict[str, float] | None:
        """
        Get learned salary adjustment based on historical feedback.
        
        Returns adjustment factors to apply to market benchmarks.
        """
        patterns = await self.get_patterns_for_context(
            db, company_id, "salary_range", role, seniority
        )
        
        if not patterns:
            return None
        
        best_pattern = patterns[0]
        pattern_value = best_pattern.pattern_value
        
        if "avg_min" in pattern_value and "avg_max" in pattern_value:
            return {
                "learned_min": pattern_value["avg_min"],
                "learned_max": pattern_value["avg_max"],
                "median_min": pattern_value.get("median_min", pattern_value["avg_min"]),
                "median_max": pattern_value.get("median_max", pattern_value["avg_max"]),
                "sample_size": best_pattern.sample_size,
                "confidence": best_pattern.confidence_score
            }
        
        return None
    
    async def get_preferred_skills(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get skills that this company historically prefers.
        
        Returns skills ranked by usage frequency.
        """
        patterns = await self.get_patterns_for_context(
            db, company_id, "skills", role, seniority
        )
        
        if not patterns:
            return []
        
        best_pattern = patterns[0]
        top_items = best_pattern.pattern_value.get("top_items", [])
        item_counts = best_pattern.pattern_value.get("item_counts", {})
        
        return [
            {
                "skill": skill,
                "usage_count": item_counts.get(skill, 0),
                "confidence": best_pattern.confidence_score
            }
            for skill in top_items[:limit]
        ]
    
    async def get_feedback_stats(
        self,
        db: AsyncSession,
        company_id: str,
        days_back: int = 30
    ) -> dict[str, Any]:
        """Get feedback statistics for analytics."""
        try:
            from app.models.intelligent_cache import FeedbackEvent
            
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            
            result = await db.execute(
                select(
                    FeedbackEvent.outcome,
                    func.count(FeedbackEvent.id).label("count")
                )
                .where(
                    and_(
                        FeedbackEvent.company_id == company_id,
                        FeedbackEvent.created_at >= cutoff
                    )
                )
                .group_by(FeedbackEvent.outcome)
            )
            
            outcome_counts = {row.outcome: row.count for row in result}
            
            total = sum(outcome_counts.values())
            
            return {
                "total_events": total,
                "outcomes": outcome_counts,
                "acceptance_rate": (
                    (outcome_counts.get("accepted", 0) + outcome_counts.get("modified", 0)) / total
                    if total > 0 else 0
                ),
                "period_days": days_back
            }
            
        except Exception as e:
            self.logger.error(f"Error getting feedback stats: {e}")
            return {}
    
    async def capture_skills_feedback(
        self,
        db: AsyncSession,
        company_id: str,
        suggested_skills: list[dict[str, Any]],
        final_skills: list[dict[str, Any]],
        job_context: dict[str, Any]
    ) -> None:
        """
        Capture feedback when skills are finalized.
        
        Compares suggested vs final skills to learn patterns:
        - accepted: skill used as suggested (same weight/level)
        - modified: skill used with different weight/level
        - rejected: suggested skill was removed
        - added: new skill not in suggestions (custom)
        
        Args:
            db: Database session
            company_id: Company identifier
            suggested_skills: List of suggested skills with metadata
            final_skills: List of final selected skills with metadata
            job_context: Context data (job_title, department, seniority, etc.)
        """
        try:
            from app.models.skills_catalog import SkillUsageAnalytics
            
            # Get job context details
            job_id = job_context.get("job_id")
            job_title = job_context.get("job_title")
            department = job_context.get("department")
            seniority = job_context.get("seniority")
            
            # Create a map of final skills for quick lookup
            final_skills_map = {}
            for skill in final_skills:
                skill_name = skill.get("name") or skill.get("skill")
                if skill_name:
                    final_skills_map[skill_name.lower()] = skill
            
            # Process suggested skills
            for suggested_skill in suggested_skills:
                suggested_name = suggested_skill.get("name") or suggested_skill.get("skill")
                if not suggested_name:
                    continue
                
                final_skill = final_skills_map.get(suggested_name.lower())
                
                # Determine outcome
                if final_skill is None:
                    outcome = "rejected"
                else:
                    # Check if skill properties match
                    suggested_weight = suggested_skill.get("weight")
                    final_weight = final_skill.get("weight")
                    suggested_level = suggested_skill.get("level")
                    final_level = final_skill.get("level")
                    
                    if (suggested_weight == final_weight and 
                        suggested_level == final_level):
                        outcome = "accepted"
                    else:
                        outcome = "modified"
                
                # Record to SkillUsageAnalytics
                analytics = SkillUsageAnalytics(
                    company_id=company_id,
                    skill_name=suggested_name,
                    skill_type=suggested_skill.get("type", "technical"),
                    category=suggested_skill.get("category"),
                    job_vacancy_id=job_id,
                    job_title=job_title,
                    department=department,
                    seniority=seniority,
                    source=suggested_skill.get("source", "llm_suggestion"),
                    outcome=outcome,
                    original_weight=suggested_skill.get("weight"),
                    final_weight=final_skill.get("weight") if final_skill else None,
                    original_level=suggested_skill.get("level"),
                    final_level=final_skill.get("level") if final_skill else None,
                    was_required=suggested_skill.get("required", False),
                    suggestion_confidence=suggested_skill.get("confidence"),
                    suggestion_reasoning=suggested_skill.get("reasoning")
                )
                db.add(analytics)
            
            # Process added skills (in final but not in suggested)
            suggested_names_lower = {
                (s.get("name") or s.get("skill")).lower() 
                for s in suggested_skills 
                if s.get("name") or s.get("skill")
            }
            
            for final_skill in final_skills:
                final_name = final_skill.get("name") or final_skill.get("skill")
                if final_name and final_name.lower() not in suggested_names_lower:
                    analytics = SkillUsageAnalytics(
                        company_id=company_id,
                        skill_name=final_name,
                        skill_type=final_skill.get("type", "technical"),
                        category=final_skill.get("category"),
                        job_vacancy_id=job_id,
                        job_title=job_title,
                        department=department,
                        seniority=seniority,
                        source="manual",
                        outcome="added",
                        final_weight=final_skill.get("weight"),
                        final_level=final_skill.get("level"),
                        was_required=final_skill.get("required", False)
                    )
                    db.add(analytics)
            
            await db.commit()
            
            # Check if we should trigger pattern generation
            unprocessed_count = await self._count_unprocessed_skill_analytics(
                db, company_id
            )
            
            if unprocessed_count >= 10:
                await self.generate_skill_patterns(db, company_id)
            
            self.logger.debug(
                f"Captured skills feedback for company {company_id}: "
                f"{len(suggested_skills)} suggested, {len(final_skills)} final"
            )
            
        except Exception as e:
            self.logger.error(f"Error capturing skills feedback: {e}")
            await db.rollback()
            raise
    
    async def _count_unprocessed_skill_analytics(
        self,
        db: AsyncSession,
        company_id: str
    ) -> int:
        """Count unprocessed skill analytics records for a company."""
        from app.models.skills_catalog import SkillUsageAnalytics
        
        result = await db.execute(
            select(func.count(SkillUsageAnalytics.id))
            .where(SkillUsageAnalytics.company_id == company_id)
        )
        return result.scalar() or 0
    
    async def generate_skill_patterns(
        self,
        db: AsyncSession,
        company_id: str
    ) -> None:
        """
        Generate skill suggestion patterns from usage analytics.
        
        Aggregates SkillUsageAnalytics data to identify:
        - Which skills are frequently used/accepted
        - Patterns by job title, department, seniority
        - High-confidence patterns to promote
        
        Args:
            db: Database session
            company_id: Company identifier
        """
        try:
            from app.models.skills_catalog import SkillSuggestionPattern, SkillUsageAnalytics
            
            # Get all analytics for the company
            result = await db.execute(
                select(SkillUsageAnalytics)
                .where(SkillUsageAnalytics.company_id == company_id)
            )
            analytics_records = result.scalars().all()
            
            if not analytics_records:
                return
            
            # Group by skill and context
            patterns_data: dict[str, dict[str, Any]] = {}
            
            for record in analytics_records:
                # Create context key
                context_key = f"{record.job_title or 'any'}:{record.department or 'any'}:{record.seniority or 'any'}"
                pattern_key = f"{record.skill_name}:{context_key}"
                
                if pattern_key not in patterns_data:
                    patterns_data[pattern_key] = {
                        "skill_name": record.skill_name,
                        "skill_type": record.skill_type,
                        "skill_category": record.category,
                        "context_key": context_key,
                        "job_title": record.job_title,
                        "department": record.department,
                        "seniority": record.seniority,
                        "total": 0,
                        "accepted": 0,
                        "modified": 0,
                        "rejected": 0,
                        "added": 0,
                        "weights": [],
                        "levels": [],
                        "was_required_count": 0
                    }
                
                # Count outcomes
                patterns_data[pattern_key]["total"] += 1
                if record.outcome == "accepted":
                    patterns_data[pattern_key]["accepted"] += 1
                elif record.outcome == "modified":
                    patterns_data[pattern_key]["modified"] += 1
                elif record.outcome == "rejected":
                    patterns_data[pattern_key]["rejected"] += 1
                elif record.outcome == "added":
                    patterns_data[pattern_key]["added"] += 1
                
                # Collect weights and levels
                if record.final_weight:
                    patterns_data[pattern_key]["weights"].append(record.final_weight)
                if record.final_level:
                    patterns_data[pattern_key]["levels"].append(record.final_level)
                if record.was_required:
                    patterns_data[pattern_key]["was_required_count"] += 1
            
            # Create or update patterns
            for pattern_key, data in patterns_data.items():
                # Calculate metrics
                acceptance_count = data["accepted"] + data["modified"]
                acceptance_rate = acceptance_count / data["total"] if data["total"] > 0 else 0
                
                # Calculate confidence
                confidence, confidence_score = self._calculate_confidence(
                    data["total"], acceptance_rate
                )
                
                # Determine suggested weight (median of final weights)
                suggested_weight = None
                if data["weights"]:
                    sorted_weights = sorted(data["weights"])
                    mid = len(sorted_weights) // 2
                    suggested_weight = (
                        sorted_weights[mid] if len(sorted_weights) % 2 == 1
                        else (sorted_weights[mid - 1] + sorted_weights[mid]) // 2
                    )
                
                # Determine suggested level (most common)
                suggested_level = None
                if data["levels"]:
                    level_counts: dict[str, int] = {}
                    for level in data["levels"]:
                        level_counts[level] = level_counts.get(level, 0) + 1
                    suggested_level = max(level_counts, key=level_counts.get)
                
                # Determine if typically required
                is_typically_required = (
                    data["was_required_count"] / data["total"] > 0.5
                    if data["total"] > 0 else False
                )
                
                # Check if pattern should be promoted (high confidence and high acceptance)
                is_promoted = (
                    confidence_score >= 0.75 and acceptance_rate >= 0.75
                )
                
                # Find or create pattern
                existing = await db.execute(
                    select(SkillSuggestionPattern)
                    .where(
                        and_(
                            SkillSuggestionPattern.company_id == company_id,
                            SkillSuggestionPattern.skill_name == data["skill_name"],
                            SkillSuggestionPattern.context_key == data["context_key"]
                        )
                    )
                )
                existing_pattern = existing.scalar_one_or_none()
                
                if existing_pattern:
                    # Update existing pattern
                    existing_pattern.sample_size = data["total"]
                    existing_pattern.acceptance_rate = acceptance_rate
                    existing_pattern.confidence_score = confidence_score
                    existing_pattern.suggested_weight = suggested_weight
                    existing_pattern.suggested_level = suggested_level
                    existing_pattern.is_typically_required = is_typically_required
                    existing_pattern.is_promoted = is_promoted
                    existing_pattern.last_computed_at = datetime.utcnow()
                    existing_pattern.context_data = {
                        "total_submissions": data["total"],
                        "accepted": data["accepted"],
                        "modified": data["modified"],
                        "rejected": data["rejected"],
                        "added": data["added"]
                    }
                else:
                    # Create new pattern
                    pattern = SkillSuggestionPattern(
                        company_id=company_id,
                        pattern_type="skill_suggestion",
                        context_key=data["context_key"],
                        skill_name=data["skill_name"],
                        skill_category=data["skill_category"],
                        suggested_weight=suggested_weight,
                        suggested_level=suggested_level,
                        is_typically_required=is_typically_required,
                        sample_size=data["total"],
                        acceptance_rate=acceptance_rate,
                        confidence_score=confidence_score,
                        context_data={
                            "total_submissions": data["total"],
                            "accepted": data["accepted"],
                            "modified": data["modified"],
                            "rejected": data["rejected"],
                            "added": data["added"],
                            "job_title": data["job_title"],
                            "department": data["department"],
                            "seniority": data["seniority"]
                        },
                        is_promoted=is_promoted
                    )
                    db.add(pattern)
            
            await db.commit()
            
            self.logger.info(
                f"Generated {len(patterns_data)} skill patterns for company {company_id}"
            )
            
        except Exception as e:
            self.logger.error(f"Error generating skill patterns: {e}")
            await db.rollback()
            raise


    async def record_interaction(
        self,
        domain_id: str,
        action_id: str,
        query: str,
        success: bool,
        confidence: float,
        response_metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a domain workflow interaction for learning purposes.

        Called automatically after each DomainWorkflow execution to capture
        interaction data without requiring a database session (lightweight logging).
        """
        try:
            self.logger.info(
                f"LearningLoop interaction: domain={domain_id} action={action_id} "
                f"success={success} confidence={confidence:.2f}"
            )
        except Exception as e:
            self.logger.warning(f"LearningLoop record_interaction logging failed: {e}")


learning_loop_service = LearningLoopService()
