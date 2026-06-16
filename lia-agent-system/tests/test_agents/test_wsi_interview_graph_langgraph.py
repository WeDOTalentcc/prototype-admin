"""
Tests for WSIInterviewGraph — LangGraph nativo.

Covers:
- _build_langgraph() compila sem erro
- route_dispatcher: "start" → lg_load_context, "submit" → lg_validate_response
- start() delega para _start_langgraph
- submit_response() delega para _submit_response_langgraph
- _start_langgraph() com grafo mockado
- _submit_response_langgraph() com grafo mockado
- Erro de build propaga (sem fallback legacy)
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


def _make_wsi_state():
    from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewState
    return WSIInterviewState(
        session_id="sess-wsi-dual-001",
        company_id="company-test",
        candidate_id="cand-001",
        job_id="job-001",
        interview_level="standard",
    )


# ---------------------------------------------------------------------------
# Section 1: _build_langgraph
# ---------------------------------------------------------------------------

class TestWSIBuildLangGraph:

    def test_build_langgraph_callable(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        assert callable(g._build_langgraph)

    def test_build_langgraph_returns_compiled(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        with patch("lia_agents_core.checkpointer.get_checkpointer") as mock_cp:
            mock_cp.return_value = None
            with patch("langgraph.graph.StateGraph.compile") as mock_compile:
                mock_compiled = MagicMock()
                mock_compile.return_value = mock_compiled
                result = g._build_langgraph()
                assert result is not None
                mock_compile.assert_called_once()

    def test_build_langgraph_uses_checkpointer(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        mock_cp = MagicMock()
        with patch("lia_agents_core.checkpointer.get_checkpointer") as mock_get_cp:
            mock_get_cp.return_value = mock_cp
            with patch("langgraph.graph.StateGraph.compile") as mock_compile:
                mock_compile.return_value = MagicMock()
                g._build_langgraph()
                mock_compile.assert_called_with(checkpointer=mock_cp)


# ---------------------------------------------------------------------------
# Section 2: route_dispatcher logic
# ---------------------------------------------------------------------------

class TestWSIRouteDispatcher:
    """Tests for the internal routing function defined inside _build_langgraph."""

    def _get_route_dispatcher(self):
        """Extrai route_dispatcher inspecionando o grafo construído."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()

        captured = {}

        original_add_conditional = None

        def fake_compile(checkpointer=None):
            compiled = MagicMock()
            compiled.ainvoke = AsyncMock()
            return compiled

        with patch("lia_agents_core.checkpointer.get_checkpointer") as mock_cp:
            mock_cp.return_value = None
            with patch("langgraph.graph.StateGraph.compile", side_effect=fake_compile):
                from langgraph.graph import StateGraph

                original_conditional = StateGraph.add_conditional_edges

                def capture_conditional(self, node, fn, mapping=None):
                    if node == "lg_dispatcher":
                        captured["route_dispatcher"] = fn
                    return original_conditional(self, node, fn, mapping)

                with patch.object(StateGraph, "add_conditional_edges", capture_conditional):
                    g._build_langgraph()

        return captured.get("route_dispatcher")

    def test_dispatcher_start_returns_load_context(self):
        route_dispatcher = self._get_route_dispatcher()
        if route_dispatcher is None:
            pytest.skip("Could not capture route_dispatcher (LangGraph internals changed)")
        result = route_dispatcher({"operation": "start"})
        assert result == "lg_load_context"

    def test_dispatcher_submit_returns_validate_response(self):
        route_dispatcher = self._get_route_dispatcher()
        if route_dispatcher is None:
            pytest.skip("Could not capture route_dispatcher (LangGraph internals changed)")
        result = route_dispatcher({"operation": "submit"})
        assert result == "lg_validate_response"

    def test_dispatcher_default_returns_validate_response(self):
        route_dispatcher = self._get_route_dispatcher()
        if route_dispatcher is None:
            pytest.skip("Could not capture route_dispatcher (LangGraph internals changed)")
        result = route_dispatcher({"operation": "anything_else"})
        assert result == "lg_validate_response"


