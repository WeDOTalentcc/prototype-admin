"""Agent J — emit canonical event agent_completed_review.

Test: pool_agents._dispatch_impl success path emite PlatformEvent canonical
event_type="agent_completed_review" via publish_platform_event apos
run_repo.update_status(run.id, "success", ...) + db.commit() + audit dim 5.
"""
from __future__ import annotations

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


def _make_agent_output():
    out = MagicMock()
    out.message = "ok"
    out.confidence = 0.95
    out.actions = []
    out.metadata = {"tokens_input": 100, "tokens_output": 50}
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


def _make_agent():
    ag = MagicMock()
    ag.id = uuid4()
    ag.name = "TestAgent"
    ag.system_prompt = "Test prompt"
    ag.allowed_tools = ["search_candidates"]
    ag.domain = "custom"
    ag.max_steps = 8
    ag.temperature = 0.7
    ag.model_override = None
    ag.config = {}
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
    return r


def _patch_db_load(fake_db, assignment, agent):
    res_a = MagicMock()
    res_a.scalar_one_or_none = MagicMock(return_value=assignment)
    res_c = MagicMock()
    res_c.scalar_one_or_none = MagicMock(return_value=agent)
    fake_db.execute = AsyncMock(side_effect=[res_a, res_c])
    fake_db.commit = AsyncMock()


@pytest.mark.asyncio
async def test_dispatch_success_emits_agent_completed_review():
    """_dispatch_impl success emite agent_completed_review canonical."""
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

    with patch.object(pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)), \
         patch("app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository", return_value=mock_repo), \
         patch("app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime", return_value=mock_runtime), \
         patch.object(pool_agents, "AuditService") as MockAudit, \
         patch.object(pool_agents, "publish_platform_event", new=AsyncMock(return_value=True)) as mock_emit:
        MockAudit.return_value.log_decision = AsyncMock()
        await pool_agents._dispatch_impl(
            assignment_id=str(assignment.id), trigger_source="cron"
        )

    mock_emit.assert_awaited()
    found = [
        c for c in mock_emit.await_args_list
        if c.args and getattr(c.args[0], "event_type", "") == "agent_completed_review"
    ]
    assert len(found) == 1, f"esperava 1 emit agent_completed_review, achei {len(found)}"
    event = found[0].args[0]
    assert event.company_id == assignment.company_id
    assert event.payload["assignment_id"] == str(assignment.id)
    assert event.payload["run_id"] == str(run.id)
    assert event.payload["agent_id"] == str(agent.id)
    assert "completed_at" in event.payload
