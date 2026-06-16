"""Sensor canonical — wizard canonical path NÃO cai silenciosamente pro legacy.

Frente 3 (2026-05-29). REGRA 4 (anti-silent-fallback, CLAUDE.md):
quando `WizardSessionService.process_message` crasha com exceção dura, os
handlers de chat (WebSocket e SSE) DEVEM falhar alto — enviar erro explícito
ao cliente e encerrar o turno — NUNCA cair no agente ReAct legacy
(`_get_agent("wizard")`). O fallback silencioso mascarava crashes do canonical
com respostas de um agente completamente diferente, escondendo o defeito.

Disciplina: harness-engineering (sensor estrutural via leitura de source) +
canonical-fix (produtor único, gêmeo WS+SSE corrigido junto).
"""
from __future__ import annotations

import os

_V1_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "app", "api", "v1",
)

WS_PATH = os.path.join(_V1_DIR, "agent_chat_ws.py")
SSE_PATH = os.path.join(_V1_DIR, "agent_chat_sse.py")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _except_block(src: str, crash_marker: str) -> str:
    """Extrai ~800 chars a partir do log de crash do canonical wizard."""
    start = src.find(crash_marker)
    assert start != -1, f"marcador de crash não encontrado: {crash_marker!r}"
    return src[start : start + 800]


# ── WebSocket (agent_chat_ws.py) ─────────────────────────────────────────────

def test_ws_wizard_failure_does_not_fall_back_to_legacy():
    block = _except_block(
        _read(WS_PATH),
        "[AgentChatWS] WizardSessionService canonical path crashed",
    )
    assert "falling back to legacy" not in block, (
        "Silent fallback ainda presente no handler WS: em exceção dura o wizard "
        "canonical cai pro ReAct legacy. Fix: enviar serialize_error + continue."
    )


def test_ws_wizard_failure_sends_explicit_error():
    block = _except_block(
        _read(WS_PATH),
        "[AgentChatWS] WizardSessionService canonical path crashed",
    )
    assert "serialize_error" in block, (
        "Handler WS deve enviar erro explícito ao cliente quando o canonical crasha."
    )
    assert "wizard_canonical_error" in block, (
        "Erro explícito deve usar o code canonical 'wizard_canonical_error'."
    )
    assert "continue" in block, (
        "Handler WS deve encerrar o turno (continue) após erro explícito, "
        "sem cair no _get_agent legacy."
    )


# ── SSE (agent_chat_sse.py) ──────────────────────────────────────────────────

def test_sse_wizard_failure_does_not_fall_back_to_generic():
    block = _except_block(
        _read(SSE_PATH),
        "[SSEChat] WizardSessionService canonical path crashed",
    )
    assert "falling back to generic agent" not in block, (
        "Silent fallback ainda presente no handler SSE: em exceção dura o wizard "
        "canonical cai pro agente genérico. Fix: yield serialize_error + return."
    )


def test_sse_wizard_failure_yields_explicit_error():
    block = _except_block(
        _read(SSE_PATH),
        "[SSEChat] WizardSessionService canonical path crashed",
    )
    assert "serialize_error" in block, (
        "Handler SSE deve emitir erro explícito ao cliente quando o canonical crasha."
    )
    assert "wizard_canonical_error" in block, (
        "Erro explícito deve usar o code canonical 'wizard_canonical_error'."
    )
    assert "return" in block, (
        "Handler SSE deve encerrar o stream (return) após erro explícito, "
        "sem cair no _get_agent genérico."
    )
