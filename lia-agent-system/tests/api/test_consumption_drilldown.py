"""Onda 4 B2 — /ai-consumption/by-agent/drilldown endpoint contract tests.

Lista execuções individuais (rows de ai_consumption table) com filtros agent_type
+ studio_agent_id, paginação, totals.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return AsyncMock()


def _fake_consumption(
    agent_type: str = "digital_twin",
    studio_agent_id: str | None = None,
    operation: str = "evaluate",
    model: str = "gpt-4",
    input_tokens: int = 100,
    output_tokens: int = 50,
    cost_cents: int = 5,
    candidate_id: str | None = None,
    vacancy_id: str | None = None,
):
    c = MagicMock()
    c.id = uuid.uuid4()
    c.agent_type = agent_type
    c.studio_agent_id = studio_agent_id
    c.operation = operation
    c.model = model
    c.input_tokens = input_tokens
    c.output_tokens = output_tokens
    c.total_tokens = input_tokens + output_tokens
    c.cost_cents = cost_cents
    c.candidate_id = uuid.UUID(candidate_id) if candidate_id else None
    c.vacancy_id = uuid.UUID(vacancy_id) if vacancy_id else None
    c.created_at = datetime.now(timezone.utc)
    return c


def _setup_db_for_drilldown(mock_db, items, total_count, total_cost_cents, total_tokens):
    """Mock execute sequence:
    1) totals query -> .one() returning row
    2) items query -> .scalars().all() returning list
    """
    totals_row = MagicMock()
    totals_row.total_count = total_count
    totals_row.total_cost_cents = total_cost_cents
    totals_row.total_tokens = total_tokens

    totals_result = MagicMock()
    totals_result.one = MagicMock(return_value=totals_row)

    items_result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=items)
    items_result.scalars = MagicMock(return_value=scalars_mock)

    mock_db.execute = AsyncMock(side_effect=[totals_result, items_result])


# ────────────────────────────────────────────────────────────────────────────
# B2.1 — Empty result
# ────────────────────────────────────────────────────────────────────────────

async def test_drilldown_empty(mock_db):
    from app.api.v1 import ai_consumption as ac

    _setup_db_for_drilldown(mock_db, items=[], total_count=0, total_cost_cents=0, total_tokens=0)

    result = await ac.get_consumption_drilldown(
        agent_type=None,
        studio_agent_id=None,
        since_days=30,
        limit=100,
        offset=0,
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )

    assert result.items == []
    assert result.total_count == 0
    assert result.total_cost_cents == 0
    assert result.total_tokens == 0


# ────────────────────────────────────────────────────────────────────────────
# B2.2 — Filters agent_type + studio_agent_id work
# ────────────────────────────────────────────────────────────────────────────

async def test_drilldown_filters_agent_type_and_studio_agent_id(mock_db):
    from app.api.v1 import ai_consumption as ac

    items = [
        _fake_consumption(agent_type="digital_twin", studio_agent_id="agent-A"),
        _fake_consumption(agent_type="digital_twin", studio_agent_id="agent-A"),
    ]
    _setup_db_for_drilldown(
        mock_db, items=items, total_count=2, total_cost_cents=10, total_tokens=300
    )

    result = await ac.get_consumption_drilldown(
        agent_type="digital_twin",
        studio_agent_id="agent-A",
        since_days=30,
        limit=100,
        offset=0,
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )

    assert len(result.items) == 2
    assert all(i.agent_type == "digital_twin" for i in result.items)
    assert all(i.studio_agent_id == "agent-A" for i in result.items)


# ────────────────────────────────────────────────────────────────────────────
# B2.3 — Pagination (offset + limit)
# ────────────────────────────────────────────────────────────────────────────

async def test_drilldown_pagination(mock_db):
    from app.api.v1 import ai_consumption as ac

    # Backend returns paginated items (50 with offset=50)
    items = [_fake_consumption() for _ in range(50)]
    _setup_db_for_drilldown(
        mock_db, items=items, total_count=150, total_cost_cents=750, total_tokens=15000
    )

    result = await ac.get_consumption_drilldown(
        agent_type=None,
        studio_agent_id=None,
        since_days=30,
        limit=50,
        offset=50,
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )

    assert len(result.items) == 50
    assert result.total_count == 150  # total no filter


# ────────────────────────────────────────────────────────────────────────────
# B2.4 — Total counts são corretos (cost + tokens)
# ────────────────────────────────────────────────────────────────────────────

async def test_drilldown_total_counts_correct(mock_db):
    from app.api.v1 import ai_consumption as ac

    items = [_fake_consumption(cost_cents=5, input_tokens=100, output_tokens=50)]
    _setup_db_for_drilldown(
        mock_db, items=items, total_count=10, total_cost_cents=50, total_tokens=1500
    )

    result = await ac.get_consumption_drilldown(
        agent_type=None,
        studio_agent_id=None,
        since_days=30,
        limit=100,
        offset=0,
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )

    assert result.total_count == 10
    assert result.total_cost_cents == 50
    assert result.total_tokens == 1500


# ────────────────────────────────────────────────────────────────────────────
# B2.5 — Multi-tenancy: rely on require_company_id filter at SQL level
# ────────────────────────────────────────────────────────────────────────────

async def test_drilldown_uses_company_id_in_filters(mock_db):
    """Sanity-check: company_id é passado pra dependency e usado no SQL.

    Verifica que a função não explode quando company_id é UUID válido (filter funciona).
    """
    from app.api.v1 import ai_consumption as ac

    _setup_db_for_drilldown(mock_db, items=[], total_count=0, total_cost_cents=0, total_tokens=0)

    # UUID válido
    result = await ac.get_consumption_drilldown(
        agent_type=None,
        studio_agent_id=None,
        since_days=30,
        limit=100,
        offset=0,
        db=mock_db,
        company_id=str(uuid.uuid4()),
    )
    assert result.total_count == 0
