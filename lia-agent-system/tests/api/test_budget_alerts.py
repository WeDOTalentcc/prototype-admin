"""Onda 4 B3 — /ai-consumption/budget-alerts endpoint contract tests.

Alertas com severity (info/warning/critical) baseado em used_pct (50/80/95).
Plus per-agent alerts quando agente consumiu > 20% do limite global.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return AsyncMock()


def _fake_balance(
    monthly_limit: int = 100000,
    current_usage: int = 0,
    period_start: date | None = None,
    period_end: date | None = None,
):
    b = MagicMock()
    b.monthly_limit = monthly_limit
    b.current_usage = current_usage
    today = date.today()
    b.period_start = period_start or today.replace(day=1)
    if today.month == 12:
        b.period_end = period_end or today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        b.period_end = period_end or today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    return b


def _setup_db(mock_db, balance, current_tokens, per_agent_rows=None):
    """Mock execute sequence for budget alerts:
    1) get balance -> scalar_one_or_none
    Quando balance is None: param-skip (sem mais queries).
    Caso contrário:
    2) sum current usage tokens -> scalar
    3) per-agent rows -> .all()
    """
    balance_result = MagicMock()
    balance_result.scalar_one_or_none = MagicMock(return_value=balance)

    if balance is None:
        mock_db.execute = AsyncMock(return_value=balance_result)
        return

    usage_result = MagicMock()
    usage_result.scalar = MagicMock(return_value=current_tokens)

    per_agent_result = MagicMock()
    per_agent_result.all = MagicMock(return_value=per_agent_rows or [])

    mock_db.execute = AsyncMock(side_effect=[balance_result, usage_result, per_agent_result])


# ────────────────────────────────────────────────────────────────────────────
# B3.1 — Sem balance row → alerts vazio (sem erro)
# ────────────────────────────────────────────────────────────────────────────

async def test_alerts_empty_when_no_balance(mock_db):
    from app.api.v1 import ai_consumption as ac

    _setup_db(mock_db, balance=None, current_tokens=0)

    result = await ac.get_budget_alerts(
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )

    assert result.alerts == []


# ────────────────────────────────────────────────────────────────────────────
# B3.2 — 60% usage → info alert global
# ────────────────────────────────────────────────────────────────────────────

async def test_alerts_60pct_emits_info(mock_db):
    from app.api.v1 import ai_consumption as ac

    balance = _fake_balance(monthly_limit=100000, current_usage=60000)
    _setup_db(mock_db, balance=balance, current_tokens=60000)

    result = await ac.get_budget_alerts(
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )

    global_alerts = [a for a in result.alerts if a.scope == "global"]
    assert len(global_alerts) == 1
    assert global_alerts[0].severity == "info"
    assert 0.59 <= global_alerts[0].used_pct <= 0.61


# ────────────────────────────────────────────────────────────────────────────
# B3.3 — 85% usage → warning alert
# ────────────────────────────────────────────────────────────────────────────

async def test_alerts_85pct_emits_warning(mock_db):
    from app.api.v1 import ai_consumption as ac

    balance = _fake_balance(monthly_limit=100000, current_usage=85000)
    _setup_db(mock_db, balance=balance, current_tokens=85000)

    result = await ac.get_budget_alerts(
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )

    global_alerts = [a for a in result.alerts if a.scope == "global"]
    assert len(global_alerts) == 1
    assert global_alerts[0].severity == "warning"


# ────────────────────────────────────────────────────────────────────────────
# B3.4 — 96% usage → critical
# ────────────────────────────────────────────────────────────────────────────

async def test_alerts_96pct_emits_critical(mock_db):
    from app.api.v1 import ai_consumption as ac

    balance = _fake_balance(monthly_limit=100000, current_usage=96000)
    _setup_db(mock_db, balance=balance, current_tokens=96000)

    result = await ac.get_budget_alerts(
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )

    global_alerts = [a for a in result.alerts if a.scope == "global"]
    assert len(global_alerts) == 1
    assert global_alerts[0].severity == "critical"


# ────────────────────────────────────────────────────────────────────────────
# B3.5 — Per-agent alert quando agente consumiu > 20% do limite
# ────────────────────────────────────────────────────────────────────────────

async def test_alerts_per_agent_when_gt_20pct(mock_db):
    from app.api.v1 import ai_consumption as ac

    balance = _fake_balance(monthly_limit=100000, current_usage=60000)
    # Per-agent row: agent X consumed 25000 tokens (25% do limit)
    agent_row = MagicMock()
    agent_row.studio_agent_id = str(uuid.uuid4())
    agent_row.agent_name = "Heavy Agent"
    agent_row.tokens = 25000
    agent_row.cost_cents = 250

    _setup_db(mock_db, balance=balance, current_tokens=60000, per_agent_rows=[agent_row])

    result = await ac.get_budget_alerts(
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )

    per_agent_alerts = [a for a in result.alerts if a.scope == "agent"]
    assert len(per_agent_alerts) == 1
    assert per_agent_alerts[0].studio_agent_id == agent_row.studio_agent_id
    assert per_agent_alerts[0].agent_name == "Heavy Agent"
    assert per_agent_alerts[0].used_pct >= 0.20


# ────────────────────────────────────────────────────────────────────────────
# B3.6 — Below 50% threshold → nenhum alert global
# ────────────────────────────────────────────────────────────────────────────

async def test_alerts_below_50pct_no_global_alert(mock_db):
    from app.api.v1 import ai_consumption as ac

    balance = _fake_balance(monthly_limit=100000, current_usage=30000)
    _setup_db(mock_db, balance=balance, current_tokens=30000)

    result = await ac.get_budget_alerts(
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )

    global_alerts = [a for a in result.alerts if a.scope == "global"]
    assert global_alerts == []
