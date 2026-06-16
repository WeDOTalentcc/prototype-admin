"""Per-conversation chat request serializer — FIX-P0-02.

Guarantees serial, ordered, fault-isolated processing of chat messages
within a conversation session. Prevents out-of-order execution when a
recruiter sends multiple messages quickly.

Architecture:
  - One ChatConversationQueue per session_id (via ChatQueueManager singleton)
  - Each message assigned UUID on enqueue (never timestamp-based)
  - FIFO: asyncio.Queue — strict arrival order
  - Serial: single worker coroutine per session (no concurrent processing)
  - Halt-on-error: queue pauses on persistent failure until cleared
  - Timeout: asyncio.wait_for wraps agent runner call
  - Retry: exponential backoff for transient errors, max_retries configurable
  - Trace: every step logged with [msg_id] prefix for correlation

Usage:
    manager = ChatQueueManager.get_instance()
    queue = manager.get_or_create("session-123", runner=my_agent_runner)
    msg_id = await queue.enqueue(ChatMessage(content="Hello", conversation_id="c-1"))
    trace = await queue.await_result(msg_id, timeout=60.0)
    if trace.status == MessageStatus.SUCCESS:
        result = trace.result
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

# ─── Status enum ─────────────────────────────────────────────────────────────


class MessageStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    RETRYING = "retrying"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


# ─── Data classes ────────────────────────────────────────────────────────────


@dataclass
class ChatMessage:
    content: str
    conversation_id: str = ""
    domain: str = "recruiter_assistant"
    context: dict[str, Any] = field(default_factory=dict)
    # UUID assigned on enqueue if not pre-set
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enqueued_at: float = field(default_factory=time.time)


@dataclass
class ProcessingTrace:
    msg_id: str
    status: MessageStatus
    enqueued_at: float
    started_at: float | None = None
    completed_at: float | None = None
    retry_count: int = 0
    result: Any | None = None
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at) * 1000
        return None


# Callable that receives a ChatMessage and returns a result (coroutine)
AgentRunner = Callable[[ChatMessage], Awaitable[Any]]

# ─── Transient error heuristic ───────────────────────────────────────────────

_TRANSIENT_KEYWORDS: frozenset[str] = frozenset(
    {
        "timeout",
        "connection",
        "service unavailable",
        "overloaded",
        "rate limit",
        "503",
        "502",
        "429",
        "temporary",
        "retry",
        "backoff",
    }
)


def _is_transient(exc: Exception) -> bool:
    """Return True if the exception looks like a transient infrastructure error."""
    msg = str(exc).lower()
    return any(kw in msg for kw in _TRANSIENT_KEYWORDS)


# ─── Per-conversation queue ───────────────────────────────────────────────────


class ChatConversationQueue:
    """Serial FIFO queue for a single conversation session.

    Invariants:
    - Messages are processed in FIFO order (one at a time).
    - No concurrent message processing within a session.
    - Queue halts after a persistent failure; call clear_halt() to resume.
    - Every transition is logged with [msg_id] for correlation.
    """

    DEFAULT_TIMEOUT_S: float = 120.0
    DEFAULT_MAX_RETRIES: int = 2
    DEFAULT_BACKOFF_BASE_S: float = 2.0

    def __init__(
        self,
        session_id: str,
        runner: AgentRunner,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base_s: float = DEFAULT_BACKOFF_BASE_S,
    ) -> None:
        self.session_id = session_id
        self._runner = runner
        self._timeout_s = timeout_s
        self._max_retries = max_retries
        self._backoff_base_s = backoff_base_s

        self._queue: asyncio.Queue[ChatMessage] = asyncio.Queue()
        self._trace: dict[str, ProcessingTrace] = {}
        self._result_events: dict[str, asyncio.Event] = {}
        self._halted: bool = False
        self._worker_task: asyncio.Task[None] | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    async def enqueue(self, message: ChatMessage) -> str:
        """Place message in queue and return its UUID.

        Lazily starts the worker on first call — safe to call from async contexts
        without pre-calling start().
        """
        if not message.id:
            message.id = str(uuid.uuid4())
        msg_id = message.id

        self._trace[msg_id] = ProcessingTrace(
            msg_id=msg_id,
            status=MessageStatus.QUEUED,
            enqueued_at=message.enqueued_at,
        )
        self._result_events[msg_id] = asyncio.Event()

        # Lazy start: worker needs a running event loop, guaranteed here.
        if self._worker_task is None or self._worker_task.done():
            self.start()

        await self._queue.put(message)
        logger.info(
            "[%s] queued — session=%s depth=%d",
            msg_id,
            self.session_id,
            self._queue.qsize(),
        )
        return msg_id

    async def await_result(
        self, msg_id: str, *, timeout: float = 120.0
    ) -> ProcessingTrace:
        """Block until the message is processed (or timeout expires)."""
        event = self._result_events.get(msg_id)
        if event is None:
            raise KeyError(f"Unknown message id: {msg_id!r}")
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except (asyncio.TimeoutError, TimeoutError):
            trace = self._trace[msg_id]
            trace.status = MessageStatus.TIMEOUT
            trace.error = f"await_result timed out after {timeout}s"
        return self._trace[msg_id]

    def get_trace(self, msg_id: str) -> ProcessingTrace | None:
        return self._trace.get(msg_id)

    def clear_halt(self) -> None:
        """Resume processing after a human-resolved failure."""
        self._halted = False
        logger.info("[queue] halt cleared — session=%s", self.session_id)

    def is_halted(self) -> bool:
        return self._halted

    def queue_depth(self) -> int:
        return self._queue.qsize()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> "asyncio.Task[None]":
        """Start the background worker (idempotent)."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(
                self._worker_loop(),
                name=f"chat-queue-{self.session_id[:8]}",
            )
        return self._worker_task

    def stop(self) -> None:
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()

    # ── Worker internals ──────────────────────────────────────────────────────

    async def _worker_loop(self) -> None:
        logger.info("[queue] worker started — session=%s", self.session_id)
        while True:
            # Pause while halted
            if self._halted:
                await asyncio.sleep(0.25)
                continue

            # Wait for next message (poll so halt can interrupt)
            try:
                message = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except (asyncio.TimeoutError, TimeoutError):
                continue
            except asyncio.CancelledError:
                break

            await self._process_message(message)
            self._queue.task_done()

        logger.info("[queue] worker stopped — session=%s", self.session_id)

    async def _process_message(self, message: ChatMessage) -> None:
        msg_id = message.id
        trace = self._trace[msg_id]
        trace.status = MessageStatus.PROCESSING
        trace.started_at = time.time()
        logger.info("[%s] processing started", msg_id)

        last_exc: Exception | None = None

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                backoff = self._backoff_base_s * (2 ** (attempt - 1))
                trace.status = MessageStatus.RETRYING
                trace.retry_count = attempt
                logger.info(
                    "[%s] retry %d/%d — backoff=%.1fs",
                    msg_id,
                    attempt,
                    self._max_retries,
                    backoff,
                )
                await asyncio.sleep(backoff)

            try:
                result = await asyncio.wait_for(
                    self._runner(message), timeout=self._timeout_s
                )
                trace.result = result
                trace.status = MessageStatus.SUCCESS
                trace.completed_at = time.time()
                logger.info("[%s] success — %.0fms", msg_id, trace.duration_ms or 0)
                self._result_events[msg_id].set()
                return

            except (asyncio.TimeoutError, TimeoutError) as exc:
                last_exc = TimeoutError(
                    f"Agent did not respond within {self._timeout_s}s"
                )
                logger.warning("[%s] timed out after %.1fs", msg_id, self._timeout_s)
                break  # Timeouts are never retried

            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if _is_transient(exc) and attempt < self._max_retries:
                    logger.warning(
                        "[%s] transient error (attempt %d): %s", msg_id, attempt + 1, exc
                    )
                else:
                    logger.error(
                        "[%s] persistent error: %s", msg_id, exc, exc_info=True
                    )
                    break

        # ── Failure path ──────────────────────────────────────────────────────
        trace.error = str(last_exc)
        trace.status = (
            MessageStatus.TIMEOUT
            if isinstance(last_exc, TimeoutError)
            else MessageStatus.ERROR
        )
        trace.completed_at = time.time()
        logger.error(
            "[%s] failed — halting queue — session=%s error=%s",
            msg_id,
            self.session_id,
            trace.error,
        )
        self._halted = True  # FIFO guarantee: halt until resolved
        self._result_events[msg_id].set()


