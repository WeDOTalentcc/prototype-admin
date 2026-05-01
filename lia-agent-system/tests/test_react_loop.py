import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lia_agents_core.react_loop import ReActLoop, ReActState, ReActConfig, ToolDefinition
from lia_agents_core.agent_interface import AgentInput, AgentOutput
from lia_agents_core.observability import ReActObserver


class TestReActState:
    def test_initial_state(self):
        state = ReActState()
        assert state.iteration == 0
        assert state.observations == []
        assert state.tool_calls_made == []
        assert state.should_respond is False
        assert state.failed_tool_calls == []
        assert state.messages == []
        assert state.current_reasoning == ""
        assert state.actions_taken == []
        assert state.final_response is None
        assert state.error is None

    def test_state_with_values(self):
        state = ReActState(
            iteration=3,
            observations=["obs1", "obs2"],
            should_respond=True,
            final_response="done",
        )
        assert state.iteration == 3
        assert len(state.observations) == 2
        assert state.should_respond is True
        assert state.final_response == "done"

    def test_failed_tool_calls_tracking(self):
        state = ReActState()
        state.failed_tool_calls.append('{"tool": "test", "args": {}}')
        assert len(state.failed_tool_calls) == 1

    def test_consecutive_duplicate_count(self):
        state = ReActState()
        assert state.consecutive_duplicate_count == 0
        assert state.last_tool_call_key is None


