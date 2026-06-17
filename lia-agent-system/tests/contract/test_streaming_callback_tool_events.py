"""Contract sensor: StreamingCallback emits tool-call activity events (Fase 1).

The StreamingCallback is wired into every ReAct agent's ainvoke config
(langgraph_base.py: config["callbacks"]). LangChain fires on_tool_start/end/error
during ainvoke, so implementing these handlers surfaces live tool activity to the
chat UI without switching to astream.

These tests capture payloads synchronously by overriding the instance's
_schedule_send (avoids needing a running event loop).
"""
from __future__ import annotations

from lia_agents_core.streaming_callback import StreamingCallback


def _capture() -> tuple[StreamingCallback, list[dict]]:
    cb = StreamingCallback(session_id="sess-1", company_id="co-1")
    sent: list[dict] = []
    cb._schedule_send = lambda data: sent.append(data)  # type: ignore[assignment]
    return cb, sent


def test_on_tool_start_emits_tool_started() -> None:
    cb, sent = _capture()
    cb.on_tool_start({"name": "search_candidates"}, "query=engenheiro", run_id="r1")
    started = [e for e in sent if e.get("type") == "tool_started"]
    assert started, "on_tool_start must emit a 'tool_started' event"
    assert started[0]["name"] == "search_candidates"


def test_on_tool_end_emits_tool_finished_with_duration() -> None:
    cb, sent = _capture()
    cb.on_tool_start({"name": "rank_cvs"}, "n=10", run_id="r2")
    cb.on_tool_end("ranked 10 cvs", run_id="r2")
    finished = [e for e in sent if e.get("type") == "tool_finished"]
    assert finished, "on_tool_end must emit a 'tool_finished' event"
    assert finished[0]["name"] == "rank_cvs"
    assert finished[0]["status"] == "ok"
    assert "duration_ms" in finished[0]


def test_on_tool_error_emits_finished_error() -> None:
    cb, sent = _capture()
    cb.on_tool_start({"name": "fetch"}, "x", run_id="r3")
    cb.on_tool_error(ValueError("boom"), run_id="r3")
    finished = [e for e in sent if e.get("type") == "tool_finished"]
    assert finished and finished[0]["status"] == "error"


def test_tool_name_falls_back_when_serialized_missing() -> None:
    cb, sent = _capture()
    cb.on_tool_start({}, "x", run_id="r4")
    started = [e for e in sent if e.get("type") == "tool_started"]
    assert started and isinstance(started[0]["name"], str) and started[0]["name"]


def test_serializers_exist_and_typed() -> None:
    from app.shared.chat_event_serializer import (
        serialize_tool_started,
        serialize_tool_finished,
        serialize_reasoning_step,
    )

    assert serialize_tool_started("t")["type"] == "tool_started"
    fin = serialize_tool_finished("t", status="ok", duration_ms=5)
    assert fin["type"] == "tool_finished" and fin["duration_ms"] == 5
    assert serialize_reasoning_step("pensando")["type"] == "reasoning_step"
