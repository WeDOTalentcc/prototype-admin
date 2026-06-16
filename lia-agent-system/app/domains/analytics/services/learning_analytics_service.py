"""
LearningAnalyticsService — Stage analytics, dashboard, and learning health.

Extracted from LearningHubService (Sprint 5).
Handles: record_stage_feedback, get_stage_analytics,
         get_learning_dashboard, _calculate_learning_health,
         _get_health_recommendations, should_skip_stage_with_learning.
"""
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company_learning import (
    CompanyPattern,
    CompanyResponsibility,
    CompanySkill,
)
from lia_models.feedback_learning import JobOutcome

logger = logging.getLogger(__name__)


class LearningAnalyticsService:
    """Handles wizard stage analytics, dashboard metrics, and skip-stage logic."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    async def record_stage_feedback(
        self,
        db: AsyncSession,
        company_id: str,
        stage_number: int,
        field_name: str,
        suggested_value: Any,
        accepted_value: Any,
        was_accepted: bool = True,
        was_modified: bool = False,
        job_id: UUID | None = None,
        stage_name: str | None = None,
        role: str | None = None,
        seniority: str | None = None,
        confidence_before: float | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        try:
            from lia_models.company_learning import StageFeedback
            from app.shared.services.learning_confirmation_service import (
                learning_confirmation_service,
            )

            feedback = StageFeedback(
                company_id=company_id,
                job_id=job_id,
                stage_number=stage_number,
                stage_name=stage_name,
                field_name=field_name,
                suggested_value=suggested_value,
                accepted_value=accepted_value,
                was_accepted=was_accepted,
                was_modified=was_modified,
                role=role,
                seniority=seniority,
                confidence_before=confidence_before,
                created_by=created_by,
            )
            db.add(feedback)
            await db.commit()

            if was_modified and suggested_value != accepted_value:
                pattern_key = (
                    f"{field_name}_{role or 'any'}_{seniority or 'any'}".lower()
                )
                await learning_confirmation_service.update_pattern(
                    db,
                    company_id,
                    "field_preference",
                    pattern_key,
                    {"value": accepted_value, "role": role, "seniority": seniority},
                    sample_size=1,
                )

            return {
                "success": True,
                "feedback_id": str(feedback.id),
                "stage": stage_number,
                "was_accepted": was_accepted,
                "was_modified": was_modified,
            }
        except Exception as exc:
            self.logger.error(f"Error recording stage feedback: {exc}")
            await db.rollback()
            return {"success": False, "error": str(exc)}

            # ADR-001-EXEMPT: single-table StageFeedback aggregation for analytics dashboard; promote to CompanyLearningRepository in Sprint 6 cleanup
    async def get_stage_analytics(
        self,
        db: AsyncSession,
        company_id: str,
        stage_number: int | None = None,
    ) -> dict[str, Any]:
        try:
            from lia_models.company_learning import StageFeedback

            base_query = select(StageFeedback).where(
                StageFeedback.company_id == company_id
            )
            if stage_number:
                base_query = base_query.where(
                    StageFeedback.stage_number == stage_number
                )
            result = await db.execute(base_query)
            feedbacks = result.scalars().all()

            if not feedbacks:
                return {"has_data": False, "message": "No feedback data"}

            total = len(feedbacks)
            accepted = sum(1 for f in feedbacks if f.was_accepted)
            modified = sum(1 for f in feedbacks if f.was_modified)

            by_stage: dict[int, dict[str, Any]] = {}
            for f in feedbacks:
                s = f.stage_number
                if s not in by_stage:
                    by_stage[s] = {"total": 0, "accepted": 0, "modified": 0}
                by_stage[s]["total"] += 1
                if f.was_accepted:
                    by_stage[s]["accepted"] += 1
                if f.was_modified:
                    by_stage[s]["modified"] += 1

            for s in by_stage:
                t = by_stage[s]["total"]
                by_stage[s]["acceptance_rate"] = by_stage[s]["accepted"] / t
                by_stage[s]["modification_rate"] = by_stage[s]["modified"] / t

            by_field: dict[str, dict[str, int]] = {}
            for f in feedbacks:
                field = f.field_name
                if field not in by_field:
                    by_field[field] = {"total": 0, "modified": 0}
                by_field[field]["total"] += 1
                if f.was_modified:
                    by_field[field]["modified"] += 1

            most_modified = sorted(
                [(k, v["modified"] / v["total"]) for k, v in by_field.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:5]

            return {
                "has_data": True,
                "total_feedback": total,
                "overall_acceptance_rate": accepted / total,
                "overall_modification_rate": modified / total,
                "by_stage": by_stage,
                "most_modified_fields": [
                    {"field": f, "modification_rate": r} for f, r in most_modified
                ],
            }
        except Exception as exc:
            self.logger.error(f"Error getting stage analytics: {exc}")
            return {"has_data": False, "error": str(exc)}

    async def get_learning_dashboard(
        self, db: AsyncSession, company_id: str
    ) -> dict[str, Any]:
        try:
            total_skills = (
                await db.execute(
                    select(func.count(CompanySkill.id)).where(
                        CompanySkill.company_id == company_id
                    )
                )
            ).scalar() or 0

            promoted_skills = (
                await db.execute(
                    select(func.count(CompanySkill.id)).where(
                        and_(
                            CompanySkill.company_id == company_id,
                            CompanySkill.is_promoted,
                        )
                    )
                )
            ).scalar() or 0

            total_responsibilities = (
                await db.execute(
                    select(func.count(CompanyResponsibility.id)).where(
                        CompanyResponsibility.company_id == company_id
                    )
                )
            ).scalar() or 0

            total_outcomes = (
                await db.execute(
                    select(func.count(JobOutcome.id)).where(
                        JobOutcome.company_id == company_id
                    )
                )
            ).scalar() or 0

            total_patterns = (
                await db.execute(
                    select(func.count(CompanyPattern.id)).where(
                        CompanyPattern.company_id == company_id
                    )
                )
            ).scalar() or 0

            from app.shared.services.learning_confirmation_service import (
                learning_confirmation_service,
            )
            from app.shared.services.learning_outcome_service import learning_outcome_service

            stage_analytics = await self.get_stage_analytics(db, company_id)
            outcome_insights = await learning_outcome_service.get_outcome_insights(
                db, company_id
            )
            success_rates = await learning_confirmation_service._get_success_rates(
                db, company_id
            )

            return {
                "summary": {
                    "total_skills_learned": total_skills,
                    "promoted_skills": promoted_skills,
                    "total_responsibilities": total_responsibilities,
                    "total_outcomes_recorded": total_outcomes,
                    "total_patterns_detected": total_patterns,
                },
                "stage_analytics": stage_analytics,
                "outcome_insights": outcome_insights,
                "success_rates": success_rates,
                "learning_health": self._calculate_learning_health(
                    total_skills, promoted_skills, total_outcomes, total_patterns
                ),
            }
        except Exception as exc:
            self.logger.error(f"Error getting learning dashboard: {exc}")
            return {"error": str(exc)}

    def _calculate_learning_health(
        self,
        total_skills: int,
        promoted_skills: int,
        total_outcomes: int,
        total_patterns: int,
    ) -> dict[str, Any]:
        scores = []
        if total_skills > 0:
            scores.append(min(100, (total_skills / 50) * 100))
            scores.append(
                min(100, (promoted_skills / total_skills) * 100 * 2)
            )
        scores.append(min(100, (total_outcomes / 20) * 100))
        scores.append(min(100, (total_patterns / 30) * 100))

        overall = sum(scores) / len(scores) if scores else 0
        if overall >= 70:
            status = "healthy"
        elif overall >= 40:
            status = "developing"
        else:
            status = "nascent"

        return {
            "score": round(overall, 1),
            "status": status,
            "recommendations": self._get_health_recommendations(
                total_skills, promoted_skills, total_outcomes, total_patterns
            ),
        }

    def _get_health_recommendations(
        self,
        total_skills: int,
        promoted_skills: int,
        total_outcomes: int,
        total_patterns: int,
    ) -> list[str]:
        recs = []
        if total_skills < 20:
            recs.append(
                "Confirme mais skills durante a criação de vagas para enriquecer o catálogo"
            )
        if promoted_skills < 3:
            recs.append(
                "Continue usando skills frequentes para que sejam promovidas automaticamente"
            )
        if total_outcomes < 5:
            recs.append("Registre outcomes de vagas fechadas para melhorar previsões")
        if total_patterns < 10:
            recs.append(
                "O sistema está aprendendo - continue usando para detectar mais padrões"
            )
        if not recs:
            recs.append(
                "Sistema de aprendizado saudável! Continue registrando feedback."
            )
        return recs

    async def should_skip_stage_with_learning(
        self,
        db: AsyncSession,
        company_id: str,
        stage_number: int,
        detected_criteria: dict[str, Any],
        role: str | None = None,
        seniority: str | None = None,
    ) -> tuple[bool, str, dict[str, Any]]:
        """Determine if a wizard stage can be auto-skipped using company learning data."""
        from app.domains.job_management.services.job_stage_config import get_stage_config, should_skip_stage
        from app.shared.services.learning_confirmation_service import (
            learning_confirmation_service,
        )

        stage_config = get_stage_config(stage_number)
        if not stage_config:
            return False, "Stage config not found", {}

        can_skip, base_reason = should_skip_stage(stage_number, detected_criteria)
        if not can_skip:
            return False, base_reason, {}

        auto_filled: dict[str, Any] = {}

        if stage_number == 2:
            learning_context = await learning_confirmation_service.get_learning_context(
                db, company_id, role=role, seniority=seniority
            )
            patterns = learning_context.patterns

            if seniority:
                if patterns.get(f"seniority_{role}", {}).get("confidence", 0) > 0.8:
                    auto_filled["seniority_from_learning"] = True

            if not role and patterns.get("department_default", {}).get("value"):
                auto_filled["department"] = patterns["department_default"]["value"]
                auto_filled["department_from_learning"] = True

        elif stage_number == 3:
            if stage_config.get("use_skills_deduplication", False):
                already_selected: list[str] = []
                for key in ("competencias_tecnicas", "skills"):
                    if detected_criteria.get(key, {}).get("value"):
                        already_selected = detected_criteria[key]["value"]
                        break

                deduplicated = await learning_confirmation_service.get_skills_without_duplicates(
                    db, company_id, role=role, exclude_already_selected=already_selected
                )
                promoted = [s for s in deduplicated if s.get("is_promoted")]
                if len(promoted) >= 3:
                    auto_filled["suggested_skills"] = promoted[:10]
                    auto_filled["skills_from_learning"] = True
                    return True, "Skills sugeridas com base no histórico da empresa", auto_filled

        if auto_filled:
            return True, f"Etapa {stage_number} preenchida com base no aprendizado", auto_filled

        return can_skip, base_reason, auto_filled


learning_analytics_service = LearningAnalyticsService()
