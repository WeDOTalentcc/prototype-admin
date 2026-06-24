"""Contract sensor — wire do RRP: compare_candidates -> response_blocks no frame.

Fecha o gap G0 (auditoria 2026-06-04): garante deterministicamente que o
response_blocks emitido por _handle_compare_candidates (em DomainResponse.data)
ATRAVESSA from_orchestrator_result (lift) E _orchestrator_result_to_frames
(serializacao WS/SSE) ate chegar ao frame que o frontend consome.

Se este teste falhar:
  -> O response_blocks parou de fluir do orquestrador ate o frame. Verifique:
     (1) ChatResponse.from_orchestrator_result faz lift de
         result["data"]["response_blocks"] (main_orchestrator.py);
     (2) _orchestrator_result_to_frames passa response_blocks=_get("response_blocks")
         para serialize_message (chat.py);
     (3) serialize_message inclui payload["response_blocks"] (chat_event_serializer.py).
  NUNCA afrouxe o teste — conserte o produtor (canonical-fix).
"""
from app.orchestrator.execution.main_orchestrator import ChatResponse
from app.api.v1.chat import _orchestrator_result_to_frames

_BLOCK = {
    "kind": "comparison_table",
    "block_id": "comparison_table:compare_candidates:1-2",
    "role": "support",
    "layout": "wide",
    "state": "ready",
    "title": "Comparacao de candidatos",
    "entity_type": "candidate",
    "columns": [{"key": "name", "label": "Candidato", "type": "text", "sortable": True}],
    "rows": [{"entity_id": "1", "cells": {"name": "Ana"}, "score_block_id": None,
              "highlight": None}],
    "default_sort": None,
    "total_count": 1,
    "shown_count": 1,
}


def _result_with_blocks():
    return {
        "content": "Comparei os candidatos",
        "data": {
            "action_id": "compare_candidates",
            "candidates": [{"id": "1", "name": "Ana"}],
            "response_blocks": [_BLOCK],
        },
    }


def test_lift_from_domain_data():
    """from_orchestrator_result eleva response_blocks de result['data']."""
    cr = ChatResponse.from_orchestrator_result(_result_with_blocks(), conv_id="c1")
    assert cr.response_blocks, "response_blocks deveria ter sido elevado de data"
    assert len(cr.response_blocks) == 1
    assert cr.response_blocks[0]["kind"] == "comparison_table"


def test_serialized_into_frame():
    """_orchestrator_result_to_frames inclui response_blocks no frame de mensagem."""
    cr = ChatResponse.from_orchestrator_result(_result_with_blocks(), conv_id="c1")
    frames = _orchestrator_result_to_frames(cr, "c1")
    carriers = [f for f in frames if isinstance(f, dict) and f.get("response_blocks")]
    assert carriers, f"nenhum frame carregou response_blocks; frames={[f.get('type') for f in frames]}"
    assert carriers[0]["response_blocks"][0]["kind"] == "comparison_table"


def test_backward_compat_no_blocks():
    """Sem response_blocks, o campo fica None e o frame nao ganha a chave."""
    cr = ChatResponse.from_orchestrator_result(
        {"content": "oi", "data": {"action_id": "x"}}, conv_id="c1"
    )
    assert cr.response_blocks is None
    frames = _orchestrator_result_to_frames(cr, "c1")
    assert not any(
        isinstance(f, dict) and "response_blocks" in f for f in frames
    ), "frame nao deveria ter response_blocks quando nao ha blocos"


def test_lift_from_action_result():
    """from_action_result (path da produtora canonical sourcing_actions via
    ActionExecutor) tambem eleva response_blocks de action_result.data."""
    from app.orchestrator.action_executor import ActionResult

    ar = ActionResult(
        status="executed",
        message="Comparei os candidatos",
        data={"candidates": [], "response_blocks": [_BLOCK]},
        action_type="compare_candidates",
    )
    cr = ChatResponse.from_action_result(ar, intent="comparar_candidatos", conv_id="c1")
    assert cr.response_blocks, "from_action_result deveria elevar response_blocks"
    assert cr.response_blocks[0]["kind"] == "comparison_table"
