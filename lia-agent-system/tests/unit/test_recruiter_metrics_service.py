"""
Unit tests — RecruiterMetricsService (Sprint 2A).

Testa lógica de negócio sem dependência de banco real:
- Thresholds de urgência por etapa
- Cálculo de urgency_score
- Classificação de criticidade (offer vs demais)
- Agregação por empresa (get_company_recruiters_backlog)
- Comportamento seguro em falhas de DB
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.shared.services.recruiter_metrics_service import (
    RecruiterMetricsService,
    _urgency_threshold,
    _urgency_weight,
    recruiter_metrics_service,
)


# ---------------------------------------------------------------------------
# TestUrgencyThreshold
# ---------------------------------------------------------------------------
class TestUrgencyThreshold:
    def test_offer_threshold_is_2(self):
        assert _urgency_threshold("offer") == 2

    def test_proposta_threshold_is_2(self):
        assert _urgency_threshold("proposta") == 2

    def test_interview_hr_threshold_is_4(self):
        assert _urgency_threshold("interview_hr") == 4

    def test_entrevista_rh_threshold_is_4(self):
        assert _urgency_threshold("entrevista_rh") == 4

    def test_screening_threshold_is_5(self):
        assert _urgency_threshold("screening") == 5

    def test_triagem_threshold_is_5(self):
        assert _urgency_threshold("triagem") == 5

    def test_applied_threshold_is_3(self):
        assert _urgency_threshold("applied") == 3

    def test_novo_threshold_is_3(self):
        assert _urgency_threshold("novo") == 3

    def test_unknown_stage_default_is_5(self):
        assert _urgency_threshold("custom_stage") == 5

    def test_empty_stage_default_is_5(self):
        assert _urgency_threshold("") == 5

    def test_case_insensitive(self):
        assert _urgency_threshold("OFFER") == 2
        assert _urgency_threshold("Interview_HR") == 4


# ---------------------------------------------------------------------------
# TestUrgencyWeight
# ---------------------------------------------------------------------------
class TestUrgencyWeight:
    def test_offer_weight_highest(self):
        assert _urgency_weight("offer") == 4.0

    def test_proposta_weight_highest(self):
        assert _urgency_weight("proposta") == 4.0

    def test_interview_weight(self):
        assert _urgency_weight("interview_hr") == 3.0
        assert _urgency_weight("entrevista_tecnica") == 3.0
        assert _urgency_weight("interview_final") == 3.0

    def test_screening_weight(self):
        assert _urgency_weight("screening") == 2.0
        assert _urgency_weight("triagem") == 2.0

    def test_applied_weight_lowest(self):
        assert _urgency_weight("applied") == 1.0
        assert _urgency_weight("novo") == 1.0

    def test_unknown_weight_lowest(self):
        assert _urgency_weight("custom_stage") == 1.0

    def test_urgency_score_offer_beats_screening(self):
        # Candidato em offer há 3 dias vs screening há 6 dias
        offer_score = 3.0 * _urgency_weight("offer")     # 12.0
        screening_score = 6.0 * _urgency_weight("screening")  # 12.0 — empate aqui
        # Offer há 4 dias vence screening há 6 dias
        offer_score_4 = 4.0 * _urgency_weight("offer")   # 16.0
        assert offer_score_4 > screening_score


# ---------------------------------------------------------------------------
# TestCriticalityClassification
# ---------------------------------------------------------------------------
class TestCriticalityClassification:
    def test_offer_above_threshold_is_critical(self):
        # Simula lógica de is_critical do backlog item
        stage = "offer"
        days_in_stage = 3.0
        threshold = _urgency_threshold(stage)
        is_critical = stage.lower() in ("offer", "proposta") and days_in_stage >= threshold
        assert is_critical is True

    def test_offer_below_threshold_not_critical(self):
        stage = "offer"
        days_in_stage = 1.0
        threshold = _urgency_threshold(stage)
        is_critical = stage.lower() in ("offer", "proposta") and days_in_stage >= threshold
        assert is_critical is False

    def test_interview_above_threshold_not_critical(self):
        # Interview acima do threshold → warning, não critical
        stage = "interview_hr"
        days_in_stage = 6.0
        is_critical = stage.lower() in ("offer", "proposta") and days_in_stage >= _urgency_threshold(stage)
        assert is_critical is False


# ---------------------------------------------------------------------------
# TestWeeklySummaryStructure
# ---------------------------------------------------------------------------
class TestWeeklySummaryStructure:
    @pytest.mark.asyncio
    async def test_weekly_summary_returns_expected_keys(self):
        svc = RecruiterMetricsService()

        with patch.object(svc, "get_action_backlog", new=AsyncMock(return_value=[])):
            with patch.object(svc, "get_response_time_avg", new=AsyncMock(return_value=2.5)):
                with patch.object(svc, "_get_advanced_this_week", new=AsyncMock(return_value=3)):
                    result = await svc.get_weekly_summary("user_1", "company_1")

        assert "backlog_count" in result
        assert "critical_count" in result
        assert "most_urgent" in result
        assert "avg_response_time_days" in result
        assert "candidates_advanced_this_week" in result
        assert "offers_pending" in result

    @pytest.mark.asyncio
    async def test_weekly_summary_empty_backlog(self):
        svc = RecruiterMetricsService()

        with patch.object(svc, "get_action_backlog", new=AsyncMock(return_value=[])):
            with patch.object(svc, "get_response_time_avg", new=AsyncMock(return_value=None)):
                with patch.object(svc, "_get_advanced_this_week", new=AsyncMock(return_value=0)):
                    result = await svc.get_weekly_summary("user_1", "company_1")

        assert result["backlog_count"] == 0
        assert result["critical_count"] == 0
        assert result["most_urgent"] is None
        assert result["offers_pending"] == 0

    @pytest.mark.asyncio
    async def test_weekly_summary_counts_offers(self):
        svc = RecruiterMetricsService()
        backlog = [
            {"stage": "offer", "is_critical": True, "urgency_score": 16.0,
             "candidate_name": "Ana", "days_in_stage": 4.0, "threshold_days": 2},
            {"stage": "interview_hr", "is_critical": False, "urgency_score": 12.0,
             "candidate_name": "Bob", "days_in_stage": 5.0, "threshold_days": 4},
            {"stage": "proposta", "is_critical": True, "urgency_score": 10.0,
             "candidate_name": "Carlos", "days_in_stage": 3.0, "threshold_days": 2},
        ]

        with patch.object(svc, "get_action_backlog", new=AsyncMock(return_value=backlog)):
            with patch.object(svc, "get_response_time_avg", new=AsyncMock(return_value=1.5)):
                with patch.object(svc, "_get_advanced_this_week", new=AsyncMock(return_value=2)):
                    result = await svc.get_weekly_summary("user_1", "company_1")

        assert result["backlog_count"] == 3
        assert result["critical_count"] == 2
        assert result["offers_pending"] == 2  # offer + proposta
        assert result["most_urgent"]["candidate_name"] == "Ana"


# ---------------------------------------------------------------------------
# TestErrorHandling
# ---------------------------------------------------------------------------
class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_get_action_backlog_returns_empty_on_db_error(self):
        svc = RecruiterMetricsService()

        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("DB connection failed")

        result = await svc.get_action_backlog("user_1", "company_1", db=mock_db)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_response_time_returns_none_on_db_error(self):
        svc = RecruiterMetricsService()

        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("DB connection failed")

        result = await svc.get_response_time_avg("user_1", "company_1", db=mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_company_recruiters_returns_empty_on_db_error(self):
        svc = RecruiterMetricsService()

        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("DB connection failed")

        result = await svc.get_company_recruiters_backlog("company_1", db=mock_db)
        assert result == []

    def test_singleton_exists(self):
        assert recruiter_metrics_service is not None
        assert isinstance(recruiter_metrics_service, RecruiterMetricsService)
