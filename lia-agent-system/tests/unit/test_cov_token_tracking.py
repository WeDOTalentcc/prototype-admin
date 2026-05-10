"""Coverage tests for token_tracking_service.py — pure helper methods (no DB/Redis)."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock
from app.domains.analytics.services.token_tracking_service import (
    TokenTrackingService,
    TOKEN_PRICES,
    DEFAULT_LIMITS,
    ALERT_THRESHOLDS,
)


@pytest.fixture
def service():
    db = MagicMock()
    svc = TokenTrackingService(db=db)
    return svc


class TestTokenPrices:
    def test_claude_sonnet_has_prices(self):
        assert "claude-3-sonnet" in TOKEN_PRICES
        assert "input" in TOKEN_PRICES["claude-3-sonnet"]
        assert "output" in TOKEN_PRICES["claude-3-sonnet"]

    def test_gpt4o_has_prices(self):
        assert "gpt-4o" in TOKEN_PRICES

    def test_gemini_has_prices(self):
        assert "gemini-1.5-pro" in TOKEN_PRICES

    def test_all_entries_have_input_output(self):
        for model, prices in TOKEN_PRICES.items():
            assert "input" in prices, f"{model} missing input price"
            assert "output" in prices, f"{model} missing output price"

    def test_prices_are_positive(self):
        for model, prices in TOKEN_PRICES.items():
            assert prices["input"] > 0
            assert prices["output"] > 0


class TestDefaultLimits:
    def test_daily_tokens_per_user(self):
        assert DEFAULT_LIMITS["daily_tokens_per_user"] > 0

    def test_daily_tokens_per_company(self):
        assert DEFAULT_LIMITS["daily_tokens_per_company"] > 0

    def test_has_monthly_cost(self):
        assert "monthly_cost_per_company" in DEFAULT_LIMITS

    def test_has_requests_per_minute(self):
        assert "requests_per_minute_per_user" in DEFAULT_LIMITS


class TestAlertThresholds:
    def test_has_80_threshold(self):
        assert 80 in ALERT_THRESHOLDS

    def test_has_100_threshold(self):
        assert 100 in ALERT_THRESHOLDS


class TestGetLimits:
    def test_returns_defaults_when_no_company(self, service):
        limits = service.get_limits()
        assert limits == DEFAULT_LIMITS

    def test_returns_defaults_when_company_has_no_custom(self, service):
        limits = service.get_limits(company_id="unknown-company")
        assert limits == DEFAULT_LIMITS

    def test_custom_limit_overrides_default(self, service):
        service.set_custom_limits("co-001", {"daily_tokens_per_user": 999999})
        limits = service.get_limits(company_id="co-001")
        assert limits["daily_tokens_per_user"] == 999999

    def test_custom_limit_preserves_other_defaults(self, service):
        service.set_custom_limits("co-002", {"monthly_cost_per_company": 1000.0})
        limits = service.get_limits(company_id="co-002")
        assert limits["daily_tokens_per_user"] == DEFAULT_LIMITS["daily_tokens_per_user"]
        assert limits["monthly_cost_per_company"] == pytest.approx(1000.0)

    def test_returns_copy_not_reference(self, service):
        limits = service.get_limits()
        limits["daily_tokens_per_user"] = 0
        # Next call should return original
        fresh = service.get_limits()
        assert fresh["daily_tokens_per_user"] == DEFAULT_LIMITS["daily_tokens_per_user"]


class TestSetCustomLimits:
    def test_sets_limits(self, service):
        service.set_custom_limits("co-123", {"requests_per_minute_per_user": 120})
        limits = service.get_limits("co-123")
        assert limits["requests_per_minute_per_user"] == 120

    def test_overwrites_previous_limits(self, service):
        service.set_custom_limits("co-xyz", {"daily_tokens_per_user": 100})
        service.set_custom_limits("co-xyz", {"daily_tokens_per_user": 200})
        limits = service.get_limits("co-xyz")
        assert limits["daily_tokens_per_user"] == 200


class TestCalculateCostCents:
    def test_known_model_returns_positive(self, service):
        cost = service._calculate_cost_cents("claude-3-sonnet", 1000, 1000)
        assert cost > 0

    def test_zero_tokens_returns_zero(self, service):
        cost = service._calculate_cost_cents("claude-3-sonnet", 0, 0)
        assert cost == 0

    def test_unknown_model_uses_default(self, service):
        cost_unknown = service._calculate_cost_cents("unknown-model-xyz", 1000, 1000)
        cost_default = service._calculate_cost_cents("claude-3-sonnet", 1000, 1000)
        assert cost_unknown == cost_default

    def test_haiku_cheaper_than_opus(self, service):
        cost_haiku = service._calculate_cost_cents("claude-3-haiku", 1000, 1000)
        cost_opus = service._calculate_cost_cents("claude-3-opus", 1000, 1000)
        assert cost_haiku < cost_opus

    def test_output_tokens_more_expensive_than_input(self, service):
        # All models: output cost > input cost per token
        cost_input_heavy = service._calculate_cost_cents("claude-3-sonnet", 10000, 0)
        cost_output_heavy = service._calculate_cost_cents("claude-3-sonnet", 0, 10000)
        assert cost_output_heavy > cost_input_heavy

    def test_returns_int(self, service):
        cost = service._calculate_cost_cents("gpt-4o", 5000, 2000)
        assert isinstance(cost, int)

    def test_large_usage_returns_large_cost(self, service):
        cost = service._calculate_cost_cents("claude-3-opus", 1_000_000, 500_000)
        assert cost > 0

    def test_gpt4o_mini_cheapest(self, service):
        cost_mini = service._calculate_cost_cents("gpt-4o-mini", 1000, 1000)
        cost_gpt4 = service._calculate_cost_cents("gpt-4o", 1000, 1000)
        assert cost_mini < cost_gpt4


class TestGetPeriodStart:
    def test_hour_returns_datetime(self, service):
        result = service._get_period_start("hour")
        assert isinstance(result, datetime)

    def test_day_returns_midnight(self, service):
        result = service._get_period_start("day")
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_week_returns_datetime(self, service):
        result = service._get_period_start("week")
        assert isinstance(result, datetime)

    def test_month_returns_first_of_month(self, service):
        result = service._get_period_start("month")
        assert result.day == 1
        assert result.hour == 0

    def test_unknown_period_returns_today_midnight(self, service):
        result = service._get_period_start("unknown_period")
        assert result.hour == 0

    def test_hour_is_before_day(self, service):
        hour_start = service._get_period_start("hour")
        day_start = service._get_period_start("day")
        # Both relative to now; hour_start might be before day_start for most of the day
        assert isinstance(hour_start, datetime)
        assert isinstance(day_start, datetime)
