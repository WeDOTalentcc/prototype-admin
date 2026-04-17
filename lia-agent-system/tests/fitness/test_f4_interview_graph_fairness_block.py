"""
Behavioral test — F4 (AUDIT 2026-04, task #352).

Exercita o helper `InterviewGraph._apply_fairness_guard_to_response` com um
`check_fairness` mockado para garantir que conteúdo discriminatório:

  1. é BLOQUEADO (mensagem original substituída pelo fallback sanitizado);
  2. tem mensagem original preservada em `fairness_blocked_original`;
  3. dispara `audit_service.log_decision(decision="blocked", ...)` com
     `criteria_used=["fairness_guard_l2"]`.

Também cobre o caminho fail-open (FG indisponível) e o caminho clean
(sem warnings) para garantir que não há regressão no fluxo feliz.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph


def _make_state_result(message: str) -> dict:
    return {
        "company_id": "company-test-123",
        "candidate_id": "candidate-test-456",
        "job_id": "job-test-789",
        "workflow_data": {
            "interview_scheduling_complete": True,
            "response_data": {
                "workflow_type": "interview_scheduling",
                "status": "completed",
                "message": message,
            },
        },
    }


@pytest.mark.asyncio
async def test_fairness_guard_blocks_biased_message_and_logs_audit():
    graph = InterviewGraph()
    biased_msg = (
        "Olá, candidata! Por ser jovem e mulher, vamos agendar sua entrevista. "
        "Confirmação enviada para seu e-mail."
    )
    result = _make_state_result(biased_msg)

    fake_fg_result = SimpleNamespace(
        has_warnings=True,
        warnings=["protected_attribute:gender", "protected_attribute:age"],
    )

    audit_mock = MagicMock()
    audit_mock.log_decision = AsyncMock()

    async def _fake_get_db():
        yield MagicMock()

    with patch(
        "app.shared.compliance.fairness_guard_middleware.check_fairness",
        return_value=fake_fg_result,
    ) as fg_call, patch(
        "app.shared.compliance.audit_service.audit_service",
        audit_mock,
    ), patch(
        "app.core.database.get_db",
        _fake_get_db,
    ):
        out = await graph._apply_fairness_guard_to_response(
            result=result,
            session_id="sess-test",
            company_id="company-test-123",
            candidate_id="candidate-test-456",
            job_id="job-test-789",
        )

    # 1. check_fairness foi chamado com o context certo
    fg_call.assert_called_once()
    _, kwargs = fg_call.call_args
    assert kwargs["context"] == "interview_scheduling_response"
    assert kwargs["company_id"] == "company-test-123"

    # 2. Mensagem ao candidato foi REGENERADA (substituída pelo fallback)
    response_data = out["workflow_data"]["response_data"]
    assert response_data["message"] == InterviewGraph._FAIRNESS_BLOCK_FALLBACK_MESSAGE
    assert response_data["message"] != biased_msg
    assert response_data["fairness_blocked"] is True
    assert response_data["fairness_warnings"] == [
        "protected_attribute:gender",
        "protected_attribute:age",
    ]
    # 2a. Mensagem original NÃO deve vazar via response_data (vai para o caller)
    assert "fairness_blocked_original" not in response_data
    assert biased_msg not in str(response_data)

    # 3. audit_service.log_decision foi chamado com decision="blocked"
    audit_mock.log_decision.assert_awaited_once()
    _, audit_kwargs = audit_mock.log_decision.call_args
    assert audit_kwargs["decision"] == "blocked"
    assert audit_kwargs["decision_type"] == "candidate_message"
    assert audit_kwargs["agent_name"] == "interview_graph"
    assert audit_kwargs["domain"] == "interview_scheduling"
    assert audit_kwargs["criteria_used"] == ["fairness_guard_l2"]
    assert audit_kwargs["candidate_id"] == "candidate-test-456"
    assert audit_kwargs["job_id"] == "job-test-789"
    assert audit_kwargs["metadata"]["warnings_count"] == 2
    assert audit_kwargs["metadata"]["path"] == "fairness_guard_l2"
    # 3a. Mensagem original PRECISA estar no audit (server-side forense)
    assert audit_kwargs["metadata"]["blocked_original_message"] == biased_msg


@pytest.mark.asyncio
async def test_fairness_guard_passthrough_when_clean():
    """Mensagem sem warnings — passa intacta, sem audit de bloqueio."""
    graph = InterviewGraph()
    clean_msg = "Entrevista agendada com sucesso. Confirmação enviada por e-mail."
    result = _make_state_result(clean_msg)

    fake_fg_result = SimpleNamespace(has_warnings=False, warnings=[])
    audit_mock = MagicMock()
    audit_mock.log_decision = AsyncMock()

    with patch(
        "app.shared.compliance.fairness_guard_middleware.check_fairness",
        return_value=fake_fg_result,
    ), patch(
        "app.shared.compliance.audit_service.audit_service",
        audit_mock,
    ):
        out = await graph._apply_fairness_guard_to_response(
            result=result,
            session_id="sess-clean",
            company_id="company-test-123",
            candidate_id="candidate-test-456",
            job_id="job-test-789",
        )

    response_data = out["workflow_data"]["response_data"]
    assert response_data["message"] == clean_msg
    assert "fairness_blocked" not in response_data
    assert "fairness_warnings" not in response_data
    audit_mock.log_decision.assert_not_called()


@pytest.mark.asyncio
async def test_fairness_guard_fail_open_on_internal_error():
    """Falha do FG (import/raise) é fail-open: não derruba o agendamento."""
    graph = InterviewGraph()
    msg = "Entrevista confirmada."
    result = _make_state_result(msg)

    with patch(
        "app.shared.compliance.fairness_guard_middleware.check_fairness",
        side_effect=RuntimeError("boom"),
    ):
        out = await graph._apply_fairness_guard_to_response(
            result=result,
            session_id="sess-error",
            company_id="company-test-123",
            candidate_id=None,
            job_id=None,
        )

    response_data = out["workflow_data"]["response_data"]
    assert response_data["message"] == msg
    assert "fairness_blocked" not in response_data


@pytest.mark.asyncio
async def test_fairness_guard_skipped_when_no_message():
    """Se response_data não tem `message`, o gate não roda."""
    graph = InterviewGraph()
    result = {
        "company_id": "c1",
        "workflow_data": {"response_data": {"status": "collecting"}},
    }
    with patch(
        "app.shared.compliance.fairness_guard_middleware.check_fairness",
    ) as fg_call:
        out = await graph._apply_fairness_guard_to_response(
            result=result,
            session_id="sess-nomsg",
            company_id="c1",
            candidate_id=None,
            job_id=None,
        )

    fg_call.assert_not_called()
    assert out is result
