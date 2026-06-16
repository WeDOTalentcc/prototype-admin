"""Coverage tests for job_report_service.py — pure computation methods."""
import pytest
from unittest.mock import MagicMock, patch

from app.domains.analytics.services.job_report_service import JobReportService


@pytest.fixture
def svc():
    return JobReportService()


class TestCalculateConversionRates:
    def test_empty_total_returns_zeros(self, svc):
        result = svc._calculate_conversion_rates({}, 0)
        assert all(v == 0.0 for v in result.values())

    def test_zero_total_each_stage_is_zero(self, svc):
        funnel = {"sourcing": 100, "screening": 50}
        result = svc._calculate_conversion_rates(funnel, 0)
        assert result["sourcing"] == 0.0

    def test_full_funnel(self, svc):
        funnel = {
            "sourcing": 100,
            "screening": 50,
            "interview": 20,
            "offer": 5,
            "hired": 2,
        }
        result = svc._calculate_conversion_rates(funnel, 200)
        # sourcing: 100/200 = 50%
        assert result["sourcing"] == 50.0
        # screening: 50/100 = 50%
        assert result["screening"] == 50.0

    def test_missing_stages_default_to_zero(self, svc):
        result = svc._calculate_conversion_rates({}, 100)
        assert result["sourcing"] == 0.0
        assert result["hired"] == 0.0

    def test_returns_dict_with_all_stages(self, svc):
        result = svc._calculate_conversion_rates({"sourcing": 10}, 10)
        assert "sourcing" in result
        assert "screening" in result
        assert "interview" in result
        assert "offer" in result
        assert "hired" in result

    def test_100_percent_conversion(self, svc):
        funnel = {"sourcing": 100, "screening": 100, "interview": 100, "offer": 100, "hired": 100}
        result = svc._calculate_conversion_rates(funnel, 100)
        assert result["sourcing"] == 100.0


class TestJobReportServiceInit:
    def test_can_instantiate(self):
        svc = JobReportService()
        assert svc is not None

    def test_has_styles_after_init(self, svc):
        # _setup_custom_styles() called in __init__
        assert hasattr(svc, "styles")
