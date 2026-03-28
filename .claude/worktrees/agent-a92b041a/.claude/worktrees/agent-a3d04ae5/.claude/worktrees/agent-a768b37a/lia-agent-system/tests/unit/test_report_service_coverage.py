"""
Unit tests for app.domains.analytics.services.report_service
Covers DemoDataGenerator pure methods without DB.
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List


class TestDemoDataGenerator:
    """Tests for DemoDataGenerator — pure deterministic methods."""

    def setup_method(self):
        from app.domains.analytics.services.report_service import DemoDataGenerator
        self.gen = DemoDataGenerator()

    def test_weekly_seed_is_int(self):
        seed = self.gen._weekly_seed()
        assert isinstance(seed, int)
        assert seed > 0

    def test_monthly_seed_is_int(self):
        seed = self.gen._monthly_seed()
        assert isinstance(seed, int)
        assert seed > 0

    def test_daily_seed_is_int(self):
        seed = self.gen._daily_seed()
        assert isinstance(seed, int)
        assert seed > 0

    def test_rng_produces_deterministic_results(self):
        r1 = self.gen._rng(42)
        r2 = self.gen._rng(42)
        assert r1.random() == r2.random()

    def test_pick_names_count(self):
        import random
        rng = random.Random(99)
        names = self.gen._pick_names(rng, 4)
        assert len(names) == 4
        for name in names:
            assert " " in name  # First Last format

    def test_pick_names_less_than_available(self):
        import random
        rng = random.Random(42)
        names = self.gen._pick_names(rng, 2)
        assert len(names) == 2

    def test_trend_direction_up_with_high_bias(self):
        import random
        # With bias_up=1.0, always "up"
        rng = random.Random(0)
        results = {self.gen._trend_direction(random.Random(i), bias_up=1.0) for i in range(20)}
        assert results == {"up"}

    def test_trend_direction_down_with_zero_bias(self):
        import random
        results = {self.gen._trend_direction(random.Random(i), bias_up=0.0) for i in range(20)}
        assert results == {"down"}

    def test_trend_pct_up_is_positive(self):
        import random
        rng = random.Random(1)
        pct = self.gen._trend_pct(rng, "up")
        assert pct > 0

    def test_trend_pct_down_is_negative(self):
        import random
        rng = random.Random(1)
        pct = self.gen._trend_pct(rng, "down")
        assert pct < 0

    def test_weekly_kpis_structure(self):
        kpis = self.gen.weekly_kpis()
        assert len(kpis) == 4
        names = [k["name"] for k in kpis]
        assert "Contratações" in names
        assert "Candidatos" in names

    def test_weekly_kpis_has_trend(self):
        kpis = self.gen.weekly_kpis()
        for kpi in kpis:
            assert kpi["trend"] in ("up", "down")
            assert "trend_percentage" in kpi

    def test_funnel_data_structure(self):
        funnel = self.gen.funnel_data()
        assert "stages" in funnel
        assert "total_candidates" in funnel
        assert "overall_conversion_rate" in funnel

    def test_funnel_data_stages_count(self):
        funnel = self.gen.funnel_data()
        assert len(funnel["stages"]) == 5

    def test_funnel_data_stage_names(self):
        funnel = self.gen.funnel_data()
        stage_names = [s["stage_name"] for s in funnel["stages"]]
        assert "Candidaturas" in stage_names
        assert "Contratado" in stage_names

    def test_funnel_data_total_candidates_positive(self):
        funnel = self.gen.funnel_data()
        assert funnel["total_candidates"] > 0

    def test_recruiter_ranking_structure(self):
        ranking = self.gen.recruiter_ranking()
        assert len(ranking) >= 4
        for r in ranking:
            assert "recruiter_name" in r
            assert "positions_filled" in r
            assert "quality_score" in r

    def test_recruiter_ranking_sorted_by_positions(self):
        ranking = self.gen.recruiter_ranking()
        filled = [r["positions_filled"] for r in ranking]
        assert filled == sorted(filled, reverse=True)

    def test_channel_performance_structure(self):
        channels = self.gen.channel_performance()
        assert len(channels) == 6  # matches CHANNELS constant
        for ch in channels:
            assert "channel_name" in ch
            assert "candidates_count" in ch
            assert "conversion_rate" in ch
            assert "cost_per_hire" in ch

    def test_strategic_kpis_structure(self):
        kpis = self.gen.strategic_kpis()
        assert len(kpis) >= 4
        kpi_names = [k["name"] for k in kpis]
        assert any("Contratações" in n for n in kpi_names)

    def test_determinism_same_week(self):
        """Same seed → same results."""
        kpis1 = self.gen.weekly_kpis()
        kpis2 = self.gen.weekly_kpis()
        assert kpis1 == kpis2

    def test_determinism_same_month(self):
        kpis1 = self.gen.strategic_kpis()
        kpis2 = self.gen.strategic_kpis()
        assert kpis1 == kpis2


class TestReportServiceImport:
    """Verify ReportService and related imports work."""

    def test_report_service_importable(self):
        from app.domains.analytics.services.report_service import ReportService
        assert ReportService is not None

    def test_demo_data_generator_importable(self):
        from app.domains.analytics.services.report_service import DemoDataGenerator
        assert DemoDataGenerator is not None

    def test_constants_available(self):
        from app.domains.analytics.services.report_service import DemoDataGenerator
        gen = DemoDataGenerator()
        assert len(gen.FIRST_NAMES) > 0
        assert len(gen.LAST_NAMES) > 0
        assert len(gen.DEPARTMENTS) > 0
        assert len(gen.CHANNELS) > 0
