"""Agent lifecycle event emitter — FIX-P0-03.

Provides a pub/sub channel per session_id. The backend emits agent lifecycle
events (thinking, action, result, context_update); SSE clients subscribe and
receive them in real-time.

Key design decisions:
- One AgentEventEmitter per session_id (isolated; no cross-session leakage)
- Multiple subscribers per session (fan-out via asyncio.Queue per subscriber)
- UUID event_id per event (stable across reconnects — clients can deduplicate)
- AgentEventBus singleton caps sessions at 1000 (memory guard)
- Subscribers use asyncio.Queue so the emit() caller is never blocked by a
  slow HTTP client (fire-and-forget with bounded buffer)
- Reconnection: client sends Last-Event-ID header; emitter replays the last
  N events (buffer) so no events are dropped on brief disconnects

Usage (backend tool function):
    bus = AgentEventBus.get_instance()
    await bus.emit(
        session_id="s-abc",
        event_type=AgentEventType.AGENT_ACTION,
        action_name="navigate_to_page",
        status="executing",
        payload={"url": "/jobs/123"},
        message_id="msg-uuid",
    )

Usage (SSE endpoint):
    async for event in bus.subscribe(session_id):
        yield format_sse_event(event.to_dict(), event_id=event.event_id)
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator

logger = logging.getLogger(__name__)

# ─── Event types ─────────────────────────────────────────────────────────────


class AgentEventType(str, Enum):
    AGENT_THINKING = "agent_thinking"        # Agent started processing
    AGENT_ACTION = "agent_action"            # About to perform action X
    AGENT_ACTION_RESULT = "agent_action_result"  # Action complete (success|error)
    AGENT_CONTEXT_UPDATE = "agent_context_update"  # Page/UI state changed

    @classmethod
    def values(cls) -> list[str]:
        return [e.value for e in cls]


# ─── Event envelope ───────────────────────────────────────────────────────────


@dataclass
class AgentEvent:
    event_type: str                          # AgentEventType value
    session_id: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    message_id: str = ""                     # Links to the chat message
    action_name: str = ""                    # Which action/tool is running
    status: str = "thinking"                 # thinking | executing | complete | error
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.event_type,
            "event_id": self.event_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "action_name": self.action_name,
            "status": self.status,
            "payload": self.payload,
        }


# ─── Per-session emitter ──────────────────────────────────────────────────────

_MAX_BUFFER = 50        # How many events to keep for reconnection replay
_SUBSCRIBER_QUEUE_MAX = 200  # Per-subscriber queue depth


class AgentEventEmitter:
    """Pub/sub channel for one session.

    Emit events → fan-out to all active subscribers via asyncio.Queue.
    A bounded circular buffer stores the last _MAX_BUFFER events so that
    reconnecting clients can replay missed events via Last-Event-ID.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._subscribers: list[asyncio.Queue[AgentEvent | None]] = []
        self._buffer: list[AgentEvent] = []  # circular replay buffer

    async def emit(self, event: AgentEvent) -> None:
        """Publish event to all subscribers (non-blocking)."""
        # Update circular buffer
        self._buffer.append(event)
        if len(self._buffer) > _MAX_BUFFER:
            self._buffer.pop(0)

        # Fan-out
        dead: list[asyncio.Queue[AgentEvent | None]] = []
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(
                    "[agent-events] subscriber queue full — dropping event session=%s",
                    self.session_id,
                )
                dead.append(q)

        for q in dead:
            self._subscribers.remove(q)

        logger.debug(
            "[agent-events] emitted %s session=%s subscribers=%d",
            event.event_type,
            self.session_id,
            len(self._subscribers),
        )

    async def subscribe(
        self, last_event_id: str | None = None
    ) -> AsyncGenerator[AgentEvent, None]:
        """Async generator yielding events for this session.

        If last_event_id is provided, replays buffered events the client missed
        before switching to live events. Yields None sentinel to detect
        generator cleanup (subscriber removal).
        """
        q: asyncio.Queue[AgentEvent | None] = asyncio.Queue(
            maxsize=_SUBSCRIBER_QUEUE_MAX
        )
        self._subscribers.append(q)
        logger.info(
            "[agent-events] subscriber added session=%s total=%d",
            self.session_id,
            len(self._subscribers),
        )

        try:
            # Replay missed events
            if last_event_id:
                replay = self._events_after(last_event_id)
                for ev in replay:
                    yield ev

            # Live events
            while True:
                event = await q.get()
                if event is None:
                    break  # Sentinel: emitter shut down this subscriber
                yield event
        finally:
            if q in self._subscribers:
                self._subscribers.remove(q)
            logger.info(
                "[agent-events] subscriber removed session=%s remaining=%d",
                self.session_id,
                len(self._subscribers),
            )

    def close_all(self) -> None:
        """Signal all subscribers to stop (sends None sentinel)."""
        for q in self._subscribers:
            try:
                q.put_nowait(None)
            except asyncio.QueueFull:
                pass
        self._subscribers.clear()

    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def buffer_size(self) -> int:
        return len(self._buffer)

    def _events_after(self, last_event_id: str) -> list[AgentEvent]:
        """Return buffered events that occurred after last_event_id."""
        try:
            idx = next(
                i for i, ev in enumerate(self._buffer)
                if ev.event_id == last_event_id
            )
            return self._buffer[idx + 1:]
        except StopIteration:
            # last_event_id not in buffer → client missed too much, replay all
            return list(self._buffer)


