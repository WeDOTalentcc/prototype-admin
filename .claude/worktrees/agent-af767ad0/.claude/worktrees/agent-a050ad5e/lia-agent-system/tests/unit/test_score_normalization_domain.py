"""
Unit tests for app.domains.cv_screening.services.score_normalization_service
Covers ScoreNormalizationService and NormalizedCandidateScore dataclass.
"""
import pytest

pytestmark = pytest.mark.medium

from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional

from app.domains.cv_screening.services.score_normalization_service import (
    ScoreNormalizationService,
    NormalizedCandidateScore,
    score_normalization_service,
)


class TestNormalizedCandidateScore:
    """Tests for NormalizedCandidateScore dataclass."""

    def test_instantiation_full(self):
        obj = NormalizedCandidateScore(
            candidate_id="cand-1",
            raw_score=3.5,
            normalized_score=3.8,
            question_set_version=2,
            difficulty_coefficient=0.7,
            normalization_factor=1.08,
            scoring_details={"method": "difficulty_adjusted"},
        )
        assert obj.candidate_id == "cand-1"
        assert obj.raw_score == 3.5
        assert obj.normalized_score == 3.8
        assert obj.question_set_version == 2
        assert obj.difficulty_coefficient == 0.7
        assert obj.normalization_factor == 1.08
        assert obj.scoring_details["method"] == "difficulty_adjusted"

    def test_instantiation_optional_none(self):
        obj = NormalizedCandidateScore(
            candidate_id="cand-2",
            raw_score=2.0,
            normalized_score=2.0,
            question_set_version=None,
            difficulty_coefficient=None,
            normalization_factor=1.0,
            scoring_details={"method": "passthrough"},
        )
        assert obj.question_set_version is None
        assert obj.difficulty_coefficient is None


class TestScoreNormalizationServiceInit:
    """Tests for service initialization."""

    def test_default_baseline_difficulty(self):
        svc = ScoreNormalizationService()
        assert svc.baseline_difficulty == 0.5

    def test_singleton_instance(self):
        assert isinstance(score_normalization_service, ScoreNormalizationService)


class TestCalculateNormalizationFactor:
    """Tests for _calculate_normalization_factor (pure method)."""

    def setup_method(self):
        self.svc = ScoreNormalizationService()
        self.svc.baseline_difficulty = 0.5

    def test_same_difficulty_returns_one(self):
        self.svc.baseline_difficulty = 0.5
        factor = self.svc._calculate_normalization_factor(0.5)
        assert factor == 1.0

    def test_higher_difficulty_boosts_score(self):
        self.svc.baseline_difficulty = 0.5
        factor = self.svc._calculate_normalization_factor(0.8)
        assert factor > 1.0

    def test_lower_difficulty_reduces_score(self):
        self.svc.baseline_difficulty = 0.5
        factor = self.svc._calculate_normalization_factor(0.2)
        assert factor < 1.0

    def test_zero_difficulty_returns_one(self):
        factor = self.svc._calculate_normalization_factor(0.0)
        assert factor == 1.0

    def test_zero_baseline_returns_one(self):
        self.svc.baseline_difficulty = 0.0
        factor = self.svc._calculate_normalization_factor(0.5)
        assert factor == 1.0

    def test_max_cap_at_1_3(self):
        self.svc.baseline_difficulty = 0.1
        factor = self.svc._calculate_normalization_factor(5.0)
        assert factor <= 1.3

    def test_min_cap_at_0_7(self):
        self.svc.baseline_difficulty = 5.0
        factor = self.svc._calculate_normalization_factor(0.1)
        assert factor >= 0.7

    def test_exact_formula_up(self):
        self.svc.baseline_difficulty = 0.5
        difficulty = 1.0
        ratio = difficulty / 0.5  # 2.0
        expected = round(min(1.3, max(0.7, 1.0 + (ratio - 1.0) * 0.3)), 4)
        factor = self.svc._calculate_normalization_factor(difficulty)
        assert factor == expected

    def test_exact_formula_down(self):
        self.svc.baseline_difficulty = 1.0
        difficulty = 0.5
        ratio = difficulty / 1.0  # 0.5
        expected = round(min(1.3, max(0.7, 1.0 - (1.0 - ratio) * 0.3)), 4)
        factor = self.svc._calculate_normalization_factor(difficulty)
        assert factor == expected


