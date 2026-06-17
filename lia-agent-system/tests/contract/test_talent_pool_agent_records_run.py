"""Contract test for TalentPoolReActAgent.process recording PoolAgentRun.

Wave 0 Fix 1 (2026-05-27).

Pina:
  - Quando input.context["assignment_id"] está presente, process() chama
    PoolAgentRunRepository.create() + update_status (queued→running→success).
  - Quando assignment_id está ausente (chat-driven path), NÃO chama o repo
    (FK constraint exigiria — fail-open silencioso é o canonical).
  - Sucesso: runtime_metrics persistidos (latency, tokens, model, cost).
  - Erro no _process_langgraph: update_status("error") chamado, exceção
    re-raised pra retry policy.
  - Falha do repo (DB down) NÃO interrompe execução principal (fail-open).
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lia_agents_core.agent_interface import AgentInput, AgentOutput


def _make_input(company_id="00000000-0000-4000-a000-000000000001", **ctx):
    return AgentInput(
        message="acha 5 candidatos pra vaga X",
        session_id="sess-1",
        company_id=company_id,
        user_id="user-1",
        context=ctx,
    )


def _make_output():
    return AgentOutput(
        message="Achei 5",
        confidence=0.82,
        metadata={
            "tokens_input": 1200,
            "tokens_output": 350,
            "model_used": "claude-3-5-sonnet",
            "cost_usd": 0.018,
        },
    )


def _make_agent_skipping_init():
    """Bypass __init__ to avoid PostgresSaver init (which requires running loop)."""
    from app.domains.talent_pool.agents.talent_pool_agent import TalentPoolReActAgent
    agent = TalentPoolReActAgent.__new__(TalentPoolReActAgent)
    # Bind logger attr if process() touches self.logger (it doesn't but defensive)
    return agent


# -- Source AST sanity checks (independent of runtime init) -------------------


def test_process_method_imports_pool_agent_run_repository():
    """Source check: process() body references PoolAgentRunRepository."""
    src = Path("app/domains/talent_pool/agents/talent_pool_agent.py").read_text()
    assert "PoolAgentRunRepository" in src, (
        "Fix 1 não aplicado: PoolAgentRunRepository não importado em talent_pool_agent.py."
    )


def test_process_handles_assignment_id_branch():
    """Source check: process() checks for assignment_id and calls repo.create."""
    src = Path("app/domains/talent_pool/agents/talent_pool_agent.py").read_text()
    assert 'assignment_id' in src, "assignment_id reference missing"
    assert 'repo.create(' in src, "PoolAgentRunRepository.create call missing"
    assert 'update_status' in src, "update_status call missing"


def test_process_records_success_metrics():
    """Source check: success path persists runtime_metrics with latency_ms."""
    src = Path("app/domains/talent_pool/agents/talent_pool_agent.py").read_text()
    assert 'latency_ms' in src, "latency_ms not tracked in runtime_metrics"
    assert '"success"' in src, "no status='success' update"


# -- Functional tests with full mocking ---------------------------------------


@pytest.mark.asyncio
async def test_records_pool_agent_run_when_assignment_in_context():
    """assignment_id no context → cria PoolAgentRun + update_status sucesso."""
    agent = _make_agent_skipping_init()
    inp = _make_input(
        assignment_id="11111111-1111-4111-8111-111111111111",
        trigger_source="manual",
    )

    fake_run = MagicMock()
    fake_run.id = "22222222-2222-4222-8222-222222222222"
    repo_mock = MagicMock()
    repo_mock.create = AsyncMock(return_value=fake_run)
    repo_mock.update_status = AsyncMock(return_value=fake_run)

    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
    session_ctx.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository",
        return_value=repo_mock,
    ), patch(
        "app.core.database.AsyncSessionLocal",
        return_value=session_ctx,
    ), patch.object(
        type(agent), "_process_langgraph", new=AsyncMock(return_value=_make_output()),
    ):
        out = await agent.process(inp)

    assert out.message == "Achei 5"
    repo_mock.create.assert_awaited_once()
    create_kwargs = repo_mock.create.await_args.kwargs
    assert create_kwargs["assignment_id"] == "11111111-1111-4111-8111-111111111111"
    assert create_kwargs["company_id"] == inp.company_id
    assert create_kwargs["trigger_source"] in ("on_demand", "manual", "cron", "event_driven")
    assert repo_mock.update_status.await_count >= 2
    # Final call should set 'success' with runtime_metrics
    statuses_seen = [
        (c.args[1] if len(c.args) > 1 else c.kwargs.get("status"))
        for c in repo_mock.update_status.await_args_list
    ]
    assert "success" in statuses_seen
    # Find the success call and verify runtime_metrics
    success_call = [
        c for c in repo_mock.update_status.await_args_list
        if (len(c.args) > 1 and c.args[1] == "success") or c.kwargs.get("status") == "success"
    ][-1]
    runtime_metrics = success_call.kwargs.get("runtime_metrics") or {}
    assert "latency_ms" in runtime_metrics
    assert runtime_metrics.get("tokens_input") == 1200


@pytest.mark.asyncio
async def test_skips_record_when_no_assignment_id():
    """Sem assignment_id no context → não toca o repo (chat-driven path)."""
    agent = _make_agent_skipping_init()
    inp = _make_input()

    repo_mock = MagicMock()
    repo_mock.create = AsyncMock()

    with patch(
        "app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository",
        return_value=repo_mock,
    ), patch.object(
        type(agent), "_process_langgraph", new=AsyncMock(return_value=_make_output()),
    ):
        out = await agent.process(inp)

    assert out.message == "Achei 5"
    repo_mock.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_records_error_status_when_langgraph_raises():
    """Erro no _process_langgraph → update_status('error') chamado."""
    agent = _make_agent_skipping_init()
    inp = _make_input(assignment_id="11111111-1111-4111-8111-111111111111")

    fake_run = MagicMock()
    fake_run.id = "22222222-2222-4222-8222-222222222222"
    repo_mock = MagicMock()
    repo_mock.create = AsyncMock(return_value=fake_run)
    repo_mock.update_status = AsyncMock(return_value=fake_run)

    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
    session_ctx.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository",
        return_value=repo_mock,
    ), patch(
        "app.core.database.AsyncSessionLocal",
        return_value=session_ctx,
    ), patch.object(
        type(agent), "_process_langgraph",
        new=AsyncMock(side_effect=RuntimeError("LLM down")),
    ):
        with pytest.raises(RuntimeError, match="LLM down"):
            await agent.process(inp)

    statuses_seen = [
        (c.args[1] if len(c.args) > 1 else c.kwargs.get("status"))
        for c in repo_mock.update_status.await_args_list
    ]
    assert "error" in statuses_seen, (
        f"Expected status='error' update; got {statuses_seen!r}"
    )


@pytest.mark.asyncio
async def test_fail_open_when_repo_create_raises():
    """Repo.create raises → execução principal continua, exceção logada."""
    agent = _make_agent_skipping_init()
    inp = _make_input(assignment_id="11111111-1111-4111-8111-111111111111")

    repo_mock = MagicMock()
    repo_mock.create = AsyncMock(side_effect=Exception("DB connection lost"))
    repo_mock.update_status = AsyncMock()

    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
    session_ctx.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "app.domains.agent_studio.repositories.pool_agent_run_repository.PoolAgentRunRepository",
        return_value=repo_mock,
    ), patch(
        "app.core.database.AsyncSessionLocal",
        return_value=session_ctx,
    ), patch.object(
        type(agent), "_process_langgraph", new=AsyncMock(return_value=_make_output()),
    ):
        out = await agent.process(inp)

    assert out.message == "Achei 5"
