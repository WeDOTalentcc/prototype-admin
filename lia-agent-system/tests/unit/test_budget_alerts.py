"""
R-022: Tests for budget_alert_service — graceful degradation and Sentry dispatch.
"""
import sys
import pytest
from unittest.mock import patch


class TestBudgetAlertService:
    @pytest.mark.asyncio
    async def test_does_not_raise_on_sentry_failure(self):
        """Alert is fire-and-forget — must never propagate exceptions."""
        with patch("sentry_sdk.capture_message", side_effect=RuntimeError("sentry down")):
            from app.domains.credits.services.budget_alert_service import send_budget_alert
            # Should complete without raising
            await send_budget_alert("test-co", 80, 800, 1000, "starter")

    @pytest.mark.asyncio
    async def test_80pct_uses_warning_level(self):
        """80% threshold maps to Sentry warning level and correct alert_type tag."""
        captured = []
        with patch("sentry_sdk.capture_message", side_effect=lambda *a, **kw: captured.append((a, kw))):
            import importlib
            import app.domains.credits.services.budget_alert_service as mod
            importlib.reload(mod)
            await mod.send_budget_alert("acme", 80, 800, 1000, "pro")
        assert len(captured) == 1, "Expected exactly one Sentry capture"
        _, kw = captured[0]
        assert kw["level"] == "warning"
        assert kw["tags"]["alert_type"] == "token_budget_80pct"
        assert kw["tags"]["company_id"] == "acme"
        assert kw["tags"]["plan_code"] == "pro"

    @pytest.mark.asyncio
    async def test_100pct_uses_error_level(self):
        """100% breach maps to Sentry error level."""
        captured = []
        with patch("sentry_sdk.capture_message", side_effect=lambda *a, **kw: captured.append((a, kw))):
            from app.domains.credits.services.budget_alert_service import send_budget_alert
            await send_budget_alert("acme", 100, 1000, 1000, "starter")
        assert len(captured) == 1
        _, kw = captured[0]
        assert kw["level"] == "error"
        assert kw["tags"]["alert_type"] == "token_budget_100pct"

    @pytest.mark.asyncio
    async def test_no_sentry_sdk_falls_through(self):
        """If sentry_sdk not importable, service still completes without raising."""
        with patch.dict(sys.modules, {"sentry_sdk": None}):
            import importlib
            import app.domains.credits.services.budget_alert_service as mod
            importlib.reload(mod)
            # Should not raise even with sentry_sdk unavailable
            await mod.send_budget_alert("co", 80, 80, 100, None)

    @pytest.mark.asyncio
    async def test_plan_code_none_uses_unknown(self):
        """None plan_code is safely coerced to 'unknown' in Sentry tags."""
        captured = []
        with patch("sentry_sdk.capture_message", side_effect=lambda *a, **kw: captured.append((a, kw))):
            from app.domains.credits.services.budget_alert_service import send_budget_alert
            await send_budget_alert("co", 80, 80, 100, None)
        assert captured[0][1]["tags"]["plan_code"] == "unknown"
