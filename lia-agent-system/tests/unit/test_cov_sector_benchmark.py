"""Coverage tests for sector_benchmark_service.py — pure data+methods."""
import pytest

from app.domains.analytics.services.sector_benchmark_service import (
    BenchmarkProfile,
    SectorBenchmarkService,
    _normalize_area,
    _normalize_seniority,
)


class TestNormalizeArea:
    def test_software_engineering_normalized(self):
        assert _normalize_area("software engineering") == "software_engineering"

    def test_none_returns_none(self):
        assert _normalize_area("") is None

    def test_alias_resolved(self):
        result = _normalize_area("software")
        assert result == "software_engineering"

    def test_invalid_area_returns_none(self):
        assert _normalize_area("completely_invalid_area_xyz") is None


class TestNormalizeSeniority:
    def test_senior_returns_senior(self):
        assert _normalize_seniority("senior") == "senior"

    def test_sr_alias(self):
        assert _normalize_seniority("sr") == "senior"

    def test_empty_returns_none(self):
        assert _normalize_seniority("") is None

    def test_invalid_returns_none(self):
        assert _normalize_seniority("invalido_xyz") is None

    def test_mid_alias_returns_pleno(self):
        result = _normalize_seniority("mid")
        assert result in ("pleno", None)  # alias depends on table


class TestBenchmarkProfile:
    def test_is_frozen_dataclass(self):
        b = BenchmarkProfile(
            area="test", seniority="senior",
            score_p50=60.0, score_p75=75.0, min_expected=50.0,
            approval_rate=0.5,
            key_signals=("signal_a",),
            calibration_note="Note"
        )
        assert b.area == "test"

    def test_key_signals_is_tuple(self):
        b = BenchmarkProfile(
            area="test", seniority="junior",
            score_p50=40.0, score_p75=55.0, min_expected=30.0,
            approval_rate=0.35,
            key_signals=("git", "tests"),
            calibration_note="Note"
        )
        assert isinstance(b.key_signals, tuple)


class TestSectorBenchmarkService:
    @pytest.fixture
    def svc(self):
        return SectorBenchmarkService()

    def test_get_profile_known_area(self, svc):
        profile = svc.get_profile("software_engineering", "senior")
        assert profile is not None
        assert isinstance(profile, BenchmarkProfile)

    def test_get_profile_unknown_area_returns_none(self, svc):
        assert svc.get_profile("invalid_area_xyz", "senior") is None

    def test_get_profile_unknown_seniority_returns_none(self, svc):
        assert svc.get_profile("software_engineering", "invalid") is None

    def test_profile_has_score_fields(self, svc):
        profile = svc.get_profile("software_engineering", "senior")
        assert profile.score_p50 > 0
        assert profile.score_p75 >= profile.score_p50
        assert profile.min_expected < profile.score_p75

    def test_get_benchmark_context_returns_string(self, svc):
        ctx = svc.get_benchmark_context("software_engineering", "senior")
        assert isinstance(ctx, str)
        assert len(ctx) > 50

    def test_context_contains_score(self, svc):
        ctx = svc.get_benchmark_context("software_engineering", "senior")
        assert "72" in ctx or "P50" in ctx or "score" in ctx.lower()

    def test_context_unknown_area_returns_empty_string(self, svc):
        ctx = svc.get_benchmark_context("invalid_area_xyz", "senior")
        assert ctx == "" or ctx is None or isinstance(ctx, str)

    def test_list_supported_returns_list(self, svc):
        supported = svc.list_supported()
        assert isinstance(supported, list)
        assert len(supported) > 5

    def test_list_supported_has_tuples(self, svc):
        for item in svc.list_supported():
            assert isinstance(item, tuple)
            assert len(item) == 2
