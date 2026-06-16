"""RRP na trilha supervisor (AUD-4 §4.2, 2026-06-07).

O sub-agente do supervisor produz response_blocks (rrp_block_sink ->
dr.metadata). O legacy orchestrator dropava antes de virar ChatResponse. Fix
carrega no result dict -> from_orchestrator_result le -> _orchestrator_result_to_frames
emite no frame message. Aqui testamos a CADEIA (carry -> ChatResponse -> frame).
"""
from __future__ import annotations

from app.orchestrator.execution.main_orchestrator import ChatResponse
from app.api.v1.chat import _orchestrator_result_to_frames

_BLOCKS = [
    {"kind": "score_explainer", "title": "Felipe Almeida"},
    {"kind": "comparison_table", "rows": []},
]


def test_from_orchestrator_result_carries_response_blocks():
    cr = ChatResponse.from_orchestrator_result(
        {"success": True, "message": "ranqueado", "response_blocks": _BLOCKS},
        "conv1",
    )
    assert cr.response_blocks == _BLOCKS


def test_from_orchestrator_result_blocks_in_data():
    # tambem aceita via structured_data/data (defesa)
    cr = ChatResponse.from_orchestrator_result(
        {"success": True, "message": "x", "data": {"response_blocks": _BLOCKS}},
        "conv1",
    )
    assert cr.response_blocks == _BLOCKS


def test_frames_emit_response_blocks():
    frames = _orchestrator_result_to_frames(
        {"success": True, "message": "ranqueado", "response_blocks": _BLOCKS},
        "conv1",
    )
    msg = next(f for f in frames if f.get("type") == "message")
    assert msg.get("response_blocks") == _BLOCKS


def test_frames_no_blocks_when_absent():
    frames = _orchestrator_result_to_frames(
        {"success": True, "message": "oi"}, "conv1"
    )
    msg = next(f for f in frames if f.get("type") == "message")
    assert not msg.get("response_blocks")
