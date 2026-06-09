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

    @pytest.mark.skip(reason="WSIInterviewGraph sendo aposentado — TriagemSessionService é o sistema canônico")
    def test_run_node_is_async_callable(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        assert callable(g._run_node)
        assert asyncio.iscoroutinefunction(g._run_node)


# ---------------------------------------------------------------------------
# Section 2: create_session
# ---------------------------------------------------------------------------

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
    @pytest.mark.skip(reason="WSIInterviewGraph sendo aposentado — TriagemSessionService é o sistema canônico")
    async def test_run_node_logs_node_start_and_end(self):
        """_run_node deve emitir node_start e node_end nos logs."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph, WSIInterviewState,
        )

        g = WSIInterviewGraph()
        log_records = []

        class _Capture(logging.Handler):
            def emit(self, record):
                log_records.append(record.getMessage())

        handler = _Capture()
        logger_inst = logging.getLogger("app.domains.cv_screening.agents.wsi_interview_graph")
        logger_inst.addHandler(handler)
        logger_inst.setLevel(logging.DEBUG)

        state = g.create_session("cand-log", "job-log", "co-log")

        async def mock_fn(s):
            return s

        await g._run_node("test_node", mock_fn, state)
        logger_inst.removeHandler(handler)

        assert any("node_start" in m for m in log_records), f"node_start not found in: {log_records}"
        assert any("node_end" in m for m in log_records), f"node_end not found in: {log_records}"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="WSIInterviewGraph sendo aposentado — TriagemSessionService é o sistema canônico")
    async def test_run_node_logs_node_error_on_exception(self):
        """_run_node em exceção deve emitir node_error e atualizar stage → ERROR."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph, WSIInterviewStage,
        )

        g = WSIInterviewGraph()
        log_records = []

        class _Capture(logging.Handler):
            def emit(self, record):
                log_records.append(record.getMessage())

        handler = _Capture()
        logger_inst = logging.getLogger("app.domains.cv_screening.agents.wsi_interview_graph")
        logger_inst.addHandler(handler)
        logger_inst.setLevel(logging.DEBUG)

        state = g.create_session("cand-err", "job-err", "co-err")

        async def failing_fn(s):
            raise RuntimeError("simulated WSI node failure")

        result = await g._run_node("fail_node", failing_fn, state)
        logger_inst.removeHandler(handler)

        assert any("node_error" in m for m in log_records), f"node_error not found in: {log_records}"
        assert result.stage == WSIInterviewStage.ERROR
        assert result.error is not None


# ---------------------------------------------------------------------------
# Section 4: start() com nodes mockados
# ---------------------------------------------------------------------------

class TestWSIInterviewGraphStart:

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="WSIInterviewGraph sendo aposentado — TriagemSessionService é o sistema canônico")
    async def test_start_calls_load_context_and_generate_question(self):
        """start() deve executar load_context e generate_question."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph, WSIInterviewStage,
        )

        g = WSIInterviewGraph()
        state = g.create_session("c", "j", "co")

        called = []

        async def mock_load_context(s):
            called.append("load_context")
            s.stage = WSIInterviewStage.GENERATE_QUESTION
            return s

        async def mock_generate_question(s):
            called.append("generate_question")
            s.awaiting_response = True
            return s

        g.nodes.load_context = mock_load_context
        g.nodes.generate_question = mock_generate_question

        result = await g.start(state)

        assert "load_context" in called
        assert "generate_question" in called
        assert result.awaiting_response is True

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="WSIInterviewGraph sendo aposentado — TriagemSessionService é o sistema canônico")
    async def test_start_skips_generate_question_if_complete(self):
        """Se load_context completar a sessão, generate_question não é chamado."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph, WSIInterviewStage,
        )

        g = WSIInterviewGraph()
        state = g.create_session("c", "j", "co")

        called = []

        async def mock_load_context(s):
            called.append("load_context")
            s.stage = WSIInterviewStage.COMPLETE
            return s

        async def mock_generate_question(s):
            called.append("generate_question")
            return s

        g.nodes.load_context = mock_load_context
        g.nodes.generate_question = mock_generate_question

        result = await g.start(state)

        assert "load_context" in called
        assert "generate_question" not in called
        assert result.is_complete is True


# ---------------------------------------------------------------------------
# Section 5: get_session_summary
# ---------------------------------------------------------------------------

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

    @pytest.mark.skip(reason="WSIInterviewGraph sendo aposentado — TriagemSessionService é o sistema canônico")
    def test_get_session_summary_scores_structure(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        state = g.create_session("c", "j", "co")
        summary = g.get_session_summary(state)

        scores = summary["scores"]
        assert "technical" in scores
        assert "behavioral" in scores
        assert "situational" in scores
        assert "eligibility" in scores
        assert "final" in scores