# ─── Session bus (singleton) ──────────────────────────────────────────────────


class AgentEventBus:
    """Global registry of per-session AgentEventEmitter instances.

    Thread-safe at the event loop level (single-threaded asyncio).
    Caps sessions at _MAX_SESSIONS to bound memory usage.
    """

    _instance: "AgentEventBus | None" = None
    _MAX_SESSIONS: int = 1000

    def __init__(self) -> None:
        self._emitters: dict[str, AgentEventEmitter] = {}

    @classmethod
    def get_instance(cls) -> "AgentEventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """For testing only."""
        if cls._instance:
            for em in cls._instance._emitters.values():
                em.close_all()
        cls._instance = None

    def get_or_create(self, session_id: str) -> AgentEventEmitter:
        if session_id not in self._emitters:
            if len(self._emitters) >= self._MAX_SESSIONS:
                self._evict_oldest()
            self._emitters[session_id] = AgentEventEmitter(session_id)
        return self._emitters[session_id]

    def get(self, session_id: str) -> AgentEventEmitter | None:
        return self._emitters.get(session_id)

    def remove(self, session_id: str) -> None:
        em = self._emitters.pop(session_id, None)
        if em:
            em.close_all()

    def active_sessions(self) -> list[str]:
        return list(self._emitters.keys())

    async def emit(
        self,
        session_id: str,
        event_type: AgentEventType | str,
        *,
        action_name: str = "",
        status: str = "thinking",
        payload: dict[str, Any] | None = None,
        message_id: str = "",
    ) -> AgentEvent:
        """Convenience method: build and emit an event in one call."""
        ev_type = (
            event_type.value
            if isinstance(event_type, AgentEventType)
            else event_type
        )
        if ev_type not in AgentEventType.values():
            raise ValueError(
                f"Unknown agent event type {ev_type!r}. "
                f"Valid: {AgentEventType.values()}"
            )

        event = AgentEvent(
            event_type=ev_type,
            session_id=session_id,
            action_name=action_name,
            status=status,
            payload=payload or {},
            message_id=message_id,
        )
        emitter = self.get_or_create(session_id)
        await emitter.emit(event)
        return event

    async def subscribe(
        self, session_id: str, last_event_id: str | None = None
    ) -> AsyncGenerator[AgentEvent, None]:
        """Subscribe to events for session_id (creates emitter if needed)."""
        emitter = self.get_or_create(session_id)
        async for event in emitter.subscribe(last_event_id=last_event_id):
            yield event

    def _evict_oldest(self) -> None:
        if self._emitters:
            oldest = min(self._emitters.keys())
            self.remove(oldest)