# ---------------------------------------------------------------------------
# Section 3: _start_langgraph
# ---------------------------------------------------------------------------

class TestWSIStartLangGraph:

    @pytest.mark.asyncio
    async def test_start_langgraph_calls_ainvoke(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph,
            _wsi_state_to_dict,
        )
        g = WSIInterviewGraph()
        state = _make_wsi_state()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={
            "wsi_data": _wsi_state_to_dict(state),
            "pending_response": "",
            "operation": "start",
        })
        g._compiled_lg = mock_compiled

        result = await g._start_langgraph(state)
        mock_compiled.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_langgraph_passes_operation_start(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph,
            _wsi_state_to_dict,
        )
        g = WSIInterviewGraph()
        state = _make_wsi_state()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={
            "wsi_data": _wsi_state_to_dict(state),
            "pending_response": "",
            "operation": "start",
        })
        g._compiled_lg = mock_compiled

        await g._start_langgraph(state)
        call_args = mock_compiled.ainvoke.call_args
        input_state = call_args[0][0]
        assert input_state["operation"] == "start"
        assert input_state["pending_response"] == ""

    @pytest.mark.asyncio
    async def test_start_langgraph_raises_on_build_error(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        g._compiled_lg = None

        with patch.object(g, "_build_langgraph", side_effect=RuntimeError("no langgraph")):
            with pytest.raises(RuntimeError, match="no langgraph"):
                await g._start_langgraph(_make_wsi_state())

    @pytest.mark.asyncio
    async def test_start_langgraph_returns_error_state_on_ainvoke_error(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph, WSIInterviewStage
        g = WSIInterviewGraph()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(side_effect=Exception("graph fail"))
        g._compiled_lg = mock_compiled

        result = await g._start_langgraph(_make_wsi_state())
        assert result.error is not None
        assert result.stage == WSIInterviewStage.ERROR


# ---------------------------------------------------------------------------
# Section 4: _submit_response_langgraph
# ---------------------------------------------------------------------------

class TestWSISubmitResponseLangGraph:

    @pytest.mark.asyncio
    async def test_submit_passes_operation_submit(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph,
            _wsi_state_to_dict,
        )
        g = WSIInterviewGraph()
        state = _make_wsi_state()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={
            "wsi_data": _wsi_state_to_dict(state),
            "pending_response": "",
            "operation": "submit",
        })
        g._compiled_lg = mock_compiled

        await g._submit_response_langgraph(state, "Minha resposta")
        call_args = mock_compiled.ainvoke.call_args
        input_state = call_args[0][0]
        assert input_state["operation"] == "submit"
        assert input_state["pending_response"] == "Minha resposta"

    @pytest.mark.asyncio
    async def test_submit_raises_on_build_error(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        g._compiled_lg = None

        with patch.object(g, "_build_langgraph", side_effect=RuntimeError("build fail")):
            with pytest.raises(RuntimeError, match="build fail"):
                await g._submit_response_langgraph(_make_wsi_state(), "resp")


# ---------------------------------------------------------------------------
# Section 5: dual-path public API
# ---------------------------------------------------------------------------

class TestWSIPublicAPI:

    @pytest.mark.asyncio
    async def test_start_calls_langgraph(self):
        """start() sempre delega para _start_langgraph (LangGraph nativo)."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        state = _make_wsi_state()

        with patch.object(g, "_start_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = state
            await g.start(state)
            mock_lg.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_calls_langgraph(self):
        """submit_response() sempre delega para _submit_response_langgraph (LangGraph nativo)."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        state = _make_wsi_state()

        with patch.object(g, "_submit_response_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = state
            await g.submit_response(state, "resposta")
            mock_lg.assert_called_once_with(state, "resposta", None)
