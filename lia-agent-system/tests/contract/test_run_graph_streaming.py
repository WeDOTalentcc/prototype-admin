"""Fase 2 integration sensor: LangGraphBase._run_graph_streaming.

Drives the astream path with a fake compiled graph (no LLM) to pin two
invariants before enabling LIA_WS_ASTREAM in production:
  1. the returned final state equals the LAST values chunk (ainvoke-equivalent)
  2. a reasoning_step is emitted ONLY for intermediate AIMessages that carry
     tool_calls — never for the final answer (no tool_calls), and never twice
     for the same message id.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from lia_agents_core.streaming_callback import StreamingCallback
from lia_agents_core.langgraph_base import LangGraphBase


class _FakeAI:
    def __init__(self, content, tool_calls=None, id=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.type = "ai"
        self.id = id


class _FakeCompiled:
    """astream yields progressive `values` snapshots like LangGraph."""

    def __init__(self, chunks):
        self._chunks = chunks

    def astream(self, initial_state, config=None, stream_mode=None):
        chunks = self._chunks

        async def _gen():
            for c in chunks:
                yield c

        return _gen()


def _capture_cb():
    cb = StreamingCallback(session_id="s")
    sent: list[dict] = []
    cb._schedule_send = lambda data: sent.append(data)  # type: ignore[assignment]
    return cb, sent


def test_returns_final_state_and_emits_reasoning_for_tool_calls_only():
    m1 = _FakeAI("Vou buscar candidatos", tool_calls=[{"name": "search"}], id="m1")
    final_answer = _FakeAI("Pronto, encontrei 5", id="m2")
    chunks = [
        {"messages": [m1]},
        {"messages": [m1, final_answer]},
    ]
    cb, sent = _capture_cb()

    final = asyncio.run(
        LangGraphBase._run_graph_streaming(
            SimpleNamespace(), _FakeCompiled(chunks), {}, {}, cb
        )
    )

    # 1. final state = last chunk
    assert final == {"messages": [m1, final_answer]}

    # 2. reasoning only for the tool_calls message, exactly once
    reasoning = [e for e in sent if e.get("type") == "reasoning_step"]
    assert len(reasoning) == 1
    assert "buscar" in reasoning[0]["label"]


def test_falls_back_when_astream_yields_nothing():
    # final_state stays None -> method must not return None; it would ainvoke,
    # but our fake has no ainvoke, so we assert it raises (not silently returns
    # None). Guards against returning a bad state.
    cb, _ = _capture_cb()

    class _Empty:
        def astream(self, *a, **k):
            async def _gen():
                if False:
                    yield {}
            return _gen()

    try:
        asyncio.run(
            LangGraphBase._run_graph_streaming(SimpleNamespace(), _Empty(), {}, {}, cb)
        )
        raised = False
    except AttributeError:
        raised = True  # tried to call .ainvoke on the fake (correct fallback path)
    assert raised
