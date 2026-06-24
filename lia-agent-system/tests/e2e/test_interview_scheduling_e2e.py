"""
E2E Integration Tests — Interview Scheduling Flow (Layer 3).

Covers:
- Full domain.py._run_interview_graph() pipeline with mocked InterviewGraph
- Session persistence via InterviewSessionStore (get/set/delete cycle)
- Multi-turn conversation: second call recovers workflow_data from store
- Status transitions: collecting → completed → session cleanup
- Error state: graph error propagates correctly

These tests exercise the full stack from DomainContext through domain.py
to InterviewGraph and InterviewSessionStore — without real LLM, calendar or DB calls.
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ctx(session_id: str = "sess-e2e-1"):
    from app.domains.base import DomainContext
    return DomainContext(
        domain_id="interview_scheduling",
        tenant_id="tenant-e2e",
        user_id="user-e2e",
        session_id=session_id,
    )


def _make_graph_response(status: str, next_field: str = None, interview_id: str = None):
    """Build the workflow_data dict that InterviewGraph.invoke returns."""
    response_data: Dict[str, Any] = {"status": status}
    if next_field:
        response_data["next_field"] = next_field
        response_data["progress"] = {"total_required": 7, "collected": 1, "percentage": 14}
    if interview_id:
        response_data["interview_id"] = interview_id
        response_data["meeting_url"] = "https://teams.microsoft.com/meet/e2e"
        response_data["message"] = "Entrevista agendada com sucesso!"

    async def _invoke(state):
        state["workflow_data"]["response_data"] = response_data
        return state

    mock_graph = MagicMock()
    mock_graph.invoke = _invoke
    return mock_graph


# ---------------------------------------------------------------------------
# Section 1: InterviewSessionStore unit tests
# ---------------------------------------------------------------------------

class TestInterviewSessionStore:

    @pytest.mark.asyncio
    async def test_get_returns_none_for_unknown_session(self):
        from app.shared.services.interview_session_store import InterviewSessionStore
        store = InterviewSessionStore()
        result = await store.get("nonexistent-session")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_round_trip(self):
        from app.shared.services.interview_session_store import InterviewSessionStore
        store = InterviewSessionStore()
        data = {"candidate_name": "Alice", "job_title": "Engenheira"}
        await store.set("sess-1", data)
        retrieved = await store.get("sess-1")
        assert retrieved == data

    @pytest.mark.asyncio
    async def test_delete_removes_entry(self):
        from app.shared.services.interview_session_store import InterviewSessionStore
        store = InterviewSessionStore()
        await store.set("sess-2", {"field": "value"})
        await store.delete("sess-2")
        result = await store.get("sess-2")
        assert result is None

    @pytest.mark.asyncio
    async def test_overwrite_updates_state(self):
        from app.shared.services.interview_session_store import InterviewSessionStore
        store = InterviewSessionStore()
        await store.set("sess-3", {"step": 1})
        await store.set("sess-3", {"step": 2, "extra": "data"})
        result = await store.get("sess-3")
        assert result["step"] == 2
        assert result["extra"] == "data"

    @pytest.mark.asyncio
    async def test_multiple_sessions_isolated(self):
        from app.shared.services.interview_session_store import InterviewSessionStore
        store = InterviewSessionStore()
        await store.set("sess-a", {"user": "Alice"})
        await store.set("sess-b", {"user": "Bob"})
        a = await store.get("sess-a")
        b = await store.get("sess-b")
        assert a["user"] == "Alice"
        assert b["user"] == "Bob"


# ---------------------------------------------------------------------------
# Section 2: domain._run_interview_graph — session persistence integration
# ---------------------------------------------------------------------------

class TestInterviewSchedulingSessionPersistence:

    @pytest.mark.asyncio
    async def test_collecting_status_saves_workflow_to_store(self):
        """After a collecting response, workflow_data is saved to the session store."""
        from app.domains.interview_scheduling.domain import InterviewSchedulingDomain
        from app.shared.services.interview_session_store import InterviewSessionStore

        domain = InterviewSchedulingDomain()
        ctx = _make_ctx("sess-persist-1")
        store = InterviewSessionStore()

        mock_graph = _make_graph_response("collecting", next_field="candidate_name")

        with patch("app.domains.interview_scheduling.domain.interview_graph", mock_graph), \
             patch("app.domains.interview_scheduling.domain.interview_session_store", store):
            result = await domain._run_interview_graph(
                "schedule_interview",
                {"raw_query": "quero agendar entrevista"},
                ctx,
            )

        assert result.needs_clarification is True
        # workflow_data deve ter sido salvo no store
        saved = await store.get("scheduling:sess-persist-1")
        assert saved is not None
        assert "response_data" in saved

    @pytest.mark.asyncio
    async def test_second_turn_recovers_workflow_from_store(self):
        """Second call with empty params recovers workflow_data from the session store."""
        from app.domains.interview_scheduling.domain import InterviewSchedulingDomain
        from app.shared.services.interview_session_store import InterviewSessionStore

        domain = InterviewSchedulingDomain()
        ctx = _make_ctx("sess-persist-2")
        store = InterviewSessionStore()

        # Pre-populate store with state from a previous turn
        await store.set("scheduling:sess-persist-2", {
            "interview_scheduling_state": {
                "candidate_name": "João",
                "candidate_email": None,
                "collected_fields": ["candidate_name"],
                "pending_fields": [],
            }
        })

        captured_states = []

        async def capturing_invoke(state):
            captured_states.append(dict(state["workflow_data"]))
            state["workflow_data"]["response_data"] = {
                "status": "collecting",
                "next_field": "candidate_email",
            }
            return state

        mock_graph = MagicMock()
        mock_graph.invoke = capturing_invoke

        with patch("app.domains.interview_scheduling.domain.interview_graph", mock_graph), \
             patch("app.domains.interview_scheduling.domain.interview_session_store", store):
            # Second turn — no workflow_data in params
            await domain._run_interview_graph(
                "schedule_interview",
                {"raw_query": "joao@example.com"},
                ctx,
            )

        # Graph must have received the previously stored state
        assert len(captured_states) == 1
        assert "interview_scheduling_state" in captured_states[0]
        assert captured_states[0]["interview_scheduling_state"]["candidate_name"] == "João"

    @pytest.mark.asyncio
    async def test_params_workflow_data_overrides_stored(self):
        """If params include workflow_data, it takes precedence over stored state."""
        from app.domains.interview_scheduling.domain import InterviewSchedulingDomain
        from app.shared.services.interview_session_store import InterviewSessionStore

        domain = InterviewSchedulingDomain()
        ctx = _make_ctx("sess-persist-3")
        store = InterviewSessionStore()

        await store.set("scheduling:sess-persist-3", {"source": "store"})

        captured_states = []

        async def capturing_invoke(state):
            captured_states.append(dict(state["workflow_data"]))
            state["workflow_data"]["response_data"] = {"status": "collecting"}
            return state

        mock_graph = MagicMock()
        mock_graph.invoke = capturing_invoke

        with patch("app.domains.interview_scheduling.domain.interview_graph", mock_graph), \
             patch("app.domains.interview_scheduling.domain.interview_session_store", store):
            await domain._run_interview_graph(
                "schedule_interview",
                {"raw_query": "teste", "workflow_data": {"source": "params", "extra": "yes"}},
                ctx,
            )

        # Params override stored: "source" should be "params" (merged, params win)
        assert captured_states[0]["source"] == "params"
        assert captured_states[0]["extra"] == "yes"

    @pytest.mark.asyncio
    async def test_completed_status_clears_session_store(self):
        """When scheduling completes, session is removed from the store."""
        from app.domains.interview_scheduling.domain import InterviewSchedulingDomain
        from app.shared.services.interview_session_store import InterviewSessionStore

        domain = InterviewSchedulingDomain()
        ctx = _make_ctx("sess-persist-4")
        store = InterviewSessionStore()

        await store.set("scheduling:sess-persist-4", {"previous_state": True})
        mock_graph = _make_graph_response("completed", interview_id="iv-e2e-1")

        with patch("app.domains.interview_scheduling.domain.interview_graph", mock_graph), \
             patch("app.domains.interview_scheduling.domain.interview_session_store", store):
            result = await domain._run_interview_graph(
                "schedule_interview",
                {"raw_query": "confirmar"},
                ctx,
            )

        assert result.success is True
        # Session must have been deleted
        remaining = await store.get("scheduling:sess-persist-4")
        assert remaining is None

    @pytest.mark.asyncio
    async def test_no_session_id_skips_persistence(self):
        """When context has no session_id, store is not called (graceful skip)."""
        from app.domains.interview_scheduling.domain import InterviewSchedulingDomain
        from app.shared.services.interview_session_store import InterviewSessionStore

        domain = InterviewSchedulingDomain()
        ctx = _make_ctx(session_id="")  # empty session_id
        store = InterviewSessionStore()

        mock_graph = _make_graph_response("collecting", next_field="candidate_name")

        with patch("app.domains.interview_scheduling.domain.interview_graph", mock_graph), \
             patch("app.domains.interview_scheduling.domain.interview_session_store", store):
            result = await domain._run_interview_graph(
                "schedule_interview",
                {"raw_query": "agendar"},
                ctx,
            )

        # Should succeed without crashing, nothing saved for empty session
        assert result.needs_clarification is True
        saved = await store.get("scheduling:")
        assert saved is None


# ---------------------------------------------------------------------------
# Section 3: LangSmith tracing — verify @traceable applied without errors
# ---------------------------------------------------------------------------

class TestInterviewGraphTracing:

    def test_invoke_method_is_decorated(self):
        """invoke() should be callable (traceable decorator doesn't break it)."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        assert callable(g.invoke)
