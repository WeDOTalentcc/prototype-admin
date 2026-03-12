"""
P3-A — Testes: Fallback LLM no KanbanReActAgent

Testa o bloco try/except P3-A em _process_react_loop():
1. Fallback Gemini ativado quando Claude lança erro de API (overloaded)
2. Evento de log warning emitido quando fallback é ativado
3. Erros não-API (ValueError) NÃO ativam fallback → re-raise
"""
import contextlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_agent():
    """Constrói KanbanReActAgent sem inicializar infra real."""
    from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
    agent = KanbanReActAgent.__new__(KanbanReActAgent)
    agent._memory_service = MagicMock()
    agent._memory_service.update_memory = AsyncMock()
    agent._memory_service.get_context_summary = AsyncMock(return_value="")
    agent._all_tool_names = []
    return agent


def _make_input():
    inp = MagicMock()
    inp.message = "mostre o funil"
    inp.company_id = "comp-1"
    inp.user_id = "user-1"
    inp.session_id = "sess-1"
    inp.context = {"current_stage": "pipeline_overview", "collected_data": {}}
    inp.conversation_history = []
    return inp


def _make_memory():
    mem = MagicMock()
    mem.current_stage = "pipeline_overview"
    return mem


def _common_patches(agent, make_loop_fn, mock_config, logger_mock=None):
    """Retorna ExitStack com todos os patches necessários para _process_react_loop."""
    stack = contextlib.ExitStack()
    stack.enter_context(patch.object(agent, "_load_memory", new=AsyncMock(return_value=_make_memory())))
    stack.enter_context(patch.object(agent, "_get_memory_context", new=AsyncMock(return_value={})))
    stack.enter_context(patch.object(agent, "_resolve_guardrails", new=AsyncMock(return_value={})))
    stack.enter_context(patch.object(agent, "_get_all_enhanced_tools", return_value=[]))
    stack.enter_context(patch.object(agent, "_fairness_pre_check", new=AsyncMock(return_value=None)))
    stack.enter_context(patch(
        "app.domains.recruiter_assistant.agents.kanban_react_agent.get_kanban_tools", return_value=[]
    ))
    stack.enter_context(patch(
        "app.domains.recruiter_assistant.agents.kanban_react_agent.get_stage_context", return_value="ctx"
    ))
    stack.enter_context(patch(
        "app.domains.recruiter_assistant.agents.kanban_react_agent.get_kanban_system_prompt", return_value="prompt"
    ))
    stack.enter_context(patch(
        "app.domains.recruiter_assistant.agents.kanban_react_agent.AuditCallback", return_value=MagicMock()
    ))
    stack.enter_context(patch(
        "app.domains.recruiter_assistant.agents.kanban_react_agent.ReActConfig", return_value=mock_config
    ))
    stack.enter_context(patch(
        "app.domains.recruiter_assistant.agents.kanban_react_agent.ReActLoop", side_effect=make_loop_fn
    ))
    stack.enter_context(patch(
        "app.domains.recruiter_assistant.agents.kanban_react_agent.ReActObserver",
        side_effect=Exception("skip-observer"),
    ))
    if logger_mock is not None:
        stack.enter_context(patch(
            "app.domains.recruiter_assistant.agents.kanban_react_agent.logger", logger_mock
        ))
    return stack


@pytest.mark.asyncio
async def test_fallback_activated_on_api_error():
    """Fallback Gemini é criado e executado quando Claude lança erro de overload."""
    agent = _make_agent()
    inp = _make_input()

    fallback_state = MagicMock()
    fallback_state.output = "resposta gemini"
    fallback_state.actions = []
    fallback_state.metadata = {}

    primary_loop = MagicMock()
    primary_loop.run = AsyncMock(side_effect=Exception("anthropic overloaded 529"))
    fallback_loop = MagicMock()
    fallback_loop.run = AsyncMock(return_value=fallback_state)

    call_count = 0

    def make_loop(config, working_memory_service):
        nonlocal call_count
        call_count += 1
        return primary_loop if call_count == 1 else fallback_loop

    mock_config = MagicMock()
    mock_config.model_copy = MagicMock(return_value=MagicMock())

    with _common_patches(agent, make_loop, mock_config):
        await agent._process_react_loop(inp)

    assert call_count == 2
    fallback_loop.run.assert_awaited_once()


@pytest.mark.asyncio
async def test_fallback_log_warning_emitted():
    """logger.warning é chamado quando fallback é ativado."""
    agent = _make_agent()
    inp = _make_input()

    fallback_state = MagicMock()
    fallback_state.output = "ok"
    fallback_state.actions = []
    fallback_state.metadata = {}

    primary_loop = MagicMock()
    primary_loop.run = AsyncMock(side_effect=Exception("rate_limit exceeded"))
    fallback_loop = MagicMock()
    fallback_loop.run = AsyncMock(return_value=fallback_state)

    call_count = 0

    def make_loop(config, working_memory_service):
        nonlocal call_count
        call_count += 1
        return primary_loop if call_count == 1 else fallback_loop

    mock_config = MagicMock()
    mock_config.model_copy = MagicMock(return_value=MagicMock())
    mock_logger = MagicMock()

    with _common_patches(agent, make_loop, mock_config, logger_mock=mock_logger):
        await agent._process_react_loop(inp)

    warning_calls = mock_logger.warning.call_args_list
    assert any("fallback" in str(c).lower() for c in warning_calls)


@pytest.mark.asyncio
async def test_non_api_error_not_caught():
    """ValueError (lógica interna) NÃO ativa fallback — deve propagar."""
    agent = _make_agent()
    inp = _make_input()

    primary_loop = MagicMock()
    primary_loop.run = AsyncMock(side_effect=ValueError("schema validation failed: missing field"))

    call_count = 0

    def make_loop(config, working_memory_service):
        nonlocal call_count
        call_count += 1
        return primary_loop

    mock_config = MagicMock()
    mock_config.model_copy = MagicMock(return_value=MagicMock())

    with _common_patches(agent, make_loop, mock_config):
        with pytest.raises(ValueError, match="schema validation"):
            await agent._process_react_loop(inp)

    assert call_count == 1
