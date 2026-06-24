"""Contract sensor: AgenticLoop emits live activity via the LLM streaming ContextVar.

The orchestrator (REST/SSE path) runs tools through AgenticLoop, not the WS
StreamingCallback. _emit_activity bridges tool events to the same _llm_streaming_callback
ContextVar the LLM service uses for token streaming, so the chat timeline can show
tool_started/finished on the orchestrator path. No-op when no callback is set (REST).
"""
import asyncio

from app.orchestrator.execution.agentic_loop import _emit_activity
from app.domains.ai.services.llm import _llm_streaming_callback


def test_emit_activity_pushes_through_contextvar():
    sent: list[dict] = []

    async def cb(e):
        sent.append(e)

    async def run():
        token = _llm_streaming_callback.set(cb)
        try:
            await _emit_activity({"type": "tool_started", "name": "search_candidates"})
            await _emit_activity(
                {"type": "tool_finished", "name": "search_candidates", "status": "ok", "duration_ms": 12}
            )
        finally:
            _llm_streaming_callback.reset(token)

    asyncio.run(run())
    assert sent == [
        {"type": "tool_started", "name": "search_candidates"},
        {"type": "tool_finished", "name": "search_candidates", "status": "ok", "duration_ms": 12},
    ]


def test_emit_activity_is_noop_without_callback():
    async def run():
        # Default ContextVar is None (REST path) — must not raise, must not send.
        await _emit_activity({"type": "tool_started", "name": "x"})

    asyncio.run(run())  # no exception = pass


def test_emit_activity_swallows_callback_errors():
    async def bad_cb(e):
        raise RuntimeError("transport down")

    async def run():
        token = _llm_streaming_callback.set(bad_cb)
        try:
            await _emit_activity({"type": "tool_started", "name": "x"})  # must not propagate
        finally:
            _llm_streaming_callback.reset(token)

    asyncio.run(run())  # no exception = pass
