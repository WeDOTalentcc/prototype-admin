"""Fase 2 sensors: reasoning_step emission + AIMessage text extraction.

The astream path itself (LIA_WS_ASTREAM=on) is integration-level and exercised
behind a default-OFF flag; here we pin its two pure/unit pieces:
  - StreamingCallback.emit_reasoning_step → reasoning_step event
  - _extract_ai_text → plain text from str or content-block AIMessages
"""
from __future__ import annotations

from lia_agents_core.streaming_callback import StreamingCallback
from lia_agents_core.langgraph_base import _extract_ai_text


def _capture():
    cb = StreamingCallback(session_id="s")
    sent: list[dict] = []
    cb._schedule_send = lambda data: sent.append(data)  # type: ignore[assignment]
    return cb, sent


def test_emit_reasoning_step_emits_event():
    cb, sent = _capture()
    cb.emit_reasoning_step("Vou buscar os candidatos antes de rankear")
    steps = [e for e in sent if e.get("type") == "reasoning_step"]
    assert steps, "emit_reasoning_step must emit a reasoning_step event"
    assert "buscar" in steps[0]["label"]


def test_emit_reasoning_step_skips_empty():
    cb, sent = _capture()
    cb.emit_reasoning_step("")
    assert not [e for e in sent if e.get("type") == "reasoning_step"]


def test_extract_ai_text_from_plain_string():
    class M:
        content = "  hello world  "

    assert _extract_ai_text(M()) == "hello world"


def test_extract_ai_text_from_content_blocks():
    class M:
        content = [
            {"type": "text", "text": "primeiro"},
            {"type": "tool_use", "name": "x"},
            "segundo",
        ]

    assert _extract_ai_text(M()) == "primeiro segundo"


def test_extract_ai_text_handles_missing_content():
    class M:
        pass

    assert _extract_ai_text(M()) == ""
