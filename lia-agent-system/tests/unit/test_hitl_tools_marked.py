"""HITL 1c + F3 — tools sensiveis gateadas via hitl_preflight (AUD-4, 2026-06-07; F3 2026-06-09).

Cada tool sensivel, com LIA_HITL_GATE on + sem aprovacao, retorna
needs_confirmation ANTES de qualquer side-effect (a maioria retorna antes de
abrir DB). Dormante com a flag off. UUIDs/ids fake (o pre-flight retorna cedo).

F3 (2026-06-09): adicionados update_candidate_stage, move_candidate (pipeline),
batch_move_candidates (kanban) — todas as mutacoes de mover candidato agora gateadas.
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from types import SimpleNamespace

from app.domains.communication.tools.communication_tools import (
    send_email,
    send_whatsapp,
    send_bulk_email,
)
from app.domains.cv_screening.tools.candidate_tools import (
    reject_candidate,
    bulk_update_candidates_stage,
    update_candidate_stage,
)
from app.domains.job_management.tools.job_tools import publish_job

_COMPANY = "00000000-0000-0000-0000-000000000099"


@contextmanager
def _tenant_ctx(company_id: str = _COMPANY):
    from app.middleware.auth_enforcement import _current_company_id
    token = _current_company_id.set(company_id)
    try:
        yield
    finally:
        _current_company_id.reset(token)

_C = "00000000-0000-0000-0000-000000000001"
_J = "00000000-0000-0000-0000-000000000002"


def _blocks(coro):
    r = asyncio.run(coro)
    return r.get("needs_confirmation") is True and r.get("success") is False


def test_send_email_gated(monkeypatch):
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    assert _blocks(send_email(candidate_id=_C, subject="s", body="b"))


def test_send_whatsapp_gated(monkeypatch):
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    assert _blocks(send_whatsapp(candidate_id=_C, message="oi"))


def test_send_bulk_email_gated(monkeypatch):
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    assert _blocks(send_bulk_email(candidate_ids=[_C], template_id="t1"))


def test_reject_candidate_gated(monkeypatch):
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    assert _blocks(reject_candidate(candidate_id=_C, job_id=_J, reason="x"))


def test_bulk_update_stage_gated(monkeypatch):
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    assert _blocks(bulk_update_candidates_stage(candidate_ids=[_C], target_stage="entrevista"))


def test_publish_job_gated(monkeypatch):
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    assert _blocks(publish_job(
        job_id=_J,
        _context=SimpleNamespace(company_id="c-test", user_id="u"),
    ))


def test_update_candidate_stage_gated(monkeypatch):
    """F3: mover candidato único é mutação gateada."""
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    assert _blocks(update_candidate_stage(candidate_id=_C, target_stage="Entrevistas"))


def test_move_candidate_pipeline_gated(monkeypatch):
    """F3: pipeline domain move_candidate gateado."""
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_move_candidate
    with _tenant_ctx():
        assert _blocks(_wrap_move_candidate(candidate_id=_C, target_stage="Entrevistas"))


def test_batch_move_kanban_gated(monkeypatch):
    """F3: kanban batch_move_candidates gateado."""
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    from app.domains.recruiter_assistant.agents.kanban_tool_registry import _wrap_batch_move_candidates
    with _tenant_ctx():
        assert _blocks(_wrap_batch_move_candidates(candidate_ids=[_C], target_stage="Entrevistas"))


def test_all_dormant_when_gate_off(monkeypatch):
    # Gate OFF: nenhuma deve devolver o bloqueio HITL cedo (segue o fluxo normal).
    monkeypatch.delenv("LIA_HITL_GATE", raising=False)
    r = asyncio.run(send_whatsapp(candidate_id=_C, message="oi"))
    # nao e o needs_confirmation do pre-flight (pode falhar por DB/candidato fake,
    # mas nunca o bloqueio dormente)
    assert not (r.get("needs_confirmation") is True and (r.get("hitl") or {}).get("tool") == "send_whatsapp")
