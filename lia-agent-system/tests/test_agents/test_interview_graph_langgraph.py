"""
Tests for InterviewGraph — LangGraph nativo.

Covers:
- _build_langgraph() compila sem erro
- _lg_route_collector: completo → validator, incompleto → router
- _lg_route_router: campo pendente → RESPONSE (sem loop), validado → VALIDATOR
- _invoke_langgraph() com grafo mockado
- invoke() delega para _invoke_langgraph
- Erro de build propaga (sem fallback legacy)
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ---------------------------------------------------------------------------
# Section 1: _build_langgraph
# ---------------------------------------------------------------------------

class TestInterviewGraphBuildLangGraph:

    def test_build_langgraph_returns_compiled_graph(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        with patch("lia_agents_core.checkpointer.get_checkpointer") as mock_cp:
            mock_cp.return_value = None
            with patch("langgraph.graph.StateGraph.compile") as mock_compile:
                mock_compile.return_value = MagicMock()
                result = g._build_langgraph()
                assert result is not None

    def test_build_langgraph_uses_checkpointer(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        mock_checkpointer = MagicMock()
        with patch("lia_agents_core.checkpointer.get_checkpointer") as mock_cp:
            mock_cp.return_value = mock_checkpointer
            with patch("langgraph.graph.StateGraph.compile") as mock_compile:
                mock_compile.return_value = MagicMock()
                g._build_langgraph()
                mock_compile.assert_called_once_with(checkpointer=mock_checkpointer)


# ---------------------------------------------------------------------------
# Section 2: _lg_route_collector
# ---------------------------------------------------------------------------

class TestInterviewGraphLGRouteCollector:

    def _complete_state(self) -> Dict[str, Any]:
        return {
            "workflow_data": {
                "interview_scheduling_state": {
                    "candidate_name": "Ana Costa",
                    "candidate_email": "ana@example.com",
                    "job_title": "Dev",
                    "interview_type": "tecnica",
                    "interviewer_email": "rec@wedotalent.com",
                    "preferred_date": "2026-04-01",
                    "preferred_time": "10:00",
                    "collected_fields": [
                        "candidate_name", "candidate_email", "job_title",
                        "interview_type", "interviewer_email",
                        "preferred_date", "preferred_time",
                    ],
                    "pending_fields": [],
                    "is_complete": False,
                    "validation_errors": [],
                    "additional_interviewers": [],
                    "preparation_materials": [],
                    "duration_minutes": 60,
                    "as_teams_meeting": True,
                }
            }
        }

    def _incomplete_state(self) -> Dict[str, Any]:
        return {
            "workflow_data": {
                "interview_scheduling_state": {
                    "candidate_name": "Ana Costa",
                    "candidate_email": None,
                    "job_title": None,
                    "interview_type": None,
                    "interviewer_email": None,
                    "preferred_date": None,
                    "preferred_time": None,
                    "collected_fields": ["candidate_name"],
                    "pending_fields": [],
                    "is_complete": False,
                    "validation_errors": [],
                    "additional_interviewers": [],
                    "preparation_materials": [],
                    "duration_minutes": 60,
                    "as_teams_meeting": False,
                }
            }
        }

    def test_complete_fields_routes_to_validator(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        result = g._lg_route_collector(self._complete_state())
        assert result == "interview_validator"

    def test_incomplete_fields_routes_to_router(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        result = g._lg_route_collector(self._incomplete_state())
        assert result == "interview_router"

    def test_delegates_to_route_after_collector(self):
        """_lg_route_collector é alias de _route_after_collector."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = self._complete_state()
        assert g._lg_route_collector(state) == g._route_after_collector(state)


# ---------------------------------------------------------------------------
# Section 3: _lg_route_router  (comportamento diferente do legado)
# ---------------------------------------------------------------------------

