"""
TDD RED→GREEN: tools_override parameter in AgenticLoop.run()

Tests:
  - T1: tools_override=["search_jobs"] filters to only that tool schema
  - T2: tools_override=None passes all tools (backward compat)
  - T3: tools_override=[] empty list = no tools → skips loop (guard)
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


@pytest.fixture
def agentic_loop():
    from app.orchestrator.execution.agentic_loop import AgenticLoop
    return AgenticLoop()


FAKE_SCHEMAS = [
    {"name": "search_jobs", "description": "Search jobs"},
    {"name": "search_candidates", "description": "Search candidates"},
    {"name": "get_job_details", "description": "Get job details"},
]


@pytest.mark.asyncio
async def test_tools_override_filters_schemas(agentic_loop):
    """T1: tools_override=['search_jobs'] → LLM receives only that schema."""
    with (
        patch.object(agentic_loop, "_ensure_deps"),
        patch.object(agentic_loop, "get_tool_schemas", return_value=FAKE_SCHEMAS),
        patch("app.shared.services.ai_credit_gate.check_credit_budget", new_callable=AsyncMock),
    ):
        _llm_calls = []

        async def _fake_llm(messages, tools, **kwargs):
            _llm_calls.append(tools)
            # respond with no tool calls so loop exits
            return MagicMock(
                content="ok",
                tool_calls=[],
                stop_reason="end_turn",
            )

        agentic_loop._llm_service = MagicMock()
        agentic_loop._llm_service.generate_with_tools = AsyncMock(side_effect=_fake_llm)
        agentic_loop._tool_registry = MagicMock()
        agentic_loop._tool_registry.list_tools.return_value = ["search_jobs"]
        agentic_loop._tool_executor = MagicMock()
        agentic_loop._ToolExecutionContext = MagicMock(return_value=MagicMock())

        await agentic_loop.run(
            user_message="teste",
            company_id="company-123",
            user_id="user-456",
            tools_override=["search_jobs"],
        )

    assert _llm_calls, "LLM must have been called"
    tools_sent = _llm_calls[0]
    tool_names = [t.get("name") for t in tools_sent]
    assert tool_names == ["search_jobs"], (
        f"Expected only ['search_jobs'], got {tool_names}"
    )


@pytest.mark.asyncio
async def test_tools_override_none_sends_all(agentic_loop):
    """T2: tools_override=None → all schemas passed to LLM (backward compat)."""
    with (
        patch.object(agentic_loop, "_ensure_deps"),
        patch.object(agentic_loop, "get_tool_schemas", return_value=FAKE_SCHEMAS),
        patch("app.shared.services.ai_credit_gate.check_credit_budget", new_callable=AsyncMock),
    ):
        _llm_calls = []

        async def _fake_llm(messages, tools, **kwargs):
            _llm_calls.append(tools)
            return MagicMock(content="ok", tool_calls=[], stop_reason="end_turn")

        agentic_loop._llm_service = MagicMock()
        agentic_loop._llm_service.generate_with_tools = AsyncMock(side_effect=_fake_llm)
        agentic_loop._tool_registry = MagicMock()
        agentic_loop._tool_registry.list_tools.return_value = list(FAKE_SCHEMAS)
        agentic_loop._tool_executor = MagicMock()
        agentic_loop._ToolExecutionContext = MagicMock(return_value=MagicMock())

        await agentic_loop.run(
            user_message="teste",
            company_id="company-123",
            user_id="user-456",
            tools_override=None,
        )

    assert _llm_calls
    tools_sent = _llm_calls[0]
    assert len(tools_sent) == 3, f"Expected all 3 schemas, got {len(tools_sent)}"


@pytest.mark.asyncio
async def test_tools_override_empty_skips_loop(agentic_loop):
    """T3: tools_override=[] after filtering yields empty list → loop skipped."""
    with (
        patch.object(agentic_loop, "_ensure_deps"),
        patch.object(agentic_loop, "get_tool_schemas", return_value=FAKE_SCHEMAS),
        patch("app.shared.services.ai_credit_gate.check_credit_budget", new_callable=AsyncMock),
    ):
        agentic_loop._llm_service = MagicMock()
        agentic_loop._tool_registry = MagicMock()
        agentic_loop._tool_executor = MagicMock()
        agentic_loop._ToolExecutionContext = MagicMock(return_value=MagicMock())

        result = await agentic_loop.run(
            user_message="teste",
            company_id="company-123",
            user_id="user-456",
            tools_override=["nonexistent_tool_xyz"],  # none match → empty after filter
        )

    # loop should be skipped (no tools)
    assert result.get("response") is None
    agentic_loop._llm_service.generate_with_tools.assert_not_called()
