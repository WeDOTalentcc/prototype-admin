"""Fase 2.5 Onda C1-core — dispatch_agent_deployment_task tests (TDD Red→Green).

O motor unificado: agent_deployments é a junction table canonical agente↔surface
(job/talent_pool/pipeline_stage/candidate_list). Esta task é o ANÁLOGO canonical
de dispatch_pool_agent_assignment_task, gravando em pool_agent_runs via
deployment_id (não assignment_id).

Cobre:
- Test 1: _dispatch_impl grava pool_agent_runs com deployment_id (não assignment_id).
- Test 2: BYOK — runtime.execute recebe company_id=deployment.company_id (chokepoint
  do tenant container via ContextVar _current_company_id → _get_model BYOK).
- Test 3: multi-tenancy — deployment de company A não vaza company B (create + queries
  usam deployment.company_id).
- Test 4: erro no runtime → status='error' + error_message, re-raise (REGRA 4).
- Test 5: CHECK constraint chk_par_source_present — run criado tem deployment_id.
- Test 6: scheduler varre só is_active + on_schedule + due (cron).
- Test 7: status transitions queued→running→success.
- Test 8: audit dim — log_decision em success + error com action agent_deployment_run.

Pattern canonical: espelha tests/jobs/test_pool_agents_dispatch_real.py.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


def _make_session_ctx(fake_db):
    class _FakeSessionCtx:
        async def __aenter__(self):
            return fake_db

        async def __aexit__(self, *a):
            return None

    return _FakeSessionCtx()


def _make_agent_output(message="ok", confidence=0.9, actions=None, metadata=None):
    out = MagicMock()
    out.message = message
    out.confidence = confidence
    out.actions = actions or []
    out.metadata = metadata or {}
    return out


def _make_deployment(
    company_id="11111111-1111-1111-1111-111111111111",
    target_type="job",
    trigger_mode="on_schedule",
):
    d = MagicMock()
    d.id = uuid4()
    d.company_id = company_id
    d.agent_id = uuid4()
    d.target_type = target_type
    d.target_id = uuid4()
    d.target_name = "Vaga Teste"
    d.trigger_mode = trigger_mode
    d.schedule_cron = "*/5 * * * *"
    d.is_active = True
    d.config_overrides = {}
    d.execution_count = 0
    d.candidates_processed = 0
    d.last_execution_at = None
    return d


def _make_agent(name="DeployAgent", config=None, category="screening", domain="custom"):
    ag = MagicMock()
    ag.id = uuid4()
    ag.name = name
    ag.system_prompt = "Test prompt"
    ag.allowed_tools = ["search_candidates"]
    ag.domain = domain
    ag.category = category
    ag.max_steps = 8
    ag.temperature = 0.7
    ag.model_override = None
    ag.config = config or {}
    ag.enable_memory = True
    ag.excluded_tools = []
    ag.context_level = "full"
    return ag


def _make_run(deployment_id, company_id):
    r = MagicMock()
    r.id = uuid4()
    r.deployment_id = deployment_id
    r.assignment_id = None
    r.company_id = company_id
    r.status = "queued"
    r.started_at = None
    r.finished_at = None
    return r


def _patch_db_load(fake_db, deployment, agent):
    """db.execute returns deployment first, then agent."""
    res_d = MagicMock()
    res_d.scalar_one_or_none = MagicMock(return_value=deployment)
    res_a = MagicMock()
    res_a.scalar_one_or_none = MagicMock(return_value=agent)
    fake_db.execute = AsyncMock(side_effect=[res_d, res_a])
    fake_db.commit = AsyncMock()


@pytest.mark.asyncio
async def test_dispatch_creates_run_with_deployment_id():
    """Test 1+5: PoolAgentRunRepository.create chamado com deployment_id (não assignment_id)."""
    from app.jobs.tasks import agent_deployments

    deployment = _make_deployment()
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, deployment, agent)
    run = _make_run(deployment.id, deployment.company_id)

    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()
    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(return_value=_make_agent_output())

    with patch.object(agent_deployments, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)), \
         patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo), \
         patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime), \
         patch.object(agent_deployments, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        await agent_deployments._dispatch_impl(
            deployment_id=str(deployment.id), trigger_source="cron"
        )

    mock_repo.create.assert_awaited_once()
    kwargs = mock_repo.create.await_args.kwargs
    assert kwargs["deployment_id"] == deployment.id
    assert kwargs.get("assignment_id") is None
    assert kwargs["company_id"] == deployment.company_id


@pytest.mark.asyncio
async def test_dispatch_byok_threads_tenant_company_id():
    """Test 2 BYOK CRÍTICO: runtime recebe company_id=deployment.company_id.

    Esse company_id é o chokepoint BYOK: runtime.execute seta _current_company_id
    ContextVar → _get_model() resolve tenant_llm_configs (chave própria do tenant).
    get_or_create_runtime ALSO recebe company_id (cache key per tenant).
    """
    from app.jobs.tasks import agent_deployments

    deployment = _make_deployment(company_id="byok-tenant-aaaa")
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, deployment, agent)
    run = _make_run(deployment.id, deployment.company_id)

    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()
    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(return_value=_make_agent_output())
    mock_factory = MagicMock(return_value=mock_runtime)

    with patch.object(agent_deployments, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)), \
         patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo), \
         patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", mock_factory), \
         patch.object(agent_deployments, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        await agent_deployments._dispatch_impl(
            deployment_id=str(deployment.id), trigger_source="cron"
        )

    # BYOK proof #1: runtime factory gets the tenant company_id (cache key + ContextVar binding).
    factory_kwargs = mock_factory.call_args.kwargs
    assert factory_kwargs["company_id"] == "byok-tenant-aaaa"
    # BYOK proof #2: execute() receives the SAME tenant company_id (sets _current_company_id
    # ContextVar that _get_model() reads to resolve tenant_llm_configs / BYOK key).
    exec_kwargs = mock_runtime.execute.await_args.kwargs
    assert exec_kwargs["company_id"] == "byok-tenant-aaaa"


@pytest.mark.asyncio
async def test_dispatch_multitenancy_no_cross_tenant_leak():
    """Test 3: company_id usado em create + runtime vem do deployment, nunca de payload."""
    from app.jobs.tasks import agent_deployments

    deployment = _make_deployment(company_id="company-A")
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, deployment, agent)
    run = _make_run(deployment.id, deployment.company_id)

    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()
    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(return_value=_make_agent_output())

    with patch.object(agent_deployments, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)), \
         patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo), \
         patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime), \
         patch.object(agent_deployments, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        # Even if a (rogue) trigger_context tried to inject another company, dispatch
        # MUST use deployment.company_id only.
        await agent_deployments._dispatch_impl(
            deployment_id=str(deployment.id),
            trigger_source="event_driven",
            trigger_context={"company_id": "company-B-EVIL"},
        )

    assert mock_repo.create.await_args.kwargs["company_id"] == "company-A"
    assert mock_runtime.execute.await_args.kwargs["company_id"] == "company-A"
    audit_kw = MockAudit.return_value.log_decision.await_args.kwargs
    assert audit_kw["company_id"] == "company-A"


@pytest.mark.asyncio
async def test_dispatch_error_persists_error_status_and_reraises():
    """Test 4 (REGRA 4): exception → status=error + error_message, re-raise (não silencia)."""
    from app.jobs.tasks import agent_deployments

    deployment = _make_deployment()
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, deployment, agent)
    run = _make_run(deployment.id, deployment.company_id)

    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()
    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(side_effect=RuntimeError("LLM broke"))

    with patch.object(agent_deployments, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)), \
         patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo), \
         patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime), \
         patch.object(agent_deployments, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        with pytest.raises(RuntimeError, match="LLM broke"):
            await agent_deployments._dispatch_impl(
                deployment_id=str(deployment.id), trigger_source="cron"
            )

    error_calls = [
        c for c in mock_repo.update_status.await_args_list
        if (len(c.args) > 1 and c.args[1] == "error") or c.kwargs.get("status") == "error"
    ]
    assert error_calls, "update_status(run_id, error) never called"
    assert "LLM broke" in (error_calls[0].kwargs.get("error_message") or "")


@pytest.mark.asyncio
async def test_dispatch_status_transitions_and_audit():
    """Test 7+8: queued→running→success + audit success com action agent_deployment_run."""
    from app.jobs.tasks import agent_deployments

    deployment = _make_deployment()
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, deployment, agent)
    run = _make_run(deployment.id, deployment.company_id)

    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()
    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(return_value=_make_agent_output())

    with patch.object(agent_deployments, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)), \
         patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo), \
         patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime), \
         patch.object(agent_deployments, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        await agent_deployments._dispatch_impl(
            deployment_id=str(deployment.id), trigger_source="cron"
        )

    calls = mock_repo.update_status.await_args_list
    statuses = [c.args[1] if len(c.args) > 1 else c.kwargs.get("status") for c in calls]
    assert "running" in statuses
    assert "success" in statuses
    audit_kw = MockAudit.return_value.log_decision.await_args.kwargs
    assert audit_kw["decision"] == "success"
    assert audit_kw["action"] == "agent_deployment_run"


@pytest.mark.asyncio
async def test_scheduler_scans_only_active_on_schedule_due():
    """Test 6: scan varre só is_active=true + trigger_mode=on_schedule + cron-due."""
    from app.jobs.tasks import agent_deployments

    now = datetime.now(timezone.utc)
    # Due: last_execution way in the past → */5 cron is due.
    due = _make_deployment(trigger_mode="on_schedule")
    due.schedule_cron = "*/5 * * * *"
    due.last_execution_at = now.replace(year=now.year - 1)
    # Not due: just ran, daily cron not yet due.
    not_due = _make_deployment(trigger_mode="on_schedule")
    not_due.schedule_cron = "0 9 * * *"
    not_due.last_execution_at = now

    fake_db = MagicMock()
    res = MagicMock()
    res.scalars.return_value.all.return_value = [due, not_due]
    fake_db.execute = AsyncMock(return_value=res)

    dispatched: list[str] = []

    fake_task = MagicMock()
    fake_task.delay = MagicMock(side_effect=lambda **kw: dispatched.append(kw["deployment_id"]))

    with patch.object(agent_deployments, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)), \
         patch.object(agent_deployments, "dispatch_agent_deployment_task", fake_task):
        await agent_deployments._scan_impl()

    assert str(due.id) in dispatched
    assert str(not_due.id) not in dispatched


@pytest.mark.asyncio
async def test_scheduler_skips_invalid_cron():
    """Scan: cron inválido → skip + continue (não silent fallback, loga warning)."""
    from app.jobs.tasks import agent_deployments

    bad = _make_deployment(trigger_mode="on_schedule")
    bad.schedule_cron = "not-a-cron"
    fake_db = MagicMock()
    res = MagicMock()
    res.scalars.return_value.all.return_value = [bad]
    fake_db.execute = AsyncMock(return_value=res)

    fake_task = MagicMock()
    fake_task.delay = MagicMock()

    with patch.object(agent_deployments, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)), \
         patch.object(agent_deployments, "dispatch_agent_deployment_task", fake_task):
        # Must not raise — bad cron skipped, scan continues.
        await agent_deployments._scan_impl()

    fake_task.delay.assert_not_called()
