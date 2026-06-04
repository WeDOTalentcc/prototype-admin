"""Fase A slice (supervisor A2): delegate_to_pipeline handoff tool.

Prova o padrao de delegacao hierarquica: o supervisor (agentic_loop) chama um
handoff tool que delega a um domain sub-agent via AgentRegistry.process(AgentInput)
e devolve dado estruturado. Determinístico: mocka AgentRegistry (sem DB/loop/pool).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class _FakeOutput:
    def __init__(self):
        self.message = "3 candidatos movidos para Entrevista"
        self.state_updates = {"moved": 3}
        self.error = None
        self.confidence = 0.9
        self.reasoning_steps = ["resolveu vaga", "moveu candidatos"]
        self.tool_results = []
        self.metadata = {}


@pytest.mark.asyncio
async def test_delegate_to_domain_calls_agent_process():
    from app.orchestrator.supervisor.handoff_tools import delegate_to_domain

    fake_agent = MagicMock()
    fake_agent.process = AsyncMock(return_value=_FakeOutput())
    fake_registry = MagicMock()
    fake_registry.get_instance.return_value = fake_agent

    with patch("app.shared.agents.agent_registry.AgentRegistry", return_value=fake_registry), \
         patch("app.api.v1.agent_chat_ws._ensure_agents_loaded", lambda: None):
        result = await delegate_to_domain(
            "pipeline",
            "mover candidatos da vaga X para Entrevista",
            company_id="00000000-0000-4000-a000-000000000001",
            user_id="u1",
            session_id="s1",
        )

    assert result["success"] is True
    assert result["message"] == "3 candidatos movidos para Entrevista"
    assert result["data"] == {"moved": 3}
    args, kwargs = fake_agent.process.call_args
    agent_input = args[0] if args else kwargs.get("input")
    assert agent_input.message == "mover candidatos da vaga X para Entrevista"
    assert agent_input.company_id == "00000000-0000-4000-a000-000000000001"


@pytest.mark.asyncio
async def test_delegate_unregistered_domain_fail_loud():
    from app.orchestrator.supervisor.handoff_tools import delegate_to_domain

    fake_registry = MagicMock()
    fake_registry.get_instance.return_value = None

    with patch("app.shared.agents.agent_registry.AgentRegistry", return_value=fake_registry), \
         patch("app.api.v1.agent_chat_ws._ensure_agents_loaded", lambda: None):
        result = await delegate_to_domain("pipeline", "x", company_id="c1", user_id="u1")

    assert result["success"] is False
    assert result["unavailable"] is True


def test_register_handoff_tools_registers_delegate_to_pipeline():
    from app.orchestrator.supervisor.handoff_tools import register_handoff_tools
    from app.tools.registry import tool_registry

    register_handoff_tools()
    tool = tool_registry.get_tool("delegate_to_pipeline")
    assert tool is not None
    assert "orchestrator" in tool.allowed_agents
    schema = getattr(tool, "parameters", None) or getattr(tool, "parameters_schema", None)
    assert "task" in (schema or {}).get("required", [])
