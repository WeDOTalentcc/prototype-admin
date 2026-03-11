"""
Tests for InterviewGraph (Phase 3) - LangGraph scheduling workflow.

Covers:
- Graph instantiation and structure
- Conditional routing logic (_route_after_collector, _route_after_validator, _route_after_router)
- invoke() with mocked nodes (no real LLM/DB/calendar calls)
- Domain.py wiring: schedule_interview action delegates to InterviewGraph
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ---------------------------------------------------------------------------
# Section 1: Structure tests (no async, no mocks needed)
# ---------------------------------------------------------------------------

class TestInterviewGraphStructure:
    """InterviewGraph instantiation and metadata."""

    def test_graph_importable(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph, interview_graph
        assert InterviewGraph is not None
        assert interview_graph is not None

    def test_singleton_is_interview_graph(self):
        from app.domains.interview_scheduling.agents.interview_graph import interview_graph, InterviewGraph
        assert isinstance(interview_graph, InterviewGraph)

    def test_graph_structure_metadata(self):
        from app.domains.interview_scheduling.agents.interview_graph import interview_graph
        structure = interview_graph.get_graph_structure()
        assert structure["graph_type"] == "InterviewGraph"
        assert structure["start_node"] == "interview_state_loader"
        assert structure["end_node"] == "interview_response_planner"
        assert structure["max_iterations"] == 8

    def test_graph_has_six_nodes(self):
        from app.domains.interview_scheduling.agents.interview_graph import interview_graph
        structure = interview_graph.get_graph_structure()
        expected_nodes = {
            "interview_state_loader",
            "interview_details_collector",
            "interview_router",
            "interview_validator",
            "interview_scheduler_executor",
            "interview_response_planner",
        }
        assert set(structure["nodes"]) == expected_nodes

    def test_graph_has_three_conditional_edges(self):
        from app.domains.interview_scheduling.agents.interview_graph import interview_graph
        structure = interview_graph.get_graph_structure()
        assert len(structure["conditional_edges"]) == 3

    def test_all_node_fns_are_callable(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        for name, fn in g._node_fns.items():
            assert callable(fn), f"Node '{name}' is not callable"


# ---------------------------------------------------------------------------
# Section 2: Conditional routing logic
# ---------------------------------------------------------------------------

class TestInterviewGraphRouting:
    """Unit tests for conditional routing methods."""

    def _make_state_with_all_fields(self) -> Dict[str, Any]:
        """State where all required fields are collected."""
        return {
            "workflow_data": {
                "interview_scheduling_state": {
                    "candidate_name": "João Silva",
                    "candidate_email": "joao@example.com",
                    "job_title": "Engenheiro de Software",
                    "interview_type": "tecnica",
                    "interviewer_email": "recruiter@wedotalent.com",
                    "preferred_date": "2026-03-15",
                    "preferred_time": "14:00",
                    "collected_fields": [
                        "candidate_name", "candidate_email", "job_title",
                        "interview_type", "interviewer_email", "preferred_date", "preferred_time"
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

    def _make_state_with_missing_fields(self) -> Dict[str, Any]:
        """State where some required fields are still missing."""
        return {
            "workflow_data": {
                "interview_scheduling_state": {
                    "candidate_name": "João Silva",
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
                    "as_teams_meeting": True,
                }
            }
        }

    def test_route_after_collector_complete_goes_to_validator(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = self._make_state_with_all_fields()
        result = g._route_after_collector(state)
        assert result == "interview_validator"

    def test_route_after_collector_incomplete_goes_to_router(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = self._make_state_with_missing_fields()
        result = g._route_after_collector(state)
        assert result == "interview_router"

    def test_route_after_validator_ready_goes_to_executor(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"workflow_data": {"interview_ready_for_scheduling": True}}
        result = g._route_after_validator(state)
        assert result == "interview_scheduler_executor"

    def test_route_after_validator_not_ready_goes_to_response(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"workflow_data": {"interview_ready_for_scheduling": False}}
        result = g._route_after_validator(state)
        assert result == "interview_response_planner"

    def test_route_after_router_pending_goes_to_collector(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"workflow_data": {"next_collection_target": "candidate_email"}}
        result = g._route_after_router(state)
        assert result == "interview_details_collector"

    def test_route_after_router_no_pending_goes_to_validator(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"workflow_data": {"next_collection_target": None}}
        result = g._route_after_router(state)
        assert result == "interview_validator"

    def test_route_after_collector_empty_workflow_goes_to_router(self):
        """Empty workflow_data (no state loaded yet) → router to collect fields."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"workflow_data": {}}
        result = g._route_after_collector(state)
        assert result == "interview_router"


