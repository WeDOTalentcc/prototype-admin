"""Tests for GET /api/v1/custom-agents/studio/quota/agents-total.

Canonical alias endpoint (Sprint 7C / 7B-3b backlog) que retorna soma das 4
categorias agent (sourcing + custom + digital_twins + campaigns) com shape
unified pra UI sidebar consumir como "X/Y agentes".

PRESERVA endpoint /studio/quota (4 categorias) e admin_external (-1 propagate).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_agents_total_endpoint_returns_canonical_shape(monkeypatch):
    """Response tem max_agents_total, current_agents_total, percentage."""
    from app.api.v1 import custom_agents as ca_module

    async def fake_get_effective_quotas(company_id, db):
        # pro: 10 + 5 + 3 + 5 = 23
        return {
            "custom_agents": 10,
            "sourcing_agents": 5,
            "digital_twins": 3,
            "campaigns": 5,
        }

    async def fake_get_current_agents_total(company_id, db):
        return 12

    monkeypatch.setattr(ca_module, "get_effective_quotas", fake_get_effective_quotas)
    monkeypatch.setattr(
        ca_module, "get_current_agents_total", fake_get_current_agents_total
    )

    user = MagicMock(company_id="00000000-0000-0000-0000-000000000001")
    db = MagicMock()
    result = await ca_module.get_studio_quota_agents_total(
        current_user=user, db=db, company_id=user.company_id
    )
    assert result["max_agents_total"] == 23
    assert result["current_agents_total"] == 12
    assert result["percentage_agents_total"] == pytest.approx(52.17, abs=0.1)
    assert result["is_unlimited"] is False


@pytest.mark.asyncio
async def test_agents_total_endpoint_unlimited_returns_zero_percentage(monkeypatch):
    """Enterprise (-1) retorna max=-1, percentage=0, is_unlimited=True."""
    from app.api.v1 import custom_agents as ca_module

    async def fake_get_effective_quotas(company_id, db):
        return {
            "custom_agents": -1,
            "sourcing_agents": -1,
            "digital_twins": -1,
            "campaigns": -1,
        }

    async def fake_get_current_agents_total(company_id, db):
        return 47

    monkeypatch.setattr(ca_module, "get_effective_quotas", fake_get_effective_quotas)
    monkeypatch.setattr(
        ca_module, "get_current_agents_total", fake_get_current_agents_total
    )

    user = MagicMock(company_id="00000000-0000-0000-0000-000000000002")
    db = MagicMock()
    result = await ca_module.get_studio_quota_agents_total(
        current_user=user, db=db, company_id=user.company_id
    )
    assert result["max_agents_total"] == -1
    assert result["current_agents_total"] == 47
    assert result["percentage_agents_total"] == 0.0
    assert result["is_unlimited"] is True
