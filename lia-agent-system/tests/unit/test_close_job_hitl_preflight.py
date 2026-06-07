"""close_job HITL pre-flight (AUD-4, 2026-06-06).

close_job NAO usa @tool_handler -> o bloqueio vem no produtor, ANTES do commit
(padrao OfferService.check_can_send). Antes: commitava (status=fechada) e SO
DEPOIS devolvia requires_confirmation = confirmacao-teatro pos-commit. Agora,
com o gate ligado e sem aprovacao, retorna needs_confirmation ANTES de abrir a
sessao DB (logo: nenhuma mutacao). Dormante quando LIA_HITL_GATE off.

NB: UUID fake de proposito - o pre-flight retorna ANTES de tocar o DB; no teste
dormente o fluxo normal so encontra job_not_found (nenhuma vaga real e mutada).
_context = ToolExecutionContext (objeto com .company_id), injetado pelo executor.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.domains.job_management.tools.job_tools import close_job

_FAKE_JOB = "00000000-0000-0000-0000-000000000000"
_FAKE_CO = "00000000-0000-0000-0000-0000000000ff"
_CTX = SimpleNamespace(company_id=_FAKE_CO, user_id="u-test")


def test_preflight_blocks_before_db_when_gate_on_unapproved(monkeypatch):
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    r = asyncio.run(close_job(
        job_id=_FAKE_JOB,
        reason="filled",
        _context=SimpleNamespace(company_id=_FAKE_CO, user_id="u-test"),
    ))
    assert r.get("needs_confirmation") is True
    assert r.get("success") is False
    assert r.get("action_taken") == "close_job"
    # retornou ANTES de qualquer mutacao: nenhum new_status='fechada' no payload
    assert (r.get("data") or {}).get("new_status") != "fechada"


def test_preflight_dormant_when_gate_off(monkeypatch):
    # Gate OFF: pre-flight NAO dispara cedo. close_job segue o fluxo normal
    # (que abre DB e, com UUID fake, retorna job_not_found ou mock). Provamos a
    # dormencia checando que NUNCA veio o bloqueio pre-DB do pre-flight.
    monkeypatch.delenv("LIA_HITL_GATE", raising=False)
    r = asyncio.run(close_job(
        job_id=_FAKE_JOB,
        reason="filled",
        _context=SimpleNamespace(company_id=_FAKE_CO, user_id="u-test"),
    ))
    assert not (
        r.get("needs_confirmation") is True
        and str(r.get("message", "")).startswith("Encerrar uma vaga")
    )
