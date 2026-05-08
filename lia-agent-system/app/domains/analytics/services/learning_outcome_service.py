"""
LearningOutcomeService — Job outcome recording and pattern updates.

Extracted from LearningHubService (Sprint 5).
Handles: record_job_outcome, get_outcome_insights,
         _update_outcome_patterns_no_commit, _update_pattern_no_commit,
         _update_outcome_patterns.

ADR-001 refactor: SQL/select() moved to CompanyLearningRepository.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company_learning import CompanyPattern, LearningSource
from lia_models.feedback_learning import JobOutcome
from app.shared.services.learning_confirmation_service import (
    _calculate_confidence,
    learning_confirmation_service,
)
from app.domains.analytics.repositories.company_learning_repository import (
    CompanyLearningRepository,
)

logger = logging.getLogger(__name__)


class LearningOutcomeService:
    """Handles job outcome recording and pattern learning from outcomes."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._confirmation = learning_confirmation_service

    async def record_job_outcome(
        self,
        db: AsyncSession,
        company_id: str,
        job_id: UUID,
        outcome: str,
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
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Record a job outcome and trigger learning pattern updates."""
        try:
            from lia_models.feedback_learning import JobOutcomeType

            outcome_enum = JobOutcomeType(outcome)
            repo = CompanyLearningRepository(db)
            existing = await repo.get_outcome_by_job(job_id)

            common_fields = dict(
                outcome=outcome_enum,
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
            )

            if existing:
                for k, v in common_fields.items():
                    setattr(existing, k, v)
                job_outcome = existing
            else:
                job_outcome = JobOutcome(
                    company_id=company_id,
                    job_id=job_id,
                    created_by=created_by,
                    **common_fields,
                )
                db.add(job_outcome)

            await db.flush()

            patterns_updated = await self._update_outcome_patterns_no_commit(
                db,
                company_id,
                outcome_enum,
                role,
                seniority,
                time_to_fill_days,
                salary_final,
                skills_used or [],
            )

            await db.commit()
            return {
                "success": True,
                "outcome_id": str(job_outcome.id),
                "outcome": outcome,
                "patterns_updated": patterns_updated,
                "message": f"Outcome recorded: {outcome}",
            }

        except ValueError as exc:
            self.logger.error(f"Invalid outcome value: {exc}")
            await db.rollback()
            raise ValueError(f"Invalid outcome value: {exc}")
        except Exception as exc:
            self.logger.error(f"Error recording job outcome: {exc}")
            await db.rollback()
            raise RuntimeError(f"Failed to record outcome: {exc}")

    async def _update_outcome_patterns_no_commit(
        self,
        db: AsyncSession,
        company_id: str,
        outcome: Any,
        role: str | None,
        seniority: str | None,
        time_to_fill: int | None,
        salary_final: float | None,
        skills_used: list[str],
    ) -> dict[str, Any]:
        """Update patterns from outcome — does not commit."""
        patterns_updated: dict[str, Any] = {}
        repo = CompanyLearningRepository(db)

        if outcome.value == "filled":
            if role and time_to_fill:
                await self._update_pattern_no_commit(
                    db,
                    company_id,
                    "time_to_fill",
                    role.lower(),
                    {"avg_days": time_to_fill, "last_value": time_to_fill},
                    sample_size=1,
                )
                patterns_updated["time_to_fill"] = True

            if role and salary_final:
                await self._update_pattern_no_commit(
                    db,
                    company_id,
                    "salary_accepted",
                    role.lower(),
                    {"value": salary_final, "seniority": seniority},
                    sample_size=1,
                )
                patterns_updated["salary"] = True

            for skill in skills_used[:10]:
                skill_record = await repo.find_skill_by_exact_name_lower(
                    company_id, skill.lower()
                )
                if skill_record:
                    skill_record.times_confirmed += 1
                    skill_record.source = LearningSource.OUTCOME_SUCCESS
                    patterns_updated[f"skill_{skill}"] = True

        return patterns_updated

    async def _update_pattern_no_commit(
        self,
        db: AsyncSession,
        company_id: str,
        pattern_type: str,
        pattern_key: str,
        pattern_value: Any,
        sample_size: int = 1,
    ) -> bool:
        repo = CompanyLearningRepository(db)
        existing = await repo.find_pattern(company_id, pattern_type, pattern_key)

        if existing:
            existing.pattern_value = pattern_value
            existing.sample_size = sample_size
            existing.confidence = _calculate_confidence(sample_size)
            existing.last_calculated_at = datetime.utcnow()
        else:
            db.add(
                CompanyPattern(
                    company_id=company_id,
                    pattern_type=pattern_type,
                    pattern_key=pattern_key,
                    pattern_value=pattern_value,
                    sample_size=sample_size,
                    confidence=_calculate_confidence(sample_size),
                )
            )
        return True

    async def get_outcome_insights(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
    ) -> dict[str, Any]:
        try:
            from lia_models.feedback_learning import JobOutcomeType

            repo = CompanyLearningRepository(db)
            outcomes = await repo.list_outcomes_filtered(
                company_id=company_id, role=role, seniority=seniority
            )

            if not outcomes:
                return {"has_data": False, "message": "No historical data"}

            filled = [o for o in outcomes if o.outcome == JobOutcomeType.FILLED]

            avg_time_to_fill = None
            if filled:
                times = [o.time_to_fill_days for o in filled if o.time_to_fill_days]
                avg_time_to_fill = sum(times) / len(times) if times else None

            salary_range = None
            if filled:
                salaries = [o.salary_final for o in filled if o.salary_final]
                if salaries:
                    salary_range = {
                        "min": min(salaries),
                        "max": max(salaries),
                        "avg": sum(salaries) / len(salaries),
                    }

            skill_frequency: dict[str, int] = {}
            for o in filled:
                for skill in o.skills_used or []:
                    skill_frequency[skill] = skill_frequency.get(skill, 0) + 1

            top_skills = sorted(
                skill_frequency.items(), key=lambda x: x[1], reverse=True
            )[:10]

            return {
                "has_data": True,
                "total_jobs": len(outcomes),
                "filled_jobs": len(filled),
                "fill_rate": len(filled) / len(outcomes) if outcomes else 0,
                "avg_time_to_fill_days": avg_time_to_fill,
                "salary_range": salary_range,
                "top_skills": [{"skill": s, "count": c} for s, c in top_skills],
                "filters_applied": {"role": role, "seniority": seniority},
            }

        except Exception as exc:
            self.logger.error(f"Error getting outcome insights: {exc}")
            return {"has_data": False, "error": str(exc)}


learning_outcome_service = LearningOutcomeService()