@pytest.mark.skip(reason="ReActLoop removido — agentes usam LangGraph nativo (create_react_agent)")
class TestReActLoop:
    @pytest.fixture
    def mock_tool_fn(self):
        fn = AsyncMock(return_value={"result": "success", "success": True})
        return fn

    @pytest.fixture
    def sample_tools(self, mock_tool_fn):
        return [
            ToolDefinition(
                name="test_tool",
                description="A test tool",
                parameters={"query": {"type": "string"}},
                function=mock_tool_fn,
            )
        ]

    @pytest.fixture
    def react_config(self, sample_tools):
        return ReActConfig(
            system_prompt="Test prompt",
            available_tools=sample_tools,
            max_iterations=3,
            domain="test",
            model_provider="claude",
        )

    @pytest.fixture
    def mock_memory_service(self):
        svc = MagicMock()
        svc.increment_iteration = AsyncMock()
        return svc

    @pytest.fixture
    def react_loop(self, react_config, mock_memory_service):
        return ReActLoop(config=react_config, working_memory_service=mock_memory_service)

    @pytest.mark.asyncio
    async def test_max_iterations_reached(self, react_loop):
        generate_response = "Final response after max iterations"

        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 6:
                return json.dumps({
                    "thought": f"need to call tool attempt {call_count}",
                    "action": "call_tool",
                    "tool_name": "test_tool",
                    "tool_args": {"query": f"test_{call_count}"},
                    "response": None,
                })
            return generate_response

        with patch("lia_agents_core.react_loop.llm_service.generate", side_effect=mock_generate):
            state = await react_loop.run(
                message="test message",
                context={},
                session_id="test-session",
            )

        assert state.should_respond is True
        assert state.final_response is not None
        assert state.iteration <= 3

    @pytest.mark.asyncio
    async def test_tool_failure_tracking(self, react_loop, mock_tool_fn):
        mock_tool_fn.return_value = {"error": "failed", "success": False}

        tool_call_response = json.dumps({
            "thought": "calling tool",
            "action": "call_tool",
            "tool_name": "test_tool",
            "tool_args": {"query": "fail"},
            "response": None,
        })

        respond_response = json.dumps({
            "thought": "tool failed, respond",
            "action": "respond",
            "tool_name": None,
            "tool_args": {},
            "response": "Sorry, the tool failed",
        })

        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return tool_call_response
            return respond_response

        with patch("lia_agents_core.react_loop.llm_service.generate", side_effect=mock_generate):
            state = await react_loop.run(
                message="test",
                context={},
                session_id="test-session",
            )

        assert len(state.failed_tool_calls) == 1

    @pytest.mark.asyncio
    async def test_duplicate_call_guard(self):
        success_tool_fn = AsyncMock(return_value={"result": "same", "success": True})
        tools = [
            ToolDefinition(
                name="dup_tool",
                description="A tool for dup testing",
                parameters={},
                function=success_tool_fn,
            )
        ]
        config = ReActConfig(
            system_prompt="Test",
            available_tools=tools,
            max_iterations=10,
            domain="test",
            model_provider="claude",
        )
        mock_mem = MagicMock()
        mock_mem.increment_iteration = AsyncMock()
        loop = ReActLoop(config=config, working_memory_service=mock_mem)

        tool_call_response = json.dumps({
            "thought": "calling tool again",
            "action": "call_tool",
            "tool_name": "dup_tool",
            "tool_args": {"query": "same"},
            "response": None,
        })

        generate_response = "Forced response"

        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 20:
                return tool_call_response
            return generate_response

        with patch("lia_agents_core.react_loop.llm_service.generate", side_effect=mock_generate):
            state = await loop.run(
                message="test",
                context={},
                session_id="test-session",
            )

        assert state.should_respond is True
        assert state.consecutive_duplicate_count >= 2

    @pytest.mark.asyncio
    async def test_successful_response(self, react_loop):
        respond_response = json.dumps({
            "thought": "I can respond directly",
            "action": "respond",
            "tool_name": None,
            "tool_args": {},
            "response": "Here is my direct response",
        })

        with patch("lia_agents_core.react_loop.llm_service.generate", new_callable=AsyncMock, return_value=respond_response):
            state = await react_loop.run(
                message="hello",
                context={},
                session_id="test-session",
            )

        assert state.should_respond is True
        assert state.final_response == "Here is my direct response"
        assert state.iteration == 1
        assert len(state.tool_calls_made) == 0

    @pytest.mark.asyncio
    async def test_unknown_tool_skipped(self, react_loop):
        unknown_tool_response = json.dumps({
            "thought": "using unknown tool",
            "action": "call_tool",
            "tool_name": "nonexistent_tool",
            "tool_args": {},
            "response": None,
        })

        respond_response = json.dumps({
            "thought": "tool not found, respond",
            "action": "respond",
            "tool_name": None,
            "tool_args": {},
            "response": "Tool not available",
        })

        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return unknown_tool_response
            return respond_response

        with patch("lia_agents_core.react_loop.llm_service.generate", side_effect=mock_generate):
            state = await react_loop.run(
                message="test",
                context={},
                session_id="test-session",
            )

        assert any("not available" in obs for obs in state.observations)

    @pytest.mark.asyncio
    async def test_observer_integration(self, react_loop):
        observer = ReActObserver(
            session_id="test-session",
            domain="test",
            agent_class="TestAgent",
        )

        respond_response = json.dumps({
            "thought": "responding",
            "action": "respond",
            "tool_name": None,
            "tool_args": {},
            "response": "Direct response",
        })

        with patch("lia_agents_core.react_loop.llm_service.generate", new_callable=AsyncMock, return_value=respond_response):
            state = await react_loop.run(
                message="hello",
                context={},
                session_id="test-session",
                observer=observer,
            )

        assert state.should_respond is True
        assert observer.log.total_iterations == 1
        assert len(observer.log.iterations) > 0

    @pytest.mark.asyncio
    async def test_guardrail_blocks_tool(self, react_loop):
        react_loop.config.guardrails = ["test_tool"]

        tool_call_response = json.dumps({
            "thought": "calling guarded tool",
            "action": "call_tool",
            "tool_name": "test_tool",
            "tool_args": {"query": "data"},
            "response": None,
        })

        with patch("lia_agents_core.react_loop.llm_service.generate", new_callable=AsyncMock, return_value=tool_call_response):
            state = await react_loop.run(
                message="test",
                context={},
                session_id="test-session",
            )

        assert state.should_respond is True
        assert "confirmation" in state.final_response.lower()
        assert any(a.get("type") == "guardrail_blocked" for a in state.actions_taken)

    @pytest.mark.asyncio
    async def test_parse_reasoning_json_code_fence(self, react_loop):
        raw = '```json\n{"thought": "test", "action": "respond", "response": "ok"}\n```'
        parsed = react_loop._parse_reasoning(raw)
        assert parsed["thought"] == "test"
        assert parsed["action"] == "respond"

    @pytest.mark.asyncio
    async def test_parse_reasoning_plain_json(self, react_loop):
        raw = '{"thought": "plain", "action": "respond", "response": "hi"}'
        parsed = react_loop._parse_reasoning(raw)
        assert parsed["thought"] == "plain"

    @pytest.mark.asyncio
    async def test_error_handling(self, react_loop):
        async def failing_generate(*args, **kwargs):
            raise RuntimeError("LLM service down")

        with patch("lia_agents_core.react_loop.llm_service.generate", side_effect=failing_generate):
            state = await react_loop.run(
                message="test",
                context={},
                session_id="test-session",
            )

        assert state.error is not None
        assert state.should_respond is True
        assert state.final_response is not None


