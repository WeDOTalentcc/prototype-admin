"""Score Normalization service — cross-version difficulty adjustment.

Sprint 6 ADR-001 cleanup: SQL extracted to ScreeningQuestionSetRepository
(2 queries on screening_question_sets) + WsiRepository (1 query on
wsi_sessions). Service is now pure normalization logic.
"""
import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.cv_screening.repositories.screening_question_set_repository import (
    ScreeningQuestionSetRepository,
)
from app.domains.voice.repositories.wsi_repository import WsiRepository

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
        self, db: AsyncSession, job_vacancy_id: str,
    ) -> dict[int | None, float | None]:
        try:
            return await ScreeningQuestionSetRepository(db).get_version_coefficients(
                job_vacancy_id,
            )
        except Exception as e:
            self.logger.warning(f"Failed to load version coefficients: {e}")
            return {}

    async def get_comparison_context(
        self,
        db: AsyncSession,
        job_vacancy_id: str,
    ) -> dict[str, Any]:
        try:
            qs_repo = ScreeningQuestionSetRepository(db)
            wsi_repo = WsiRepository(db)

            versions = await qs_repo.get_versions_with_metadata(job_vacancy_id)
            session_counts = await wsi_repo.get_completed_sessions_count_by_version(
                job_vacancy_id,
            )

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
