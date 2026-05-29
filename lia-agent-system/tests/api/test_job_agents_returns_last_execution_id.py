"""
Onda 5+2 D (2026-05-29) — contract test: GET /jobs/{job_id}/agents
expõe `last_execution_id` (PoolAgentRun.id mais recente, filtrado por
agent_id + company_id).

3 cenários canonical:
  1. Deployment sem runs → last_execution_id = None.
  2. Deployment com 3 runs → retorna ID do MAIS RECENTE.
  3. Multi-tenancy: company_id de outro tenant é filtrado via _fetch_last_execution_id_map.

Sensor pinning: deployment.id NÃO pode ser usado como execution_id; o frontend
chama /agent-monitoring/executions/{id}/reasoning que valida UUID + lookup em
PoolAgentRun. Antes deste fix o JobAgentsTab usava deployment.id como fallback,
sempre causando 400/404 no Drawer.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1 import jobs_agents as ja_api

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    u = MagicMock()
    u.id = uuid.uuid4()
    u.company_id = "comp-D-1"
    return u


def _fake_deployment(*, job_id, agent_id, company_id):
    d = MagicMock()
    d.id = uuid.uuid4()
    d.agent_id = agent_id
    d.company_id = company_id
    d.target_type = "job"
    d.target_id = job_id
    d.target_name = None
    d.trigger_mode = "manual"
    d.schedule_cron = None
    d.is_active = True
    d.config_overrides = {}
    d.execution_count = 0
    d.candidates_processed = 0
    d.last_execution_at = None
    d.created_by = "u-1"
    d.created_at = datetime.now(timezone.utc)
    d.updated_at = datetime.now(timezone.utc)
    d.to_dict = lambda: {
        "id": str(d.id),
        "agent_id": str(d.agent_id),
        "company_id": d.company_id,
        "target_type": "job",
        "target_id": str(d.target_id),
        "target_name": None,
        "trigger_mode": "manual",
        "schedule_cron": None,
        "is_active": True,
        "config_overrides": {},
        "execution_count": 0,
        "candidates_processed": 0,
        "last_execution_at": None,
        "created_by": d.created_by,
        "created_at": d.created_at.isoformat(),
        "updated_at": d.updated_at.isoformat(),
    }
    return d


def _fake_agent(*, agent_id, company_id, name="Bot"):
    a = MagicMock()
    a.id = agent_id
    a.company_id = company_id
    a.name = name
    a.status = "active"
    a.category = "screening"
    a.domain = "ats"
    return a


def _fake_job(*, job_id, company_id):
    j = MagicMock()
    j.id = job_id
    j.company_id = company_id
    return j


def _mock_job_repo(monkeypatch, *, job):
    repo = MagicMock()
    repo.get_vacancy_by_id_and_company = AsyncMock(return_value=job)
    monkeypatch.setattr(ja_api, "JobVacancyCRUDRepository", lambda db: repo)
    return repo


async def test_last_execution_id_is_none_when_no_runs(mock_db, mock_user, monkeypatch):
    """Deployment cujo agent nunca rodou → last_execution_id=None."""
    job_id = str(uuid.uuid4())
    agent_id = uuid.uuid4()
    _mock_job_repo(
        monkeypatch,
        job=_fake_job(job_id=job_id, company_id=mock_user.company_id),
    )
    dep = _fake_deployment(
        job_id=uuid.UUID(job_id), agent_id=agent_id, company_id=mock_user.company_id
    )
    agent = _fake_agent(agent_id=agent_id, company_id=mock_user.company_id)

    fake_svc = MagicMock()
    fake_svc.list_by_target = AsyncMock(return_value=[dep])
    monkeypatch.setattr(ja_api, "agent_deployment_service", fake_svc)

    # Patch helper directly — keeps test focused on contract semantics.
    monkeypatch.setattr(
        ja_api,
        "_fetch_last_execution_id_map",
        AsyncMock(return_value={}),
    )

    # CustomAgent join (agents in tenant)
    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=[agent])
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=scalars_mock)
    mock_db.execute = AsyncMock(return_value=result_mock)

    result = await ja_api.list_job_agents(
        job_id=job_id,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )
    assert result.total == 1
    assert result.deployments[0].last_execution_id is None


async def test_last_execution_id_returns_most_recent_run(mock_db, mock_user, monkeypatch):
    """Deployment com 3 runs → endpoint expõe o MAIS RECENTE.

    Validamos via mock do helper: o endpoint deve repassar o run_id retornado
    pelo helper sem filtrar nem inverter ordem.
    """
    job_id = str(uuid.uuid4())
    agent_id = uuid.uuid4()
    _mock_job_repo(
        monkeypatch,
        job=_fake_job(job_id=job_id, company_id=mock_user.company_id),
    )
    dep = _fake_deployment(
        job_id=uuid.UUID(job_id), agent_id=agent_id, company_id=mock_user.company_id
    )
    agent = _fake_agent(agent_id=agent_id, company_id=mock_user.company_id)

    fake_svc = MagicMock()
    fake_svc.list_by_target = AsyncMock(return_value=[dep])
    monkeypatch.setattr(ja_api, "agent_deployment_service", fake_svc)

    most_recent_run_id = str(uuid.uuid4())
    monkeypatch.setattr(
        ja_api,
        "_fetch_last_execution_id_map",
        AsyncMock(return_value={str(agent_id): most_recent_run_id}),
    )

    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=[agent])
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=scalars_mock)
    mock_db.execute = AsyncMock(return_value=result_mock)

    result = await ja_api.list_job_agents(
        job_id=job_id,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )
    assert result.total == 1
    assert result.deployments[0].last_execution_id == most_recent_run_id


async def test_multi_tenancy_helper_filters_by_company_id(mock_db):
    """_fetch_last_execution_id_map deve filtrar company_id em AMBAS as tabelas.

    Sensor: query stmt deve incluir PoolAgentRun.company_id == company_id E
    PoolAgentAssignment.company_id == company_id. Defense-in-depth.
    """
    from lia_models.pool_agent_assignment import PoolAgentAssignment
    from lia_models.pool_agent_run import PoolAgentRun

    captured_stmts: list = []

    async def fake_execute(stmt):
        captured_stmts.append(stmt)
        result = MagicMock()
        result.all = MagicMock(return_value=[])
        return result

    mock_db.execute = fake_execute

    out = await ja_api._fetch_last_execution_id_map(
        db=mock_db,
        agent_ids=[str(uuid.uuid4())],
        company_id="tenant-X",
    )
    assert out == {}
    assert len(captured_stmts) == 1

    # Render statement to string to assert filters lexically.
    rendered = str(
        captured_stmts[0].compile(compile_kwargs={"literal_binds": False})
    )
    # Both company_id filters must appear in the WHERE clause.
    assert "pool_agent_runs.company_id" in rendered
    assert "pool_agent_assignments.company_id" in rendered


async def test_fetch_helper_empty_agent_ids_short_circuits(mock_db):
    """agent_ids=[] → retorna {} SEM disparar query (otimização)."""
    mock_db.execute = AsyncMock()
    out = await ja_api._fetch_last_execution_id_map(
        db=mock_db,
        agent_ids=[],
        company_id="tenant-X",
    )
    assert out == {}
    mock_db.execute.assert_not_called()


async def test_fetch_helper_first_hit_wins_in_python_aggregate(mock_db):
    """Helper consome rows DESC e mantém primeiro hit por custom_agent_id.

    Cenário: agent A teve 3 runs. SQL retorna [run3, run2, run1] (DESC).
    Mapping resultante deve ser {A: run3}.
    """
    agent_a = uuid.uuid4()
    run3 = uuid.uuid4()
    run2 = uuid.uuid4()
    run1 = uuid.uuid4()

    result_mock = MagicMock()
    # Rows: (custom_agent_id, run_id), already sorted DESC by SQL.
    result_mock.all = MagicMock(return_value=[
        (agent_a, run3),
        (agent_a, run2),
        (agent_a, run1),
    ])
    mock_db.execute = AsyncMock(return_value=result_mock)

    out = await ja_api._fetch_last_execution_id_map(
        db=mock_db,
        agent_ids=[str(agent_a)],
        company_id="tenant-X",
    )
    assert out == {str(agent_a): str(run3)}
