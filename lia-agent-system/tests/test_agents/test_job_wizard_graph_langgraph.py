"""
Tests for JobWizardGraph — LangGraph dual-path (Phase 3.2).

Covers:
- _build_langgraph() compila sem erro
- route_intent_classifier: START_FROM_SCRATCH/HELP/USE_TEMPLATE → response_generator,
  SKIP/GO_BACK/CONFIRM → stage_transition, PROVIDE_INFO/MODIFY → field_extractor
- route_tool_router: tool_calls presente → tool_executor, vazio → response_generator
- route_stage_transition: should_continue=False → end, True → continue
- _invoke_langgraph() com grafo mockado
- dual-path invoke()
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


def _make_state(intent: str = "", should_continue: bool = True) -> Dict[str, Any]:
    return {
        "session_id": "sess-wizard-lg-001",
        "company_id": "company-test",
        "intent": intent,
        "should_continue": should_continue,
        "tool_calls": [],
        "message": "",
        "response": "",
        "error": None,
    }


# ---------------------------------------------------------------------------
# Section 1: _build_langgraph
# ---------------------------------------------------------------------------

class TestJobWizardBuildLangGraph:

    def test_build_langgraph_callable(self):
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()
        assert callable(g._build_langgraph)

    def test_build_langgraph_returns_compiled(self):
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()
        with patch("lia_agents_core.checkpointer.get_checkpointer") as mock_cp:
            mock_cp.return_value = None
            with patch("langgraph.graph.StateGraph.compile") as mock_compile:
                mock_compile.return_value = MagicMock()
                result = g._build_langgraph()
                assert result is not None

    def test_build_langgraph_uses_checkpointer(self):
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()
        mock_cp = MagicMock()
        with patch("lia_agents_core.checkpointer.get_checkpointer") as mock_get_cp:
            mock_get_cp.return_value = mock_cp
            with patch("langgraph.graph.StateGraph.compile") as mock_compile:
                mock_compile.return_value = MagicMock()
                g._build_langgraph()
                mock_compile.assert_called_with(checkpointer=mock_cp)


# ---------------------------------------------------------------------------
# Section 2: routing functions (captured from _build_langgraph)
# ---------------------------------------------------------------------------

def _capture_routing_functions():
    """Captura as routing functions definidas dentro de _build_langgraph."""
    from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
    from langgraph.graph import StateGraph, END

    g = JobWizardGraph()
    captured = {}

    original_conditional = StateGraph.add_conditional_edges

    def capture_conditional(self_sg, node, fn, mapping=None):
        captured[node] = fn
        return original_conditional(self_sg, node, fn, mapping)

    def fake_compile(checkpointer=None):
        return MagicMock()

    with patch("lia_agents_core.checkpointer.get_checkpointer") as mock_cp:
        mock_cp.return_value = None
        with patch("langgraph.graph.StateGraph.compile", side_effect=fake_compile):
            with patch.object(StateGraph, "add_conditional_edges", capture_conditional):
                g._build_langgraph()

    return captured


class TestJobWizardRouteIntentClassifier:

    def setup_method(self):
        self.fns = _capture_routing_functions()
        self.route_intent = self.fns.get("intent_classifier")

    def test_start_from_scratch_goes_to_response_generator(self):
        if not self.route_intent:
            pytest.skip("Could not capture route_intent_classifier")
        from app.domains.job_management.agents.job_wizard_graph import WizardIntent
        state = _make_state(intent=WizardIntent.START_FROM_SCRATCH.value)
        assert self.route_intent(state) == "response_generator"

    def test_use_template_goes_to_response_generator(self):
        if not self.route_intent:
            pytest.skip("Could not capture route_intent_classifier")
        from app.domains.job_management.agents.job_wizard_graph import WizardIntent
        state = _make_state(intent=WizardIntent.USE_TEMPLATE.value)
        assert self.route_intent(state) == "response_generator"

    def test_help_goes_to_response_generator(self):
        if not self.route_intent:
            pytest.skip("Could not capture route_intent_classifier")
        from app.domains.job_management.agents.job_wizard_graph import WizardIntent
        state = _make_state(intent=WizardIntent.HELP.value)
        assert self.route_intent(state) == "response_generator"

    def test_ask_question_goes_to_response_generator(self):
        if not self.route_intent:
            pytest.skip("Could not capture route_intent_classifier")
        from app.domains.job_management.agents.job_wizard_graph import WizardIntent
        state = _make_state(intent=WizardIntent.ASK_QUESTION.value)
        assert self.route_intent(state) == "response_generator"

    def test_skip_goes_to_stage_transition(self):
        if not self.route_intent:
            pytest.skip("Could not capture route_intent_classifier")
        from app.domains.job_management.agents.job_wizard_graph import WizardIntent
        state = _make_state(intent=WizardIntent.SKIP.value)
        assert self.route_intent(state) == "stage_transition"

    def test_go_back_goes_to_stage_transition(self):
        if not self.route_intent:
            pytest.skip("Could not capture route_intent_classifier")
        from app.domains.job_management.agents.job_wizard_graph import WizardIntent
        state = _make_state(intent=WizardIntent.GO_BACK.value)
        assert self.route_intent(state) == "stage_transition"

    def test_confirm_goes_to_stage_transition(self):
        if not self.route_intent:
            pytest.skip("Could not capture route_intent_classifier")
        from app.domains.job_management.agents.job_wizard_graph import WizardIntent
        state = _make_state(intent=WizardIntent.CONFIRM.value)
        assert self.route_intent(state) == "stage_transition"

    def test_provide_info_goes_to_field_extractor(self):
        if not self.route_intent:
            pytest.skip("Could not capture route_intent_classifier")
        from app.domains.job_management.agents.job_wizard_graph import WizardIntent
        state = _make_state(intent=WizardIntent.PROVIDE_INFO.value)
        assert self.route_intent(state) == "field_extractor"

    def test_unknown_intent_goes_to_field_extractor(self):
        if not self.route_intent:
            pytest.skip("Could not capture route_intent_classifier")
        state = _make_state(intent="unknown_intent")
        assert self.route_intent(state) == "field_extractor"


class TestJobWizardRouteToolRouter:

    def setup_method(self):
        self.fns = _capture_routing_functions()
        self.route_tool = self.fns.get("tool_router")

    def test_with_tool_calls_goes_to_executor(self):
        if not self.route_tool:
            pytest.skip("Could not capture route_tool_router")
        state = {**_make_state(), "tool_calls": [{"tool": "search_jobs"}]}
        assert self.route_tool(state) == "tool_executor"

    def test_empty_tool_calls_goes_to_response_generator(self):
        if not self.route_tool:
            pytest.skip("Could not capture route_tool_router")
        state = {**_make_state(), "tool_calls": []}
        assert self.route_tool(state) == "response_generator"

    def test_no_tool_calls_key_goes_to_response_generator(self):
        if not self.route_tool:
            pytest.skip("Could not capture route_tool_router")
        state = _make_state()
        state.pop("tool_calls", None)
        assert self.route_tool(state) == "response_generator"


class TestJobWizardRouteStageTransition:

    def setup_method(self):
        self.fns = _capture_routing_functions()
        self.route_stage = self.fns.get("stage_transition")

    def test_should_continue_false_goes_to_end(self):
        if not self.route_stage:
            pytest.skip("Could not capture route_stage_transition")
        state = _make_state(should_continue=False)
        assert self.route_stage(state) == "end"

    def test_should_continue_true_goes_to_continue(self):
        if not self.route_stage:
            pytest.skip("Could not capture route_stage_transition")
        state = _make_state(should_continue=True)
        assert self.route_stage(state) == "continue"

    def test_missing_should_continue_defaults_to_continue(self):
        if not self.route_stage:
            pytest.skip("Could not capture route_stage_transition")
        state = _make_state()
        state.pop("should_continue", None)
        assert self.route_stage(state) == "continue"


# ---------------------------------------------------------------------------
# Section 3: _invoke_langgraph
# ---------------------------------------------------------------------------

class TestJobWizardInvokeLangGraph:

    @pytest.mark.asyncio
    async def test_invoke_langgraph_calls_ainvoke(self):
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()
        state = _make_state()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value=state)
        g._compiled_lg = mock_compiled

        result = await g._invoke_langgraph(state)
        mock_compiled.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_invoke_langgraph_passes_session_id_as_thread_id(self):
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()
        state = _make_state()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value=state)
        g._compiled_lg = mock_compiled

        await g._invoke_langgraph(state)
        call_kwargs = mock_compiled.ainvoke.call_args
        config = call_kwargs[1].get("config") or call_kwargs[0][1]
        assert config["configurable"]["thread_id"] == "sess-wizard-lg-001"

    @pytest.mark.asyncio
    async def test_invoke_langgraph_raises_on_build_error(self):
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()
        g._compiled_lg = None

        with patch.object(g, "_build_langgraph", side_effect=RuntimeError("no lg")):
            with pytest.raises(RuntimeError, match="no lg"):
                await g._invoke_langgraph(_make_state())

    @pytest.mark.asyncio
    async def test_invoke_langgraph_sets_error_on_ainvoke_failure(self):
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(side_effect=Exception("graph crash"))
        g._compiled_lg = mock_compiled

        result = await g._invoke_langgraph(_make_state())
        assert isinstance(result, dict)
        assert "error" in result


# ---------------------------------------------------------------------------
# Section 4: dual-path invoke()
# ---------------------------------------------------------------------------

class TestJobWizardInvoke:

    @pytest.mark.asyncio
    async def test_invoke_calls_langgraph_by_default(self):
        """invoke() sem start_node customizado delega para _invoke_langgraph."""
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()
        state = _make_state()

        with patch.object(g, "_invoke_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = state
            await g.invoke(state)
            mock_lg.assert_called_once()

    @pytest.mark.asyncio
    async def test_custom_start_node_still_uses_langgraph(self):
        """invoke() com start_node customizado também delega para _invoke_langgraph."""
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()
        state = _make_state()

        with patch.object(g, "_invoke_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = state
            await g.invoke(state, start_node="field_extractor")
            mock_lg.assert_called_once()
