"""Onda 2 B3 — /agent-monitoring/candidate/{id}/touches contract tests.

4 testes obrigatórios:
1. Sem touches → touch_count=0, list vazia
2. Com touches → ordenado desc por timestamp
3. since_hours filtra
4. Multi-tenancy (não vaza touches de outro company)

Multi-tenancy: validar candidate.company_id == current_user.company_id
antes de retornar (fail-closed via 404).

MVP scope: lê pool_agent_runs.results JSONB procurando candidate_ids
arrays. Forward-compat — quando agents canonical popularem este campo,
endpoint só passa a retornar dados sem mudança de contrato.
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


def _fake_candidate(candidate_id, company_id):
    c = MagicMock()
    c.id = candidate_id
    c.company_id = company_id
    return c


def _fake_run_touched(
    run_id,
    assignment_id,
    company_id,
    candidate_id,
    started_at=None,
    status="success",
    action_type="screened",
    deployment_id=None,
):
    """Cria fake run cujo results JSONB referencia candidate_id."""
    r = MagicMock()
    r.id = run_id
    r.assignment_id = assignment_id
    r.deployment_id = deployment_id
    r.company_id = company_id
    r.status = status
    r.started_at = started_at or datetime.now(timezone.utc)
    r.finished_at = (started_at or datetime.now(timezone.utc)) + timedelta(seconds=5)
    r.error_message = None
    r.results = {
        "candidate_ids": [str(candidate_id)],
        "action_type": action_type,
        "outcome": "approved" if status == "success" else "pending",
    }
    r.dispatch_metadata = {}
    r.runtime_metrics = {}
    return r


def _fake_assignment(assignment_id, custom_agent_id, company_id):
    a = MagicMock()
    a.id = assignment_id
    a.custom_agent_id = custom_agent_id
    a.company_id = company_id
    return a


def _fake_agent(agent_id, name="ScreeningAgent"):
    a = MagicMock()
    a.id = agent_id
    a.name = name
    return a


def _fake_deployment(
    deployment_id, agent_id, target_type="job", target_name="Vaga Dev"
):
    """C1.6a: agent_deployments row (multi-surface)."""
    d = MagicMock()
    d.id = deployment_id
    d.agent_id = agent_id
    d.target_type = target_type
    d.target_id = uuid.uuid4()
    d.target_name = target_name
    return d


def _row_assignment(run, assignment, agent):
    """Tuple canonical C1.6a: run via assignment (talent_pool legacy).

    Shape: (run, assignment, agent_via_assignment, pool=None,
            deployment=None, agent_via_deployment=None).
    """
    return (run, assignment, agent, None, None, None)


def _row_deployment(run, deployment, agent):
    """Tuple canonical C1.6a: run via deployment (qualquer surface).

    Shape: (run, assignment=None, agent_via_assignment=None, pool=None,
            deployment, agent_via_deployment).
    """
    return (run, None, None, None, deployment, agent)


def _mock_db_pipeline(mock_db, candidate, runs_rows):
    """Configure mock_db.execute pra:
    - 1ª call: lookup candidate (scalar_one_or_none retorna candidate ou None)
    - 2ª call: lookup runs (all retorna rows)
    """
    queue = [candidate, runs_rows]

    async def _exec(stmt, *a, **kw):
        r = MagicMock()
        try:
            payload = queue.pop(0)
        except IndexError:
            payload = None
        if isinstance(payload, list):
            r.all = MagicMock(return_value=payload)
            r.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=payload)))
        else:
            r.scalar_one_or_none = MagicMock(return_value=payload)
            r.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=payload)))
        return r

    mock_db.execute = AsyncMock(side_effect=_exec)


# ─────────────────────────────────────────────────────────────────────
# B3 — /candidate/{id}/touches
# ─────────────────────────────────────────────────────────────────────


async def test_candidate_touches_zero_when_no_runs(mock_db):
    """Candidato sem touches → touch_count=0, list vazia."""
    from app.api.v1 import agent_monitoring as am

    candidate_id = uuid.uuid4()
    company_id = "comp-1"
    candidate = _fake_candidate(candidate_id, company_id)
    _mock_db_pipeline(mock_db, candidate, [])

    response = await am.list_candidate_touches(
        candidate_id=str(candidate_id),
        since_hours=24,
        db=mock_db,
        company_id=company_id,
    )
    assert response.candidate_id == str(candidate_id)
    assert response.touch_count == 0
    assert response.touches == []
    assert response.last_touch_at is None


async def test_candidate_touches_ordered_desc_by_timestamp(mock_db):
    """Múltiplos touches → ordenados desc por started_at."""
    from app.api.v1 import agent_monitoring as am

    candidate_id = uuid.uuid4()
    company_id = "comp-1"
    candidate = _fake_candidate(candidate_id, company_id)
    now = datetime.now(timezone.utc)

    agent_id = uuid.uuid4()
    runs_rows = [
        _row_assignment(
            _fake_run_touched(
                uuid.uuid4(),
                uuid.uuid4(),
                company_id,
                candidate_id,
                started_at=now - timedelta(hours=1),
                action_type="messaged",
            ),
            _fake_assignment(uuid.uuid4(), agent_id, company_id),
            _fake_agent(agent_id, name="MsgAgent"),
        ),
        _row_assignment(
            _fake_run_touched(
                uuid.uuid4(),
                uuid.uuid4(),
                company_id,
                candidate_id,
                started_at=now - timedelta(hours=3),
                action_type="screened",
            ),
            _fake_assignment(uuid.uuid4(), agent_id, company_id),
            _fake_agent(agent_id, name="ScreenAgent"),
        ),
    ]
    _mock_db_pipeline(mock_db, candidate, runs_rows)

    response = await am.list_candidate_touches(
        candidate_id=str(candidate_id),
        since_hours=24,
        db=mock_db,
        company_id=company_id,
    )
    assert response.touch_count == 2
    # Desc: o mais recente (1h atrás) vem primeiro.
    assert response.touches[0].action_type == "messaged"
    assert response.touches[1].action_type == "screened"
    assert response.last_touch_at == response.touches[0].timestamp


async def test_candidate_touches_since_hours_filter(mock_db):
    """since_hours filtra runs antigos.

    Smoke test: o filtro está no WHERE. Validamos via captura da query.
    """
    from app.api.v1 import agent_monitoring as am

    candidate_id = uuid.uuid4()
    company_id = "comp-1"
    captured: list[str] = []

    async def _exec(stmt, *a, **kw):
        captured.append(str(stmt))
        r = MagicMock()
        if len(captured) == 1:
            # 1st call: candidate lookup
            r.scalar_one_or_none = MagicMock(
                return_value=_fake_candidate(candidate_id, company_id)
            )
        else:
            r.all = MagicMock(return_value=[])
        return r

    mock_db.execute = AsyncMock(side_effect=_exec)

    await am.list_candidate_touches(
        candidate_id=str(candidate_id),
        since_hours=2,
        db=mock_db,
        company_id=company_id,
    )
    # Query 2 (runs lookup) deve referenciar started_at filter
    assert len(captured) >= 2
    runs_query = captured[1].lower()
    assert "started_at" in runs_query or "created_at" in runs_query


async def test_candidate_touches_multi_tenancy_isolation(mock_db):
    """Candidato de outro tenant → HTTPException 404 (não vaza dados).

    Multi-tenancy fail-closed: lookup do candidate FILTRA por company_id;
    se candidate.company_id != current_company_id, retorna None → 404.
    """
    from app.api.v1 import agent_monitoring as am

    candidate_id = uuid.uuid4()
    # Mock retorna None (candidate não pertence ao tenant)
    _mock_db_pipeline(mock_db, None, [])

    with pytest.raises(HTTPException) as exc_info:
        await am.list_candidate_touches(
            candidate_id=str(candidate_id),
            since_hours=24,
            db=mock_db,
            company_id="comp-OUTRO",
        )
    assert exc_info.value.status_code == 404


async def test_candidate_touches_includes_deployment_run(mock_db):
    """C1.6a — touch de run de deployment (job/funil) também aparece."""
    from app.api.v1 import agent_monitoring as am

    candidate_id = uuid.uuid4()
    company_id = "comp-1"
    candidate = _fake_candidate(candidate_id, company_id)
    deployment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    run = _fake_run_touched(
        uuid.uuid4(),
        None,
        company_id,
        candidate_id,
        action_type="ranked",
        deployment_id=deployment_id,
    )
    runs_rows = [
        _row_deployment(
            run,
            _fake_deployment(deployment_id, agent_id, target_type="job"),
            _fake_agent(agent_id, name="Ranker Vaga"),
        )
    ]
    _mock_db_pipeline(mock_db, candidate, runs_rows)

    response = await am.list_candidate_touches(
        candidate_id=str(candidate_id),
        since_hours=24,
        db=mock_db,
        company_id=company_id,
    )
    assert response.touch_count == 1
    assert response.touches[0].agent_name == "Ranker Vaga"
    assert response.touches[0].action_type == "ranked"
