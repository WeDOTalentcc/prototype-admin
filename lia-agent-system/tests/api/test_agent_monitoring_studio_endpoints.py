"""Studio Control Room endpoints — Onda 1 B4 contract tests.

3 endpoints novos em /agent-monitoring/:
- active-executions (B4.1)
- executions/{id}/reasoning (B4.2)
- recent-executions (B4.3)

Mock-based — exercita wiring + multi-tenancy + LGPD declarative trail.
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
    db = AsyncMock()
    return db


def _fake_run(
    run_id,
    assignment_id,
    company_id,
    status="running",
    started_at=None,
    finished_at=None,
    reasoning_payload=None,
):
    r = MagicMock()
    r.id = run_id
    r.assignment_id = assignment_id
    r.company_id = company_id
    r.trigger_source = "on_demand"
    r.status = status
    r.started_at = started_at or datetime.now(timezone.utc)
    r.finished_at = finished_at
    r.dispatch_metadata = {}
    r.results = {"response": "Found 5 candidates"}
    r.runtime_metrics = {
        "latency_ms": 1200,
        "tokens_input": 500,
        "tokens_output": 200,
        "input_tokens": 500,
        "output_tokens": 200,
        "model_used": "gpt-4",
        "cost_usd": 0.012,
    }
    r.reasoning_payload = reasoning_payload
    r.error_message = None
    r.created_at = datetime.now(timezone.utc)
    return r


def _fake_assignment(assignment_id, pool_id, custom_agent_id, company_id):
    a = MagicMock()
    a.id = assignment_id
    a.talent_pool_id = pool_id
    a.custom_agent_id = custom_agent_id
    a.company_id = company_id
    return a


def _fake_agent(agent_id, name="TestAgent"):
    a = MagicMock()
    a.id = agent_id
    a.name = name
    return a


def _fake_pool(pool_id, name="Pool X"):
    p = MagicMock()
    p.id = pool_id
    p.name = name
    return p


def _mock_db_with_rows(mock_db, rows):
    """Helper: configure mock_db.execute to return rows."""
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    result.one_or_none = MagicMock(return_value=rows[0] if rows else None)
    mock_db.execute = AsyncMock(return_value=result)


# ────────────────────────────────────────────────────────────────────────────
# B4.1 — /active-executions
# ────────────────────────────────────────────────────────────────────────────


async def test_active_executions_returns_empty_when_no_running(mock_db):
    from app.api.v1 import agent_monitoring as am

    _mock_db_with_rows(mock_db, [])
    result = await am.list_active_executions(
        surface=None, db=mock_db, company_id="comp-1"
    )
    assert result == []


async def test_active_executions_returns_running_with_target_name(mock_db):
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    pool_id = uuid.uuid4()
    rows = [
        (
            _fake_run(run_id, assignment_id, "comp-1"),
            _fake_assignment(assignment_id, pool_id, agent_id, "comp-1"),
            _fake_agent(agent_id, name="Sourcing X"),
            _fake_pool(pool_id, name="Top Dev"),
        )
    ]
    _mock_db_with_rows(mock_db, rows)

    result = await am.list_active_executions(
        surface=None, db=mock_db, company_id="comp-1"
    )
    assert len(result) == 1
    r = result[0]
    assert r.execution_id == str(run_id)
    assert r.agent_name == "Sourcing X"
    assert r.target_name == "Top Dev"
    assert r.target_type == "talent_pool"
    assert r.status == "running"


async def test_active_executions_filter_surface_talent_pool(mock_db):
    """Filter surface=talent_pool retorna rows; outros surfaces filtram."""
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    pool_id = uuid.uuid4()
    rows = [
        (
            _fake_run(run_id, assignment_id, "comp-1"),
            _fake_assignment(assignment_id, pool_id, agent_id, "comp-1"),
            _fake_agent(agent_id),
            _fake_pool(pool_id),
        )
    ]
    _mock_db_with_rows(mock_db, rows)

    result = await am.list_active_executions(
        surface="talent_pool", db=mock_db, company_id="comp-1"
    )
    assert len(result) == 1

    # Outro surface filtra
    _mock_db_with_rows(mock_db, rows)
    result_empty = await am.list_active_executions(
        surface="job", db=mock_db, company_id="comp-1"
    )
    assert len(result_empty) == 0


# ────────────────────────────────────────────────────────────────────────────
# B4.2 — /executions/{id}/reasoning
# ────────────────────────────────────────────────────────────────────────────


async def test_reasoning_endpoint_400_when_bad_uuid(mock_db):
    from app.api.v1 import agent_monitoring as am

    with pytest.raises(HTTPException) as exc:
        await am.get_execution_reasoning(
            execution_id="not-a-uuid",
            db=mock_db,
            company_id="comp-1",
        )
    assert exc.value.status_code == 400


async def test_reasoning_endpoint_404_when_not_found(mock_db):
    from app.api.v1 import agent_monitoring as am

    _mock_db_with_rows(mock_db, [])
    with pytest.raises(HTTPException) as exc:
        await am.get_execution_reasoning(
            execution_id=str(uuid.uuid4()),
            db=mock_db,
            company_id="comp-1",
        )
    assert exc.value.status_code == 404


async def test_reasoning_endpoint_404_when_payload_none(mock_db):
    """Legacy run sem reasoning_payload → 404 com mensagem clara."""
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    rows = [
        (
            _fake_run(run_id, assignment_id, "comp-1", reasoning_payload=None),
            _fake_assignment(assignment_id, uuid.uuid4(), agent_id, "comp-1"),
            _fake_agent(agent_id),
        )
    ]
    _mock_db_with_rows(mock_db, rows)
    with pytest.raises(HTTPException) as exc:
        await am.get_execution_reasoning(
            execution_id=str(run_id),
            db=mock_db,
            company_id="comp-1",
        )
    assert exc.value.status_code == 404
    assert "reasoning_payload" in str(exc.value.detail) or "Decision tree" in str(
        exc.value.detail
    )


async def test_reasoning_endpoint_returns_LGPD_canonical_fields(mock_db):
    """B5.2 invariant: data_fields_NOT_accessed sempre inclui 5 tokens."""
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    payload = [
        {
            "step_type": "action",
            "label": "Chamada: search_candidates",
            "data_fields_accessed": ["email", "nome"],
        }
    ]
    rows = [
        (
            _fake_run(
                run_id,
                assignment_id,
                "comp-1",
                reasoning_payload=payload,
            ),
            _fake_assignment(assignment_id, uuid.uuid4(), agent_id, "comp-1"),
            _fake_agent(agent_id),
        )
    ]
    _mock_db_with_rows(mock_db, rows)

    resp = await am.get_execution_reasoning(
        execution_id=str(run_id),
        db=mock_db,
        company_id="comp-1",
    )
    # LGPD canonical 5 sempre na response
    canonical = {"cpf", "raca", "religiao", "genero", "estado_civil"}
    assert canonical.issubset(set(resp.data_fields_NOT_accessed))
    # Aggregated summary não contém forbidden
    assert canonical.isdisjoint(set(resp.data_fields_accessed_summary))
    assert resp.reasoning_trace[0].step_type == "action"


async def test_reasoning_endpoint_strips_forbidden_from_summary(mock_db):
    """Defense-in-depth: se payload corrupto contém 'cpf', summary remove."""
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    # Payload "corrupto" inclui 'cpf' (no shouldnt happen, mas defense)
    payload = [
        {
            "step_type": "action",
            "label": "Chamada: x",
            "data_fields_accessed": ["email", "cpf", "nome"],
        }
    ]
    rows = [
        (
            _fake_run(run_id, assignment_id, "comp-1", reasoning_payload=payload),
            _fake_assignment(assignment_id, uuid.uuid4(), agent_id, "comp-1"),
            _fake_agent(agent_id),
        )
    ]
    _mock_db_with_rows(mock_db, rows)
    resp = await am.get_execution_reasoning(
        execution_id=str(run_id),
        db=mock_db,
        company_id="comp-1",
    )
    assert "cpf" not in resp.data_fields_accessed_summary


# ────────────────────────────────────────────────────────────────────────────
# B4.3 — /recent-executions
# ────────────────────────────────────────────────────────────────────────────


async def test_recent_executions_basic_paginated(mock_db):
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    pool_id = uuid.uuid4()
    rows = [
        (
            _fake_run(
                run_id, assignment_id, "comp-1", status="success",
                finished_at=datetime.now(timezone.utc),
            ),
            _fake_assignment(assignment_id, pool_id, agent_id, "comp-1"),
            _fake_agent(agent_id),
            _fake_pool(pool_id),
        )
    ]
    _mock_db_with_rows(mock_db, rows)
    result = await am.list_recent_executions(
        limit=10, agent_id=None, surface=None, status="all",
        db=mock_db, company_id="comp-1",
    )
    assert len(result) == 1
    assert result[0].status == "success"
    assert result[0].latency_ms == 1200


async def test_recent_executions_bad_agent_id_400(mock_db):
    from app.api.v1 import agent_monitoring as am

    with pytest.raises(HTTPException) as exc:
        await am.list_recent_executions(
            limit=10, agent_id="not-uuid", surface=None, status="all",
            db=mock_db, company_id="comp-1",
        )
    assert exc.value.status_code == 400


async def test_recent_executions_success_summary_truncated(mock_db):
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    pool_id = uuid.uuid4()
    fake = _fake_run(run_id, assignment_id, "comp-1", status="success")
    fake.results = {"response": "A" * 500}
    rows = [
        (
            fake,
            _fake_assignment(assignment_id, pool_id, agent_id, "comp-1"),
            _fake_agent(agent_id),
            _fake_pool(pool_id),
        )
    ]
    _mock_db_with_rows(mock_db, rows)
    result = await am.list_recent_executions(
        limit=10, agent_id=None, surface=None, status="all",
        db=mock_db, company_id="comp-1",
    )
    assert result[0].success_summary is not None
    assert len(result[0].success_summary) <= 140
