"""UC-P1-08: Token budget 80% alert fires when usage crosses threshold."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_alert_fires_at_80_percent():
    """When usage hits 80% of limit, a Sentry warning is captured."""
    company_id = "company-test-80"
    plan_code = "pro"  # limit = 100_000

    mock_redis = AsyncMock()
    mock_redis.incrby = AsyncMock(return_value=80_100)  # 80.1%
    mock_redis.expire = AsyncMock()
    mock_redis.aclose = AsyncMock()

    sentry_calls = []

    with (
        patch(
            'app.domains.credits.services.token_budget_service._get_redis',
            return_value=mock_redis,
        ),
        patch(
            'app.domains.credits.services.token_budget_service.get_plan_for_company',
            new=AsyncMock(return_value=plan_code),
        ),
        patch('sentry_sdk.capture_message', side_effect=lambda *a, **kw: sentry_calls.append((a, kw))),
    ):
        from app.domains.credits.services.token_budget_service import increment_usage
        result = await increment_usage(company_id, 500)

    assert result == 80_100
    assert len(sentry_calls) == 1, f"Expected 1 Sentry call, got {sentry_calls}"
    assert 'token_budget_80pct' in str(sentry_calls[0])


@pytest.mark.asyncio
async def test_no_alert_below_80_percent():
    """No alert fired when usage < 80%."""
    company_id = "company-test-low"
    plan_code = "pro"  # limit = 100_000

    mock_redis = AsyncMock()
    mock_redis.incrby = AsyncMock(return_value=50_000)  # 50%
    mock_redis.expire = AsyncMock()
    mock_redis.aclose = AsyncMock()

    sentry_calls = []

    with (
        patch(
            'app.domains.credits.services.token_budget_service._get_redis',
            return_value=mock_redis,
        ),
        patch(
            'app.domains.credits.services.token_budget_service.get_plan_for_company',
            new=AsyncMock(return_value=plan_code),
        ),
        patch('sentry_sdk.capture_message', side_effect=lambda *a, **kw: sentry_calls.append((a, kw))),
    ):
        from app.domains.credits.services.token_budget_service import increment_usage
        result = await increment_usage(company_id, 500)

    assert result == 50_000
    assert sentry_calls == [], f"Unexpected Sentry call: {sentry_calls}"


@pytest.mark.asyncio
async def test_no_alert_unlimited_plan():
    """No alert for enterprise/unlimited plans (limit=-1)."""
    company_id = "company-enterprise"
    plan_code = "enterprise"  # limit = -1

    mock_redis = AsyncMock()
    mock_redis.incrby = AsyncMock(return_value=999_999)
    mock_redis.expire = AsyncMock()
    mock_redis.aclose = AsyncMock()

    sentry_calls = []

    with (
        patch(
            'app.domains.credits.services.token_budget_service._get_redis',
            return_value=mock_redis,
        ),
        patch(
            'app.domains.credits.services.token_budget_service.get_plan_for_company',
            new=AsyncMock(return_value=plan_code),
        ),
        patch('sentry_sdk.capture_message', side_effect=lambda *a, **kw: sentry_calls.append((a, kw))),
    ):
        from app.domains.credits.services.token_budget_service import increment_usage
        result = await increment_usage(company_id, 1000)

    assert result == 999_999
    assert sentry_calls == [], f"Unexpected Sentry call for unlimited plan: {sentry_calls}"


@pytest.mark.asyncio
async def test_alert_fires_exactly_at_80_percent():
    """Alert fires exactly at 80% boundary (new_total == 80% of limit)."""
    company_id = "company-exact-80"
    plan_code = "starter"  # limit = 10_000

    mock_redis = AsyncMock()
    mock_redis.incrby = AsyncMock(return_value=8_000)  # exactly 80%
    mock_redis.expire = AsyncMock()
    mock_redis.aclose = AsyncMock()

    sentry_calls = []

    with (
        patch(
            'app.domains.credits.services.token_budget_service._get_redis',
            return_value=mock_redis,
        ),
        patch(
            'app.domains.credits.services.token_budget_service.get_plan_for_company',
            new=AsyncMock(return_value=plan_code),
        ),
        patch('sentry_sdk.capture_message', side_effect=lambda *a, **kw: sentry_calls.append((a, kw))),
    ):
        from app.domains.credits.services.token_budget_service import increment_usage
        result = await increment_usage(company_id, 100)

    assert result == 8_000
    assert len(sentry_calls) == 1, f"Expected alert at 80%, got: {sentry_calls}"
