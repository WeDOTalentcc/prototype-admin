"""Sensor — reasoning/atividade progressiva chega ao transporte SSE (não só WS).

Causa raiz (auditoria 2026-06-06): o StreamingCallback dos domain agents
(LangGraphReActBase) emite tool_started/tool_finished/reasoning_step só pro
ws_manager (_send). O chat lateral ao vivo roda em SSE (NEXT_PUBLIC_CHAT_TRANSPORT=sse)
e não escutava nada disso → "Pensando" estático.

Fix no produtor (1 ponto, transport-agnostic): _send repassa frames de atividade
pro contextvar _sse_frame_sink quando o handler SSE o registra.
"""
from __future__ import annotations

import asyncio

from lia_agents_core.streaming_callback import (
    StreamingCallback,
    set_sse_frame_sink,
    reset_sse_frame_sink,
)


def test_send_forwards_activity_frames_to_sse_sink() -> None:
    captured: list[dict] = []

    async def _sink(frame: dict) -> None:
        captured.append(frame)

    async def _run() -> None:
        # o sink e registrado ANTES da construcao (espelha o fluxo real:
        # agent_chat_sse registra o sink antes da task -> _process_langgraph
        # constroi o StreamingCallback, que captura no __init__).
        tok = set_sse_frame_sink(_sink)
        cb = StreamingCallback(session_id="sess-1", company_id="co-1")
        try:
            await cb._send({"type": "tool_started", "name": "rank_candidates"})
            await cb._send({"type": "tool_finished", "name": "rank_candidates", "status": "ok"})
            await cb._send({"type": "reasoning_step", "label": "analisando vaga"})
            # tokens NÃO são repassados pelo sink (evita double-stream; o SSE
            # serializa a mensagem final pelo seu próprio caminho).
            await cb._send({"type": "token", "content": "x"})
        finally:
            reset_sse_frame_sink(tok)

    asyncio.run(_run())
    types = [f.get("type") for f in captured]
    assert "tool_started" in types
    assert "tool_finished" in types
    assert "reasoning_step" in types
    assert "token" not in types


def test_send_noop_when_no_sink_registered() -> None:
    # Sem sink (ex: transporte WS): _send não deve levantar.
    cb = StreamingCallback(session_id="sess-2")
    asyncio.run(cb._send({"type": "tool_started", "name": "t"}))


def test_callback_to_sink_end_to_end_via_on_tool_start() -> None:
    # on_tool_start (LangChain) -> _schedule_send -> _send -> sink.
    # Aqui chamamos _send direto com o frame serializado p/ determinismo.
    from app.shared.chat_event_serializer import serialize_tool_started

    captured: list[dict] = []

    async def _sink(frame: dict) -> None:
        captured.append(frame)

    async def _run() -> None:
        tok = set_sse_frame_sink(_sink)
        cb = StreamingCallback(session_id="sess-3")
        try:
            await cb._send(serialize_tool_started(name="view_candidate", args="id=1", tool_id="r1"))
        finally:
            reset_sse_frame_sink(tok)

    asyncio.run(_run())
    assert captured and captured[0]["type"] == "tool_started"
    assert captured[0]["name"] == "view_candidate"
