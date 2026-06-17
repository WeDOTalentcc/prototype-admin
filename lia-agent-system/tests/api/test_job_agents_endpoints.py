"""
Onda 3.B2 — /jobs/{job_id}/agents canonical shortcut contract.

6 testes:
1. GET vazio
2. GET com deployments + joined agent metadata
3. POST cria deployment (delega ao service canonical)
4. POST validação trigger_mode (combo inválido = 422)
5. DELETE remove
6. Multi-tenancy (job de outra company = 404)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1 import jobs_agents as ja_api
from app.schemas.agent_deployment import AttachJobAgentRequest

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
    u.company_id = "comp-jobs-1"
    return u


def _fake_deployment(*, job_id, agent_id, company_id, trigger_mode="manual"):
    d = MagicMock()
    d.id = uuid.uuid4()
    d.agent_id = agent_id
    d.company_id = company_id
    d.target_type = "job"
    d.target_id = job_id
    d.target_name = None
    d.trigger_mode = trigger_mode
    d.schedule_cron = None
    d.is_active = True
    d.config_overrides = {}
    d.execution_count = 0
    d.candidates_processed = 0
    d.last_execution_at = None
    d.created_by = "user-1"
    d.created_at = datetime.now(timezone.utc)
    d.updated_at = datetime.now(timezone.utc)
    d.to_dict = lambda: {
        "id": str(d.id),
        "agent_id": str(d.agent_id),
        "company_id": d.company_id,
        "target_type": d.target_type,
        "target_id": str(d.target_id),
        "target_name": None,
        "trigger_mode": d.trigger_mode,
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


def _fake_agent(*, agent_id, company_id, name="MyAgent", status="active"):
    a = MagicMock()
    a.id = agent_id
    a.company_id = company_id
    a.name = name
    a.status = status
    a.category = "screening"
    a.domain = "ats"
    return a


def _fake_job(*, job_id, company_id):
    j = MagicMock()
    j.id = job_id
    j.company_id = company_id
    return j


def _mock_job_repo(mock_db, monkeypatch, *, job=None):
    """Patch JobVacancyCRUDRepository.get_vacancy_by_id_and_company."""
    repo = MagicMock()
    repo.get_vacancy_by_id_and_company = AsyncMock(return_value=job)
    monkeypatch.setattr(
        ja_api, "JobVacancyCRUDRepository", lambda db: repo
    )
    return repo


async def test_list_job_agents_empty(mock_db, mock_user, monkeypatch):
    """GET /jobs/{id}/agents sem deployments → list vazia."""
    job_id = str(uuid.uuid4())
    _mock_job_repo(mock_db, monkeypatch, job=_fake_job(job_id=job_id, company_id=mock_user.company_id))

    fake_svc = MagicMock()
    fake_svc.list_by_target = AsyncMock(return_value=[])
    monkeypatch.setattr(ja_api, "agent_deployment_service", fake_svc)

    result = await ja_api.list_job_agents(
        job_id=job_id,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )
    assert result.total == 0
    assert result.deployments == []


async def test_list_job_agents_with_joined_metadata(mock_db, mock_user, monkeypatch):
    """GET retorna deployments + agent_name/category/status/domain."""
    job_id = str(uuid.uuid4())
    agent_id = uuid.uuid4()
    _mock_job_repo(
        mock_db, monkeypatch,
        job=_fake_job(job_id=job_id, company_id=mock_user.company_id),
    )

    dep = _fake_deployment(job_id=uuid.UUID(job_id), agent_id=agent_id, company_id=mock_user.company_id)
    agent = _fake_agent(agent_id=agent_id, company_id=mock_user.company_id, name="SourcerBot")

    fake_svc = MagicMock()
    fake_svc.list_by_target = AsyncMock(return_value=[dep])
    monkeypatch.setattr(ja_api, "agent_deployment_service", fake_svc)

    # mock db.execute for CustomAgent join
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
    assert result.deployments[0].agent_name == "SourcerBot"
    assert result.deployments[0].agent_status == "active"
    assert result.deployments[0].target_type == "job"


async def test_post_attach_agent_to_job(mock_db, mock_user, monkeypatch):
    """POST /jobs/{id}/agents cria AgentDeployment(target_type='job')."""
    job_id = str(uuid.uuid4())
    agent_id = uuid.uuid4()
    _mock_job_repo(
        mock_db, monkeypatch,
        job=_fake_job(job_id=job_id, company_id=mock_user.company_id),
    )

    agent = _fake_agent(agent_id=agent_id, company_id=mock_user.company_id, name="ScoutBot")
    scalars_mock = MagicMock()
    scalars_mock.scalar_one_or_none = MagicMock(return_value=agent)
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=agent)
    mock_db.execute = AsyncMock(return_value=result_mock)

    dep = _fake_deployment(
        job_id=uuid.UUID(job_id), agent_id=agent_id, company_id=mock_user.company_id
    )
    fake_svc = MagicMock()
    fake_svc.create_deployment = AsyncMock(return_value=dep)
    monkeypatch.setattr(ja_api, "agent_deployment_service", fake_svc)

    body = AttachJobAgentRequest(agent_id=str(agent_id), trigger_mode="manual")
    result = await ja_api.attach_agent_to_job(
        job_id=job_id,
        body=body,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )
    assert result.target_type == "job"
    assert result.agent_name == "ScoutBot"
    fake_svc.create_deployment.assert_awaited_once()


async def test_post_attach_validates_trigger_mode(mock_db, mock_user, monkeypatch):
    """POST com trigger_mode='on_enter_stage' (só pipeline_stage) → 422."""
    job_id = str(uuid.uuid4())
    _mock_job_repo(
        mock_db, monkeypatch,
        job=_fake_job(job_id=job_id, company_id=mock_user.company_id),
    )

    body = AttachJobAgentRequest(
        agent_id=str(uuid.uuid4()), trigger_mode="on_enter_stage"
    )
    with pytest.raises(HTTPException) as exc:
        await ja_api.attach_agent_to_job(
            job_id=job_id,
            body=body,
            current_user=mock_user,
            db=mock_db,
            company_id=mock_user.company_id,
        )
    assert exc.value.status_code == 422
    assert "trigger_mode" in str(exc.value.detail)


async def test_delete_agent_from_job(mock_db, mock_user, monkeypatch):
    """DELETE /jobs/{id}/agents/{deployment_id} remove deployment."""
    job_id = str(uuid.uuid4())
    deployment_id = str(uuid.uuid4())
    _mock_job_repo(
        mock_db, monkeypatch,
        job=_fake_job(job_id=job_id, company_id=mock_user.company_id),
    )

    dep = _fake_deployment(
        job_id=uuid.UUID(job_id),
        agent_id=uuid.uuid4(),
        company_id=mock_user.company_id,
    )
    fake_svc = MagicMock()
    fake_svc.get_deployment = AsyncMock(return_value=dep)
    fake_svc.delete_deployment = AsyncMock(return_value=True)
    monkeypatch.setattr(ja_api, "agent_deployment_service", fake_svc)

    # Should return None (status 204).
    result = await ja_api.detach_agent_from_job(
        job_id=job_id,
        deployment_id=deployment_id,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )
    assert result is None
    fake_svc.delete_deployment.assert_awaited_once()


async def test_multi_tenancy_job_not_owned_returns_404(mock_db, mock_user, monkeypatch):
    """Job de outra company → repo retorna None → 404."""
    job_id = str(uuid.uuid4())
    _mock_job_repo(mock_db, monkeypatch, job=None)  # ownership fails

    with pytest.raises(HTTPException) as exc:
        await ja_api.list_job_agents(
            job_id=job_id,
            current_user=mock_user,
            db=mock_db,
            company_id=mock_user.company_id,
        )
    assert exc.value.status_code == 404


async def test_last_execution_id_resolved_via_deployment_id(
    mock_db, mock_user, monkeypatch
):
    """C1.6-FINAL — deployment de vaga com run via deployment_id retorna
    last_execution_id NAO-None (motor unificado grava deployment_id no run).

    Antes do fix, last_execution_id resolvia so via assignment.custom_agent_id,
    entao deployments de vaga ficavam com None mesmo tendo runs reais ->
    botao "Ver raciocinio" desabilitado erroneamente.
    """
    job_id = str(uuid.uuid4())
    agent_id = uuid.uuid4()
    _mock_job_repo(
        mock_db, monkeypatch,
        job=_fake_job(job_id=job_id, company_id=mock_user.company_id),
    )

    dep = _fake_deployment(
        job_id=uuid.UUID(job_id), agent_id=agent_id, company_id=mock_user.company_id
    )
    agent = _fake_agent(agent_id=agent_id, company_id=mock_user.company_id)
    run_id = uuid.uuid4()

    fake_svc = MagicMock()
    fake_svc.list_by_target = AsyncMock(return_value=[dep])
    monkeypatch.setattr(ja_api, "agent_deployment_service", fake_svc)

    # execute() called 2x: (1) CustomAgent join, (2) deployment-scoped run query.
    # Origin 1 finds the run, so the legacy fallback query is NOT executed.
    agent_scalars = MagicMock()
    agent_scalars.all = MagicMock(return_value=[agent])
    agent_result = MagicMock()
    agent_result.scalars = MagicMock(return_value=agent_scalars)

    dep_run_result = MagicMock()
    dep_run_result.all = MagicMock(return_value=[(dep.id, run_id)])

    mock_db.execute = AsyncMock(side_effect=[agent_result, dep_run_result])

    result = await ja_api.list_job_agents(
        job_id=job_id,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )
    assert result.total == 1
    assert result.deployments[0].last_execution_id == str(run_id)
    # Origin 1 hit -> only 2 execute calls (no legacy fallback query).
    assert mock_db.execute.call_count == 2


async def test_last_execution_id_fallback_via_assignment_legacy(
    mock_db, mock_user, monkeypatch
):
    """C1.6-FINAL — quando NAO ha run via deployment_id, cai no fallback
    legacy via assignment.custom_agent_id (defense-in-depth talent_pool)."""
    job_id = str(uuid.uuid4())
    agent_id = uuid.uuid4()
    _mock_job_repo(
        mock_db, monkeypatch,
        job=_fake_job(job_id=job_id, company_id=mock_user.company_id),
    )

    dep = _fake_deployment(
        job_id=uuid.UUID(job_id), agent_id=agent_id, company_id=mock_user.company_id
    )
    agent = _fake_agent(agent_id=agent_id, company_id=mock_user.company_id)
    legacy_run_id = uuid.uuid4()

    fake_svc = MagicMock()
    fake_svc.list_by_target = AsyncMock(return_value=[dep])
    monkeypatch.setattr(ja_api, "agent_deployment_service", fake_svc)

    # execute() called 3x: CustomAgent join, deployment-scoped (empty),
    # legacy assignment fallback (finds run).
    agent_scalars = MagicMock()
    agent_scalars.all = MagicMock(return_value=[agent])
    agent_result = MagicMock()
    agent_result.scalars = MagicMock(return_value=agent_scalars)

    dep_run_result = MagicMock()
    dep_run_result.all = MagicMock(return_value=[])  # no deployment-scoped run

    legacy_result = MagicMock()
    legacy_result.all = MagicMock(return_value=[(agent_id, legacy_run_id)])

    mock_db.execute = AsyncMock(
        side_effect=[agent_result, dep_run_result, legacy_result]
    )

    result = await ja_api.list_job_agents(
        job_id=job_id,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )
    assert result.total == 1
    assert result.deployments[0].last_execution_id == str(legacy_run_id)
    assert mock_db.execute.call_count == 3


async def test_last_execution_id_none_when_no_runs(
    mock_db, mock_user, monkeypatch
):
    """C1.6-FINAL — deployment sem nenhum run (nem deployment_id nem legacy)
    retorna last_execution_id=None (UX honesta: botao desabilitado)."""
    job_id = str(uuid.uuid4())
    agent_id = uuid.uuid4()
    _mock_job_repo(
        mock_db, monkeypatch,
        job=_fake_job(job_id=job_id, company_id=mock_user.company_id),
    )

    dep = _fake_deployment(
        job_id=uuid.UUID(job_id), agent_id=agent_id, company_id=mock_user.company_id
    )
    agent = _fake_agent(agent_id=agent_id, company_id=mock_user.company_id)

    fake_svc = MagicMock()
    fake_svc.list_by_target = AsyncMock(return_value=[dep])
    monkeypatch.setattr(ja_api, "agent_deployment_service", fake_svc)

    agent_scalars = MagicMock()
    agent_scalars.all = MagicMock(return_value=[agent])
    agent_result = MagicMock()
    agent_result.scalars = MagicMock(return_value=agent_scalars)

    empty_result = MagicMock()
    empty_result.all = MagicMock(return_value=[])

    mock_db.execute = AsyncMock(
        side_effect=[agent_result, empty_result, empty_result]
    )

    result = await ja_api.list_job_agents(
        job_id=job_id,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )
    assert result.total == 1
    assert result.deployments[0].last_execution_id is None
