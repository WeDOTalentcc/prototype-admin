"""Tests for max_agents_total alias canonical (Sprint 7C / 7B-3b backlog).

Validates get_max_agents_total + get_current_agents_total functions sum
the 4 canonical agent categories (sourcing/custom/digital_twins/campaigns)
preserving the dict structure (no breaking refactor) and the -1 semantic
(any unlimited propagates to -1 total).
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.quota_enforcement import (
    PLAN_AGENT_QUOTAS,
    get_current_agents_total,
    get_max_agents_total,
)


def test_get_max_agents_total_starter_sums_four_categories():
    # starter: custom=2 + sourcing=1 + digital_twins=0 + campaigns=1 = 4
    assert get_max_agents_total("starter") == 4


def test_get_max_agents_total_enterprise_propagates_unlimited():
    # enterprise: any -1 → -1 result
    assert get_max_agents_total("enterprise") == -1


def test_get_max_agents_total_unknown_plan_returns_zero():
    assert get_max_agents_total("plano-inexistente") == 0


def test_get_max_agents_total_pro_sums_correctly():
    # pro: 10 + 5 + 3 + 5 = 23
    assert get_max_agents_total("pro") == 23


def test_plan_agent_quotas_preserves_four_categories():
    """Sensor: garante que ninguém removeu uma categoria do dict canonical."""
    for plan in ("starter", "pro", "business", "enterprise"):
        quota = PLAN_AGENT_QUOTAS[plan]
        assert "sourcing_agents" in quota
        assert "custom_agents" in quota
        assert "digital_twins" in quota
        assert "campaigns" in quota


@pytest.mark.asyncio
async def test_get_current_agents_total_sums_four_categories(monkeypatch):
    """Mock get_current_count per resource, assert soma das 4."""
    from app.services import quota_enforcement as qe

    calls = []

    async def fake_get_current_count(resource_key, company_id, db):
        calls.append(resource_key)
        return {"custom_agents": 3, "sourcing_agents": 2, "digital_twins": 1, "campaigns": 4}[resource_key]

    monkeypatch.setattr(qe, "get_current_count", fake_get_current_count)
    db = MagicMock()
    total = await get_current_agents_total("00000000-0000-0000-0000-000000000001", db)
    assert total == 10
    assert sorted(calls) == sorted(
        ["custom_agents", "sourcing_agents", "digital_twins", "campaigns"]
    )
