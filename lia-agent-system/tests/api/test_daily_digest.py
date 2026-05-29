"""Onda C4.2 — /agent-monitoring/daily-digest contract tests.

5 testes obrigatórios:
1. Empty (tenant sem runs nem aprovações)
2. Items ordenados por relevância (error > pending > celebration > surfaced > info)
3. Multi-surface (runs de assignment E deployment entram no digest)
4. Multi-tenancy fail-closed (filtro company_id no WHERE)
5. since_hours respeitado (janela configurável)

Mock-based — exercita curadoria por relevância + multi-tenancy + multi-surface.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return AsyncMock()


def _fake_run(
    run_id,
    company_id,
    status="success",
    assignment_id=None,
    deployment_id=None,
    results=None,
    runtime_metrics=None,
    error_message=None,
    started_at=None,
):
    r = MagicMock()
    r.id = run_id
    r.assignment_id = assignment_id
    r.deployment_id = deployment_id
    r.company_id = company_id
    r.status = status
    now = started_at or datetime.now(timezone.utc)
    r.started_at = now
    r.finished_at = now
    r.created_at = now
    r.results = results if results is not None else {}
    r.runtime_metrics = runtime_metrics if runtime_metrics is not None else {}
    r.error_message = error_message
    return r


def _fake_assignment(assignment_id, pool_id, custom_agent_id, company_id):
    a = MagicMock()
    a.id = assignment_id
    a.talent_pool_id = pool_id
    a.custom_agent_id = custom_agent_id
    a.company_id = company_id
    return a


def _fake_agent(agent_id, name="Catarina", category="screening"):
    a = MagicMock()
    a.id = agent_id
    a.name = name
    a.category = category
    return a


def _fake_pool(pool_id, name="SP Tech"):
    p = MagicMock()
    p.id = pool_id
    p.name = name
    return p


def _fake_deployment(
    deployment_id, agent_id, target_type="job", target_id=None, target_name="Dev Sênior"
):
    d = MagicMock()
    d.id = deployment_id
    d.agent_id = agent_id
    d.target_type = target_type
    d.target_id = target_id or uuid.uuid4()
    d.target_name = target_name
    return d


def _row_assignment(run, assignment, agent, pool):
    """Tuple canonical C1.6a: run via assignment (talent_pool legacy)."""
    return (run, assignment, agent, pool, None, None)


def _row_deployment(run, deployment, agent):
    """Tuple canonical C1.6a: run via deployment (qualquer surface)."""
    return (run, None, None, None, deployment, agent)


def _mock_db_executes(mock_db, runs_rows, approval_rows=None):
    """1ª call: runs_rows (6-tuplas). 2ª call: approval rows (fetchall)."""
    approval_rows = approval_rows or []
    results_iter = iter([runs_rows, approval_rows])

    async def _exec(stmt, *a, **kw):
        r = MagicMock()
        try:
            payload = next(results_iter)
        except StopIteration:
            payload = []
        r.all = MagicMock(return_value=payload)
        r.fetchall = MagicMock(return_value=payload)
        r.scalar_one_or_none = MagicMock(return_value=None)
        return r

    mock_db.execute = AsyncMock(side_effect=_exec)


# ─────────────────────────────────────────────────────────────────────
# 1 — empty
# ─────────────────────────────────────────────────────────────────────
async def test_daily_digest_empty_when_no_activity(mock_db):
    from app.api.v1 import agent_monitoring as am

    _mock_db_executes(mock_db, [], [])
    resp = await am.get_daily_digest(
        since_hours=24, limit=8, db=mock_db, company_id="comp-1"
    )
    assert resp.items == []
    assert resp.total_runs == 0
    assert resp.total_candidates_processed == 0
    assert resp.period_hours == 24


# ─────────────────────────────────────────────────────────────────────
# 2 — relevância: error > pending > celebration(approved) > surfaced > high_cost
# ─────────────────────────────────────────────────────────────────────
async def test_daily_digest_items_ordered_by_relevance(mock_db):
    from app.api.v1 import agent_monitoring as am

    company_id = "comp-1"
    cid_pool = uuid.uuid4()

    # success com approval (celebration)
    run_approved = _fake_run(
        uuid.uuid4(),
        company_id,
        status="success",
        assignment_id=uuid.uuid4(),
        results={"approved_count": 4},
    )
    agent_a1 = _fake_agent(uuid.uuid4(), name="Catarina")
    asg1 = _fake_assignment(run_approved.assignment_id, cid_pool, agent_a1.id, company_id)

    # success com surfaced
    run_surfaced = _fake_run(
        uuid.uuid4(),
        company_id,
        status="success",
        assignment_id=uuid.uuid4(),
        results={"candidate_ids": ["c1", "c2", "c3"]},
    )
    agent_a2 = _fake_agent(uuid.uuid4(), name="Pedro")
    asg2 = _fake_assignment(run_surfaced.assignment_id, cid_pool, agent_a2.id, company_id)

    # error
    run_error = _fake_run(
        uuid.uuid4(),
        company_id,
        status="error",
        assignment_id=uuid.uuid4(),
        error_message="boom",
    )
    agent_a3 = _fake_agent(uuid.uuid4(), name="Ana")
    asg3 = _fake_assignment(run_error.assignment_id, cid_pool, agent_a3.id, company_id)

    # high_cost
    run_cost = _fake_run(
        uuid.uuid4(),
        company_id,
        status="success",
        assignment_id=uuid.uuid4(),
        runtime_metrics={"cost_usd": 1.25},
    )
    agent_a4 = _fake_agent(uuid.uuid4(), name="Bruno")
    asg4 = _fake_assignment(run_cost.assignment_id, cid_pool, agent_a4.id, company_id)

    rows = [
        _row_assignment(run_approved, asg1, agent_a1, _fake_pool(cid_pool)),
        _row_assignment(run_surfaced, asg2, agent_a2, _fake_pool(cid_pool)),
        _row_assignment(run_error, asg3, agent_a3, _fake_pool(cid_pool)),
        _row_assignment(run_cost, asg4, agent_a4, _fake_pool(cid_pool)),
    ]

    # pending approval
    pending_agent_id = uuid.uuid4()
    approval_rows = [
        (pending_agent_id, "Sofia", datetime.now(timezone.utc)),
        (pending_agent_id, "Sofia", datetime.now(timezone.utc)),
    ]

    _mock_db_executes(mock_db, rows, approval_rows)
    resp = await am.get_daily_digest(
        since_hours=24, limit=8, db=mock_db, company_id=company_id
    )

    kinds = [it.kind for it in resp.items]
    # error primeiro, pending segundo, depois approved (celebration), surfaced, high_cost
    assert kinds[0] == "agent_error"
    assert kinds[1] == "pending_approval"
    assert "decision_approved" in kinds
    assert "candidates_surfaced" in kinds
    assert "high_cost" in kinds
    # relevância monotônica não-decrescente
    weights = [am._DIGEST_RELEVANCE_WEIGHT[k] for k in kinds]
    assert weights == sorted(weights)
    # pending approval agrega count=2
    pending_item = next(it for it in resp.items if it.kind == "pending_approval")
    assert pending_item.count == 2
    # approved count=4 + severity celebration
    approved_item = next(it for it in resp.items if it.kind == "decision_approved")
    assert approved_item.count == 4
    assert approved_item.severity == "celebration"


# ─────────────────────────────────────────────────────────────────────
# 3 — multi-surface (deployment job + assignment pool entram juntos)
# ─────────────────────────────────────────────────────────────────────
async def test_daily_digest_multi_surface(mock_db):
    from app.api.v1 import agent_monitoring as am

    company_id = "comp-1"

    # deployment surface (job) — surfaced
    dep_agent = _fake_agent(uuid.uuid4(), name="Catarina")
    dep = _fake_deployment(uuid.uuid4(), dep_agent.id, target_type="job", target_name="Dev Sênior")
    run_dep = _fake_run(
        uuid.uuid4(),
        company_id,
        status="success",
        deployment_id=dep.id,
        results={"candidate_ids": ["c1", "c2"]},
    )

    # assignment surface (pool) — approved
    asg_agent = _fake_agent(uuid.uuid4(), name="Pedro")
    pool_id = uuid.uuid4()
    asg = _fake_assignment(uuid.uuid4(), pool_id, asg_agent.id, company_id)
    run_asg = _fake_run(
        uuid.uuid4(),
        company_id,
        status="success",
        assignment_id=asg.id,
        results={"approved_count": 3},
    )

    rows = [
        _row_deployment(run_dep, dep, dep_agent),
        _row_assignment(run_asg, asg, asg_agent, _fake_pool(pool_id)),
    ]
    _mock_db_executes(mock_db, rows, [])
    resp = await am.get_daily_digest(
        since_hours=24, limit=8, db=mock_db, company_id=company_id
    )

    target_types = {it.target_type for it in resp.items}
    assert "job" in target_types
    assert "talent_pool" in target_types
    # deployment run trouxe target_name denormalizado
    dep_item = next(it for it in resp.items if it.target_type == "job")
    assert dep_item.target_name == "Dev Sênior"
    assert resp.total_runs == 2


# ─────────────────────────────────────────────────────────────────────
# 4 — multi-tenancy: filtro company_id no WHERE (smoke)
# ─────────────────────────────────────────────────────────────────────
async def test_daily_digest_multi_tenancy_filter(mock_db):
    from app.api.v1 import agent_monitoring as am

    captured = {}

    async def _exec(stmt, *a, **kw):
        captured["stmt"] = str(stmt)
        r = MagicMock()
        r.all = MagicMock(return_value=[])
        r.fetchall = MagicMock(return_value=[])
        return r

    mock_db.execute = AsyncMock(side_effect=_exec)
    resp = await am.get_daily_digest(
        since_hours=24, limit=8, db=mock_db, company_id="comp-XYZ"
    )
    assert resp.items == []
    # o WHERE referencia company_id (compilado no SQL textual)
    assert "company_id" in captured["stmt"]


# ─────────────────────────────────────────────────────────────────────
# 5 — since_hours respeitado (período no response + parametrizável)
# ─────────────────────────────────────────────────────────────────────
async def test_daily_digest_respects_since_hours(mock_db):
    from app.api.v1 import agent_monitoring as am

    _mock_db_executes(mock_db, [], [])
    resp = await am.get_daily_digest(
        since_hours=72, limit=8, db=mock_db, company_id="comp-1"
    )
    assert resp.period_hours == 72


# ─────────────────────────────────────────────────────────────────────
# bonus — limit trunca items
# ─────────────────────────────────────────────────────────────────────
async def test_daily_digest_respects_limit(mock_db):
    from app.api.v1 import agent_monitoring as am

    company_id = "comp-1"
    pool_id = uuid.uuid4()
    rows = []
    for i in range(12):
        agent = _fake_agent(uuid.uuid4(), name=f"Agent-{i}")
        asg = _fake_assignment(uuid.uuid4(), pool_id, agent.id, company_id)
        run = _fake_run(
            uuid.uuid4(),
            company_id,
            status="success",
            assignment_id=asg.id,
            results={"candidate_ids": ["c1"]},
        )
        rows.append(_row_assignment(run, asg, agent, _fake_pool(pool_id)))
    _mock_db_executes(mock_db, rows, [])
    resp = await am.get_daily_digest(
        since_hours=24, limit=5, db=mock_db, company_id=company_id
    )
    assert len(resp.items) == 5
    assert resp.total_runs == 12
