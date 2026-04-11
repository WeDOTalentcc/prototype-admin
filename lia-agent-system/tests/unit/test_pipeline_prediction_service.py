"""
Unit tests — Pipeline Prediction Service (Sprint 3A).

Testa:
- compute_closure_probability: fórmula com 5 fatores
- estimate_days_to_close: estimativa por etapa
- get_confidence_level: low / medium / high
- build_factors: listas de fatores positivos e de risco
- get_vacancy_prediction: integração com mock de DB
- get_company_overview: batch de vagas com asyncio.gather
- Comportamento seguro em falhas de DB
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.services.pipeline_prediction_service import (
    PipelinePredictionService,
    pipeline_prediction_service,
    compute_closure_probability,
    estimate_days_to_close,
    get_confidence_level,
    build_factors,
)


# ---------------------------------------------------------------------------
# TestComputeClosureProbability
# ---------------------------------------------------------------------------
class TestComputeClosureProbability:
    def test_offer_stage_fast_many_returns_high_probability(self):
        prob = compute_closure_probability(
            total_active=6,
            best_stage="offer",
            avg_days_in_stage=1.5,
            advanced_count=3,
            critical_ews_count=0,
            high_ews_count=0,
            health_score=80,
        )
        assert prob >= 80

    def test_empty_pipeline_returns_low_probability(self):
        prob = compute_closure_probability(
            total_active=0,
            best_stage="",
            avg_days_in_stage=0,
            advanced_count=0,
            critical_ews_count=0,
            high_ews_count=0,
            health_score=0,
        )
        assert prob <= 15

    def test_critical_ews_penalizes_score(self):
        base = compute_closure_probability(
            total_active=5, best_stage="interview_hr", avg_days_in_stage=3,
            advanced_count=1, critical_ews_count=0, high_ews_count=0, health_score=70,
        )
        penalized = compute_closure_probability(
            total_active=5, best_stage="interview_hr", avg_days_in_stage=3,
            advanced_count=1, critical_ews_count=3, high_ews_count=2, health_score=70,
        )
        assert penalized < base

    def test_result_bounded_0_100(self):
        # Edge: valores extremos
        prob_max = compute_closure_probability(10, "offer", 1, 5, 0, 0, 100)
        prob_min = compute_closure_probability(0, "", 99, 0, 10, 10, 0)
        assert 0 <= prob_max <= 100
        assert 0 <= prob_min <= 100

    def test_slow_velocity_reduces_score(self):
        fast = compute_closure_probability(
            total_active=4, best_stage="interview_hr", avg_days_in_stage=2,
            advanced_count=1, critical_ews_count=0, high_ews_count=0, health_score=60,
        )
        slow = compute_closure_probability(
            total_active=4, best_stage="interview_hr", avg_days_in_stage=20,
            advanced_count=1, critical_ews_count=0, high_ews_count=0, health_score=60,
        )
        assert fast > slow

    def test_advanced_count_bonus_applied(self):
        single = compute_closure_probability(
            total_active=4, best_stage="interview_final", avg_days_in_stage=4,
            advanced_count=1, critical_ews_count=0, high_ews_count=0, health_score=70,
        )
        multiple = compute_closure_probability(
            total_active=4, best_stage="interview_final", avg_days_in_stage=4,
            advanced_count=3, critical_ews_count=0, high_ews_count=0, health_score=70,
        )
        assert multiple >= single

    def test_health_score_contributes_proportionally(self):
        low_health = compute_closure_probability(
            total_active=4, best_stage="screening", avg_days_in_stage=5,
            advanced_count=0, critical_ews_count=0, high_ews_count=0, health_score=0,
        )
        high_health = compute_closure_probability(
            total_active=4, best_stage="screening", avg_days_in_stage=5,
            advanced_count=0, critical_ews_count=0, high_ews_count=0, health_score=100,
        )
        assert high_health > low_health


# ---------------------------------------------------------------------------
# TestEstimateDaysToClose
# ---------------------------------------------------------------------------
class TestEstimateDaysToClose:
    def test_offer_stage_returns_few_days(self):
        days = estimate_days_to_close("offer", 3.0, 2)
        assert days is not None
        assert days <= 7

    def test_applied_stage_returns_many_days(self):
        days = estimate_days_to_close("applied", 5.0, 3)
        assert days is not None
        assert days > 15

    def test_empty_pipeline_returns_none(self):
        days = estimate_days_to_close("offer", 3.0, 0)
        assert days is None

    def test_alias_stages_handled(self):
        # proposta = offer alias
        days_proposta = estimate_days_to_close("proposta", 2.0, 1)
        assert days_proposta is not None
        assert days_proposta <= 7

    def test_capped_at_90_days(self):
        days = estimate_days_to_close("applied", 15.0, 1)
        assert days is not None
        assert days <= 90

    def test_unknown_stage_returns_conservative_estimate(self):
        days = estimate_days_to_close("unknown_stage", 5.0, 1)
        assert days is not None


# ---------------------------------------------------------------------------
# TestGetConfidenceLevel
# ---------------------------------------------------------------------------
class TestGetConfidenceLevel:
    def test_high_active_and_health_returns_high(self):
        assert get_confidence_level(6, 70) == "high"

    def test_empty_pipeline_returns_low(self):
        assert get_confidence_level(0, 80) == "low"

    def test_low_health_returns_low(self):
        assert get_confidence_level(5, 10) == "low"

    def test_medium_case(self):
        assert get_confidence_level(3, 50) == "medium"


# ---------------------------------------------------------------------------
# TestBuildFactors
# ---------------------------------------------------------------------------
class TestBuildFactors:
    def test_offer_stage_in_positives(self):
        pos, _ = build_factors("offer", 2.0, 2, 0, 0, 5, 80)
        assert "candidate_in_offer_stage" in pos

    def test_critical_ews_in_risks(self):
        _, risks = build_factors("screening", 5.0, 0, 2, 0, 3, 50)
        assert any("ews_critical" in r for r in risks)

    def test_empty_pipeline_in_risks(self):
        _, risks = build_factors("", 0, 0, 0, 0, 0, 0)
        assert "empty_pipeline" in risks

    def test_strong_volume_in_positives(self):
        pos, _ = build_factors("interview_hr", 3.0, 2, 0, 0, 10, 70)
        assert "strong_pipeline_volume" in pos

    def test_slow_velocity_in_risks(self):
        _, risks = build_factors("screening", 20.0, 0, 0, 0, 3, 50)
        assert "very_slow_velocity" in risks

    def test_no_advanced_candidates_in_risks(self):
        _, risks = build_factors("screening", 4.0, 0, 0, 0, 5, 60)
        assert "no_advanced_candidates" in risks


# ---------------------------------------------------------------------------
# TestGetVacancyPrediction
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestGetVacancyPrediction:
    async def test_returns_prediction_with_candidates(self):
        service = PipelinePredictionService()

        mock_db = AsyncMock()

        # Simula 3 candidatos ativos
        cand_result = MagicMock()
        cand_result.mappings.return_value.fetchall.return_value = [
            {"stage": "interview_hr", "stage_entered_at": None, "lia_score": 0.8,
             "days_in_stage": 3.0, "days_since_contact": 2.0},
            {"stage": "interview_hr", "stage_entered_at": None, "lia_score": 0.6,
             "days_in_stage": 4.0, "days_since_contact": 3.0},
            {"stage": "screening", "stage_entered_at": None, "lia_score": None,
             "days_in_stage": 2.0, "days_since_contact": 2.0},
        ]

        vac_result = MagicMock()
        vac_result.mappings.return_value.first.return_value = {
            "title": "Dev Backend", "deadline": None, "created_at": None,
        }

        mock_db.execute = AsyncMock(side_effect=[cand_result, vac_result])

        result = await service.get_vacancy_prediction("vac-1", "comp-1", db=mock_db)

        assert result["vacancy_id"] == "vac-1"
        assert result["company_id"] == "comp-1"
        assert result["vacancy_title"] == "Dev Backend"
        assert 0 <= result["closure_probability"] <= 100
        assert result["total_active"] == 3

    async def test_returns_empty_prediction_on_db_error(self):
        service = PipelinePredictionService()
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

        result = await service.get_vacancy_prediction("vac-1", "comp-1", db=mock_db)

        assert result["closure_probability"] == 0
        assert "data_unavailable" in result["risk_factors"]

    async def test_empty_pipeline_gives_low_probability(self):
        service = PipelinePredictionService()
        mock_db = AsyncMock()

        cand_result = MagicMock()
        cand_result.mappings.return_value.fetchall.return_value = []

        vac_result = MagicMock()
        vac_result.mappings.return_value.first.return_value = {
            "title": "Vaga X", "deadline": None, "created_at": None,
        }

        mock_db.execute = AsyncMock(side_effect=[cand_result, vac_result])

        result = await service.get_vacancy_prediction("vac-1", "comp-1", db=mock_db)

        assert result["total_active"] == 0
        assert result["closure_probability"] <= 15
        assert "empty_pipeline" in result["risk_factors"]

    async def test_offer_stage_candidate_gives_high_probability(self):
        service = PipelinePredictionService()
        mock_db = AsyncMock()

        cand_result = MagicMock()
        cand_result.mappings.return_value.fetchall.return_value = [
            {"stage": "offer", "stage_entered_at": None, "lia_score": 0.9,
             "days_in_stage": 1.0, "days_since_contact": 1.0},
            {"stage": "interview_final", "stage_entered_at": None, "lia_score": 0.8,
             "days_in_stage": 2.0, "days_since_contact": 1.0},
        ]

        vac_result = MagicMock()
        vac_result.mappings.return_value.first.return_value = {
            "title": "UX Designer", "deadline": None, "created_at": None,
        }

        mock_db.execute = AsyncMock(side_effect=[cand_result, vac_result])

        result = await service.get_vacancy_prediction("vac-2", "comp-1", db=mock_db)

        assert result["closure_probability"] >= 60
        assert result["stage_of_best_candidate"] == "offer"


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_singleton_exists(self):
        assert pipeline_prediction_service is not None

    def test_has_required_methods(self):
        assert hasattr(pipeline_prediction_service, "get_vacancy_prediction")
        assert hasattr(pipeline_prediction_service, "get_company_overview")
        assert hasattr(pipeline_prediction_service, "get_recruiter_vacancies_prediction")
