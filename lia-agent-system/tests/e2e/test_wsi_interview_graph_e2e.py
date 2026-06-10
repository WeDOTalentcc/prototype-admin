"""
E2E Tests — WSIInterviewGraph (state machine de entrevistas WSI).

Cobre:
- Importação e singleton
- _run_node emite node_start / node_end / node_error
- start() / submit_response() decorados com @_traceable e chamáveis
- Sessão criada com campos corretos
- Erro em nó atualiza stage → ERROR
"""
import pytest
import logging
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Section 1: Importação e estrutura
# ---------------------------------------------------------------------------

class TestWSIInterviewGraphImport:

    def test_graph_importable(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        assert g is not None

    def test_singleton_importable(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import wsi_interview_graph
        assert wsi_interview_graph is not None

    def test_start_is_async_callable(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        assert callable(g.start)
        assert asyncio.iscoroutinefunction(g.start)

    def test_submit_response_is_async_callable(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        assert callable(g.submit_response)
        assert asyncio.iscoroutinefunction(g.submit_response)

class TestWSIInterviewGraphSession:

    def test_create_session_returns_state_with_correct_fields(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph, WSIInterviewState,
        )
        g = WSIInterviewGraph()
        state = g.create_session(
            candidate_id="cand-1",
            job_id="job-1",
            company_id="co-1",
            interview_level="standard",
        )
        assert isinstance(state, WSIInterviewState)
        assert state.candidate_id == "cand-1"
        assert state.job_id == "job-1"
        assert state.company_id == "co-1"
        assert state.interview_level == "standard"
        assert state.session_id  # deve ser não-vazio

    def test_create_session_initial_stage_is_init(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph, WSIInterviewStage,
        )
        g = WSIInterviewGraph()
        state = g.create_session("c", "j", "co")
        assert state.stage == WSIInterviewStage.INIT

    def test_is_complete_false_at_start(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        state = g.create_session("c", "j", "co")
        assert state.is_complete is False


# ---------------------------------------------------------------------------
# Section 3: _run_node logging estruturado (BCB 498 / SOX)
# ---------------------------------------------------------------------------

class TestWSIInterviewGraphNodeLogging:

    @pytest.mark.asyncio
    @pytest.mark.asyncio
class TestWSIInterviewGraphStart:

    @pytest.mark.asyncio
    @pytest.mark.asyncio
class TestWSIInterviewGraphSummary:

    def test_get_session_summary_returns_required_fields(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        state = g.create_session("c", "j", "co")

        summary = g.get_session_summary(state)

        assert "session_id" in summary
        assert "candidate_id" in summary
        assert "job_id" in summary
        assert "stage" in summary
        assert "is_complete" in summary
        assert "scores" in summary
        assert "execution_log" in summary

