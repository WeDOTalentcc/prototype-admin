"""
UC-P0-10 — Fail-closed tenant guard in AgenticLoop.run()

Before the fix: exec_context=None when company_id/user_id absent, loop
continued and tool calls were executed without any tenant isolation.

After the fix: run() must return immediately with an empty response dict
when either company_id or user_id is None/empty, never invoking the
ToolExecutor.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loop_with_deps():
    """
    Instantiate AgenticLoop and inject fake deps so _ensure_deps() is a no-op.
    Returns (loop, mock_tool_executor).
    """
    from app.orchestrator.execution.agentic_loop import AgenticLoop

    loop = AgenticLoop()

    # Fake ToolExecutionContext class
    class FakeCtx:
        def __init__(self, user_id, company_id):
            self.user_id = user_id
            self.company_id = company_id

    # Fake tool registry that always returns one schema so the
    # "no tools → early return" branch is NOT taken.
    fake_registry = MagicMock()
    fake_registry.list_tools.return_value = [object()]
    fake_registry.get_all_schemas.return_value = [
        {"name": "dummy_tool", "description": "dummy", "input_schema": {}}
    ]

    # Fake tool executor — must never be called in our tests
    fake_executor = MagicMock()
    fake_executor.execute = AsyncMock()

    # Fake LLM service — returns a text response (no tool calls) if somehow
    # the loop is reached, so the test doesn't hang on a real LLM call.
    fake_llm = MagicMock()
    llm_response = MagicMock()
    llm_response.is_tool_call = False
    llm_response.text_response = "fallback response"
    fake_llm.generate_with_tools = AsyncMock(return_value=llm_response)

    loop._tool_registry = fake_registry
    loop._tool_executor = fake_executor
    loop._llm_service = fake_llm
    loop._ToolExecutionContext = FakeCtx

    return loop, fake_executor


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAgenticLoopTenantGuard:

    @pytest.mark.asyncio
    async def test_missing_company_id_returns_empty_response(self):
        """company_id=None → immediate empty return, no tool execution."""
        loop, mock_executor = _make_loop_with_deps()

        result = await loop.run(
            user_message="test",
            company_id=None,
            user_id="user-123",
        )

        # Must return the empty-response shape
        assert result["response"] is None
        assert result["tool_calls_made"] == []
        assert result["iterations"] == 0

        # ToolExecutor must never have been called
        mock_executor.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_user_id_returns_empty_response(self):
        """user_id=None → immediate empty return, no tool execution."""
        loop, mock_executor = _make_loop_with_deps()

        result = await loop.run(
            user_message="test",
            company_id="company-abc",
            user_id=None,
        )

        assert result["response"] is None
        assert result["tool_calls_made"] == []
        assert result["iterations"] == 0

        mock_executor.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_both_missing_returns_empty_response(self):
        """company_id=None AND user_id=None → immediate empty return."""
        loop, mock_executor = _make_loop_with_deps()

        result = await loop.run(
            user_message="test",
            company_id=None,
            user_id=None,
        )

        assert result["response"] is None
        assert result["tool_calls_made"] == []
        assert result["iterations"] == 0

        mock_executor.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_string_company_id_returns_empty_response(self):
        """company_id='' (falsy) is treated same as None — guard triggers."""
        loop, mock_executor = _make_loop_with_deps()

        result = await loop.run(
            user_message="test",
            company_id="",
            user_id="user-123",
        )

        assert result["response"] is None
        assert result["tool_calls_made"] == []
        assert result["iterations"] == 0

        mock_executor.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_tenant_context_reaches_llm(self):
        """With valid company_id + user_id the loop proceeds normally (reaches LLM)."""
        loop, mock_executor = _make_loop_with_deps()

        result = await loop.run(
            user_message="test",
            company_id="company-abc",
            user_id="user-123",
        )

        # The fake LLM returns a text response, so the loop returns it
        assert result["response"] == "fallback response"
        # ToolExecutor was NOT called (LLM chose not to call a tool)
        mock_executor.execute.assert_not_called()
