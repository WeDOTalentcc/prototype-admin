"""
Unit tests for SilverMedalistService — Sprint 1E.

Tests scoring functions that are pure Python (no DB required).
"""
import pytest
from app.shared.services.silver_medalist_service import (
    SilverMedalistService,
    _stage_weight,
    _recency_score,
    INTERVIEW_STAGES,
)


# ─── Stage weight ─────────────────────────────────────────────────────────────

class TestStageWeight:
    def test_offer_has_max_weight(self):
        assert _stage_weight("offer") == 1.0

    def test_proposta_equals_offer(self):
        assert _stage_weight("proposta") == _stage_weight("offer")

    def test_interview_hr_lower_than_technical(self):
        assert _stage_weight("interview_hr") < _stage_weight("interview_technical")

    def test_interview_final_higher_than_hr(self):
        assert _stage_weight("interview_final") > _stage_weight("interview_hr")

    def test_unknown_stage_returns_default(self):
        assert _stage_weight("etapa_desconhecida") == 0.5

    def test_empty_string_returns_default(self):
        assert _stage_weight("") == 0.5

    def test_case_insensitive(self):
        assert _stage_weight("OFFER") == _stage_weight("offer")


# ─── Recency score ────────────────────────────────────────────────────────────

class TestRecencyScore:
    def test_today_is_perfect(self):
        assert _recency_score(0) == 1.0

    def test_180_days_is_minimum(self):
        score = _recency_score(180)
        assert score <= 0.1

    def test_90_days_is_between_min_and_max(self):
        score = _recency_score(90)
        assert 0.1 < score < 1.0

    def test_decreasing_over_time(self):
        assert _recency_score(0) > _recency_score(30)
        assert _recency_score(30) > _recency_score(90)
        assert _recency_score(90) > _recency_score(180)

    def test_negative_days_treated_as_today(self):
        # days_ago < 0 não deve estoura — tratado como 0
        score = _recency_score(-5)
        assert score == 1.0


# ─── INTERVIEW_STAGES set ─────────────────────────────────────────────────────

class TestInterviewStagesSet:
    def test_contains_standard_english_stages(self):
        assert "interview_hr" in INTERVIEW_STAGES
        assert "interview_technical" in INTERVIEW_STAGES
        assert "interview_manager" in INTERVIEW_STAGES
        assert "interview_final" in INTERVIEW_STAGES
        assert "offer" in INTERVIEW_STAGES

    def test_contains_portuguese_stages(self):
        assert "entrevista_rh" in INTERVIEW_STAGES
        assert "entrevista_tecnica" in INTERVIEW_STAGES
        assert "entrevista_final" in INTERVIEW_STAGES
        assert "proposta" in INTERVIEW_STAGES

    def test_does_not_contain_early_stages(self):
        assert "applied" not in INTERVIEW_STAGES
        assert "triagem" not in INTERVIEW_STAGES
        assert "screening" not in INTERVIEW_STAGES


# ─── Relevance score composition ─────────────────────────────────────────────

class TestRelevanceComposition:
    """Test the composite relevance formula used inside find_for_vacancy."""

    def _compute_relevance(self, stage: str, days_ago: float, lia_score: float) -> float:
        """Mirror the formula from SilverMedalistService.find_for_vacancy."""
        return round(
            0.4 * _stage_weight(stage)
            + 0.35 * _recency_score(days_ago)
            + 0.25 * lia_score,
            3,
        )

    def test_recent_offer_stage_has_high_relevance(self):
        score = self._compute_relevance("offer", 5, 0.9)
        assert score > 0.8

    def test_old_interview_hr_has_lower_relevance(self):
        score = self._compute_relevance("interview_hr", 150, 0.5)
        assert score < 0.6

    def test_offer_beats_interview_hr_same_recency_lia(self):
        offer = self._compute_relevance("offer", 30, 0.7)
        hr = self._compute_relevance("interview_hr", 30, 0.7)
        assert offer > hr

    def test_score_always_between_0_and_1(self):
        for stage in ["interview_hr", "interview_technical", "offer"]:
            for days in [0, 45, 90, 180]:
                for lia in [0.0, 0.5, 1.0]:
                    score = self._compute_relevance(stage, days, lia)
                    assert 0.0 <= score <= 1.0, f"score={score} out of [0,1]"


# ─── Service error handling ───────────────────────────────────────────────────

class TestSilverMedalistServiceErrorHandling:
    @pytest.mark.asyncio
    async def test_find_for_vacancy_returns_list_on_db_error(self):
        svc = SilverMedalistService()
        result = await svc.find_for_vacancy(
            target_vacancy_id="invalid-uuid-xxx",
            company_id="invalid-company",
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find_for_company_returns_list_on_db_error(self):
        svc = SilverMedalistService()
        result = await svc.find_for_company(company_id="invalid-company")
        assert isinstance(result, list)
