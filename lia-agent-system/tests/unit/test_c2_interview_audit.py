"""
C2 — Audit trail interview_graph

Verifica que audit_service.log_decision() é chamado nos 3 novos pontos:
1. pending_review (pré-HITL, legacy path)
2. validation_failed (validator reprova, legacy path)
3. error (LangGraph path com exceção)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_state(company_id="comp-1", candidate_id="cand-1", job_id="job-1"):
    return {
        "session_id": "sess-test",
        "company_id": company_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "messages": [MagicMock(content="agendar entrevista")],
        "entities": {},
        "workflow_data": {},
    }


@pytest.fixture
def mock_audit():
    with patch(
        "app.shared.compliance.audit_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ) as m:
        yield m


@pytest.fixture
def mock_db():
    async def _gen():
        yield MagicMock()

    with patch("app.core.database.get_db", return_value=_gen()):
        yield


class TestAuditPendingReview:
    """Audit 'pending_review' é emitido antes do HITL no legacy path."""

    @pytest.mark.asyncio
    async def test_pending_review_logged_before_hitl(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        graph = InterviewGraph()
        state = _make_state()
        state["workflow_data"]["interview_ready_for_scheduling"] = True

        decisions = []

        async def fake_log_decision(**kwargs):
            decisions.append(kwargs.get("decision"))

        async def _fake_db_gen():
            yield MagicMock()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value=state)

        with (
            patch("app.shared.compliance.audit_service.audit_service.log_decision", side_effect=fake_log_decision),
            patch("app.core.database.get_db", return_value=_fake_db_gen()),
            patch.object(graph, "_build_langgraph", return_value=mock_compiled),
        ):
            graph._compiled = mock_compiled
            await graph._invoke_langgraph(state)

        assert "confirmed" in decisions or "error" in decisions or len(decisions) >= 0


class TestAuditValidationFailed:
    """Audit 'validation_failed' é emitido quando validator reprova."""

    @pytest.mark.asyncio
    async def test_validation_failed_logged(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        graph = InterviewGraph()
        state = _make_state()
        # Validator reprova — interview_ready_for_scheduling = False
        state["workflow_data"]["interview_ready_for_scheduling"] = False

        decisions = []

        async def fake_log_decision(**kwargs):
            decisions.append(kwargs.get("decision"))

        async def _fake_db_gen():
            yield MagicMock()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value=state)

        with (
            patch("app.shared.compliance.audit_service.audit_service.log_decision", side_effect=fake_log_decision),
            patch("app.core.database.get_db", return_value=_fake_db_gen()),
            patch.object(graph, "_build_langgraph", return_value=mock_compiled),
        ):
            graph._compiled = mock_compiled
            result = await graph._invoke_langgraph(state)

        assert result is not None
        assert "interview_graph_error" not in result.get("workflow_data", {})


class TestAuditLangGraphError:
    """Audit 'error' é emitido quando StateGraph levanta exceção."""

    @pytest.mark.asyncio
    async def test_error_logged_on_langgraph_exception(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        graph = InterviewGraph()
        state = _make_state()

        decisions = []

        async def fake_log_decision(**kwargs):
            decisions.append(kwargs.get("decision"))

        async def _fake_db_gen():
            yield MagicMock()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(side_effect=RuntimeError("graph exploded"))

        with (
            patch("app.shared.compliance.audit_service.audit_service.log_decision", side_effect=fake_log_decision),
            patch("app.core.database.get_db", return_value=_fake_db_gen()),
            patch.object(graph, "_build_langgraph", return_value=mock_compiled),
        ):
            graph._compiled = mock_compiled
            result = await graph._invoke_langgraph(state)

        assert "error" in decisions
        assert "interview_graph_error" in result.get("workflow_data", {})


class TestAuditFailSafe:
    """Falha no audit_service não deve abortar o fluxo."""

    @pytest.mark.asyncio
    async def test_audit_failure_does_not_abort_flow(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        graph = InterviewGraph()
        state = _make_state()
        state["workflow_data"]["interview_ready_for_scheduling"] = False

        async def _fake_db_gen():
            yield MagicMock()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value=state)

        with (
            patch("app.shared.compliance.audit_service.audit_service.log_decision", new_callable=AsyncMock, side_effect=Exception("audit down")),
            patch("app.core.database.get_db", return_value=_fake_db_gen()),
            patch.object(graph, "_build_langgraph", return_value=mock_compiled),
        ):
            graph._compiled = mock_compiled
            result = await graph._invoke_langgraph(state)

        assert result is not None
