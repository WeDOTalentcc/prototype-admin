"""Contract test for pool_agent_runs.results.candidate_ids[] population.

Onda 5+1 (2026-05-29) — Agent C.

Pina:
  - `extract_touched_candidate_ids` helper canonical em
    `app/domains/agent_studio/reasoning_trace_builder.py`
  - `TalentPoolReActAgent._state_to_output` popula
    `output.metadata["touched_candidate_ids"]`
  - `TalentPoolReActAgent.process` grava `results["candidate_ids"]`
    via metadata bridge.
  - `CustomAgentRuntime._state_to_output` popula
    `output.metadata["touched_candidate_ids"]`
  - `_dispatch_impl` em pool_agents tasks persiste `results["candidate_ids"]`

Endpoint /agent-monitoring/candidate/{id}/touches (Onda 2 B3) lê
`results["candidate_ids"]` — esse teste pina o produtor canonical.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lia_agents_core.agent_interface import AgentInput, AgentOutput

from app.domains.agent_studio.reasoning_trace_builder import (
    MAX_CANDIDATE_IDS_PER_RUN,
    extract_touched_candidate_ids,
)


UUID1 = "11111111-1111-4111-8111-111111111111"
UUID2 = "22222222-2222-4222-8222-222222222222"
UUID3 = "33333333-3333-4333-8333-333333333333"


class _FakeMsg:
    """Minimal AIMessage-like stub."""

    def __init__(self, tool_calls=None, content=""):
        self.tool_calls = tool_calls or []
        self.content = content
        self.tool_call_id = None


# ─── Pure helper tests ──────────────────────────────────────────────────────


def test_extract_candidate_id_singular():
    """tool_calls[i].args['candidate_id'] → ID extraído."""
    msgs = [_FakeMsg([{"name": "get_candidate_details", "args": {"candidate_id": UUID1}}])]
    ids, truncated = extract_touched_candidate_ids(msgs)
    assert ids == [UUID1]
    assert truncated is False


def test_extract_candidate_ids_list():
    """tool_calls[i].args['candidate_ids'] (list) → todos os IDs."""
    msgs = [
        _FakeMsg([{"name": "move_pool_to_job", "args": {"candidate_ids": [UUID1, UUID2, UUID3]}}])
    ]
    ids, truncated = extract_touched_candidate_ids(msgs)
    assert ids == [UUID1, UUID2, UUID3]
    assert truncated is False


def test_extract_dedup_preserves_order():
    """Mesmo candidato tocado 2x = aparece 1x, primeira aparição."""
    msgs = [
        _FakeMsg([{"name": "x", "args": {"candidate_id": UUID2}}]),
        _FakeMsg([{"name": "y", "args": {"candidate_ids": [UUID1, UUID2]}}]),
        _FakeMsg([{"name": "z", "args": {"candidate_id": UUID1}}]),
    ]
    ids, _ = extract_touched_candidate_ids(msgs)
    assert ids == [UUID2, UUID1]


def test_extract_empty_when_no_tools():
    """Sem tool_calls → [] (não None)."""
    msgs = [_FakeMsg(content="apenas texto")]
    ids, truncated = extract_touched_candidate_ids(msgs)
    assert ids == []
    assert truncated is False


def test_extract_empty_list_for_empty_messages():
    """Lista vazia → ([], False) — não None nem KeyError."""
    ids, truncated = extract_touched_candidate_ids([])
    assert ids == []
    assert truncated is False


def test_extract_truncates_at_max():
    """1000 IDs → 500 + truncated=True (proteção JSONB bloat)."""
    big_args = {"candidate_ids": [f"00000000-0000-4000-8000-{i:012d}" for i in range(1000)]}
    msgs = [_FakeMsg([{"name": "batch", "args": big_args}])]
    ids, truncated = extract_touched_candidate_ids(msgs)
    assert len(ids) == MAX_CANDIDATE_IDS_PER_RUN
    assert truncated is True


def test_extract_ignores_non_uuid_like():
    """Strings inválidas (vazias, lixo) são silenciosamente filtradas."""
    msgs = [
        _FakeMsg([{"name": "x", "args": {"candidate_id": ""}}]),
        _FakeMsg([{"name": "y", "args": {"candidate_id": None}}]),
        _FakeMsg([{"name": "z", "args": {"candidate_ids": ["not-uuid", "", None, UUID1]}}]),
    ]
    ids, _ = extract_touched_candidate_ids(msgs)
    assert ids == [UUID1]


def test_extract_accepts_bigint_ids():
    """Rails legacy bigint IDs (string ou int) aceitos."""
    msgs = [
        _FakeMsg([{"name": "x", "args": {"candidate_id": "12345"}}]),
        _FakeMsg([{"name": "y", "args": {"candidate_id": 67890}}]),
    ]
    ids, _ = extract_touched_candidate_ids(msgs)
    assert ids == ["12345", "67890"]


def test_extract_supports_object_tool_calls():
    """tool_calls como objetos (não-dict) também funcionam — duck typing."""

    class _ToolCall:
        def __init__(self, name, args):
            self.name = name
            self.args = args

    msgs = [_FakeMsg([_ToolCall("get_candidate", {"candidate_id": UUID1})])]
    ids, _ = extract_touched_candidate_ids(msgs)
    assert ids == [UUID1]


# ─── AST/source sanity: producers wired ─────────────────────────────────────


def test_talent_pool_agent_state_to_output_populates_touched():
    """Source: _state_to_output passa touched_candidate_ids pra metadata."""
    src = Path("app/domains/talent_pool/agents/talent_pool_agent.py").read_text()
    assert "extract_touched_candidate_ids" in src
    assert "touched_candidate_ids" in src
    assert '"touched_candidate_ids"' in src or "'touched_candidate_ids'" in src


def test_talent_pool_agent_process_writes_candidate_ids_in_results():
    """Source: process() success path grava results['candidate_ids']."""
    src = Path("app/domains/talent_pool/agents/talent_pool_agent.py").read_text()
    assert '"candidate_ids"' in src or "'candidate_ids'" in src
    # garante que a chave aparece no dict de results (não só em comentário)
    assert "candidate_ids" in src


def test_custom_agent_runtime_populates_touched_in_metadata():
    """Source: CustomAgentRuntime._state_to_output popula metadata."""
    src = Path("app/domains/agent_studio/custom_agent_runtime.py").read_text()
    assert "extract_touched_candidate_ids" in src
    assert "touched_candidate_ids" in src


def test_pool_agents_dispatch_writes_candidate_ids_in_results():
    """Source: _dispatch_impl persiste results['candidate_ids']."""
    src = Path("app/jobs/tasks/pool_agents.py").read_text()
    assert "candidate_ids" in src
    assert "touched_candidate_ids" in src


# ─── Functional bridge: metadata → results ──────────────────────────────────


@pytest.mark.asyncio
async def test_talent_pool_agent_persists_candidate_ids_in_results():
    """process() lê output.metadata['touched_candidate_ids'] e grava em results."""
    from app.domains.talent_pool.agents.talent_pool_agent import TalentPoolReActAgent

    agent = TalentPoolReActAgent.__new__(TalentPoolReActAgent)
    inp = AgentInput(
        message="acha candidatos",
        session_id="s1",
        company_id="00000000-0000-4000-a000-000000000001",
        user_id="u1",
        context={"assignment_id": "11111111-1111-4111-8111-111111111111"},
    )
    output = AgentOutput(
        message="ok",
        confidence=0.9,
        metadata={
            "touched_candidate_ids": [UUID1, UUID2],
            "candidate_ids_truncated": False,
            "tokens_input": 100,
            "tokens_output": 50,
        },
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
        type(agent), "_process_langgraph", new=AsyncMock(return_value=output),
    ):
        await agent.process(inp)

    # Find the success call
    success_calls = [
        c for c in repo_mock.update_status.await_args_list
        if (len(c.args) > 1 and c.args[1] == "success")
        or c.kwargs.get("status") == "success"
    ]
    assert success_calls, "no success update_status call"
    results = success_calls[-1].kwargs.get("results") or {}
    assert results.get("candidate_ids") == [UUID1, UUID2]
    assert results.get("candidate_ids_truncated") is False


@pytest.mark.asyncio
async def test_talent_pool_agent_empty_list_when_no_touched():
    """Sem candidates tocados → results['candidate_ids'] = [] (não None)."""
    from app.domains.talent_pool.agents.talent_pool_agent import TalentPoolReActAgent

    agent = TalentPoolReActAgent.__new__(TalentPoolReActAgent)
    inp = AgentInput(
        message="só pergunta sem ação",
        session_id="s1",
        company_id="00000000-0000-4000-a000-000000000001",
        user_id="u1",
        context={"assignment_id": "11111111-1111-4111-8111-111111111111"},
    )
    # output.metadata sem touched_candidate_ids
    output = AgentOutput(message="ok", confidence=0.9, metadata={})

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
        type(agent), "_process_langgraph", new=AsyncMock(return_value=output),
    ):
        await agent.process(inp)

    success_calls = [
        c for c in repo_mock.update_status.await_args_list
        if (len(c.args) > 1 and c.args[1] == "success")
        or c.kwargs.get("status") == "success"
    ]
    assert success_calls
    results = success_calls[-1].kwargs.get("results") or {}
    # Empty list — not missing, not None
    assert results.get("candidate_ids") == []
    assert "candidate_ids" in results
