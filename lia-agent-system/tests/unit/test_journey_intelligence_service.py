"""
Unit tests — JourneyIntelligenceService (Sprint 2C).

Testa lógica de negócio sem dependência de banco real:
- compute_health_score: todos os componentes e edge cases
- health_label: mapeamento de score para label
- detect_risk_patterns: todos os padrões preditivos
- get_vacancy_metrics: com mock de DB
- get_company_overview: agregação por vaga
- get_company_recruiters_journey: agrupamento por recrutador
- Comportamento seguro em falhas de DB
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.shared.services.journey_intelligence_service import (
    JourneyIntelligenceService,
    compute_health_score,
    health_label,
    detect_risk_patterns,
    _stage_rank,
    journey_intelligence_service,
)


# ---------------------------------------------------------------------------
# TestComputeHealthScore
# ---------------------------------------------------------------------------
class TestComputeHealthScore:
    def test_perfect_pipeline_scores_100(self):
        score = compute_health_score(
            total_active=10,
            conversion_rate_overall=0.30,
            avg_drop_off_rate=0.20,
            candidates_in_advanced_stages=4,
            has_critical_ews=False,
            days_since_last_movement=1.0,
        )
        assert score == 100

    def test_empty_pipeline_scores_low(self):
        score = compute_health_score(
            total_active=0,
            conversion_rate_overall=0.0,
            avg_drop_off_rate=1.0,
            candidates_in_advanced_stages=0,
            has_critical_ews=True,
            days_since_last_movement=30.0,
        )
        assert score < 30

    def test_zero_active_no_volume_points(self):
        score_zero = compute_health_score(
            total_active=0,
            conversion_rate_overall=0.0,
            avg_drop_off_rate=0.0,
            candidates_in_advanced_stages=0,
            has_critical_ews=False,
            days_since_last_movement=1.0,
        )
        score_five = compute_health_score(
            total_active=5,
            conversion_rate_overall=0.0,
            avg_drop_off_rate=0.0,
            candidates_in_advanced_stages=0,
            has_critical_ews=False,
            days_since_last_movement=1.0,
        )
        assert score_five > score_zero

    def test_high_conversion_adds_points(self):
        score_high = compute_health_score(
            total_active=5,
            conversion_rate_overall=0.25,
            avg_drop_off_rate=0.3,
            candidates_in_advanced_stages=2,
            has_critical_ews=False,
            days_since_last_movement=2.0,
        )
        score_low = compute_health_score(
            total_active=5,
            conversion_rate_overall=0.05,
            avg_drop_off_rate=0.3,
            candidates_in_advanced_stages=2,
            has_critical_ews=False,
            days_since_last_movement=2.0,
        )
        assert score_high > score_low

    def test_ews_critical_reduces_score(self):
        score_safe = compute_health_score(
            total_active=5,
            conversion_rate_overall=0.20,
            avg_drop_off_rate=0.3,
            candidates_in_advanced_stages=2,
            has_critical_ews=False,
            days_since_last_movement=1.0,
        )
        score_ews = compute_health_score(
            total_active=5,
            conversion_rate_overall=0.20,
            avg_drop_off_rate=0.3,
            candidates_in_advanced_stages=2,
            has_critical_ews=True,
            days_since_last_movement=1.0,
        )
        assert score_safe > score_ews

    def test_score_capped_at_100(self):
        score = compute_health_score(
            total_active=100,
            conversion_rate_overall=1.0,
            avg_drop_off_rate=0.0,
            candidates_in_advanced_stages=50,
            has_critical_ews=False,
            days_since_last_movement=0.0,
        )
        assert score <= 100

    def test_score_never_negative(self):
        score = compute_health_score(
            total_active=0,
            conversion_rate_overall=0.0,
            avg_drop_off_rate=1.0,
            candidates_in_advanced_stages=0,
            has_critical_ews=True,
            days_since_last_movement=999.0,
        )
        assert score >= 0

    def test_two_advanced_candidates_gives_full_advanced_points(self):
        score_two = compute_health_score(
            total_active=5,
            conversion_rate_overall=0.0,
            avg_drop_off_rate=0.3,
            candidates_in_advanced_stages=2,
            has_critical_ews=False,
            days_since_last_movement=1.0,
        )
        score_zero = compute_health_score(
            total_active=5,
            conversion_rate_overall=0.0,
            avg_drop_off_rate=0.3,
            candidates_in_advanced_stages=0,
            has_critical_ews=False,
            days_since_last_movement=1.0,
        )
        assert score_two > score_zero


# ---------------------------------------------------------------------------
# TestHealthLabel
# ---------------------------------------------------------------------------
class TestHealthLabel:
    def test_score_70_is_healthy(self):
        assert health_label(70) == "healthy"

    def test_score_100_is_healthy(self):
        assert health_label(100) == "healthy"

    def test_score_45_is_warning(self):
        assert health_label(45) == "warning"

    def test_score_69_is_warning(self):
        assert health_label(69) == "warning"

    def test_score_44_is_critical(self):
        assert health_label(44) == "critical"

    def test_score_0_is_critical(self):
        assert health_label(0) == "critical"


# ---------------------------------------------------------------------------
# TestStageRank
# ---------------------------------------------------------------------------
class TestStageRank:
    def test_applied_before_screening(self):
        assert _stage_rank("applied") < _stage_rank("screening")

    def test_screening_before_interview_hr(self):
        assert _stage_rank("screening") < _stage_rank("interview_hr")

    def test_interview_hr_before_offer(self):
        assert _stage_rank("interview_hr") < _stage_rank("offer")

    def test_unknown_stage_gets_max_rank(self):
        known = _stage_rank("offer")
        unknown = _stage_rank("unknown_xyz")
        assert unknown > known


# ---------------------------------------------------------------------------
# TestDetectRiskPatterns
# ---------------------------------------------------------------------------
class TestDetectRiskPatterns:
    def _base_funnel(self):
        return [
            {"stage": "screening", "active_count": 3},
            {"stage": "interview_hr", "active_count": 1},
        ]

    def test_detects_empty_advanced_funnel(self):
        funnel = [{"stage": "screening", "active_count": 5}]
        patterns = detect_risk_patterns(
            funnel=funnel,
            total_active=5,
            candidates_in_advanced=0,
            drop_off_by_stage={},
            health_score=40,
        )
        types = [p["pattern"] for p in patterns]
        assert "empty_advanced_funnel" in types

    def test_detects_zero_pipeline(self):
        patterns = detect_risk_patterns(
            funnel=[],
            total_active=0,
            candidates_in_advanced=0,
            drop_off_by_stage={},
            health_score=0,
        )
        types = [p["pattern"] for p in patterns]
        assert "zero_pipeline" in types

    def test_detects_high_offer_rejection(self):
        patterns = detect_risk_patterns(
            funnel=self._base_funnel(),
            total_active=4,
            candidates_in_advanced=2,
            drop_off_by_stage={"offer": 0.50},
            health_score=60,
        )
        types = [p["pattern"] for p in patterns]
        assert "high_offer_rejection" in types

    def test_detects_top_heavy_funnel(self):
        funnel = [
            {"stage": "applied", "active_count": 8},
            {"stage": "screening", "active_count": 2},
            {"stage": "interview_hr", "active_count": 0},
        ]
        patterns = detect_risk_patterns(
            funnel=funnel,
            total_active=10,
            candidates_in_advanced=0,
            drop_off_by_stage={},
            health_score=40,
        )
        types = [p["pattern"] for p in patterns]
        assert "top_heavy_funnel" in types

    def test_detects_critical_health(self):
        patterns = detect_risk_patterns(
            funnel=self._base_funnel(),
            total_active=2,
            candidates_in_advanced=1,
            drop_off_by_stage={},
            health_score=20,
        )
        types = [p["pattern"] for p in patterns]
        assert "critical_health" in types

    def test_healthy_pipeline_no_patterns(self):
        funnel = [
            {"stage": "screening", "active_count": 3},
            {"stage": "interview_hr", "active_count": 2},
            {"stage": "offer", "active_count": 1},
        ]
        patterns = detect_risk_patterns(
            funnel=funnel,
            total_active=6,
            candidates_in_advanced=3,
            drop_off_by_stage={"offer": 0.10},
            health_score=80,
        )
        assert patterns == []

    def test_no_top_heavy_with_less_than_4_candidates(self):
        funnel = [
            {"stage": "applied", "active_count": 2},
            {"stage": "screening", "active_count": 1},
        ]
        patterns = detect_risk_patterns(
            funnel=funnel,
            total_active=3,
            candidates_in_advanced=0,
            drop_off_by_stage={},
            health_score=40,
        )
        types = [p["pattern"] for p in patterns]
        assert "top_heavy_funnel" not in types


# ---------------------------------------------------------------------------
# TestGetVacancyMetrics
# ---------------------------------------------------------------------------
def _make_funnel_row(stage, active=2, exited=1, hired=0, avg_days=3.0):
    row = MagicMock()
    row.stage = stage
    row.active_count = active
    row.exited_count = exited
    row.hired_count = hired
    row.total_count = active + exited + hired
    row.avg_days_in_stage = avg_days
    row.last_movement = datetime.now(timezone.utc) - timedelta(days=2)
    return row


def _make_vac_row(title="Dev Backend", status="open", recruiter_id="rec-1", deadline=None):
    row = MagicMock()
    row.vacancy_id = "vac-1"
    row.title = title
    row.status = status
    row.recruiter_id = recruiter_id
    row.created_at = datetime.now(timezone.utc) - timedelta(days=30)
    row.deadline = deadline
    return row


@pytest.mark.asyncio
class TestGetVacancyMetrics:
    async def test_returns_health_score_and_funnel(self):
        service = JourneyIntelligenceService()

        funnel_rows = [
            _make_funnel_row("screening", active=3, exited=1),
            _make_funnel_row("interview_hr", active=2, exited=0),
        ]
        vac_row = _make_vac_row()

        mock_db = AsyncMock()
        funnel_result = MagicMock()
        funnel_result.fetchall.return_value = funnel_rows
        vac_result = MagicMock()
        vac_result.fetchone.return_value = vac_row
        ews_result = MagicMock()
        ews_result.fetchall.return_value = []

        mock_db.execute = AsyncMock(side_effect=[funnel_result, vac_result, ews_result])

        result = await service.get_vacancy_metrics("vac-1", "company-1", db=mock_db)

        assert result["success"] is True
        assert "health_score" in result
        assert "health_label" in result
        assert "funnel" in result
        assert "summary" in result
        assert "risk_patterns" in result
        assert result["health_score"] >= 0
        assert result["health_score"] <= 100

    async def test_funnel_sorted_by_stage_rank(self):
        service = JourneyIntelligenceService()

        funnel_rows = [
            _make_funnel_row("interview_hr", active=1),
            _make_funnel_row("screening", active=3),
            _make_funnel_row("applied", active=5),
        ]
        vac_row = _make_vac_row()

        mock_db = AsyncMock()
        f_result = MagicMock()
        f_result.fetchall.return_value = funnel_rows
        v_result = MagicMock()
        v_result.fetchone.return_value = vac_row
        e_result = MagicMock()
        e_result.fetchall.return_value = []

        mock_db.execute = AsyncMock(side_effect=[f_result, v_result, e_result])

        result = await service.get_vacancy_metrics("vac-1", "company-1", db=mock_db)

        stages = [f["stage"] for f in result["funnel"]]
        ranks = [_stage_rank(s) for s in stages]
        assert ranks == sorted(ranks)

    async def test_returns_error_on_db_failure(self):
        service = JourneyIntelligenceService()
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

        result = await service.get_vacancy_metrics("vac-1", "company-1", db=mock_db)

        assert result.get("success") is False

    async def test_candidates_in_advanced_counted(self):
        service = JourneyIntelligenceService()

        funnel_rows = [
            _make_funnel_row("screening", active=4, exited=2),
            _make_funnel_row("interview_hr", active=2, exited=0),
            _make_funnel_row("offer", active=1, exited=0),
        ]
        vac_row = _make_vac_row()

        mock_db = AsyncMock()
        f_result = MagicMock()
        f_result.fetchall.return_value = funnel_rows
        v_result = MagicMock()
        v_result.fetchone.return_value = vac_row
        e_result = MagicMock()
        e_result.fetchall.return_value = []

        mock_db.execute = AsyncMock(side_effect=[f_result, v_result, e_result])

        result = await service.get_vacancy_metrics("vac-1", "company-1", db=mock_db)

        assert result["summary"]["candidates_in_advanced_stages"] == 3  # interview_hr(2) + offer(1)


# ---------------------------------------------------------------------------
# TestGetCompanyOverview
# ---------------------------------------------------------------------------
def _make_overview_row(
    vacancy_id, title, recruiter_id="rec-1",
    total_active=5, candidates_in_advanced=2,
    total_exited=3, days_ago=2
):
    row = MagicMock()
    row.vacancy_id = vacancy_id
    row.vacancy_title = title
    row.recruiter_id = recruiter_id
    row.total_active = total_active
    row.candidates_in_advanced = candidates_in_advanced
    row.total_exited = total_exited
    row.last_movement = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return row


@pytest.mark.asyncio
class TestGetCompanyOverview:
    async def test_returns_vacancies_sorted_by_health_asc(self):
        service = JourneyIntelligenceService()

        rows = [
            _make_overview_row("vac-1", "Dev Backend", total_active=8, candidates_in_advanced=3),
            _make_overview_row("vac-2", "Analista RH", total_active=0, candidates_in_advanced=0),
        ]

        mock_db = AsyncMock()
        result_mock = MagicMock()
        result_mock.fetchall.return_value = rows
        mock_db.execute = AsyncMock(return_value=result_mock)

        result = await service.get_company_overview("company-1", db=mock_db)

        assert result["success"] is True
        vacancies = result["vacancies"]
        assert len(vacancies) == 2
        # Deve estar ordenado por health_score ASC (pior primeiro)
        assert vacancies[0]["health_score"] <= vacancies[1]["health_score"]

    async def test_summary_counts_labels(self):
        service = JourneyIntelligenceService()

        rows = [
            _make_overview_row("vac-1", "Vaga A", total_active=0, candidates_in_advanced=0),
            _make_overview_row("vac-2", "Vaga B", total_active=8, candidates_in_advanced=3),
        ]

        mock_db = AsyncMock()
        result_mock = MagicMock()
        result_mock.fetchall.return_value = rows
        mock_db.execute = AsyncMock(return_value=result_mock)

        result = await service.get_company_overview("company-1", db=mock_db)

        summary = result["summary"]
        total = summary["critical"] + summary["warning"] + summary["healthy"]
        assert total == 2

    async def test_returns_empty_on_db_error(self):
        service = JourneyIntelligenceService()
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

        result = await service.get_company_overview("company-1", db=mock_db)

        assert result.get("vacancies") == []


# ---------------------------------------------------------------------------
# TestGetCompanyRecruitersJourney
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestGetCompanyRecruitersJourney:
    async def test_groups_at_risk_vacancies_by_recruiter(self):
        service = JourneyIntelligenceService()

        overview_data = {
            "success": True,
            "vacancies": [
                {"vacancy_id": "v1", "vacancy_title": "Dev", "recruiter_id": "rec-1",
                 "health_score": 30, "health_label": "critical",
                 "total_active": 2, "candidates_in_advanced_stages": 0,
                 "conversion_rate": 0.0, "days_since_last_movement": 5.0},
                {"vacancy_id": "v2", "vacancy_title": "RH", "recruiter_id": "rec-1",
                 "health_score": 70, "health_label": "healthy",
                 "total_active": 5, "candidates_in_advanced_stages": 2,
                 "conversion_rate": 0.2, "days_since_last_movement": 1.0},
                {"vacancy_id": "v3", "vacancy_title": "UX", "recruiter_id": "rec-2",
                 "health_score": 40, "health_label": "warning",
                 "total_active": 3, "candidates_in_advanced_stages": 1,
                 "conversion_rate": 0.1, "days_since_last_movement": 3.0},
            ],
        }

        with patch.object(service, "get_company_overview", return_value=overview_data):
            result = await service.get_company_recruiters_journey("company-1")

        # rec-1 tem 1 vaga crítica (score 30) + 1 saudável (score 70 → excluída por >= 50)
        # rec-2 tem 1 vaga em warning (score 40)
        recruiter_ids = {r["recruiter_id"] for r in result}
        assert "rec-1" in recruiter_ids
        assert "rec-2" in recruiter_ids

        rec1 = next(r for r in result if r["recruiter_id"] == "rec-1")
        assert len(rec1["at_risk_vacancies"]) == 1  # só v1, v2 é healthy
        assert rec1["critical_count"] == 1

    async def test_excludes_healthy_vacancies(self):
        service = JourneyIntelligenceService()

        overview_data = {
            "success": True,
            "vacancies": [
                {"vacancy_id": "v1", "vacancy_title": "Dev", "recruiter_id": "rec-1",
                 "health_score": 80, "health_label": "healthy",
                 "total_active": 5, "candidates_in_advanced_stages": 2,
                 "conversion_rate": 0.2, "days_since_last_movement": 1.0},
            ],
        }

        with patch.object(service, "get_company_overview", return_value=overview_data):
            result = await service.get_company_recruiters_journey("company-1")

        assert result == []


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_singleton_exists(self):
        assert journey_intelligence_service is not None

    def test_singleton_is_instance(self):
        assert isinstance(journey_intelligence_service, JourneyIntelligenceService)
