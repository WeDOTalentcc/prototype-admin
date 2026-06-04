"""Fase A sensor: PII masking no PRODUTOR do stream (canonical-fix).

Conteúdo streamado (tokens) DEVE ser mascarado no produtor (llm.py), não por
transporte — assim todos os caminhos SSE/WS saem seguros. Activity events do
AgenticLoop NUNCA carregam args/resultados crus de tool (PII de candidato).
"""
from __future__ import annotations

import re
from pathlib import Path

from app.domains.ai.services.llm import _mask_stream_text
from app.shared.pii_masking import mask_pii


def test_mask_stream_text_applies_mask_pii():
    # Pina o WIRING (helper == mask_pii), independente do que mask_pii mascara.
    sample = "candidato joao.silva@empresa.com CPF 123.456.789-00 tel 11 98765-4321"
    assert _mask_stream_text(sample) == mask_pii(sample)


def test_mask_stream_text_handles_empty_and_none_safe():
    assert _mask_stream_text("") == ""


def test_agentic_loop_emits_no_raw_tool_pii():
    # Activity events não podem carregar tc.parameters / tool_result_content crus.
    al = (
        Path(__file__).resolve().parents[2]
        / "app" / "orchestrator" / "execution" / "agentic_loop.py"
    )
    src = al.read_text(encoding="utf-8")
    emits = re.findall(r"_emit_activity\(\s*\{.*?\}", src, re.DOTALL)
    assert emits, "nenhum _emit_activity({...}) encontrado — o AgenticLoop mudou de forma?"
    for e in emits:
        assert "parameters" not in e, f"activity event carrega 'parameters' (PII): {e[:120]}"
        assert "tool_result" not in e, f"activity event carrega 'tool_result' (PII): {e[:120]}"
        assert "to_llm_content" not in e, f"activity event carrega resultado de tool (PII): {e[:120]}"


def test_sse_passthrough_masks_tool_event_freetext():
    """0.3b (2026-06-04) defesa em profundidade: o transporte SSE e a ultima
    linha de defesa. Mesmo que um produtor futuro emita args/result/detail com
    PII, o passthrough em agent_chat_sse.py DEVE aplicar mask_pii nesses campos
    livres antes de serializar (hoje agentic_loop manda vazio, mas o contrato
    nao pode depender disso)."""
    sse_src = (
        Path(__file__).resolve().parents[2]
        / "app" / "api" / "v1" / "agent_chat_sse.py"
    ).read_text(encoding="utf-8")
    assert "args=mask_pii(" in sse_src, (
        "agent_chat_sse: tool_started repassa args sem mask_pii (PII pode vazar). "
        "Envolva args com mask_pii no passthrough de tool_started."
    )
    assert "result=mask_pii(" in sse_src, (
        "agent_chat_sse: tool_finished repassa result sem mask_pii. "
        "Envolva result com mask_pii no passthrough de tool_finished."
    )
    assert "detail=mask_pii(" in sse_src, (
        "agent_chat_sse: reasoning_step repassa detail sem mask_pii. "
        "Envolva detail com mask_pii no passthrough de reasoning_step."
    )
