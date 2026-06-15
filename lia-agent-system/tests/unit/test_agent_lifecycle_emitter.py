"""TDD — AgentLifecycleEmitter (FIX-P0-03).

17 test cases:
  1.  AgentEvent UUID is unique across instances
  2.  AgentEvent timestamp is populated
  3.  AgentEvent.to_dict() contains all required fields
  4.  AgentEventType.values() returns all 4 types
  5.  Bus.emit() raises ValueError for unknown event type
  6.  Subscriber receives emitted event
  7.  Multiple subscribers receive same event (fan-out)
  8.  Subscriber is removed after generator exits
  9.  Replay: subscriber gets missed events via last_event_id
  10. Replay: unknown last_event_id replays entire buffer
  11. Replay: last_event_id at end replays nothing (empty slice)
  12. Buffer cap: only last _MAX_BUFFER events kept
  13. Session isolation: event only reaches matching session
  14. Bus: 100 concurrent sessions (scalability)
  15. Bus singleton pattern
  16. Bus.remove() closes subscribers
  17. Bus.emit() convenience method returns AgentEvent
"""
from __future__ import annotations

import asyncio
import time
import uuid

import pytest

from app.shared.events.agent_lifecycle_emitter import (
    AgentEvent,
    AgentEventBus,
    AgentEventEmitter,
    AgentEventType,
    _MAX_BUFFER,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_bus():
    AgentEventBus.reset_instance()
    yield
    AgentEventBus.reset_instance()


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_event(session_id: str = "s-1", event_type: str = AgentEventType.AGENT_THINKING) -> AgentEvent:
    return AgentEvent(
        event_type=event_type if isinstance(event_type, str) else event_type.value,
        session_id=session_id,
    )


async def _collect_n(gen, n: int, timeout: float = 2.0) -> list[AgentEvent]:
    collected = []
    async def _inner():
        async for ev in gen:
            collected.append(ev)
            if len(collected) >= n:
                break
    await asyncio.wait_for(_inner(), timeout=timeout)
    return collected


# ─── AgentEvent ──────────────────────────────────────────────────────────────


class TestAgentEvent:
    def test_uuid_unique(self):
        e1 = _make_event()
        e2 = _make_event()
        assert e1.event_id != e2.event_id

    def test_timestamp_populated(self):
        before = time.time()
        ev = _make_event()
        after = time.time()
        assert before <= ev.timestamp <= after

    def test_to_dict_has_all_fields(self):
        ev = AgentEvent(
            event_type="agent_action",
            session_id="s-test",
            message_id="msg-1",
            action_name="navigate",
            status="executing",
            payload={"url": "/jobs"},
        )
        d = ev.to_dict()
        assert d["type"] == "agent_action"
        assert d["event_id"] == ev.event_id
        assert d["session_id"] == "s-test"
        assert "timestamp" in d
        assert d["message_id"] == "msg-1"
        assert d["action_name"] == "navigate"
        assert d["status"] == "executing"
        assert d["payload"] == {"url": "/jobs"}

    def test_event_type_enum_values(self):
        values = AgentEventType.values()
        assert "agent_thinking" in values
        assert "agent_action" in values
        assert "agent_action_result" in values
        assert "agent_context_update" in values
        assert len(values) == 4


# ─── AgentEventBus validation ────────────────────────────────────────────────


class TestBusValidation:
    @pytest.mark.asyncio
    async def test_emit_raises_for_unknown_type(self):
        bus = AgentEventBus.get_instance()
        with pytest.raises(ValueError, match="Unknown agent event type"):
            await bus.emit("s-1", "invalid_type")

    @pytest.mark.asyncio
    async def test_emit_convenience_returns_agent_event(self):
        bus = AgentEventBus.get_instance()

        # Need a subscriber to prevent queue-full issue
        emitter = bus.get_or_create("s-ret")

        async def _drain():
            async for _ in emitter.subscribe():
                break

        task = asyncio.create_task(_drain())
        await asyncio.sleep(0)  # Let subscriber register

        result = await bus.emit("s-ret", AgentEventType.AGENT_THINKING, status="thinking")
        assert isinstance(result, AgentEvent)
        assert result.event_type == "agent_thinking"
        assert result.session_id == "s-ret"
        assert result.event_id  # UUID populated

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# ─── Pub/sub ─────────────────────────────────────────────────────────────────


class TestPubSub:
    @pytest.mark.asyncio
    async def test_subscriber_receives_emitted_event(self):
        emitter = AgentEventEmitter("s-sub1")
        ev = _make_event()

        received = []

        async def _subscriber():
            async for event in emitter.subscribe():
                received.append(event)
                break  # Exit after first

        task = asyncio.create_task(_subscriber())
        await asyncio.sleep(0)  # Let subscriber register

        await emitter.emit(ev)
        await asyncio.wait_for(task, timeout=2.0)

        assert len(received) == 1
        assert received[0].event_id == ev.event_id

    @pytest.mark.asyncio
    async def test_fan_out_to_multiple_subscribers(self):
        emitter = AgentEventEmitter("s-fanout")
        ev = _make_event()

        results: list[list[AgentEvent]] = [[], [], []]
        tasks = []

        for i in range(3):
            idx = i

            async def _sub(i=idx):
                async for event in emitter.subscribe():
                    results[i].append(event)
                    break

            tasks.append(asyncio.create_task(_sub()))

        await asyncio.sleep(0)  # Let all subscribers register
        assert emitter.subscriber_count() == 3

        await emitter.emit(ev)
        await asyncio.gather(*tasks)

        for r in results:
            assert len(r) == 1
            assert r[0].event_id == ev.event_id

    @pytest.mark.asyncio
    async def test_subscriber_removed_after_exit(self):
        emitter = AgentEventEmitter("s-cleanup")

        async def _sub():
            async for _ in emitter.subscribe():
                break

        task = asyncio.create_task(_sub())
        await asyncio.sleep(0)
        assert emitter.subscriber_count() == 1

        await emitter.emit(_make_event())
        await asyncio.wait_for(task, timeout=2.0)

        assert emitter.subscriber_count() == 0


# ─── Replay / reconnection ────────────────────────────────────────────────────


class TestReplay:
    @pytest.mark.asyncio
    async def test_replay_events_after_last_event_id(self):
        emitter = AgentEventEmitter("s-replay")

        # Emit 3 events directly into buffer (no subscriber yet)
        events = [_make_event() for _ in range(3)]
        for ev in events:
            await emitter.emit(ev)

        # Subscribe with last_event_id = events[0].event_id → should get events[1] and [2]
        collected = []
        async def _sub():
            async for ev in emitter.subscribe(last_event_id=events[0].event_id):
                collected.append(ev)
                if len(collected) == 2:
                    break

        await asyncio.wait_for(_sub(), timeout=2.0)
        assert len(collected) == 2
        assert collected[0].event_id == events[1].event_id
        assert collected[1].event_id == events[2].event_id

    @pytest.mark.asyncio
    async def test_unknown_last_event_id_replays_all(self):
        emitter = AgentEventEmitter("s-unknown-leid")

        events = [_make_event() for _ in range(3)]
        for ev in events:
            await emitter.emit(ev)

        collected = []
        async def _sub():
            async for ev in emitter.subscribe(last_event_id="nonexistent-id"):
                collected.append(ev)
                if len(collected) == 3:
                    break

        await asyncio.wait_for(_sub(), timeout=2.0)
        assert len(collected) == 3

    @pytest.mark.asyncio
    async def test_last_event_id_at_end_replays_nothing(self):
        emitter = AgentEventEmitter("s-end-leid")

        events = [_make_event() for _ in range(3)]
        for ev in events:
            await emitter.emit(ev)

        collected = []
        # A subscriber receives a subsequent event (not a replay)
        subsequent_event = _make_event()

        async def _sub():
            async for ev in emitter.subscribe(last_event_id=events[-1].event_id):
                collected.append(ev)
                break  # Should be the subsequent_event, not a replay

        task = asyncio.create_task(_sub())
        await asyncio.sleep(0)  # Let subscriber register (after replays)
        await emitter.emit(subsequent_event)
        await asyncio.wait_for(task, timeout=2.0)

        assert len(collected) == 1
        assert collected[0].event_id == subsequent_event.event_id

    @pytest.mark.asyncio
    async def test_buffer_cap(self):
        emitter = AgentEventEmitter("s-cap")
        events = [_make_event() for _ in range(_MAX_BUFFER + 10)]
        for ev in events:
            await emitter.emit(ev)

        assert emitter.buffer_size() == _MAX_BUFFER
        # Oldest events are evicted; newest are kept
        oldest_kept = events[10]
        assert any(e.event_id == oldest_kept.event_id for e in emitter._buffer)


# ─── Session isolation ────────────────────────────────────────────────────────


class TestSessionIsolation:
    @pytest.mark.asyncio
    async def test_event_only_reaches_own_session(self):
        bus = AgentEventBus.get_instance()
        em_a = bus.get_or_create("sess-a")
        em_b = bus.get_or_create("sess-b")

        received_b = []

        async def _sub_b():
            async for ev in em_b.subscribe():
                received_b.append(ev)
                break

        task_b = asyncio.create_task(_sub_b())
        await asyncio.sleep(0)

        # Emit ONLY to session A
        await bus.emit("sess-a", AgentEventType.AGENT_ACTION, action_name="test")

        # Give session B a moment (it should NOT receive anything)
        await asyncio.sleep(0.1)
        assert len(received_b) == 0

        task_b.cancel()
        try:
            await task_b
        except asyncio.CancelledError:
            pass


# ─── Scalability ─────────────────────────────────────────────────────────────


class TestScalability:
    @pytest.mark.asyncio
    async def test_100_concurrent_sessions(self):
        bus = AgentEventBus.get_instance()

        sessions = [f"scale-sess-{i}" for i in range(100)]
        results: dict[str, list[AgentEvent]] = {s: [] for s in sessions}

        async def _sub_and_receive(session_id: str):
            em = bus.get_or_create(session_id)
            async for ev in em.subscribe():
                results[session_id].append(ev)
                break

        tasks = [asyncio.create_task(_sub_and_receive(s)) for s in sessions]
        await asyncio.sleep(0)  # Let all subscribers register

        # Emit to each session
        for s in sessions:
            await bus.emit(s, AgentEventType.AGENT_THINKING)

        await asyncio.gather(*tasks)

        # Every session must have received exactly 1 event
        for s in sessions:
            assert len(results[s]) == 1, f"Session {s} got {len(results[s])} events"

        assert len(bus.active_sessions()) == 100


# ─── Bus lifecycle ────────────────────────────────────────────────────────────


class TestBusLifecycle:
    def test_singleton(self):
        b1 = AgentEventBus.get_instance()
        b2 = AgentEventBus.get_instance()
        assert b1 is b2

    @pytest.mark.asyncio
    async def test_remove_closes_subscribers(self):
        bus = AgentEventBus.get_instance()
        em = bus.get_or_create("s-remove")

        closed = []

        async def _sub():
            async for _ in em.subscribe():
                pass  # Will exit when None sentinel is sent
            closed.append(True)

        task = asyncio.create_task(_sub())
        await asyncio.sleep(0)
        assert em.subscriber_count() == 1

        bus.remove("s-remove")
        await asyncio.wait_for(task, timeout=2.0)
        assert len(closed) == 1
        assert bus.get("s-remove") is None