class TestInterviewGraphLGRouteRouter:

    def test_pending_field_routes_to_response_not_collector(self):
        """LangGraph: campo pendente → RESPONSE (pede ao usuário), não COLLECTOR."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"workflow_data": {"next_collection_target": "candidate_email"}}
        result = g._lg_route_router(state)
        assert result == "interview_response_planner"

    def test_no_pending_field_routes_to_validator(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"workflow_data": {"next_collection_target": None}}
        result = g._lg_route_router(state)
        assert result == "interview_validator"

    def test_empty_workflow_data_routes_to_validator(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"workflow_data": {}}
        result = g._lg_route_router(state)
        assert result == "interview_validator"

    def test_differs_from_legacy_when_pending(self):
        """_lg_route_router difere do _route_after_router quando campo pendente."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"workflow_data": {"next_collection_target": "preferred_date"}}
        lg_result = g._lg_route_router(state)
        legacy_result = g._route_after_router(state)
        assert lg_result == "interview_response_planner"
        assert legacy_result == "interview_details_collector"
        assert lg_result != legacy_result


# ---------------------------------------------------------------------------
# Section 4: _invoke_langgraph
# ---------------------------------------------------------------------------

class TestInterviewGraphInvokeLangGraph:

    def _make_state(self) -> Dict[str, Any]:
        return {
            "session_id": "sess-test-001",
            "workflow_data": {
                "interview_scheduling_state": {
                    "candidate_name": "Carlos Lima",
                    "candidate_email": "carlos@example.com",
                    "job_title": "QA Engineer",
                    "interview_type": "tecnica",
                    "interviewer_email": "rec@wedotalent.com",
                    "preferred_date": "2026-04-10",
                    "preferred_time": "15:00",
                    "collected_fields": [
                        "candidate_name", "candidate_email", "job_title",
                        "interview_type", "interviewer_email",
                        "preferred_date", "preferred_time",
                    ],
                    "pending_fields": [],
                    "is_complete": True,
                    "validation_errors": [],
                    "additional_interviewers": [],
                    "preparation_materials": [],
                    "duration_minutes": 45,
                    "as_teams_meeting": True,
                }
            },
        }

    @pytest.mark.asyncio
    async def test_invoke_langgraph_calls_compiled_graph(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value=self._make_state())
        g._compiled = mock_compiled

        result = await g._invoke_langgraph(self._make_state())
        mock_compiled.ainvoke.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_invoke_langgraph_passes_session_id_as_thread_id(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = self._make_state()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value=state)
        g._compiled = mock_compiled

        await g._invoke_langgraph(state)
        call_kwargs = mock_compiled.ainvoke.call_args
        config = call_kwargs[1].get("config") or call_kwargs[0][1]
        assert config["configurable"]["thread_id"] == "sess-test-001"

    @pytest.mark.asyncio
    async def test_invoke_langgraph_raises_on_build_error(self):
        """Se _build_langgraph lança, a exceção propaga (sem fallback legacy)."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        g._compiled = None

        with patch.object(g, "_build_langgraph", side_effect=RuntimeError("no langgraph")):
            with pytest.raises(RuntimeError, match="no langgraph"):
                await g._invoke_langgraph(self._make_state())

    @pytest.mark.asyncio
    async def test_invoke_langgraph_falls_back_on_ainvoke_error(self):
        """Se ainvoke lança, retorna estado com error key."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = self._make_state()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(side_effect=Exception("graph crash"))
        g._compiled = mock_compiled

        result = await g._invoke_langgraph(state)
        assert "interview_graph_error" in result.get("workflow_data", {}) or \
               result.get("workflow_data", {}).get("interview_graph_error") is not None


# ---------------------------------------------------------------------------
# Section 5: invoke() always calls LangGraph
# ---------------------------------------------------------------------------

class TestInterviewGraphInvoke:

    def _make_state(self) -> Dict[str, Any]:
        return {"session_id": "sess-dual-001", "workflow_data": {}}

    @pytest.mark.asyncio
    async def test_invoke_calls_langgraph(self):
        """invoke() sempre delega para _invoke_langgraph (LangGraph nativo)."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()

        with patch.object(g, "_invoke_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = self._make_state()
            await g.invoke(self._make_state())
            mock_lg.assert_called_once()
