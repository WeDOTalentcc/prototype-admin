import pytest
from unittest.mock import AsyncMock, MagicMock

from app.shared.agents.react_loop import ReActConfig, ToolDefinition
from app.shared.agents.observability import ReActObserver


@pytest.fixture
def mock_tool():
    fn = AsyncMock(return_value={"result": "ok", "success": True})
    return ToolDefinition(
        name="mock_tool",
        description="A mock tool for testing",
        parameters={"input": {"type": "string"}},
        function=fn,
    )


@pytest.fixture
def mock_memory_service():
    svc = MagicMock()
    svc.increment_iteration = AsyncMock()
    svc.get_or_create = AsyncMock()
    svc.update_memory = AsyncMock()
    svc.get_context_summary = AsyncMock(return_value="Test memory summary")
    return svc


@pytest.fixture
def base_react_config(mock_tool):
    return ReActConfig(
        system_prompt="You are a test agent.",
        available_tools=[mock_tool],
        max_iterations=3,
        domain="test",
        model_provider="claude",
    )


@pytest.fixture
def observer():
    return ReActObserver(
        session_id="test-session",
        domain="test",
        agent_class="TestAgent",
    )