class TestReActObserver:
    def test_observer_initialization(self):
        observer = ReActObserver(
            session_id="s1",
            domain="wizard",
            agent_class="WizardReActAgent",
        )
        assert observer.log.session_id == "s1"
        assert observer.log.domain == "wizard"
        assert observer.log.agent_class == "WizardReActAgent"
        assert observer.log.start_time is not None
        assert observer.log.total_iterations == 0

    def test_start_iteration(self):
        observer = ReActObserver("s1", "wizard", "WizardReActAgent")
        observer.start_iteration(1)
        assert observer.log.total_iterations == 1
        assert observer._iteration_start is not None

    def test_log_reasoning(self):
        observer = ReActObserver("s1", "wizard", "WizardReActAgent")
        observer.start_iteration(1)
        observer.log_reasoning(1, "Thinking about the problem")
        assert len(observer.log.iterations) == 1
        assert observer.log.iterations[0]["phase"] == "reason"
        assert observer.log.iterations[0]["reasoning"] == "Thinking about the problem"

    def test_log_tool_call_success(self):
        observer = ReActObserver("s1", "wizard", "WizardReActAgent")
        observer.log_tool_call(1, "search_tool", {"query": "test"}, True, 150.5)
        assert observer.log.tools_succeeded == 1
        assert observer.log.tools_failed == 0
        assert "search_tool" in observer.log.tools_called
        assert len(observer.log.iterations) == 1
        assert observer.log.iterations[0]["tool_success"] is True

    def test_log_tool_call_failure(self):
        observer = ReActObserver("s1", "wizard", "WizardReActAgent")
        observer.log_tool_call(1, "bad_tool", {}, False, 50.0)
        assert observer.log.tools_succeeded == 0
        assert observer.log.tools_failed == 1

    def test_log_decision(self):
        observer = ReActObserver("s1", "wizard", "WizardReActAgent")
        observer.start_iteration(1)
        observer.log_decision(1, "continue")
        assert len(observer.log.iterations) == 1
        assert observer.log.iterations[0]["phase"] == "decide"
        assert observer.log.iterations[0]["decision"] == "continue"

    def test_finalize(self):
        observer = ReActObserver("s1", "wizard", "WizardReActAgent")
        observer.log.stage_before = "input-evaluation"
        observer.start_iteration(1)
        observer.log_tool_call(1, "tool_a", {}, True, 100.0)
        observer.log_decision(1, "respond")

        result = observer.finalize(
            confidence=0.85,
            response_length=120,
            stage_after="jd-enrichment",
        )

        assert result["final_confidence"] == 0.85
        assert result["response_length"] == 120
        assert result["stage_after"] == "jd-enrichment"
        assert result["stage_transitioned"] is True
        assert result["end_time"] is not None
        assert result["total_duration_ms"] > 0
        assert result["error"] is None

    def test_finalize_no_transition(self):
        observer = ReActObserver("s1", "wizard", "WizardReActAgent")
        observer.log.stage_before = "input-evaluation"

        result = observer.finalize(
            confidence=0.7,
            response_length=50,
            stage_after="input-evaluation",
        )

        assert result["stage_transitioned"] is False

    def test_finalize_with_error(self):
        observer = ReActObserver("s1", "wizard", "WizardReActAgent")

        result = observer.finalize(
            confidence=0.0,
            response_length=0,
            error="Something went wrong",
        )

        assert result["error"] == "Something went wrong"
        assert result["final_confidence"] == 0.0


