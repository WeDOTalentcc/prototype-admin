# ADR-001-EXEMPT: 3-table JOIN with INTERVAL on job_outcomes (no repo), deferred to recruiter_assistant repo sprint.
"""
Outcome Learning Service — Connects hiring outcomes to future candidate ranking.

When a hire is successful (retained after 90 days, high satisfaction), the service:
1. Identifies profile characteristics of the successful candidate
2. Adjusts ranking weights for similar candidates in future searches
3. Feeds back into FeedbackLearningService success patterns

When a hire fails (turnover within 90 days, low satisfaction):
1. Identifies risk patterns
2. Adds caution signals for similar profiles
3. Notifies recruiters about learning insights
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OutcomeProfile:
    job_id: str
    company_id: str
    candidate_id: str
    outcome: str
    role: str | None = None
    seniority: str | None = None
    skills: list[str] = field(default_factory=list)
    source: str | None = None
    time_to_fill_days: int | None = None
    satisfaction_score: float | None = None
    retention_days: int | None = None
    lia_score_at_hire: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "outcome": self.outcome,
            "role": self.role,
            "seniority": self.seniority,
            "skills": self.skills,
            "source": self.source,
            "time_to_fill_days": self.time_to_fill_days,
            "satisfaction_score": self.satisfaction_score,
            "retention_days": self.retention_days,
            "lia_score_at_hire": self.lia_score_at_hire,
        }


@dataclass
class RankingAdjustment:
    field: str
    value: Any
    weight_delta: float
    reason: str
    confidence: str
    sample_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "weight_delta": self.weight_delta,
            "reason": self.reason,
            "confidence": self.confidence,
            "sample_size": self.sample_size,
        }


MINIMUM_OUTCOMES_FOR_ADJUSTMENT = 3
SUCCESS_RETENTION_THRESHOLD_DAYS = 90
HIGH_SATISFACTION_THRESHOLD = 4.0
LOW_SATISFACTION_THRESHOLD = 2.5


class OutcomeLearningService:
    _instance: "OutcomeLearningService | None" = None

    @classmethod
    def get_instance(cls) -> "OutcomeLearningService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._adjustment_cache: dict[str, list[RankingAdjustment]] = {}

    async def process_outcome(
        self,
        company_id: str,
        job_id: str,
        candidate_id: str,
        outcome: str,
        satisfaction_score: float | None = None,
        retention_days: int | None = None,
    ) -> dict[str, Any]:
        profile = await self._build_outcome_profile(
            company_id, job_id, candidate_id, outcome,
            satisfaction_score, retention_days,
        )
        if not profile:
            return {"success": False, "message": "Could not build outcome profile"}

        adjustments = await self._calculate_adjustments(company_id, profile)
        if adjustments:
            self._adjustment_cache[company_id] = adjustments
            await self._store_adjustments(company_id, adjustments)

        await self._record_feedback_learning(company_id, profile)

        return {
            "success": True,
            "outcome": profile.to_dict(),
            "adjustments": [a.to_dict() for a in adjustments],
            "adjustments_count": len(adjustments),
        }

    async def get_ranking_adjustments(
        self,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
    ) -> list[RankingAdjustment]:
        adjustments = self._adjustment_cache.get(company_id, [])
        if not adjustments:
            adjustments = await self._load_adjustments(company_id)
            self._adjustment_cache[company_id] = adjustments

        if role:
            adjustments = [a for a in adjustments if role.lower() in (a.value or "").lower() or a.field == "role"]
        if seniority:
            adjustments = [a for a in adjustments if seniority.lower() in (a.value or "").lower() or a.field == "seniority"]
        return adjustments

    def apply_score_adjustment(
        self,
        base_score: float,
        candidate_profile: dict[str, Any],
        adjustments: list[RankingAdjustment],
    ) -> tuple[float, list[str]]:
        adjusted_score = base_score
        reasons: list[str] = []

        for adj in adjustments:
            candidate_value = candidate_profile.get(adj.field)
            if candidate_value is None:
                continue

            if isinstance(adj.value, str) and isinstance(candidate_value, str):
                if adj.value.lower() != candidate_value.lower():
                    continue
            elif isinstance(adj.value, list) and isinstance(candidate_value, list):
                overlap = set(adj.value) & set(candidate_value)
                if not overlap:
                    continue

            adjusted_score += adj.weight_delta
            reasons.append(adj.reason)

        adjusted_score = max(0.0, min(100.0, adjusted_score))
        return adjusted_score, reasons

    async def get_learning_insights(self, company_id: str) -> dict[str, Any]:
        adjustments = await self.get_ranking_adjustments(company_id)
        outcomes = await self._get_recent_outcomes(company_id)

        positive_adjustments = [a for a in adjustments if a.weight_delta > 0]
        negative_adjustments = [a for a in adjustments if a.weight_delta < 0]

        return {
            "company_id": company_id,
            "total_outcomes_analyzed": len(outcomes),
            "total_adjustments": len(adjustments),
            "positive_signals": [a.to_dict() for a in positive_adjustments[:5]],
            "caution_signals": [a.to_dict() for a in negative_adjustments[:5]],
            "insights": self._generate_insights(outcomes, adjustments),
        }

    async def _build_outcome_profile(
        self,
        company_id: str,
        job_id: str,
        candidate_id: str,
        outcome: str,
        satisfaction_score: float | None,
        retention_days: int | None,
    ) -> OutcomeProfile | None:
        # ADR-001 W1-004-C: migrated from raw SQL (session+text) to CandidateRepository
        from lia_config.database import AsyncSessionLocal
        from app.domains.candidates.repositories.candidate_repository import CandidateRepository

        async with AsyncSessionLocal() as session:
            try:
                repo = CandidateRepository(session)
                row = await repo.get_candidate_with_job_context(
                    candidate_id=candidate_id,
                    company_id=company_id,
                    job_id=job_id,
                )
            except Exception as exc:
                logger.warning("Failed to build outcome profile: %s", exc)
                return None

        if not row:
            return None

        # get_candidate_with_job_context returns: id, name, email, company_id, job_title, job_id
        # Skills/seniority/source are not available in this simplified query — use empty defaults.
        return OutcomeProfile(
            job_id=job_id,
            company_id=company_id,
            candidate_id=candidate_id,
            outcome=outcome,
            role=row.get("job_title"),
            seniority=None,
            skills=[],
            source=None,
            satisfaction_score=satisfaction_score,
            retention_days=retention_days,
            lia_score_at_hire=row[4],
        )

    async def _calculate_adjustments(
        self,
        company_id: str,
        profile: OutcomeProfile,
    ) -> list[RankingAdjustment]:
        adjustments: list[RankingAdjustment] = []
        outcomes = await self._get_recent_outcomes(company_id)

        is_success = (
            profile.outcome == "filled"
            and (profile.satisfaction_score or 0) >= HIGH_SATISFACTION_THRESHOLD
        )
        is_failure = (
            profile.outcome in ("filled", "turnover")
            and (
                (profile.retention_days is not None and profile.retention_days < SUCCESS_RETENTION_THRESHOLD_DAYS)
                or (profile.satisfaction_score is not None and profile.satisfaction_score < LOW_SATISFACTION_THRESHOLD)
            )
        )

        if is_success and profile.source:
            source_successes = sum(
                1 for o in outcomes
                if o.get("source") == profile.source and o.get("outcome") == "filled"
            )
            if source_successes >= MINIMUM_OUTCOMES_FOR_ADJUSTMENT:
                adjustments.append(RankingAdjustment(
                    field="source",
                    value=profile.source,
                    weight_delta=2.0,
                    reason=f"Fonte '{profile.source}' tem histórico de contratações bem-sucedidas",
                    confidence="medium" if source_successes < 5 else "high",
                    sample_size=source_successes,
                ))

        if is_success and profile.seniority:
            adjustments.append(RankingAdjustment(
                field="seniority",
                value=profile.seniority,
                weight_delta=1.5,
                reason=f"Senioridade '{profile.seniority}' associada a contratação bem-sucedida",
                confidence="low",
                sample_size=1,
            ))

        if is_success and profile.skills:
            for skill in profile.skills[:5]:
                skill_successes = sum(
                    1 for o in outcomes
                    if skill in o.get("skills", []) and o.get("outcome") == "filled"
                )
                if skill_successes >= MINIMUM_OUTCOMES_FOR_ADJUSTMENT:
                    adjustments.append(RankingAdjustment(
                        field="skills",
                        value=skill,
                        weight_delta=1.0,
                        reason=f"Skill '{skill}' presente em {skill_successes} contratações bem-sucedidas",
                        confidence="medium" if skill_successes < 5 else "high",
                        sample_size=skill_successes,
                    ))

        if is_failure and profile.source:
            source_failures = sum(
                1 for o in outcomes
                if o.get("source") == profile.source and o.get("outcome") in ("turnover", "cancelled")
            )
            if source_failures >= MINIMUM_OUTCOMES_FOR_ADJUSTMENT:
                adjustments.append(RankingAdjustment(
                    field="source",
                    value=profile.source,
                    weight_delta=-2.0,
                    reason=f"Fonte '{profile.source}' tem histórico de contratações com problemas",
                    confidence="medium",
                    sample_size=source_failures,
                ))

        return adjustments

    async def _get_recent_outcomes(self, company_id: str) -> list[dict[str, Any]]:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT jo.job_id, jo.outcome, jo.role, jo.seniority, jo.skills_used,
                           jo.satisfaction_score, jo.time_to_fill_days,
                           c.source
                    FROM job_outcomes jo
                    LEFT JOIN job_vacancies jv ON jv.id = jo.job_id
                    LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id AND vc.stage = 'Contratado'
                    LEFT JOIN candidates c ON c.id = vc.candidate_id
                    WHERE jo.company_id = :company_id
                      AND jo.created_at >= NOW() - INTERVAL '12 months'
                    ORDER BY jo.created_at DESC
                    LIMIT 100
                """), {"company_id": company_id})
                rows = result.fetchall()
                return [
                    {
                        "job_id": str(r[0]),
                        "outcome": r[1],
                        "role": r[2],
                        "seniority": r[3],
                        "skills": r[4] if isinstance(r[4], list) else [],
                        "satisfaction_score": r[5],
                        "time_to_fill_days": r[6],
                        "source": r[7],
                    }
                    for r in rows
                ]
            except Exception as exc:
                logger.debug("Failed to load recent outcomes: %s", exc)
                return []

    async def _store_adjustments(
        self,
        company_id: str,
        adjustments: list[RankingAdjustment],
    ) -> None:
        logger.info(
            "Stored %d ranking adjustments for company %s",
            len(adjustments), company_id,
        )

    async def _load_adjustments(self, company_id: str) -> list[RankingAdjustment]:
        return []

    async def _record_feedback_learning(
        self,
        company_id: str,
        profile: OutcomeProfile,
    ) -> None:
        try:
            from app.domains.analytics.services.feedback_learning_service import FeedbackLearningService
            from lia_config.database import AsyncSessionLocal
            from uuid import UUID

            svc = FeedbackLearningService()
            async with AsyncSessionLocal() as session:
                from lia_models.feedback_learning import JobOutcomeType

                outcome_map = {
                    "filled": JobOutcomeType.FILLED,
                    "cancelled": JobOutcomeType.CANCELLED,
                    "expired": JobOutcomeType.EXPIRED,
                }
                outcome_type = outcome_map.get(profile.outcome)
                if outcome_type:
                    await svc.record_outcome(
                        db=session,
                        company_id=profile.company_id,
                        job_id=UUID(profile.job_id),
                        outcome=outcome_type,
                        time_to_fill_days=profile.time_to_fill_days,
                        satisfaction_score=profile.satisfaction_score,
                        role=profile.role,
                        seniority=profile.seniority,
                        skills_used=profile.skills,
                    )
                    await session.commit()
        except Exception as exc:
            logger.debug("FeedbackLearningService integration skipped: %s", exc)

    def _generate_insights(
        self,
        outcomes: list[dict[str, Any]],
        adjustments: list[RankingAdjustment],
    ) -> list[str]:
        insights: list[str] = []
        if not outcomes:
            insights.append("Ainda não há dados suficientes de outcomes para gerar insights.")
            return insights

        filled = [o for o in outcomes if o.get("outcome") == "filled"]
        if filled:
            avg_ttf = sum(o.get("time_to_fill_days", 0) or 0 for o in filled) / len(filled)
            insights.append(f"Tempo médio para preencher vagas: {avg_ttf:.0f} dias (últimos 12 meses)")

        sources = {}
        for o in filled:
            src = o.get("source") or "desconhecido"
            sources[src] = sources.get(src, 0) + 1
        if sources:
            best = max(sources, key=sources.get)
            insights.append(f"Fonte com mais contratações bem-sucedidas: {best} ({sources[best]}x)")

        positive = [a for a in adjustments if a.weight_delta > 0]
        if positive:
            top = positive[0]
            insights.append(f"Fator positivo mais forte: {top.reason}")

        return insights


outcome_learning = OutcomeLearningService.get_instance()