# ---------------------------------------------------------------------------
# Section 3: invoke() with mocked nodes
# ---------------------------------------------------------------------------

class TestInterviewGraphInvoke:
    """invoke() flow with mocked node functions."""

    def _base_state(self) -> Dict[str, Any]:
        class _Msg:
            content = "agendar entrevista com João amanhã às 14h"
        return {
            "messages": [_Msg()],
            "workflow_data": {},
            "entities": {},
            "session_id": "test-session",
            "company_id": "tenant-1",
            "user_id": "user-1",
        }

    @pytest.mark.asyncio
    async def test_invoke_collecting_phase_returns_state(self):
        """When fields are pending, graph runs loader + collector then returns for clarification."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        async def mock_loader(s):
            return s

        async def mock_collector(s):
            # Simula coleta parcial — ainda faltam campos
            s["workflow_data"]["interview_scheduling_state"] = {
                "candidate_name": "João",
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
                "as_teams_meeting": True,
            }
            return s

        async def mock_router(s):
            s["workflow_data"]["next_collection_target"] = "candidate_email"
            return s

        async def mock_response(s):
            s["workflow_data"]["response_data"] = {
                "status": "collecting",
                "next_field": "candidate_email",
                "progress": {"total_required": 7, "collected": 1, "percentage": 14},
            }
            return s

        g = InterviewGraph()
        g._node_fns["interview_state_loader"] = mock_loader
        g._node_fns["interview_details_collector"] = mock_collector
        g._node_fns["interview_router"] = mock_router
        g._node_fns["interview_response_planner"] = mock_response

        final = await g.invoke(self._base_state())

        response_data = final["workflow_data"].get("response_data", {})
        assert response_data.get("status") == "collecting"
        assert response_data.get("next_field") == "candidate_email"

    @pytest.mark.asyncio
    async def test_invoke_complete_flow_schedules_interview(self):
        """When all fields collected, graph goes through validator → executor → response."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        complete_interview_state = {
            "candidate_name": "João Silva",
            "candidate_email": "joao@example.com",
            "job_title": "Engenheiro de Software",
            "interview_type": "tecnica",
            "interviewer_email": "recruiter@wedotalent.com",
            "preferred_date": "2026-03-15",
            "preferred_time": "14:00",
            "collected_fields": [
                "candidate_name", "candidate_email", "job_title",
                "interview_type", "interviewer_email", "preferred_date", "preferred_time"
            ],
            "pending_fields": [],
            "is_complete": True,
            "validation_errors": [],
            "additional_interviewers": [],
            "preparation_materials": [],
            "duration_minutes": 60,
            "as_teams_meeting": True,
        }

        async def mock_loader(s):
            s["workflow_data"]["interview_scheduling_state"] = complete_interview_state
            return s

        async def mock_collector(s):
            return s  # Campos já coletados — collector não adiciona nada

        async def mock_validator(s):
            s["workflow_data"]["interview_ready_for_scheduling"] = True
            return s

        async def mock_executor(s):
            s["workflow_data"]["interview_scheduling_complete"] = True
            s["workflow_data"]["created_interview_id"] = "interview-abc-123"
            s["workflow_data"]["meeting_url"] = "https://teams.microsoft.com/meet/abc123"
            return s

        async def mock_response(s):
            s["workflow_data"]["response_data"] = {
                "status": "completed",
                "interview_id": "interview-abc-123",
                "meeting_url": "https://teams.microsoft.com/meet/abc123",
                "message": "✅ Entrevista agendada com sucesso!",
            }
            return s

        g = InterviewGraph()
        g._node_fns["interview_state_loader"] = mock_loader
        g._node_fns["interview_details_collector"] = mock_collector
        g._node_fns["interview_validator"] = mock_validator
        g._node_fns["interview_scheduler_executor"] = mock_executor
        g._node_fns["interview_response_planner"] = mock_response

        final = await g.invoke(self._base_state())

        response_data = final["workflow_data"].get("response_data", {})
        assert response_data.get("status") == "completed"
        assert response_data.get("interview_id") == "interview-abc-123"
        assert "teams.microsoft.com" in response_data.get("meeting_url", "")

    @pytest.mark.asyncio
    async def test_invoke_node_error_does_not_abort_graph(self):
        """Node errors are caught and stored — graph continues to response."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        async def failing_loader(s):
            raise RuntimeError("DB connection failed")

        async def mock_response(s):
            s["workflow_data"]["response_data"] = {"status": "collecting"}
            return s

        g = InterviewGraph()
        g._node_fns["interview_state_loader"] = failing_loader
        # Remaining nodes: router/validator/response will receive empty workflow_data
        g._node_fns["interview_response_planner"] = mock_response

        final = await g.invoke(self._base_state())

        # Error captured in workflow_data, graph did not raise
        assert "interview_graph_error" in final["workflow_data"]
        assert "DB connection failed" in final["workflow_data"]["interview_graph_error"]


# ---------------------------------------------------------------------------
# Section 4: Domain wiring — schedule_interview → InterviewGraph
# ---------------------------------------------------------------------------

class TestInterviewSchedulingDomainWiring:
    """Verify domain.py routes schedule_interview through InterviewGraph."""

    def test_graph_actions_set_contains_schedule_interview(self):
        from app.domains.interview_scheduling.domain import _GRAPH_ACTIONS
        assert "schedule_interview" in _GRAPH_ACTIONS

    def test_domain_has_run_interview_graph_method(self):
        from app.domains.interview_scheduling.domain import InterviewSchedulingDomain
        domain = InterviewSchedulingDomain()
        assert hasattr(domain, "_run_interview_graph")
        assert callable(domain._run_interview_graph)

    @pytest.mark.asyncio
    async def test_execute_action_schedule_interview_delegates_to_graph(self):
        """execute_action('schedule_interview') should call _run_interview_graph."""
        from app.domains.interview_scheduling.domain import InterviewSchedulingDomain
        from app.domains.base import DomainContext

        domain = InterviewSchedulingDomain()
        ctx = DomainContext(
            domain_id="interview_scheduling",
            tenant_id="tenant-1",
            user_id="user-1",
            session_id="session-1",
        )

        call_log = []

        async def mock_run_graph(action_id, params, context):
            call_log.append({"action_id": action_id, "params": params})
            from app.domains.base import DomainResponse
            return DomainResponse.success_response(
                message="mock graph result",
                domain_id="interview_scheduling",
                action_id=action_id,
            )

        domain._run_interview_graph = mock_run_graph

        result = await domain.execute_action(
            action_id="schedule_interview",
            params={"raw_query": "agendar entrevista técnica"},
            context=ctx,
        )

        assert result.success is True
        assert len(call_log) == 1
        assert call_log[0]["action_id"] == "schedule_interview"

    @pytest.mark.asyncio
    async def test_run_interview_graph_collecting_returns_clarification(self):
        """_run_interview_graph with 'collecting' status returns clarification_response."""
        from app.domains.interview_scheduling.domain import InterviewSchedulingDomain
        from app.domains.base import DomainContext

        domain = InterviewSchedulingDomain()
        ctx = DomainContext(
            domain_id="interview_scheduling",
            tenant_id="tenant-1",
            user_id="user-1",
            session_id="session-1",
        )

        async def mock_invoke(state):
            state["workflow_data"]["response_data"] = {
                "status": "collecting",
                "next_field": "candidate_name",
                "progress": {"total_required": 7, "collected": 0, "percentage": 0},
            }
            return state

        mock_graph = MagicMock()
        mock_graph.invoke = mock_invoke

        with patch("app.domains.interview_scheduling.domain.interview_graph", mock_graph):
            result = await domain._run_interview_graph(
                "schedule_interview",
                {"raw_query": "agendar entrevista"},
                ctx,
            )

        assert result.needs_clarification is True
        assert "nome do candidato" in result.message

    @pytest.mark.asyncio
    async def test_run_interview_graph_completed_returns_success(self):
        """_run_interview_graph with 'completed' status returns success_response."""
        from app.domains.interview_scheduling.domain import InterviewSchedulingDomain
        from app.domains.base import DomainContext

        domain = InterviewSchedulingDomain()
        ctx = DomainContext(
            domain_id="interview_scheduling",
            tenant_id="tenant-1",
            user_id="user-1",
            session_id="session-1",
        )

        async def mock_invoke(state):
            state["workflow_data"]["response_data"] = {
                "status": "completed",
                "interview_id": "iv-999",
                "meeting_url": "https://teams.microsoft.com/meet/999",
                "message": "✅ Entrevista agendada com sucesso!",
            }
            return state

        mock_graph = MagicMock()
        mock_graph.invoke = mock_invoke

        with patch("app.domains.interview_scheduling.domain.interview_graph", mock_graph):
            result = await domain._run_interview_graph(
                "schedule_interview",
                {"raw_query": "agendar entrevista"},
                ctx,
            )

        assert result.success is True
        assert result.data["interview_id"] == "iv-999"
        assert "teams.microsoft.com" in result.data["meeting_url"]