class TestWizardStageDefinitions:
    def test_stage_validation(self):
        from app.domains.job_management.agents.stage_context import STAGE_DEFINITIONS

        for stage_name, stage in STAGE_DEFINITIONS.items():
            assert stage.get("name"), f"Stage {stage_name} missing 'name'"
            assert stage.get("description"), f"Stage {stage_name} missing 'description'"
            assert isinstance(stage.get("required_fields", []), list), (
                f"Stage {stage_name} required_fields should be a list"
            )
            assert isinstance(stage.get("optional_fields", []), list), (
                f"Stage {stage_name} optional_fields should be a list"
            )
            assert "next_stage" in stage, f"Stage {stage_name} missing 'next_stage'"
            assert "phase" in stage, f"Stage {stage_name} missing 'phase'"
            assert stage.get("transition_criteria"), (
                f"Stage {stage_name} missing 'transition_criteria'"
            )

    def test_stage_chain_completeness(self):
        from app.domains.job_management.agents.stage_context import STAGE_DEFINITIONS

        for stage_name, stage in STAGE_DEFINITIONS.items():
            next_stage = stage.get("next_stage", "")
            if next_stage and next_stage != "complete":
                assert next_stage in STAGE_DEFINITIONS, (
                    f"Stage {stage_name} references unknown next_stage '{next_stage}'"
                )

    def test_get_stage_context(self):
        from app.domains.job_management.agents.stage_context import get_stage_context

        context = get_stage_context("input-evaluation", {})
        assert "Coleta de Informacoes Basicas" in context
        assert "title" in context
        assert "OBRIGATORIO" in context

    def test_get_stage_context_with_filled_fields(self):
        from app.domains.job_management.agents.stage_context import get_stage_context

        context = get_stage_context(
            "input-evaluation",
            {"title": "Software Engineer", "department": "Engineering"},
        )
        assert "Software Engineer" in context
        assert "OBRIGATORIO" not in context

    def test_get_stage_context_unknown_stage(self):
        from app.domains.job_management.agents.stage_context import get_stage_context

        context = get_stage_context("nonexistent-stage", {})
        assert "desconhecido" in context.lower()

    def test_get_transition_prompt(self):
        from app.domains.job_management.agents.stage_context import get_transition_prompt

        prompt = get_transition_prompt("input-evaluation", {"title": "Dev", "department": "Eng"})
        assert "atendidos" in prompt.lower()

    def test_get_transition_prompt_missing_fields(self):
        from app.domains.job_management.agents.stage_context import get_transition_prompt

        prompt = get_transition_prompt("input-evaluation", {})
        assert "NAO atendidos" in prompt


class TestConfirmationWords:
    def test_confirmation_words_exist(self):
        from app.domains.job_management.agents.wizard_react_agent import _CONFIRMATION_WORDS

        assert "sim" in _CONFIRMATION_WORDS
        assert "ok" in _CONFIRMATION_WORDS
        assert "pode" in _CONFIRMATION_WORDS
        assert "vamos" in _CONFIRMATION_WORDS
        assert "bora" in _CONFIRMATION_WORDS
        assert "confirmo" in _CONFIRMATION_WORDS

    def test_confirmation_words_are_lowercase(self):
        from app.domains.job_management.agents.wizard_react_agent import _CONFIRMATION_WORDS

        for word in _CONFIRMATION_WORDS:
            assert word == word.lower(), f"Confirmation word '{word}' should be lowercase"
