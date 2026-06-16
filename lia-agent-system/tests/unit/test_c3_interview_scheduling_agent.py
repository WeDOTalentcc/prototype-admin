"""
C3 — Interview Scheduling Agent: FairnessGuard + Confidence Score + HITL

Verifica:
1. FairnessGuard bloqueia mensagem com critério discriminatório
2. FairnessGuard passa mensagem legítima
3. _compute_confidence_score: 0.10 sem campos coletados
4. _compute_confidence_score: 0.95 com todos os campos
5. _compute_confidence_score: 1.0 quando scheduling_complete
6. _compute_confidence_score: 0.1 quando scheduling_error
7. _compute_confidence_score: 0.1 quando fairness_blocked
8. interview_details_collector: retorno precoce com response_data quando fairness blocked
9. interview_scheduler_executor: confidence_score=1.0 após agendamento bem-sucedido
10. interview_graph._invoke_langgraph usa confidence_score do estado (não hardcoded)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# 1–2 — FairnessGuard integration
# ---------------------------------------------------------------------------

class TestFairnessGuardInCollector:
    """FairnessGuard bloqueia mensagem discriminatória no nó collector."""

    def _make_state(self, message: str) -> dict:
        from app.schemas.interview_scheduling_state import InterviewSchedulingState
        interview_state = InterviewSchedulingState()
        return {
            "messages": [MagicMock(content=message)],
            "entities": {},
            "workflow_data": {
                "interview_scheduling_state": interview_state.model_dump(mode="json"),
            },
        }

    @pytest.mark.asyncio
    async def test_fairness_guard_blocks_discriminatory_message(self):
        """Mensagem com critério discriminatório retorna response_data de bloqueio."""
        state = self._make_state("Agende entrevista apenas com candidatos brancos abaixo de 30 anos")

        blocked_result = MagicMock()
        blocked_result.is_blocked = True
        blocked_result.category = "race_discrimination"
        blocked_result.blocked_terms = ["brancos"]
        blocked_result.educational_message = "Critério discriminatório detectado."

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard"
        ) as MockFG:
            MockFG.return_value.check.return_value = blocked_result
            from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
                interview_details_collector,
            )
            result = await interview_details_collector(state)

        assert result["workflow_data"].get("fairness_blocked") is True
        assert result["workflow_data"]["confidence_score"] == 0.1
        rd = result["workflow_data"].get("response_data", {})
        assert rd.get("status") == "fairness_blocked"
        assert "discriminatório" in rd.get("message", "") or "Critério" in rd.get("message", "")

    @pytest.mark.asyncio
    async def test_fairness_guard_passes_legitimate_message(self):
        """Mensagem legítima não é bloqueada e collector continua normalmente."""
        state = self._make_state("Agende entrevista técnica com João Silva amanhã às 14h")

        ok_result = MagicMock()
        ok_result.is_blocked = False

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard"
        ) as MockFG:
            MockFG.return_value.check.return_value = ok_result
            MockFG.return_value.check_implicit_bias.return_value = []
            # Mock Anthropic para evitar chamada real
            with patch(
                "app.domains.interview_scheduling.agents.interview_scheduling_nodes.AsyncAnthropic"
            ) as MockAnth:
                mock_resp = MagicMock()
                mock_resp.content = [MagicMock(text='{"candidate_name": "João Silva"}')]
                MockAnth.return_value.messages.create = AsyncMock(return_value=mock_resp)
                from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
                    interview_details_collector,
                )
                result = await interview_details_collector(state)

        assert result["workflow_data"].get("fairness_blocked") is not True

    @pytest.mark.asyncio
    async def test_fairness_guard_fail_safe(self):
        """Falha no FairnessGuard não interrompe o collector."""
        state = self._make_state("Agende entrevista com Maria")

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard",
            side_effect=ImportError("fairness_guard not available"),
        ):
            with patch(
                "app.domains.interview_scheduling.agents.interview_scheduling_nodes.AsyncAnthropic"
            ) as MockAnth:
                mock_resp = MagicMock()
                mock_resp.content = [MagicMock(text='{}')]
                MockAnth.return_value.messages.create = AsyncMock(return_value=mock_resp)
                from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
                    interview_details_collector,
                )
                result = await interview_details_collector(state)

        # Deve retornar sem exceção
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# 3–7 — _compute_confidence_score
# ---------------------------------------------------------------------------

class TestComputeConfidenceScore:
    """Testes do cálculo dinâmico de confidence score."""

    def _make_interview_state(self, filled_fields: list):
        from app.schemas.interview_scheduling_state import InterviewSchedulingState
        state = InterviewSchedulingState()
        for field in filled_fields:
            setattr(state, field, "valor_teste")
            state.mark_field_collected(field)
        return state

    def test_confidence_zero_fields(self):
        from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
            _compute_confidence_score,
        )
        s = self._make_interview_state([])
        result = _compute_confidence_score(s, {})
        assert result == pytest.approx(0.10, abs=0.01)

    def test_confidence_all_fields(self):
        from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
            _compute_confidence_score,
        )
        all_fields = [
            "candidate_name", "candidate_email", "job_title",
            "interview_type", "interviewer_email", "preferred_date", "preferred_time",
        ]
        s = self._make_interview_state(all_fields)
        result = _compute_confidence_score(s, {})
        assert result == pytest.approx(0.95, abs=0.01)

    def test_confidence_scheduling_complete(self):
        from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
            _compute_confidence_score,
        )
        s = self._make_interview_state([])
        result = _compute_confidence_score(s, {"interview_scheduling_complete": True})
        assert result == 1.0

    def test_confidence_scheduling_error(self):
        from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
            _compute_confidence_score,
        )
        s = self._make_interview_state([])
        result = _compute_confidence_score(s, {"interview_scheduling_error": "calendar unavailable"})
        assert result == 0.1

    def test_confidence_fairness_blocked(self):
        from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
            _compute_confidence_score,
        )
        s = self._make_interview_state(["candidate_name"])
        result = _compute_confidence_score(s, {"fairness_blocked": True})
        assert result == 0.1

    def test_confidence_partial_collection(self):
        """3 de 7 campos coletados → entre 0.10 e 0.95."""
        from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
            _compute_confidence_score,
        )
        s = self._make_interview_state(["candidate_name", "candidate_email", "job_title"])
        result = _compute_confidence_score(s, {})
        assert 0.10 < result < 0.95


# ---------------------------------------------------------------------------
# 9 — interview_scheduler_executor sets confidence_score = 1.0
# ---------------------------------------------------------------------------

class TestSchedulerExecutorConfidence:

    @pytest.mark.asyncio
    async def test_confidence_set_to_1_after_success(self):
        """interview_scheduler_executor define confidence_score=1.0 após agendamento OK."""
        from app.schemas.interview_scheduling_state import InterviewSchedulingState
        from datetime import datetime, timedelta, date

        _scheduled_at = datetime.now() + timedelta(days=1)
        interview_state = InterviewSchedulingState(
            candidate_name="Ana Lima",
            candidate_email="ana@empresa.com",
            job_title="Engenheira",
            interview_type="tecnica",
            interviewer_email="hr@empresa.com",
            preferred_date=_scheduled_at.date(),
            preferred_time="14:00",
            start_time=_scheduled_at,
            interview_mode="remoto",
        )

        state = {
            "workflow_data": {
                "interview_scheduling_state": interview_state.model_dump(mode="json"),
            }
        }

        mock_event = {"id": "evt-123", "onlineMeeting": {"joinUrl": "https://teams.link"}}
        mock_interview = MagicMock()
        mock_interview.id = "int-456"

        with patch(
            "app.domains.interview_scheduling.agents.interview_scheduling_nodes.calendar_service"
        ) as mock_cal:
            mock_cal.schedule_interview = AsyncMock(return_value=mock_event)

            mock_db = AsyncMock()
            mock_db.add = MagicMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock(side_effect=lambda x: setattr(x, "id", "int-456"))

            async def _fake_get_db():
                yield mock_db

            with patch(
                "app.domains.interview_scheduling.agents.interview_scheduling_nodes.get_db",
                _fake_get_db,
            ):
                from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
                    interview_scheduler_executor,
                )
                result = await interview_scheduler_executor(state)

        assert result["workflow_data"].get("confidence_score") == 1.0
        assert result["workflow_data"].get("interview_scheduling_complete") is True


# ---------------------------------------------------------------------------
# 10 — interview_graph._invoke_langgraph usa confidence do estado
# ---------------------------------------------------------------------------

class TestInterviewGraphConfidenceWiring:

    @pytest.mark.asyncio
    async def test_invoke_langgraph_uses_confidence_from_state(self):
        """_invoke_langgraph lê confidence_score do workflow_data, não hardcoded."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        ig = InterviewGraph()

        state = {
            "session_id": "sess-test",
            "company_id": "co-1",
            "messages": [MagicMock(content="teste")],
            "workflow_data": {"confidence_score": 0.75},
        }

        mock_callback = AsyncMock()
        mock_callback.on_chain_start_manual = MagicMock()
        mock_callback.on_chain_end_manual = AsyncMock()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value=state)

        with patch.object(ig, "_build_langgraph", return_value=mock_compiled):
            ig._compiled = mock_compiled
            result = await ig._invoke_langgraph(state, mock_callback)

        mock_callback.on_chain_end_manual.assert_called_once()
        call_kwargs = mock_callback.on_chain_end_manual.call_args
        called_confidence = call_kwargs[1].get("confidence") if call_kwargs[1] else call_kwargs[0][0]
        assert called_confidence == 0.75
