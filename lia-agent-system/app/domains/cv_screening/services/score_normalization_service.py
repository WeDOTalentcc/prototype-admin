# ADR-001-EXEMPT (Sprint 6 follow-up): 3 SELECTs on screening_question_sets
# for cross-version score normalization. Belongs in a new
# ScreeningQuestionSetRepository (does not exist yet — covers ~15 queries
# across this file + screening_question_set_service.py). Tracked separately.
import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class NormalizedCandidateScore:
    candidate_id: str
    raw_score: float
    normalized_score: float
    question_set_version: int | None
    difficulty_coefficient: float | None
    normalization_factor: float
    scoring_details: dict[str, Any]


class ScoreNormalizationService:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.baseline_difficulty = 0.5

    async def normalize_candidate_scores(
        self,
        db: AsyncSession,
        job_vacancy_id: str,
        candidate_scores: list[dict[str, Any]],
    ) -> list[NormalizedCandidateScore]:
        version_coefficients = await self._load_version_coefficients(db, job_vacancy_id)

        if not version_coefficients:
            return [
                NormalizedCandidateScore(
                    candidate_id=cs.get("candidate_id", ""),
                    raw_score=cs.get("score", 0.0),
                    normalized_score=cs.get("score", 0.0),
                    question_set_version=cs.get("question_set_version"),
                    difficulty_coefficient=None,
                    normalization_factor=1.0,
                    scoring_details={"method": "passthrough", "reason": "no_version_data"},
                )
                for cs in candidate_scores
            ]

        all_coefficients = [c for c in version_coefficients.values() if c is not None]
        if all_coefficients:
            self.baseline_difficulty = sum(all_coefficients) / len(all_coefficients)

        results = []
        for cs in candidate_scores:
            version = cs.get("question_set_version")
            raw_score = cs.get("score", 0.0)
            difficulty = version_coefficients.get(version)

            if difficulty is not None and difficulty != self.baseline_difficulty:
                normalization_factor = self._calculate_normalization_factor(difficulty)
                normalized = raw_score * normalization_factor
                normalized = round(max(0.0, min(5.0, normalized)), 2)
                method = "difficulty_adjusted"
            else:
                normalization_factor = 1.0
                normalized = raw_score
                method = "same_difficulty"

            results.append(NormalizedCandidateScore(
                candidate_id=cs.get("candidate_id", ""),
                raw_score=raw_score,
                normalized_score=normalized,
                question_set_version=version,
                difficulty_coefficient=difficulty,
                normalization_factor=normalization_factor,
                scoring_details={
                    "method": method,
                    "baseline_difficulty": self.baseline_difficulty,
                    "version_difficulty": difficulty,
                    "adjustment": round(normalization_factor - 1.0, 4) if normalization_factor != 1.0 else 0,
                },
            ))

        return sorted(results, key=lambda x: x.normalized_score, reverse=True)

    def _calculate_normalization_factor(self, difficulty: float) -> float:
        if difficulty <= 0 or self.baseline_difficulty <= 0:
            return 1.0

        ratio = difficulty / self.baseline_difficulty

        if ratio > 1.0:
            factor = 1.0 + (ratio - 1.0) * 0.3
        elif ratio < 1.0:
            factor = 1.0 - (1.0 - ratio) * 0.3
        else:
            factor = 1.0

        return round(max(0.7, min(1.3, factor)), 4)

    async def _load_version_coefficients(
        self, db: AsyncSession, job_vacancy_id: str
    ) -> dict[int | None, float | None]:
        try:
            result = await db.execute(text("""
                SELECT version, difficulty_coefficient
                FROM screening_question_sets
                WHERE job_vacancy_id = :job_vacancy_id
                ORDER BY version
            """), {"job_vacancy_id": job_vacancy_id})
            rows = result.fetchall()
            return {row[0]: row[1] for row in rows}
        except Exception as e:
            self.logger.warning(f"Failed to load version coefficients: {e}")
            return {}

    async def get_comparison_context(
        self,
        db: AsyncSession,
        job_vacancy_id: str,
    ) -> dict[str, Any]:
        try:
            versions_result = await db.execute(text("""
                SELECT version, difficulty_coefficient, questions_count, source, is_active
                FROM screening_question_sets
                WHERE job_vacancy_id = :job_vacancy_id
                ORDER BY version DESC
            """), {"job_vacancy_id": job_vacancy_id})
            versions = versions_result.fetchall()

            sessions_result = await db.execute(text("""
                SELECT question_set_version, COUNT(*) as count
                FROM wsi_sessions
                WHERE job_vacancy_id = :job_vacancy_id AND status = 'completed'
                GROUP BY question_set_version
            """), {"job_vacancy_id": job_vacancy_id})
            session_counts = {row[0]: row[1] for row in sessions_result.fetchall()}

            version_details = []
            for v in versions:
                version_details.append({
                    "version": v[0],
                    "difficulty_coefficient": v[1],
                    "questions_count": v[2],
                    "source": v[3],
                    "is_active": v[4],
                    "sessions_count": session_counts.get(v[0], 0),
                })

            coefficients = [v[1] for v in versions if v[1] is not None]
            needs_normalization = False
            if len(coefficients) >= 2:
                max_diff = max(coefficients) - min(coefficients)
                needs_normalization = max_diff > 0.05

            return {
                "total_versions": len(versions),
                "version_details": version_details,
                "needs_normalization": needs_normalization,
                "active_version": next((v[0] for v in versions if v[4]), None),
                "total_sessions": sum(session_counts.values()),
                "sessions_by_version": session_counts,
            }
        except Exception as e:
            self.logger.error(f"Failed to get comparison context: {e}")
            return {
                "total_versions": 0,
                "version_details": [],
                "needs_normalization": False,
                "active_version": None,
                "total_sessions": 0,
                "sessions_by_version": {},
            }


score_normalization_service = ScoreNormalizationService()