# ─── Session manager (singleton) ─────────────────────────────────────────────


class ChatQueueManager:
    """Registry of per-session ChatConversationQueue instances.

    Usage:
        manager = ChatQueueManager.get_instance()
        queue = manager.get_or_create("session-abc", runner=my_runner)
    """

    _instance: "ChatQueueManager | None" = None
    _MAX_SESSIONS: int = 1000  # Prevent unbounded memory growth

    def __init__(self) -> None:
        self._queues: dict[str, ChatConversationQueue] = {}
        self._runners: dict[str, AgentRunner] = {}

    @classmethod
    def get_instance(cls) -> "ChatQueueManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """For testing only — resets singleton state."""
        if cls._instance:
            for q in cls._instance._queues.values():
                q.stop()
        cls._instance = None

    def register_runner(self, session_id: str, runner: AgentRunner) -> None:
        """Pre-register a runner so get_or_create doesn't need it inline."""
        self._runners[session_id] = runner

    def get_or_create(
        self,
        session_id: str,
        runner: AgentRunner | None = None,
        *,
        timeout_s: float = ChatConversationQueue.DEFAULT_TIMEOUT_S,
        max_retries: int = ChatConversationQueue.DEFAULT_MAX_RETRIES,
    ) -> ChatConversationQueue:
        """Return existing queue for session_id or create a new one.

        The worker is NOT started here — it starts lazily on first enqueue().
        This keeps get_or_create safe to call from synchronous contexts.
        """
        if session_id not in self._queues:
            if len(self._queues) >= self._MAX_SESSIONS:
                self._evict_oldest()
            _runner = runner or self._runners.get(session_id)
            if _runner is None:
                raise ValueError(
                    f"No runner registered for session {session_id!r}. "
                    "Pass runner= or call register_runner() first."
                )
            q = ChatConversationQueue(
                session_id,
                _runner,
                timeout_s=timeout_s,
                max_retries=max_retries,
            )
            # Worker starts lazily on first enqueue() — do NOT call q.start() here.
            self._queues[session_id] = q
        return self._queues[session_id]

    def get(self, session_id: str) -> ChatConversationQueue | None:
        return self._queues.get(session_id)

    def remove(self, session_id: str) -> None:
        q = self._queues.pop(session_id, None)
        if q:
            q.stop()

    def active_sessions(self) -> list[str]:
        return list(self._queues.keys())

    def _evict_oldest(self) -> None:
        """Evict the lexicographically first session (FIFO approximation)."""
        if self._queues:
            oldest = min(self._queues.keys())
            self.remove(oldest)
