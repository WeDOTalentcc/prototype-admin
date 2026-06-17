"""HITL bird supervisor (AUD-4 §4.2, 2026-06-07).

O sub-agente ReAct do supervisor pode bloquear uma tool sensivel -> hitl_pending
viaja no dr.metadata -> legacy carrega -> ChatResponse.hitl_pending -> o drain SSE
minta + emite approval_required. Aqui testamos o carry ate o ChatResponse (o mint
no drain e glue, validado live; _build_approval_frame ja tem teste proprio).
"""
from __future__ import annotations

from app.orchestrator.execution.main_orchestrator import ChatResponse

_HP = {"tool": "close_job", "domain": "job_management", "message": "Confirme?"}


def test_from_orchestrator_result_carries_hitl_pending():
    cr = ChatResponse.from_orchestrator_result(
        {"success": True, "message": "x", "hitl_pending": _HP}, "conv1"
    )
    assert cr.hitl_pending == _HP


def test_from_orchestrator_result_no_hitl_pending():
    cr = ChatResponse.from_orchestrator_result(
        {"success": True, "message": "x"}, "conv1"
    )
    assert cr.hitl_pending is None
