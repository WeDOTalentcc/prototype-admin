"""Sprint 7C Part 1.5b/c — orchestrator real wire CustomAgentRuntime tests.

Cobre:
- Test 1: _dispatch_impl cria PoolAgentRun record canonical.
- Test 2: status transitions queued→running→success.
- Test 3: error path persiste status=error + error_message.
- Test 4: audit dim 5 wired pra success + error.
- Test 5: assignment.last_run_at + last_run_status updated.
- Test 6: stateless (session_id=run.id, sem shared state cross-runs).

Pattern canonical: mock CustomAgentRuntime.execute via AsyncMock; mock
PoolAgentRunRepository ops; verifica chamadas + side effects.
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


def _make_assignment(company_id="11111111-1111-1111-1111-111111111111"):
    a = MagicMock()
    a.id = uuid4()
    a.company_id = company_id
    a.talent_pool_id = uuid4()
    a.custom_agent_id = uuid4()
    a.last_run_at = None
    a.last_run_status = None
    return a


def _make_agent(name="TestAgent", config=None):
    ag = MagicMock()
    ag.id = uuid4()
    ag.name = name
    ag.system_prompt = "Test prompt"
    ag.allowed_tools = ["search_candidates"]
    ag.domain = "custom"
    ag.max_steps = 8
    ag.temperature = 0.7
    ag.model_override = None
    ag.config = config or {}
    ag.enable_memory = True
    ag.excluded_tools = []
    ag.context_level = "full"
    return ag


def _make_run(assignment_id, company_id):
    r = MagicMock()
    r.id = uuid4()
    r.assignment_id = assignment_id
    r.company_id = company_id
    r.status = "queued"
    r.started_at = None
    r.finished_at = None
    return r


def _patch_db_load(fake_db, assignment, agent):
    """Make db.execute return assignment first, then agent."""
    res_a = MagicMock()
    res_a.scalar_one_or_none = MagicMock(return_value=assignment)
    res_c = MagicMock()
    res_c.scalar_one_or_none = MagicMock(return_value=agent)
    fake_db.execute = AsyncMock(side_effect=[res_a, res_c])
    fake_db.commit = AsyncMock()


@pytest.mark.asyncio
async def test_dispatch_real_creates_run_record():
    """Test 1: PoolAgentRunRepository.create chamada com canonical args."""
    from app.jobs.tasks import pool_agents

    assignment = _make_assignment()
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, assignment, agent)
    run = _make_run(assignment.id, assignment.company_id)

    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()

    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(return_value=_make_agent_output())

    with patch.object(pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)),          patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo),          patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime),          patch.object(pool_agents, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        await pool_agents._dispatch_impl(
            assignment_id=str(assignment.id), trigger_source="cron"
        )

    mock_repo.create.assert_awaited_once()
    kwargs = mock_repo.create.await_args.kwargs
    assert kwargs["assignment_id"] == assignment.id
    assert kwargs["company_id"] == assignment.company_id
    assert kwargs["trigger_source"] == "cron"


@pytest.mark.asyncio
async def test_dispatch_real_status_transitions_success():
    """Test 2: update_status chamado queued→running→success."""
    from app.jobs.tasks import pool_agents

    assignment = _make_assignment()
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, assignment, agent)
    run = _make_run(assignment.id, assignment.company_id)

    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()

    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(return_value=_make_agent_output())

    with patch.object(pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)),          patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo),          patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime),          patch.object(pool_agents, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        await pool_agents._dispatch_impl(
            assignment_id=str(assignment.id), trigger_source="on_demand"
        )

    calls = mock_repo.update_status.await_args_list
    statuses = [c.args[1] if len(c.args) > 1 else c.kwargs.get("status") for c in calls]
    assert "running" in statuses
    assert "success" in statuses


@pytest.mark.asyncio
async def test_dispatch_real_error_persists_error_status():
    """Test 3: exception em runtime.execute → run.status=error + error_message persistido."""
    from app.jobs.tasks import pool_agents

    assignment = _make_assignment()
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, assignment, agent)
    run = _make_run(assignment.id, assignment.company_id)

    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()

    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(side_effect=RuntimeError("LLM broke"))

    with patch.object(pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)),          patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo),          patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime),          patch.object(pool_agents, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        with pytest.raises(RuntimeError, match="LLM broke"):
            await pool_agents._dispatch_impl(
                assignment_id=str(assignment.id), trigger_source="cron"
            )

    # error update_status was called.
    error_calls = [
        c for c in mock_repo.update_status.await_args_list
        if (len(c.args) > 1 and c.args[1] == "error") or c.kwargs.get("status") == "error"
    ]
    assert error_calls, "update_status(run_id, error) never called"
    assert "LLM broke" in (error_calls[0].kwargs.get("error_message") or "")


@pytest.mark.asyncio
async def test_dispatch_real_audit_success_and_error_paths():
    """Test 4: AuditService.log_decision wired em both paths (success + error)."""
    from app.jobs.tasks import pool_agents

    # SUCCESS path
    assignment = _make_assignment()
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, assignment, agent)
    run = _make_run(assignment.id, assignment.company_id)
    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()
    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(return_value=_make_agent_output())

    with patch.object(pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)),          patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo),          patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime),          patch.object(pool_agents, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        await pool_agents._dispatch_impl(
            assignment_id=str(assignment.id), trigger_source="cron"
        )
        kw = MockAudit.return_value.log_decision.await_args.kwargs
        assert kw["decision"] == "success"
        assert "pool_agent_dispatch_cron" in kw["action"]

    # ERROR path
    assignment2 = _make_assignment()
    agent2 = _make_agent()
    fake_db2 = MagicMock()
    _patch_db_load(fake_db2, assignment2, agent2)
    run2 = _make_run(assignment2.id, assignment2.company_id)
    mock_repo2 = MagicMock()
    mock_repo2.create = AsyncMock(return_value=run2)
    mock_repo2.update_status = AsyncMock()
    mock_runtime2 = MagicMock()
    mock_runtime2.execute = AsyncMock(side_effect=RuntimeError("boom"))

    with patch.object(pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db2)),          patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo2),          patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime2),          patch.object(pool_agents, "AuditService") as MockAudit2:
        MockAudit2.return_value.log_decision = AsyncMock()
        with pytest.raises(RuntimeError):
            await pool_agents._dispatch_impl(
                assignment_id=str(assignment2.id), trigger_source="on_demand"
            )
        kw2 = MockAudit2.return_value.log_decision.await_args.kwargs
        assert kw2["decision"] == "error"


@pytest.mark.asyncio
async def test_dispatch_real_updates_assignment_last_run():
    """Test 5: assignment.last_run_at + last_run_status setados (success path)."""
    from app.jobs.tasks import pool_agents

    assignment = _make_assignment()
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, assignment, agent)
    run = _make_run(assignment.id, assignment.company_id)
    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()
    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(return_value=_make_agent_output())

    with patch.object(pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)),          patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo),          patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime),          patch.object(pool_agents, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        await pool_agents._dispatch_impl(
            assignment_id=str(assignment.id), trigger_source="cron"
        )

    assert assignment.last_run_at is not None
    assert assignment.last_run_status == "success"


@pytest.mark.asyncio
async def test_dispatch_real_stateless_session_id_per_run():
    """Test 6: runtime.execute chamado com session_id=str(run.id) — stateless per dispatch.

    Cada dispatch usa run.id como session_id → conversation isolada, sem shared memory.
    """
    from app.jobs.tasks import pool_agents

    assignment = _make_assignment()
    agent = _make_agent()
    fake_db = MagicMock()
    _patch_db_load(fake_db, assignment, agent)
    run = _make_run(assignment.id, assignment.company_id)
    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=run)
    mock_repo.update_status = AsyncMock()
    mock_runtime = MagicMock()
    mock_runtime.execute = AsyncMock(return_value=_make_agent_output())

    with patch.object(pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)),          patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo),          patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime),          patch.object(pool_agents, "AuditService") as MockAudit:
        MockAudit.return_value.log_decision = AsyncMock()
        await pool_agents._dispatch_impl(
            assignment_id=str(assignment.id), trigger_source="cron"
        )

    mock_runtime.execute.assert_awaited_once()
    exec_kwargs = mock_runtime.execute.await_args.kwargs
    assert exec_kwargs["session_id"] == str(run.id)
    assert exec_kwargs["context"]["run_id"] == str(run.id)
