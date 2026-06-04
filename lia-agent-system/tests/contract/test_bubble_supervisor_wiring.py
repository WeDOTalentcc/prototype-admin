"""Fase 2 item 6 — sensor de wiring (source-based, padrao test_sse_passthrough).

Garante que o desvio da bolha pro MainOrchestrator esta cabeado atras da flag
LIA_BUBBLE_VIA_SUPERVISOR, usa o produtor unico de serializacao, e acontece
DEPOIS do branch wizard (preserva o wizard na bolha = evita divergencia #2).
O comportamento funcional real (roteamento/delegacao) so valida live.
"""
from pathlib import Path

_SSE = (
    Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "agent_chat_sse.py"
)


def test_bubble_via_supervisor_flag_wired():
    src = _SSE.read_text(encoding="utf-8")
    assert "LIA_BUBBLE_VIA_SUPERVISOR" in src, (
        "flag LIA_BUBBLE_VIA_SUPERVISOR nao lida em agent_chat_sse -> bolha nunca "
        "roteia pro supervisor")
    assert "_orchestrator_result_to_frames" in src, (
        "serializacao do ChatResponse deve reusar o produtor unico "
        "_orchestrator_result_to_frames (chat.py), nao reimplementar")
    assert "get_main_orchestrator" in src, "desvio deve chamar o MainOrchestrator"


def test_supervisor_branch_after_wizard():
    src = _SSE.read_text(encoding="utf-8")
    flag_pos = src.index("LIA_BUBBLE_VIA_SUPERVISOR")
    wizard_pos = src.index('resolved_domain == "wizard"')
    assert flag_pos > wizard_pos, (
        "o desvio pro supervisor deve vir DEPOIS do branch wizard para preservar "
        "o wizard na bolha (Task #1080 / divergencia #2 do parity audit)")
