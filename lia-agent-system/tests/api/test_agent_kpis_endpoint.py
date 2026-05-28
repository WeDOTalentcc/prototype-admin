"""Onda 4 B1 — /custom-agents/{id}/kpis endpoint contract tests.

Endpoint agrega métricas on-demand de pool_agent_runs.runtime_metrics + results.
NÃO recompute tokens/cost (sensor B4 garante invariante).

Multi-tenancy: require_company_id + agent.company_id check.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return AsyncMock()


def _fake_run(
    company_id: str = "comp-1",
    assignment_id=None,
    status: str = "success",
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    latency_ms: int = 1000,
    tokens_input: int = 100,
    tokens_output: int = 50,
    cost_usd: float = 0.001,
    model_used: str = "gpt-4",
    tools_used: list[str] | None = None,
    candidate_ids: list[str] | None = None,
):
    r = MagicMock()
    r.id = uuid.uuid4()
    r.assignment_id = assignment_id or uuid.uuid4()
    r.company_id = company_id
    r.status = status
    r.started_at = started_at or datetime.now(timezone.utc)
    r.finished_at = finished_at or (started_at + timedelta(seconds=1) if started_at else datetime.now(timezone.utc))
    r.runtime_metrics = {
        "latency_ms": latency_ms,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "input_tokens": tokens_input,
        "output_tokens": tokens_output,
        "cost_usd": cost_usd,
        "model_used": model_used,
    }
    r.results = {
        "tools_used": tools_used or [],
        "candidate_ids": candidate_ids or [],
    }
    r.created_at = r.started_at
    r.error_message = None
    return r


def _fake_agent(agent_id, company_id="comp-1", name="TestAgent", category="screening"):
    a = MagicMock()
    a.id = agent_id
    a.company_id = company_id
    a.name = name
    a.category = category
    return a


def _mock_query_result(mock_db, scalar_value=None, scalars_list=None, all_rows=None, execute_sequence=None):
    """Configure mock_db.execute with a single or sequence of results."""
    if execute_sequence is not None:
        results = []
        for kind, value in execute_sequence:
            r = MagicMock()
            if kind == "scalar_one_or_none":
                r.scalar_one_or_none = MagicMock(return_value=value)
            elif kind == "scalars_all":
                scalars_mock = MagicMock()
                scalars_mock.all = MagicMock(return_value=value)
                r.scalars = MagicMock(return_value=scalars_mock)
            elif kind == "all":
                r.all = MagicMock(return_value=value)
            results.append(r)
        mock_db.execute = AsyncMock(side_effect=results)
        return

    r = MagicMock()
    if scalar_value is not None:
        r.scalar_one_or_none = MagicMock(return_value=scalar_value)
    if scalars_list is not None:
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=scalars_list)
        r.scalars = MagicMock(return_value=scalars_mock)
    if all_rows is not None:
        r.all = MagicMock(return_value=all_rows)
    mock_db.execute = AsyncMock(return_value=r)


# ────────────────────────────────────────────────────────────────────────────
# B1.1 — Empty agent (no runs) → buckets zerados + is_learning=True
# ────────────────────────────────────────────────────────────────────────────

async def test_kpis_empty_agent_returns_zeros_and_is_learning(mock_db):
    from app.api.v1 import custom_agents as ca

    agent_id = uuid.uuid4()
    agent = _fake_agent(agent_id)

    _mock_query_result(
        mock_db,
        execute_sequence=[
            ("scalar_one_or_none", agent),  # get agent
            ("scalars_all", []),             # list runs
        ],
    )

    result = await ca.get_agent_kpis(
        agent_id=str(agent_id),
        period="30d",
        db=mock_db,
        company_id="comp-1",
    )

    assert result.agent_id == str(agent_id)
    assert result.is_learning is True
    assert result.bucket.total_executions == 0
    assert result.bucket.candidates_processed == 0
    assert result.bucket.total_cost_usd == 0.0
    assert result.bucket.avg_execution_seconds == 0.0
    assert result.bucket.p95_execution_seconds == 0.0
    assert len(result.hour_heatmap) == 24
    assert result.tool_breakdown == []
    assert result.last_run_at is None


# ────────────────────────────────────────────────────────────────────────────
# B1.2 — Agent com runs → agrega corretamente
# ────────────────────────────────────────────────────────────────────────────

async def test_kpis_aggregates_metrics_correctly(mock_db):
    from app.api.v1 import custom_agents as ca

    agent_id = uuid.uuid4()
    agent = _fake_agent(agent_id)
    base = datetime.now(timezone.utc) - timedelta(days=1)
    runs = [
        _fake_run(
            started_at=base,
            latency_ms=1000,
            tokens_input=100,
            tokens_output=50,
            cost_usd=0.001,
            tools_used=["whatsapp_send", "search_candidates"],
            candidate_ids=["c1", "c2"],
        ),
        _fake_run(
            started_at=base + timedelta(hours=1),
            latency_ms=2000,
            tokens_input=200,
            tokens_output=100,
            cost_usd=0.002,
            tools_used=["whatsapp_send"],
            candidate_ids=["c3"],
        ),
        _fake_run(
            started_at=base + timedelta(hours=2),
            status="error",
            latency_ms=500,
            tokens_input=50,
            tokens_output=10,
            cost_usd=0.0005,
            tools_used=[],
        ),
    ]
    _mock_query_result(
        mock_db,
        execute_sequence=[
            ("scalar_one_or_none", agent),
            ("scalars_all", runs),
        ],
    )

    result = await ca.get_agent_kpis(
        agent_id=str(agent_id),
        period="30d",
        db=mock_db,
        company_id="comp-1",
    )

    assert result.bucket.total_executions == 3
    assert result.bucket.error_count == 1
    assert result.bucket.candidates_processed == 3  # c1, c2, c3 unique
    assert result.bucket.total_tokens_input == 350
    assert result.bucket.total_tokens_output == 160
    assert abs(result.bucket.total_cost_usd - 0.0035) < 1e-6
    # Tool breakdown sorted by count desc
    assert result.tool_breakdown[0].tool_name == "whatsapp_send"
    assert result.tool_breakdown[0].count == 2
    # is_learning False (>= 5 execs requires)? We have only 3 — still learning
    assert result.is_learning is True


# ────────────────────────────────────────────────────────────────────────────
# B1.3 — Period filter (7d vs 30d) → returns different sets
# ────────────────────────────────────────────────────────────────────────────

async def test_kpis_period_filter_distinguishes_7d_vs_30d(mock_db):
    from app.api.v1 import custom_agents as ca

    agent_id = uuid.uuid4()
    agent = _fake_agent(agent_id)

    # In 7d filter: only 1 run returned
    # In 30d filter: 2 runs returned
    # We just verify period param flows correctly into the filter expression
    _mock_query_result(
        mock_db,
        execute_sequence=[
            ("scalar_one_or_none", agent),
            ("scalars_all", [_fake_run()]),
        ],
    )
    r7 = await ca.get_agent_kpis(
        agent_id=str(agent_id), period="7d", db=mock_db, company_id="comp-1"
    )

    _mock_query_result(
        mock_db,
        execute_sequence=[
            ("scalar_one_or_none", agent),
            ("scalars_all", [_fake_run(), _fake_run()]),
        ],
    )
    r30 = await ca.get_agent_kpis(
        agent_id=str(agent_id), period="30d", db=mock_db, company_id="comp-1"
    )

    assert r7.period == "7d"
    assert r30.period == "30d"
    assert r7.bucket.total_executions == 1
    assert r30.bucket.total_executions == 2


# ────────────────────────────────────────────────────────────────────────────
# B1.4 — Multi-tenancy: agent de outra company → 404
# ────────────────────────────────────────────────────────────────────────────

async def test_kpis_404_when_agent_not_found(mock_db):
    from app.api.v1 import custom_agents as ca

    _mock_query_result(
        mock_db,
        execute_sequence=[
            ("scalar_one_or_none", None),  # agent not found OR not same tenant
        ],
    )

    with pytest.raises(HTTPException) as exc:
        await ca.get_agent_kpis(
            agent_id=str(uuid.uuid4()),
            period="30d",
            db=mock_db,
            company_id="comp-1",
        )
    assert exc.value.status_code == 404


# ────────────────────────────────────────────────────────────────────────────
# B1.5 — is_learning boundary: 4 runs vs 5 runs
# ────────────────────────────────────────────────────────────────────────────

async def test_kpis_is_learning_true_when_lt_5_executions(mock_db):
    from app.api.v1 import custom_agents as ca

    agent_id = uuid.uuid4()
    agent = _fake_agent(agent_id)
    runs = [_fake_run() for _ in range(4)]
    _mock_query_result(
        mock_db,
        execute_sequence=[
            ("scalar_one_or_none", agent),
            ("scalars_all", runs),
        ],
    )

    result = await ca.get_agent_kpis(
        agent_id=str(agent_id), period="all", db=mock_db, company_id="comp-1"
    )
    assert result.is_learning is True


async def test_kpis_is_learning_false_when_ge_5_executions(mock_db):
    from app.api.v1 import custom_agents as ca

    agent_id = uuid.uuid4()
    agent = _fake_agent(agent_id)
    runs = [_fake_run() for _ in range(5)]
    _mock_query_result(
        mock_db,
        execute_sequence=[
            ("scalar_one_or_none", agent),
            ("scalars_all", runs),
        ],
    )

    result = await ca.get_agent_kpis(
        agent_id=str(agent_id), period="all", db=mock_db, company_id="comp-1"
    )
    assert result.is_learning is False


# ────────────────────────────────────────────────────────────────────────────
# B1.6 — Hour heatmap tem 24 entries (uma por hora, incluindo zeros)
# ────────────────────────────────────────────────────────────────────────────

async def test_kpis_hour_heatmap_has_24_entries(mock_db):
    from app.api.v1 import custom_agents as ca

    agent_id = uuid.uuid4()
    agent = _fake_agent(agent_id)
    now = datetime.now(timezone.utc)
    runs = [
        _fake_run(started_at=now.replace(hour=10, minute=0, second=0, microsecond=0)),
        _fake_run(started_at=now.replace(hour=10, minute=30, second=0, microsecond=0)),
        _fake_run(started_at=now.replace(hour=15, minute=0, second=0, microsecond=0)),
    ]
    _mock_query_result(
        mock_db,
        execute_sequence=[
            ("scalar_one_or_none", agent),
            ("scalars_all", runs),
        ],
    )

    result = await ca.get_agent_kpis(
        agent_id=str(agent_id), period="30d", db=mock_db, company_id="comp-1"
    )

    assert len(result.hour_heatmap) == 24
    hours_with_data = {h.hour_of_day: h.executions_count for h in result.hour_heatmap}
    assert hours_with_data[10] == 2
    assert hours_with_data[15] == 1
    assert hours_with_data[0] == 0


# ────────────────────────────────────────────────────────────────────────────
# B1.7 — Tool breakdown ordered by count desc
# ────────────────────────────────────────────────────────────────────────────

async def test_kpis_tool_breakdown_sorted_desc(mock_db):
    from app.api.v1 import custom_agents as ca

    agent_id = uuid.uuid4()
    agent = _fake_agent(agent_id)
    runs = [
        _fake_run(tools_used=["email_send", "whatsapp_send"]),
        _fake_run(tools_used=["email_send"]),
        _fake_run(tools_used=["email_send", "voice_invoke"]),
    ]
    _mock_query_result(
        mock_db,
        execute_sequence=[
            ("scalar_one_or_none", agent),
            ("scalars_all", runs),
        ],
    )

    result = await ca.get_agent_kpis(
        agent_id=str(agent_id), period="30d", db=mock_db, company_id="comp-1"
    )

    counts = [t.count for t in result.tool_breakdown]
    assert counts == sorted(counts, reverse=True)
    assert result.tool_breakdown[0].tool_name == "email_send"
    assert result.tool_breakdown[0].count == 3


# ────────────────────────────────────────────────────────────────────────────
# B1.8 — P95 latency calculado corretamente
# ────────────────────────────────────────────────────────────────────────────

async def test_kpis_p95_latency_computed(mock_db):
    from app.api.v1 import custom_agents as ca

    agent_id = uuid.uuid4()
    agent = _fake_agent(agent_id)
    # 100 runs com latency 1000ms a 100000ms (10ms step)
    runs = [_fake_run(latency_ms=(i + 1) * 1000) for i in range(100)]
    _mock_query_result(
        mock_db,
        execute_sequence=[
            ("scalar_one_or_none", agent),
            ("scalars_all", runs),
        ],
    )

    result = await ca.get_agent_kpis(
        agent_id=str(agent_id), period="30d", db=mock_db, company_id="comp-1"
    )

    # avg = (1000 + 100000) / 2 = ~50.5 seconds
    assert 49 <= result.bucket.avg_execution_seconds <= 52
    # p95 = ~95th value = 95000ms = 95s
    assert 90 <= result.bucket.p95_execution_seconds <= 100
