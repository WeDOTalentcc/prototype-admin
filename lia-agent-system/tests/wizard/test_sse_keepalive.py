"""Sensor (harness) — keepalive SSE em operações longas do wizard.

Root cause do 502: geração WSI (~104s) deixava o stream SSE mudo → gateway
derrubava a conexão. _drain_queue_with_keepalive garante heartbeat em silêncio
prolongado. Sensor computacional: pina que o keepalive é emitido.
"""
from __future__ import annotations
import asyncio
import pytest

from app.api.v1.agent_chat_sse import _drain_queue_with_keepalive
from app.shared.chat_event_serializer import format_sse_keepalive, serialize_token


@pytest.mark.asyncio
async def test_keepalive_emitted_during_long_silence():
    """Sem eventos na fila, o helper emite keepalive (impede 502 do gateway)."""
    q: asyncio.Queue = asyncio.Queue()
    done = {"v": False}

    async def _flip():
        await asyncio.sleep(0.35)
        done["v"] = True

    t = asyncio.create_task(_flip())
    events = [
        ev async for ev in _drain_queue_with_keepalive(
            q, lambda: done["v"], lambda: "id", poll_s=0.05, keepalive_after_s=0.1
        )
    ]
    await t
    assert format_sse_keepalive() in events  # houve heartbeat durante o silêncio


@pytest.mark.asyncio
async def test_queued_token_passes_through_without_premature_keepalive():
    q: asyncio.Queue = asyncio.Queue()
    await q.put(serialize_token("oi"))
    done = {"v": False}

    async def _flip():
        await asyncio.sleep(0.2)
        done["v"] = True

    t = asyncio.create_task(_flip())
    events = [
        ev async for ev in _drain_queue_with_keepalive(
            q, lambda: done["v"], lambda: "i", poll_s=0.05, keepalive_after_s=99.0
        )
    ]
    await t
    assert len(events) >= 1  # o token da fila foi emitido
    assert format_sse_keepalive() not in events  # keepalive_after alto → sem heartbeat
