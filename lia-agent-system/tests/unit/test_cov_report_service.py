"""Coverage tests for report_service.py — DemoDataGenerator pure methods."""
import random
import pytest

from app.domains.analytics.services.report_service import DemoDataGenerator


@pytest.fixture
def gen():
    return DemoDataGenerator()


class TestDemoDataGeneratorSeeds:
    def test_weekly_seed_returns_int(self, gen):
        seed = gen._weekly_seed()
        assert isinstance(seed, int)
        assert seed > 0

    def test_monthly_seed_returns_int(self, gen):
        seed = gen._monthly_seed()
        assert isinstance(seed, int)
        assert seed > 0

    def test_daily_seed_returns_int(self, gen):
        seed = gen._daily_seed()
        assert isinstance(seed, int)
        assert seed > 0

    def test_rng_returns_random(self, gen):
        rng = gen._rng(42)
        assert isinstance(rng, random.Random)

    def test_rng_deterministic(self, gen):
        r1 = gen._rng(42).random()
        r2 = gen._rng(42).random()
        assert r1 == r2


class TestPickNames:
    def test_returns_list(self, gen):
        rng = gen._rng(42)
        result = gen._pick_names(rng, 3)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_names_are_strings(self, gen):
        rng = gen._rng(42)
        result = gen._pick_names(rng, 2)
        for name in result:
            assert isinstance(name, str)
            assert " " in name  # first + last

    def test_count_larger_than_pool_clamped(self, gen):
        rng = gen._rng(42)
        result = gen._pick_names(rng, 999)
        assert len(result) <= len(gen.FIRST_NAMES)


class TestTrendHelpers:
    def test_trend_direction_returns_up_or_down(self, gen):
        rng = gen._rng(42)
        result = gen._trend_direction(rng, 0.6)
        assert result in ("up", "down")

    def test_trend_pct_up_positive(self, gen):
        rng = gen._rng(42)
        # Force "up" direction
        val = gen._trend_pct(rng, "up")
        assert val > 0

    def test_trend_pct_down_negative(self, gen):
        rng = gen._rng(42)
        val = gen._trend_pct(rng, "down")
        assert val < 0

    def test_trend_pct_within_range(self, gen):
        rng = gen._rng(42)
        val = abs(gen._trend_pct(rng, "up", 5.0, 10.0))
        assert 5.0 <= val <= 10.0


class TestWeeklyKpis:
    def test_returns_list_of_four(self, gen):
        result = gen.weekly_kpis()
        assert isinstance(result, list)
        assert len(result) == 4

    def test_kpi_structure(self, gen):
        kpis = gen.weekly_kpis()
        for kpi in kpis:
            assert "name" in kpi
            assert "value" in kpi
            assert "trend" in kpi
            assert kpi["trend"] in ("up", "down")

    def test_deterministic_across_calls(self, gen):
        kpis1 = gen.weekly_kpis()
        kpis2 = gen.weekly_kpis()
        assert kpis1[0]["value"] == kpis2[0]["value"]


class TestFunnelData:
    def test_returns_dict(self, gen):
        result = gen.funnel_data()
        assert isinstance(result, dict)

    def test_has_stages(self, gen):
        result = gen.funnel_data()
        assert "stages" in result or len(result) > 0

    def test_deterministic(self, gen):
        r1 = gen.funnel_data()
        r2 = gen.funnel_data()
        assert r1 == r2


class TestRecruiterRanking:
    def test_returns_list(self, gen):
        result = gen.recruiter_ranking()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_each_entry_has_required_fields(self, gen):
        ranking = gen.recruiter_ranking()
        for entry in ranking:
            assert "recruiter_name" in entry  # actual field name
            assert "positions_filled" in entry


class TestChannelPerformance:
    def test_returns_list(self, gen):
        result = gen.channel_performance()
        assert isinstance(result, list)
        assert len(result) > 0


class TestStrategicKpis:
    def test_returns_list(self, gen):
        result = gen.strategic_kpis()
        assert isinstance(result, list)


class TestDailySample:
    def test_returns_dict(self, gen):
        result = gen.daily_sample("Recruiter", "ACME Corp")
        assert isinstance(result, dict)
        assert len(result) > 0


class TestExecutiveSummary:
    def test_returns_dict(self, gen):
        result = gen.executive_summary()
        assert isinstance(result, dict)


class TestDepartmentBreakdown:
    def test_returns_list(self, gen):
        result = gen.department_breakdown()
        assert isinstance(result, list)
        assert len(result) > 0


class TestPredictions:
    def test_returns_list(self, gen):
        result = gen.predictions()
        assert isinstance(result, list)
        assert len(result) > 0
