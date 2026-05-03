"""UC-P2-08: ToolExecutor.execute() must add a Sentry breadcrumb on tool failure."""
import asyncio
from unittest.mock import MagicMock


def _make_executor_with_failing_tool():
    """Build a ToolExecutor whose registered tool always raises RuntimeError."""
    from app.tools.executor import ToolExecutor, ToolRegistry

    registry = ToolRegistry()

    async def _failing_handler(**kwargs):
        raise RuntimeError("simulated tool failure")

    tool_def = MagicMock()
    tool_def.name = "test_fail_tool"
    tool_def.allowed_agents = None
    tool_def.parameters_schema = {"type": "object", "properties": {}}
    tool_def.handler = _failing_handler

    registry._tools = {"test_fail_tool": tool_def}
    executor = ToolExecutor(registry=registry)
    return executor


def test_tool_failure_adds_sentry_breadcrumb(monkeypatch):
    """UC-P2-08: failed tool call triggers sentry_sdk.add_breadcrumb with category=tool.error."""
    import app.tools.executor as executor_mod

    breadcrumb_calls = []
    tag_calls = []

    fake_sentry = MagicMock()
    fake_sentry.add_breadcrumb.side_effect = lambda **kw: breadcrumb_calls.append(kw)
    fake_sentry.set_tag.side_effect = lambda k, v: tag_calls.append((k, v))

    monkeypatch.setattr(executor_mod, "_sentry_sdk", fake_sentry)
    monkeypatch.setattr(executor_mod, "_SENTRY_AVAILABLE", True)

    executor = _make_executor_with_failing_tool()
    result = asyncio.get_event_loop().run_until_complete(
        executor.execute("test_fail_tool", {}, agent_type="test_agent")
    )

    assert not result.success, "Expected failure result"
    assert len(breadcrumb_calls) == 1, f"Expected 1 breadcrumb, got {len(breadcrumb_calls)}"
    crumb = breadcrumb_calls[0]
    assert crumb["category"] == "tool.error", f"Wrong category: {crumb['category']}"
    assert crumb["level"] == "error"
    assert "test_fail_tool" in crumb["message"]
    assert crumb["data"]["tool_name"] == "test_fail_tool"
    assert crumb["data"]["error_type"] == "RuntimeError"

    assert any(k == "tool.last_failed" and v == "test_fail_tool" for k, v in tag_calls), (
        f"set_tag not called correctly: {tag_calls}"
    )


def test_tool_failure_no_breadcrumb_when_sentry_unavailable(monkeypatch):
    """UC-P2-08: when sentry is unavailable, no AttributeError is raised."""
    import app.tools.executor as executor_mod

    monkeypatch.setattr(executor_mod, "_SENTRY_AVAILABLE", False)
    monkeypatch.setattr(executor_mod, "_sentry_sdk", None)

    executor = _make_executor_with_failing_tool()
    result = asyncio.get_event_loop().run_until_complete(
        executor.execute("test_fail_tool", {}, agent_type="test_agent")
    )
    assert not result.success
