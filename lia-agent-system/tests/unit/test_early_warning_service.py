"""
Unit tests — EarlyWarningService (Sprint 2B).

Testa lógica de negócio sem dependência de banco real:
- Thresholds por etapa (_thresholds_for_stage)
- Fórmula EWS score (compute_ews_score)
- Classificação por risk_level (risk_level_for_score)
- get_at_risk_candidates com mock de DB
- get_summary_by_risk_level
- Comportamento seguro em falhas de DB
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.shared.services.early_warning_service import (
    EarlyWarningService,
    compute_ews_score,
    risk_level_for_score,
    _thresholds_for_stage,
    early_warning_service,
)


# ---------------------------------------------------------------------------
# TestThresholdsForStage
# ---------------------------------------------------------------------------
class TestThresholdsForStage:
    def test_offer_thresholds(self):
        assert _thresholds_for_stage("offer") == (2, 4)

    def test_proposta_thresholds(self):
        assert _thresholds_for_stage("proposta") == (2, 4)

    def test_interview_hr_thresholds(self):
        assert _thresholds_for_stage("interview_hr") == (3, 5)

    def test_entrevista_rh_thresholds(self):
        assert _thresholds_for_stage("entrevista_rh") == (3, 5)

    def test_interview_technical_thresholds(self):
        assert _thresholds_for_stage("interview_technical") == (3, 5)

    def test_screening_thresholds(self):
        assert _thresholds_for_stage("screening") == (5, 8)

    def test_triagem_thresholds(self):
        assert _thresholds_for_stage("triagem") == (5, 8)

    def test_applied_thresholds(self):
        assert _thresholds_for_stage("applied") == (7, 12)

    def test_novo_thresholds(self):
        assert _thresholds_for_stage("novo") == (7, 12)

    def test_unknown_stage_uses_default(self):
        assert _thresholds_for_stage("unknown_stage") == (5, 10)

    def test_empty_stage_uses_default(self):
        assert _thresholds_for_stage("") == (5, 10)

    def test_case_insensitive(self):
        assert _thresholds_for_stage("OFFER") == (2, 4)
        assert _thresholds_for_stage("Screening") == (5, 8)


# ---------------------------------------------------------------------------
# TestComputeEwsScore
# ---------------------------------------------------------------------------
class TestComputeEwsScore:
    def test_zero_days_is_zero_score(self):
        score = compute_ews_score(0, "offer", lia_score=0.5)
        assert score == 0.0

    def test_at_critical_threshold_without_lia_score_exceeds_one(self):
        # critical=4, lia_score=None → weight=1.25 → base=1.0 → ews=1.0 (capped)
        score = compute_ews_score(4, "offer", lia_score=None)
        assert score == 1.0

    def test_at_critical_threshold_with_lia_score_is_capped_at_one(self):
        score = compute_ews_score(4, "offer", lia_score=1.0)
        assert score == 1.0

    def test_half_critical_with_neutral_lia_score(self):
        # offer critical=4, days=2, lia_score=0.5
        # base=0.5, weight=1.25, ews=0.625
        score = compute_ews_score(2, "offer", lia_score=0.5)
        assert score == pytest.approx(0.625, rel=1e-3)

    def test_lia_score_increases_urgency(self):
        score_low_lia = compute_ews_score(3, "interview_hr", lia_score=0.0)
        score_high_lia = compute_ews_score(3, "interview_hr", lia_score=1.0)
        assert score_high_lia > score_low_lia

    def test_none_lia_score_uses_default_weight(self):
        score_none = compute_ews_score(3, "interview_hr", lia_score=None)
        score_half = compute_ews_score(3, "interview_hr", lia_score=0.5)
        assert score_none == score_half

    def test_score_is_capped_at_one(self):
        score = compute_ews_score(100, "offer", lia_score=1.0)
        assert score == 1.0

    def test_score_rounds_to_three_decimals(self):
        score = compute_ews_score(2, "offer", lia_score=0.5)
        assert score == round(score, 3)

    def test_screening_stage_different_from_offer(self):
        # Same days but different critical thresholds → different scores
        score_offer = compute_ews_score(3, "offer")     # critical=4
        score_screen = compute_ews_score(3, "screening") # critical=8
        assert score_screen < score_offer


# ---------------------------------------------------------------------------
# TestRiskLevelForScore
# ---------------------------------------------------------------------------
class TestRiskLevelForScore:
    def test_score_1_is_critical(self):
        assert risk_level_for_score(1.0) == "critical"

    def test_score_above_1_is_critical(self):
        assert risk_level_for_score(1.5) == "critical"

    def test_score_0_6_is_high(self):
        assert risk_level_for_score(0.6) == "high"

    def test_score_0_99_is_high(self):
        assert risk_level_for_score(0.99) == "high"

    def test_score_0_3_is_medium(self):
        assert risk_level_for_score(0.3) == "medium"

    def test_score_0_59_is_medium(self):
        assert risk_level_for_score(0.59) == "medium"

    def test_score_0_29_is_low(self):
        assert risk_level_for_score(0.29) == "low"

    def test_score_0_is_low(self):
        assert risk_level_for_score(0.0) == "low"


# ---------------------------------------------------------------------------
# TestGetAtRiskCandidates
# ---------------------------------------------------------------------------
def _make_row(**kwargs):
    row = MagicMock()
    defaults = {
        "vacancy_candidate_id": "vc-1",
        "candidate_id": "cand-1",
        "candidate_name": "Ana Silva",
        "vacancy_id": "vac-1",
        "vacancy_title": "Dev Backend",
        "stage": "screening",
        "lia_score": 0.8,
        "recruiter_id": "rec-1",
        "last_contact_at": None,
        "days_since_contact": 6.0,
    }
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


@pytest.mark.asyncio
class TestGetAtRiskCandidates:
    async def test_returns_candidates_beyond_warning_threshold(self):
        service = EarlyWarningService()
        row = _make_row(stage="screening", days_since_contact=6.0, lia_score=0.5)

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row]

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_at_risk_candidates("company-1", min_risk_level="medium", db=mock_db)

        assert len(result) == 1
        assert result[0]["candidate_name"] == "Ana Silva"
        assert result[0]["stage"] == "screening"
        assert result[0]["days_since_contact"] == 6.0
        assert "ews_score" in result[0]
        assert "risk_level" in result[0]

    async def test_filters_candidates_below_warning_threshold(self):
        service = EarlyWarningService()
        # screening warning=5 days — 3 days is below threshold
        row = _make_row(stage="screening", days_since_contact=3.0)

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row]

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_at_risk_candidates("company-1", db=mock_db)
        assert len(result) == 0

    async def test_filters_by_min_risk_level_high(self):
        service = EarlyWarningService()
        # screening critical=8d, lia=0.5, weight=1.25
        # days=6: base=6/8=0.75, ews=0.938 → high
        # days=4: base=4/8=0.5, ews=0.625 → high
        # days=2: below warning(5) → excluded
        row_high = _make_row(stage="screening", days_since_contact=6.0, lia_score=0.5)
        row_medium = _make_row(
            vacancy_candidate_id="vc-2", candidate_id="cand-2", candidate_name="Bob",
            stage="applied", days_since_contact=8.0, lia_score=0.0
        )
        # applied critical=12, days=8, base=0.667, weight=1.0, ews=0.667 → high

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row_high, row_medium]

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_at_risk_candidates("company-1", min_risk_level="high", db=mock_db)
        for r in result:
            assert r["risk_level"] in ("high", "critical")

    async def test_results_sorted_by_ews_score_descending(self):
        service = EarlyWarningService()
        row1 = _make_row(stage="offer", days_since_contact=4.0, lia_score=1.0)   # critical
        row2 = _make_row(
            vacancy_candidate_id="vc-2", candidate_id="cand-2", candidate_name="Bob",
            stage="screening", days_since_contact=6.0, lia_score=0.3
        )

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row2, row1]  # intentionally reversed

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_at_risk_candidates("company-1", db=mock_db)
        if len(result) >= 2:
            assert result[0]["ews_score"] >= result[1]["ews_score"]

    async def test_returns_empty_list_on_db_error(self):
        service = EarlyWarningService()
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

        result = await service.get_at_risk_candidates("company-1", db=mock_db)
        assert result == []

    async def test_handles_none_lia_score(self):
        service = EarlyWarningService()
        row = _make_row(stage="screening", days_since_contact=6.0, lia_score=None)

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row]

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_at_risk_candidates("company-1", db=mock_db)
        assert len(result) == 1
        assert result[0]["lia_score"] is None

    async def test_last_contact_at_isoformat_when_present(self):
        service = EarlyWarningService()
        contact_dt = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
        row = _make_row(stage="screening", days_since_contact=5.0, last_contact_at=contact_dt)
        row.last_contact_at = contact_dt  # explicit set

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row]

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_at_risk_candidates("company-1", db=mock_db)
        assert len(result) == 1
        assert result[0]["last_contact_at"] == contact_dt.isoformat()


# ---------------------------------------------------------------------------
# TestGetSummaryByRiskLevel
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestGetSummaryByRiskLevel:
    async def test_summary_counts_by_level(self):
        service = EarlyWarningService()

        candidates = [
            {"risk_level": "critical", "ews_score": 1.0},
            {"risk_level": "critical", "ews_score": 1.0},
            {"risk_level": "high", "ews_score": 0.8},
            {"risk_level": "medium", "ews_score": 0.4},
        ]

        with patch.object(service, "get_at_risk_candidates", return_value=candidates):
            summary = await service.get_summary_by_risk_level("company-1")

        assert summary["total"] == 4
        assert summary["by_risk_level"]["critical"] == 2
        assert summary["by_risk_level"]["high"] == 1
        assert summary["by_risk_level"]["medium"] == 1

    async def test_top_critical_capped_at_5(self):
        service = EarlyWarningService()

        candidates = [
            {"risk_level": "critical", "ews_score": 1.0, "candidate_id": str(i)}
            for i in range(8)
        ]

        with patch.object(service, "get_at_risk_candidates", return_value=candidates):
            summary = await service.get_summary_by_risk_level("company-1")

        assert len(summary["top_critical"]) == 5

    async def test_top_high_capped_at_5(self):
        service = EarlyWarningService()

        candidates = [
            {"risk_level": "high", "ews_score": 0.8, "candidate_id": str(i)}
            for i in range(7)
        ]

        with patch.object(service, "get_at_risk_candidates", return_value=candidates):
            summary = await service.get_summary_by_risk_level("company-1")

        assert len(summary["top_high"]) == 5

    async def test_empty_when_no_candidates(self):
        service = EarlyWarningService()

        with patch.object(service, "get_at_risk_candidates", return_value=[]):
            summary = await service.get_summary_by_risk_level("company-1")

        assert summary["total"] == 0
        assert summary["by_risk_level"] == {"critical": 0, "high": 0, "medium": 0}
        assert summary["top_critical"] == []
        assert summary["top_high"] == []


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_singleton_exists(self):
        assert early_warning_service is not None

    def test_singleton_is_instance_of_service(self):
        assert isinstance(early_warning_service, EarlyWarningService)
