"""
Unit tests — Recruiter Performance Benchmarking (Sprint 2D).

Testa:
- _median: cálculo de mediana com valores pares/ímpares/vazios
- get_company_benchmark: agregação anônima, guard de privacidade (< 2 recrutadores)
- get_recruiter_benchmark_comparison: comparação pessoal vs mediana, labels, performance
- Comportamento seguro em falhas de DB
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.services.recruiter_metrics_service import (
    RecruiterMetricsService,
    recruiter_metrics_service,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_weekly_summary(
    backlog=3,
    critical=0,
    avg_response=2.5,
    advanced=5,
    offers=1,
) -> dict:
    return {
        "backlog_count": backlog,
        "critical_count": critical,
        "most_urgent": None,
        "avg_response_time_days": avg_response,
        "candidates_advanced_this_week": advanced,
        "offers_pending": offers,
    }


# ---------------------------------------------------------------------------
# TestGetCompanyBenchmark
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestGetCompanyBenchmark:
    async def test_returns_unavailable_with_only_one_recruiter(self):
        service = RecruiterMetricsService()

        mock_db = AsyncMock()
        id_result = MagicMock()
        id_result.fetchall.return_value = [("rec-1",)]
        mock_db.execute = AsyncMock(return_value=id_result)

        result = await service.get_company_benchmark("company-1", db=mock_db)

        assert result["benchmark_available"] is False

    async def test_returns_unavailable_with_zero_recruiters(self):
        service = RecruiterMetricsService()

        mock_db = AsyncMock()
        id_result = MagicMock()
        id_result.fetchall.return_value = []
        mock_db.execute = AsyncMock(return_value=id_result)

        result = await service.get_company_benchmark("company-1", db=mock_db)

        assert result["benchmark_available"] is False

    async def test_returns_benchmark_with_two_recruiters(self):
        service = RecruiterMetricsService()

        mock_db = AsyncMock()
        id_result = MagicMock()
        id_result.fetchall.return_value = [("rec-1",), ("rec-2",)]
        mock_db.execute = AsyncMock(return_value=id_result)

        summaries = [
            _make_weekly_summary(backlog=4, avg_response=3.0, advanced=6),
            _make_weekly_summary(backlog=2, avg_response=2.0, advanced=4),
        ]

        with patch.object(service, "get_weekly_summary", side_effect=summaries):
            result = await service.get_company_benchmark("company-1", db=mock_db)

        assert result["benchmark_available"] is True
        assert result["recruiter_count"] == 2
        # median of [4, 2] = 3.0
        assert result["median_backlog_count"] == 3.0
        # median of [3.0, 2.0] = 2.5
        assert result["median_response_time_days"] == 2.5
        # median of [6, 4] = 5.0
        assert result["median_advanced_per_week"] == 5.0

    async def test_median_odd_count(self):
        service = RecruiterMetricsService()

        mock_db = AsyncMock()
        id_result = MagicMock()
        id_result.fetchall.return_value = [("r1",), ("r2",), ("r3",)]
        mock_db.execute = AsyncMock(return_value=id_result)

        summaries = [
            _make_weekly_summary(backlog=2, avg_response=1.0, advanced=3),
            _make_weekly_summary(backlog=4, avg_response=2.0, advanced=5),
            _make_weekly_summary(backlog=6, avg_response=3.0, advanced=7),
        ]

        with patch.object(service, "get_weekly_summary", side_effect=summaries):
            result = await service.get_company_benchmark("company-1", db=mock_db)

        # median of [2, 4, 6] = 4.0
        assert result["median_backlog_count"] == 4.0
        # median of [1.0, 2.0, 3.0] = 2.0
        assert result["median_response_time_days"] == 2.0

    async def test_returns_unavailable_on_db_error(self):
        service = RecruiterMetricsService()
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

        result = await service.get_company_benchmark("company-1", db=mock_db)

        assert result["benchmark_available"] is False

    async def test_excludes_none_response_times_from_median(self):
        service = RecruiterMetricsService()

        mock_db = AsyncMock()
        id_result = MagicMock()
        id_result.fetchall.return_value = [("r1",), ("r2",), ("r3",)]
        mock_db.execute = AsyncMock(return_value=id_result)

        summaries = [
            _make_weekly_summary(avg_response=None),
            _make_weekly_summary(avg_response=2.0),
            _make_weekly_summary(avg_response=4.0),
        ]

        with patch.object(service, "get_weekly_summary", side_effect=summaries):
            result = await service.get_company_benchmark("company-1", db=mock_db)

        # median of [2.0, 4.0] = 3.0 (None excluído)
        assert result["median_response_time_days"] == 3.0


# ---------------------------------------------------------------------------
# TestGetRecruiterBenchmarkComparison
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestGetRecruiterBenchmarkComparison:
    async def test_returns_above_average_when_better_on_most_metrics(self):
        service = RecruiterMetricsService()

        personal = _make_weekly_summary(backlog=1, avg_response=1.0, advanced=8, offers=0)
        benchmark = {
            "benchmark_available": True,
            "recruiter_count": 3,
            "median_response_time_days": 3.0,
            "median_advanced_per_week": 5.0,
            "median_backlog_count": 4.0,
            "median_offers_pending": 1.0,
        }

        with patch.object(service, "get_weekly_summary", return_value=personal), \
             patch.object(service, "get_company_benchmark", return_value=benchmark):
            result = await service.get_recruiter_benchmark_comparison("rec-1", "company-1")

        assert result["benchmark_available"] is True
        assert result["overall_performance"] == "above_average"

    async def test_returns_below_average_when_worse_on_most_metrics(self):
        service = RecruiterMetricsService()

        personal = _make_weekly_summary(backlog=10, avg_response=8.0, advanced=1, offers=5)
        benchmark = {
            "benchmark_available": True,
            "recruiter_count": 3,
            "median_response_time_days": 2.0,
            "median_advanced_per_week": 5.0,
            "median_backlog_count": 3.0,
            "median_offers_pending": 1.0,
        }

        with patch.object(service, "get_weekly_summary", return_value=personal), \
             patch.object(service, "get_company_benchmark", return_value=benchmark):
            result = await service.get_recruiter_benchmark_comparison("rec-1", "company-1")

        assert result["overall_performance"] == "below_average"

    async def test_response_time_lower_is_better(self):
        service = RecruiterMetricsService()

        personal = _make_weekly_summary(avg_response=1.0)
        benchmark = {
            "benchmark_available": True,
            "recruiter_count": 2,
            "median_response_time_days": 3.0,
            "median_advanced_per_week": 5.0,
            "median_backlog_count": 3.0,
            "median_offers_pending": 1.0,
        }

        with patch.object(service, "get_weekly_summary", return_value=personal), \
             patch.object(service, "get_company_benchmark", return_value=benchmark):
            result = await service.get_recruiter_benchmark_comparison("rec-1", "company-1")

        rt = result["comparison"]["response_time"]
        assert rt["performance"] == "better"
        assert rt["delta"] == pytest.approx(-2.0, rel=1e-2)

    async def test_advanced_higher_is_better(self):
        service = RecruiterMetricsService()

        personal = _make_weekly_summary(advanced=10)
        benchmark = {
            "benchmark_available": True,
            "recruiter_count": 2,
            "median_response_time_days": 2.0,
            "median_advanced_per_week": 5.0,
            "median_backlog_count": 3.0,
            "median_offers_pending": 1.0,
        }

        with patch.object(service, "get_weekly_summary", return_value=personal), \
             patch.object(service, "get_company_benchmark", return_value=benchmark):
            result = await service.get_recruiter_benchmark_comparison("rec-1", "company-1")

        adv = result["comparison"]["advanced_per_week"]
        assert adv["performance"] == "better"

    async def test_at_par_within_15_percent_tolerance(self):
        service = RecruiterMetricsService()

        personal = _make_weekly_summary(avg_response=2.2)  # 2.2 vs 2.0 = +10% → within ±15%
        benchmark = {
            "benchmark_available": True,
            "recruiter_count": 2,
            "median_response_time_days": 2.0,
            "median_advanced_per_week": 5.0,
            "median_backlog_count": 3.0,
            "median_offers_pending": 1.0,
        }

        with patch.object(service, "get_weekly_summary", return_value=personal), \
             patch.object(service, "get_company_benchmark", return_value=benchmark):
            result = await service.get_recruiter_benchmark_comparison("rec-1", "company-1")

        rt = result["comparison"]["response_time"]
        assert rt["percentile_label"] == "at_par"
        assert rt["performance"] == "at_par"

    async def test_benchmark_unavailable_propagated(self):
        service = RecruiterMetricsService()

        personal = _make_weekly_summary()
        benchmark = {"benchmark_available": False}

        with patch.object(service, "get_weekly_summary", return_value=personal), \
             patch.object(service, "get_company_benchmark", return_value=benchmark):
            result = await service.get_recruiter_benchmark_comparison("rec-1", "company-1")

        assert result["benchmark_available"] is False

    async def test_result_includes_personal_metrics(self):
        service = RecruiterMetricsService()

        personal = _make_weekly_summary(backlog=5, avg_response=2.5, advanced=7)
        benchmark = {
            "benchmark_available": True,
            "recruiter_count": 2,
            "median_response_time_days": 2.0,
            "median_advanced_per_week": 5.0,
            "median_backlog_count": 3.0,
            "median_offers_pending": 1.0,
        }

        with patch.object(service, "get_weekly_summary", return_value=personal), \
             patch.object(service, "get_company_benchmark", return_value=benchmark):
            result = await service.get_recruiter_benchmark_comparison("rec-1", "company-1")

        assert result["personal"]["backlog_count"] == 5
        assert result["personal"]["avg_response_time_days"] == 2.5
        assert result["recruiter_id"] == "rec-1"
        assert result["company_id"] == "company-1"

    async def test_unknown_performance_when_benchmark_zero(self):
        service = RecruiterMetricsService()

        personal = _make_weekly_summary(avg_response=2.0, advanced=5)
        benchmark = {
            "benchmark_available": True,
            "recruiter_count": 2,
            "median_response_time_days": 0,  # edge: zero benchmark
            "median_advanced_per_week": 0,
            "median_backlog_count": 0,
            "median_offers_pending": 0,
        }

        with patch.object(service, "get_weekly_summary", return_value=personal), \
             patch.object(service, "get_company_benchmark", return_value=benchmark):
            result = await service.get_recruiter_benchmark_comparison("rec-1", "company-1")

        # Zero benchmark → unknown comparison (avoid division by zero)
        for cmp in result["comparison"].values():
            assert cmp["performance"] == "unknown"


# ---------------------------------------------------------------------------
# TestSingleton
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_singleton_exists(self):
        assert recruiter_metrics_service is not None

    def test_has_benchmark_methods(self):
        assert hasattr(recruiter_metrics_service, "get_company_benchmark")
        assert hasattr(recruiter_metrics_service, "get_recruiter_benchmark_comparison")
