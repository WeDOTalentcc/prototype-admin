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
        AsyncMock(return_value={str(dep.id): most_recent_run_id}),
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
    """_fetch_last_execution_id_map filtra company_id em TODAS as tabelas.

    Sensor: origem 1 (deployment_id) filtra PoolAgentRun.company_id; origem 2
    (fallback legacy assignment-join) filtra PoolAgentRun.company_id E
    PoolAgentAssignment.company_id. Defense-in-depth.

    C1.6-FINAL (2026-05-29): helper agora recebe `deployments=[AgentDeployment]`
    keyed por deployment_id; assignment-join e apenas fallback.
    """
    captured_stmts: list = []

    async def fake_execute(stmt):
        captured_stmts.append(stmt)
        result = MagicMock()
        result.all = MagicMock(return_value=[])
        return result

    mock_db.execute = fake_execute

    dep = MagicMock()
    dep.id = uuid.uuid4()
    dep.agent_id = uuid.uuid4()

    out = await ja_api._fetch_last_execution_id_map(
        db=mock_db,
        deployments=[dep],
        company_id="tenant-X",
    )
    assert out == {}
    # Origem 1 (deployment_id) + origem 2 (fallback, pois origem 1 vazia).
    assert len(captured_stmts) == 2

    rendered_all = "\n".join(
        str(s.compile(compile_kwargs={"literal_binds": False})) for s in captured_stmts
    )
    # PoolAgentRun.company_id filtrado em ambas as origens.
    assert "pool_agent_runs.company_id" in rendered_all
    # PoolAgentAssignment.company_id filtrado na origem 2 (fallback legacy).
    assert "pool_agent_assignments.company_id" in rendered_all


async def test_fetch_helper_empty_deployments_short_circuits(mock_db):
    """deployments=[] retorna {} SEM disparar query (otimizacao)."""
    mock_db.execute = AsyncMock()
    out = await ja_api._fetch_last_execution_id_map(
        db=mock_db,
        deployments=[],
        company_id="tenant-X",
    )
    assert out == {}
    mock_db.execute.assert_not_called()


async def test_fetch_helper_first_hit_wins_in_python_aggregate(mock_db):
    """Helper consome rows DESC e mantem primeiro hit por deployment_id.

    Cenario: deployment D teve 3 runs. SQL (origem 1) retorna [run3, run2, run1]
    (DESC por started_at). Mapping resultante deve ser {D: run3}. Como origem 1
    resolveu o deployment, a origem 2 (fallback) nao e mais necessaria.
    """
    dep = MagicMock()
    dep.id = uuid.uuid4()
    dep.agent_id = uuid.uuid4()
    run3 = uuid.uuid4()
    run2 = uuid.uuid4()
    run1 = uuid.uuid4()

    result_mock = MagicMock()
    # Rows: (deployment_id, run_id), already sorted DESC by SQL.
    result_mock.all = MagicMock(return_value=[
        (dep.id, run3),
        (dep.id, run2),
        (dep.id, run1),
    ])
    mock_db.execute = AsyncMock(return_value=result_mock)

    out = await ja_api._fetch_last_execution_id_map(
        db=mock_db,
        deployments=[dep],
        company_id="tenant-X",
    )
    assert out == {str(dep.id): str(run3)}
    # Origem 1 resolveu -> fallback (origem 2) nao dispara segunda query.
    assert mock_db.execute.await_count == 1
