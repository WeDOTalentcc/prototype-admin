"""TDD: candidate_portal.py deve mascarar PII antes de enviar ao LLM.

Gap F (auditoria enterprise-readiness 2026-06-08, verificado adversarial
CONFIRMED HIGH): o handler candidate_chat passava request_data.message CRU
para CandidateSelfServiceAgent.process(), sem passar pela camada C3b nem por
strip_pii_for_llm_prompt. O chat do recrutador (agent_chat_sse.py) mascara;
o portal do candidato (caminho separado) nunca foi conectado.

Surface candidate-facing => mask_names=True (default): candidatos digitam
CPF/RG/email/telefone (próprios ou de terceiros) e isso não pode chegar cru
ao LLM. Diferente do chat do recrutador (mask_names=False p/ busca de entidade).
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_candidate_chat_strips_cpf_before_llm():
    """POST com CPF cru -> o message que chega ao agente NAO contem o CPF."""
    from app.api.v1.candidate_portal import candidate_chat, CandidateChatRequest

    captured = {}

    async def fake_process(agent_input):
        captured["message"] = agent_input.message
        out = MagicMock()
        out.message = "ok"
        out.tools_called = []
        out.fairness_triggered = False
        return out

    # Mock da CLASSE inteira: instanciar o agent real dispara get_checkpointer()
    # (RuntimeError em APP_ENV=production no ambiente de teste). O MagicMock como
    # classe retorna mock_instance quando chamado como CandidateSelfServiceAgent().
    mock_instance = MagicMock()
    mock_instance.process = fake_process

    req = CandidateChatRequest(
        message="meu CPF e 123.456.789-00 e meu email joao@example.com",
        candidate_token="tok",
        vacancy_id="vac_456",
    )

    _svc = "app.domains.candidate_self_service.services.candidate_status_service.CandidateStatusService"
    _agent = "app.domains.candidate_self_service.agents.candidate_react_agent.CandidateSelfServiceAgent"
    _repo = "app.domains.candidate_self_service.repositories.candidate_status_repository.CandidateSelfServiceRepository"

    with patch(
        _svc + ".validate_token",
        new=AsyncMock(return_value={
            "candidate_id": "c1", "vacancy_id": "vac_456", "company_id": "comp",
        }),
    ), patch(
        _svc + ".check_rate_limit",
        new=AsyncMock(return_value={"allowed": True}),
    ), patch(
        _agent, return_value=mock_instance,
    ), patch(
        _repo + ".log_portal_access", new=AsyncMock(),
    ):
        await candidate_chat(
            request_data=req, request=MagicMock(), company_id="comp",
        )

    assert "message" in captured, "agent.process nao foi chamado"
    assert "123.456.789-00" not in captured["message"], (
        "CPF cru vazou para o LLM no portal do candidato (Gap F)"
    )
    assert "joao@example.com" not in captured["message"], (
        "email cru vazou para o LLM no portal do candidato (Gap F)"
    )