class TestNormalizeCandidateScores:
    """Tests for normalize_candidate_scores async method."""

    def setup_method(self):
        self.svc = ScoreNormalizationService()

    @pytest.mark.asyncio
    async def test_passthrough_when_no_version_data(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.fetchall.return_value = []
        db.execute = AsyncMock(return_value=result_mock)

        candidates = [
            {"candidate_id": "c1", "score": 3.0},
            {"candidate_id": "c2", "score": 4.5},
        ]
        results = await self.svc.normalize_candidate_scores(db, "job-1", candidates)

        assert len(results) == 2
        for r in results:
            assert r.normalization_factor == 1.0
            assert r.scoring_details["method"] == "passthrough"

    @pytest.mark.asyncio
    async def test_passthrough_preserves_raw_scores(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.fetchall.return_value = []
        db.execute = AsyncMock(return_value=result_mock)

        candidates = [{"candidate_id": "c1", "score": 2.75}]
        results = await self.svc.normalize_candidate_scores(db, "job-1", candidates)

        assert results[0].normalized_score == 2.75
        assert results[0].raw_score == 2.75

    @pytest.mark.asyncio
    async def test_with_version_coefficients_single(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.fetchall.return_value = [(1, 0.5), (2, 0.8)]
        db.execute = AsyncMock(return_value=result_mock)

        candidates = [
            {"candidate_id": "c1", "score": 3.0, "question_set_version": 2},
        ]
        results = await self.svc.normalize_candidate_scores(db, "job-1", candidates)

        assert len(results) == 1
        # score should be clipped to [0.0, 5.0]
        assert 0.0 <= results[0].normalized_score <= 5.0

    @pytest.mark.asyncio
    async def test_results_sorted_descending(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.fetchall.return_value = [(1, 0.5)]
        db.execute = AsyncMock(return_value=result_mock)

        candidates = [
            {"candidate_id": "c3", "score": 1.0, "question_set_version": 1},
            {"candidate_id": "c1", "score": 4.0, "question_set_version": 1},
            {"candidate_id": "c2", "score": 2.5, "question_set_version": 1},
        ]
        results = await self.svc.normalize_candidate_scores(db, "job-1", candidates)

        scores = [r.normalized_score for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_same_difficulty_uses_passthrough_method(self):
        db = AsyncMock()
        result_mock = MagicMock()
        # Single version → baseline == difficulty → same difficulty path
        result_mock.fetchall.return_value = [(1, 0.5)]
        db.execute = AsyncMock(return_value=result_mock)

        candidates = [{"candidate_id": "c1", "score": 3.0, "question_set_version": 1}]
        results = await self.svc.normalize_candidate_scores(db, "job-1", candidates)

        assert results[0].scoring_details["method"] == "same_difficulty"

    @pytest.mark.asyncio
    async def test_none_difficulty_version_uses_passthrough(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.fetchall.return_value = [(1, None)]
        db.execute = AsyncMock(return_value=result_mock)

        candidates = [{"candidate_id": "c1", "score": 3.0, "question_set_version": 1}]
        results = await self.svc.normalize_candidate_scores(db, "job-1", candidates)

        assert results[0].normalization_factor == 1.0

    @pytest.mark.asyncio
    async def test_exception_in_db_returns_passthrough(self):
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("DB error"))

        candidates = [{"candidate_id": "c1", "score": 2.0}]
        results = await self.svc.normalize_candidate_scores(db, "job-1", candidates)

        assert results[0].scoring_details["method"] == "passthrough"

    @pytest.mark.asyncio
    async def test_empty_candidates_list(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.fetchall.return_value = []
        db.execute = AsyncMock(return_value=result_mock)

        results = await self.svc.normalize_candidate_scores(db, "job-1", [])
        assert results == []

    @pytest.mark.asyncio
    async def test_normalized_score_clamped_to_5(self):
        db = AsyncMock()
        result_mock = MagicMock()
        # Two versions with large difference so normalization actually runs
        result_mock.fetchall.return_value = [(1, 0.1), (2, 5.0)]
        db.execute = AsyncMock(return_value=result_mock)

        candidates = [{"candidate_id": "c1", "score": 5.0, "question_set_version": 2}]
        results = await self.svc.normalize_candidate_scores(db, "job-1", candidates)

        assert results[0].normalized_score <= 5.0


class TestGetComparisonContext:
    """Tests for get_comparison_context async method."""

    def setup_method(self):
        self.svc = ScoreNormalizationService()

    @pytest.mark.asyncio
    async def test_returns_defaults_on_db_error(self):
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("fail"))

        ctx = await self.svc.get_comparison_context(db, "job-1")

        assert ctx["total_versions"] == 0
        assert ctx["needs_normalization"] is False
        assert ctx["active_version"] is None

    @pytest.mark.asyncio
    async def test_needs_normalization_when_diff_above_threshold(self):
        db = AsyncMock()

        versions_result = MagicMock()
        versions_result.fetchall.return_value = [
            (1, 0.3, 10, "manual", True),
            (2, 0.7, 10, "auto", False),
        ]
        sessions_result = MagicMock()
        sessions_result.fetchall.return_value = [(1, 5), (2, 3)]

        db.execute = AsyncMock(side_effect=[versions_result, sessions_result])

        ctx = await self.svc.get_comparison_context(db, "job-1")

        assert ctx["needs_normalization"] is True
        assert ctx["total_versions"] == 2

    @pytest.mark.asyncio
    async def test_no_normalization_when_diff_small(self):
        db = AsyncMock()

        versions_result = MagicMock()
        versions_result.fetchall.return_value = [
            (1, 0.5, 10, "manual", True),
            (2, 0.52, 10, "auto", False),
        ]
        sessions_result = MagicMock()
        sessions_result.fetchall.return_value = []

        db.execute = AsyncMock(side_effect=[versions_result, sessions_result])

        ctx = await self.svc.get_comparison_context(db, "job-1")

        assert ctx["needs_normalization"] is False

    @pytest.mark.asyncio
    async def test_active_version_returned(self):
        db = AsyncMock()

        versions_result = MagicMock()
        versions_result.fetchall.return_value = [
            (3, 0.5, 10, "manual", True),
            (2, 0.5, 10, "auto", False),
        ]
        sessions_result = MagicMock()
        sessions_result.fetchall.return_value = []

        db.execute = AsyncMock(side_effect=[versions_result, sessions_result])

        ctx = await self.svc.get_comparison_context(db, "job-1")

        assert ctx["active_version"] == 3
