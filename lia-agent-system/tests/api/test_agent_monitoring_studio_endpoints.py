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
    deployment_id=None,
):
    r = MagicMock()
    r.id = run_id
    r.assignment_id = assignment_id
    r.deployment_id = deployment_id
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


def _fake_deployment(
    deployment_id, agent_id, target_type="job", target_id=None, target_name="Vaga Dev"
):
    """C1.6a: agent_deployments row — fonte canonical de target_* multi-surface."""
    d = MagicMock()
    d.id = deployment_id
    d.agent_id = agent_id
    d.target_type = target_type
    d.target_id = target_id or uuid.uuid4()
    d.target_name = target_name
    return d


def _row_assignment(run, assignment, agent, pool):
    """Tuple canonical C1.6a para um run via assignment (talent_pool legacy).

    Shape: (run, assignment, agent_via_assignment, pool, deployment=None,
            agent_via_deployment=None).
    """
    return (run, assignment, agent, pool, None, None)


def _row_deployment(run, deployment, agent):
    """Tuple canonical C1.6a para um run via deployment (qualquer surface).

    Shape: (run, assignment=None, agent_via_assignment=None, pool=None,
            deployment, agent_via_deployment).
    """
    return (run, None, None, None, deployment, agent)


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
        _row_assignment(
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
        _row_assignment(
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
        _row_assignment(
            _fake_run(run_id, assignment_id, "comp-1", reasoning_payload=None),
            _fake_assignment(assignment_id, uuid.uuid4(), agent_id, "comp-1"),
            _fake_agent(agent_id),
            None,
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
        _row_assignment(
            _fake_run(
                run_id,
                assignment_id,
                "comp-1",
                reasoning_payload=payload,
            ),
            _fake_assignment(assignment_id, uuid.uuid4(), agent_id, "comp-1"),
            _fake_agent(agent_id),
            None,
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
        _row_assignment(
            _fake_run(run_id, assignment_id, "comp-1", reasoning_payload=payload),
            _fake_assignment(assignment_id, uuid.uuid4(), agent_id, "comp-1"),
            _fake_agent(agent_id),
            None,
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
        _row_assignment(
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
        _row_assignment(
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


# ────────────────────────────────────────────────────────────────────────────
# C1.6a (2026-05-29) — multi-surface: runs sourced via deployment_id
# (job / pipeline_stage / candidate_list), não só talent_pool via assignment.
# ────────────────────────────────────────────────────────────────────────────


async def test_active_executions_surfaces_deployment_run_job(mock_db):
    """Run de deployment de VAGA (deployment_id, sem assignment) aparece."""
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    deployment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    target_id = uuid.uuid4()
    run = _fake_run(run_id, None, "comp-1", deployment_id=deployment_id)
    rows = [
        _row_deployment(
            run,
            _fake_deployment(
                deployment_id,
                agent_id,
                target_type="job",
                target_id=target_id,
                target_name="Engenheiro Backend",
            ),
            _fake_agent(agent_id, name="Sourcing Vaga"),
        )
    ]
    _mock_db_with_rows(mock_db, rows)
    result = await am.list_active_executions(
        surface=None, db=mock_db, company_id="comp-1"
    )
    assert len(result) == 1
    r = result[0]
    assert r.execution_id == str(run_id)
    assert r.agent_name == "Sourcing Vaga"
    assert r.target_type == "job"
    assert r.target_id == str(target_id)
    assert r.target_name == "Engenheiro Backend"


async def test_active_executions_surface_job_filters_to_job_deployment(mock_db):
    """surface=job retorna runs de deployment job; surface=funil filtra fora."""
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    deployment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    rows = [
        _row_deployment(
            _fake_run(run_id, None, "comp-1", deployment_id=deployment_id),
            _fake_deployment(deployment_id, agent_id, target_type="job"),
            _fake_agent(agent_id),
        )
    ]
    _mock_db_with_rows(mock_db, rows)
    result_job = await am.list_active_executions(
        surface="job", db=mock_db, company_id="comp-1"
    )
    assert len(result_job) == 1

    _mock_db_with_rows(mock_db, rows)
    result_funil = await am.list_active_executions(
        surface="pipeline_stage", db=mock_db, company_id="comp-1"
    )
    assert len(result_funil) == 0


async def test_recent_executions_includes_deployment_run(mock_db):
    """recent-executions surfaca runs concluídos de deployment (multi-surface)."""
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    deployment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    run = _fake_run(
        run_id, None, "comp-1", status="success", deployment_id=deployment_id,
        finished_at=datetime.now(timezone.utc),
    )
    rows = [
        _row_deployment(
            run,
            _fake_deployment(
                deployment_id, agent_id, target_type="pipeline_stage",
                target_name="Entrevista Técnica",
            ),
            _fake_agent(agent_id, name="Triagem Funil"),
        )
    ]
    _mock_db_with_rows(mock_db, rows)
    result = await am.list_recent_executions(
        limit=10, agent_id=None, surface=None, status="all",
        db=mock_db, company_id="comp-1",
    )
    assert len(result) == 1
    assert result[0].target_type == "pipeline_stage"
    assert result[0].target_name == "Entrevista Técnica"
    assert result[0].agent_name == "Triagem Funil"


async def test_recent_executions_agent_filter_matches_deployment_agent(mock_db):
    """agent_id filter casa deployment.agent_id (não só assignment)."""
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    deployment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    rows = [
        _row_deployment(
            _fake_run(
                run_id, None, "comp-1", status="success",
                deployment_id=deployment_id,
            ),
            _fake_deployment(deployment_id, agent_id, target_type="job"),
            _fake_agent(agent_id),
        )
    ]
    _mock_db_with_rows(mock_db, rows)
    # Mock retorna a row (filtro SQL é exercitado em integração; aqui validamos
    # que a query não rejeita o agent_id e o run de deployment surfaca).
    result = await am.list_recent_executions(
        limit=10, agent_id=str(agent_id), surface=None, status="all",
        db=mock_db, company_id="comp-1",
    )
    assert len(result) == 1
    assert result[0].agent_id == str(agent_id)


async def test_reasoning_endpoint_works_for_deployment_run(mock_db):
    """reasoning endpoint resolve run com deployment_id (sem assignment)."""
    from app.api.v1 import agent_monitoring as am

    run_id = uuid.uuid4()
    deployment_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    payload = [
        {
            "step_type": "action",
            "label": "Chamada: rank_candidates",
            "data_fields_accessed": ["email", "nome"],
        }
    ]
    run = _fake_run(
        run_id, None, "comp-1", reasoning_payload=payload,
        deployment_id=deployment_id,
    )
    rows = [
        _row_deployment(
            run,
            _fake_deployment(deployment_id, agent_id, target_type="job"),
            _fake_agent(agent_id, name="Ranker Vaga"),
        )
    ]
    _mock_db_with_rows(mock_db, rows)
    resp = await am.get_execution_reasoning(
        execution_id=str(run_id),
        db=mock_db,
        company_id="comp-1",
    )
    assert resp.execution_id == str(run_id)
    assert resp.agent_name == "Ranker Vaga"
    assert resp.reasoning_trace[0].step_type == "action"
    canonical = {"cpf", "raca", "religiao", "genero", "estado_civil"}
    assert canonical.issubset(set(resp.data_fields_NOT_accessed))


async def test_active_executions_cross_tenant_isolated_deployment(mock_db):
    """Multi-tenancy: company_id filter na query (driver run) protege deployment.

    O mock não filtra SQL, então simulamos o caso onde a query (com
    company_id no .where) retorna vazio pra outro tenant.
    """
    from app.api.v1 import agent_monitoring as am

    _mock_db_with_rows(mock_db, [])
    result = await am.list_active_executions(
        surface=None, db=mock_db, company_id="other-tenant"
    )
    assert result == []
