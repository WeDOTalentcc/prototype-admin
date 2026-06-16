"""Navigate na trilha supervisor (AUD-4 §4.1, 2026-06-07).

A LLM do supervisor emite [NAVIGATE:<page>] como texto; _orchestrator_result_to_frames
deve fazer strip + injetar ui_action/ui_action_params (contrato FE), espelhando o
ramo agente. Sem isto o marker vaza como texto e nao navega.
"""
from __future__ import annotations

from app.api.v1.chat import _orchestrator_result_to_frames


def _msg(result):
    frames = _orchestrator_result_to_frames(result, "c1")
    return next(f for f in frames if f.get("type") == "message")


def test_marker_stripped_and_ui_action_injected():
    m = _msg({"success": True, "message": "Te levo pra Configurações [NAVIGATE:configuracoes]"})
    assert "[NAVIGATE" not in str(m)  # leak removido do frame inteiro
    assert m.get("ui_action") == "navigate_to"
    assert m.get("ui_action_params", {}).get("page") == "configuracoes"


def test_marker_with_id_and_query():
    m = _msg({"success": True, "message": "abrindo [NAVIGATE:vaga_detalhe:abc-123?tab=edit&section=descricao]"})
    assert "[NAVIGATE" not in str(m)
    p = m.get("ui_action_params", {})
    assert p.get("id") == "abc-123"
    assert (p.get("query") or {}).get("tab") == "edit"


def test_no_marker_no_ui_action():
    m = _msg({"success": True, "message": "Aqui esta o resumo da vaga."})
    assert not m.get("ui_action")


def test_explicit_ui_action_preserved():
    m = _msg({
        "success": True, "message": "x",
        "ui_action": "navigate_to",
        "ui_action_params": {"page": "pipeline_kanban"},
    })
    assert m.get("ui_action") == "navigate_to"
    assert m.get("ui_action_params", {}).get("page") == "pipeline_kanban"
