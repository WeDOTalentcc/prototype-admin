"""TDD — ChatConversationQueue (FIX-P0-02).

18 test cases covering:
  1.  UUID assigned on enqueue (never empty)
  2.  Pre-set UUID preserved
  3.  FIFO ordering (messages processed in arrival order)
  4.  Serial execution (no concurrent processing)
  5.  Successful trace after processing
  6.  Queue halts on persistent error
  7.  Halt: subsequent messages not processed while halted
  8.  clear_halt resumes processing
  9.  Timeout triggers TIMEOUT status
  10. Transient retry: succeeds on 3rd attempt
  11. Transient retry exhausted → ERROR + halt
  12. await_result returns SUCCESS trace
  13. await_result times out → TIMEOUT in returned trace
  14. await_result raises KeyError for unknown msg_id
  15. queue_depth decreases after processing
  16. ChatQueueManager singleton pattern
  17. ChatQueueManager: missing runner raises ValueError
  18. _is_transient heuristic (positive + negative cases)
"""
from __future__ import annotations

import asyncio
import pytest

from app.shared.async_processing.chat_queue_serializer import (
    ChatConversationQueue,
    ChatMessage,
    ChatQueueManager,
    MessageStatus,
    ProcessingTrace,
    _is_transient,
)

# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _run_and_drain(queue: ChatConversationQueue, msg: ChatMessage) -> ProcessingTrace:
    """Enqueue, then wait for processing with a generous timeout."""
    msg_id = await queue.enqueue(msg)
    return await queue.await_result(msg_id, timeout=5.0)


def _make_success_runner(result: object = "ok") -> object:
    async def _runner(msg: ChatMessage) -> object:
        return result

    return _runner


def _make_error_runner(exc: Exception) -> object:
    async def _runner(msg: ChatMessage) -> object:
        raise exc

    return _runner


def _make_slow_runner(delay: float) -> object:
    async def _runner(msg: ChatMessage) -> object:
        await asyncio.sleep(delay)
        return "slow_ok"

    return _runner


def _make_ordered_runner(order_log: list[str]) -> object:
    """Records message IDs in the order they are processed."""

    async def _runner(msg: ChatMessage) -> object:
        order_log.append(msg.id)
        await asyncio.sleep(0)  # yield to event loop
        return "ok"

    return _runner


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_manager():
    """Ensure a clean singleton between tests."""
    ChatQueueManager.reset_instance()
    yield
    ChatQueueManager.reset_instance()


# ─── Tests ───────────────────────────────────────────────────────────────────


class TestChatMessage:
    def test_uuid_auto_assigned(self):
        msg = ChatMessage(content="hello")
        assert msg.id
        assert len(msg.id) == 36  # standard UUID4 length

    def test_preset_uuid_preserved(self):
        msg = ChatMessage(content="hello", id="my-fixed-id")
        assert msg.id == "my-fixed-id"

    def test_fields_default(self):
        msg = ChatMessage(content="test")
        assert msg.domain == "recruiter_assistant"
        assert msg.conversation_id == ""
        assert msg.context == {}


class TestSuccessPath:
    @pytest.mark.asyncio
    async def test_success_status(self):
        q = ChatConversationQueue("s1", _make_success_runner("done"), max_retries=0)
        q.start()
        trace = await _run_and_drain(q, ChatMessage(content="hi"))
        assert trace.status == MessageStatus.SUCCESS
        assert trace.result == "done"
        assert trace.error is None
        q.stop()

    @pytest.mark.asyncio
    async def test_uuid_in_trace_matches_enqueued(self):
        q = ChatConversationQueue("s2", _make_success_runner(), max_retries=0)
        q.start()
        msg = ChatMessage(content="hi", id="fixed-uuid")
        msg_id = await q.enqueue(msg)
        trace = await q.await_result(msg_id, timeout=5.0)
        assert trace.msg_id == "fixed-uuid"
        q.stop()

    @pytest.mark.asyncio
    async def test_duration_ms_populated(self):
        q = ChatConversationQueue("s3", _make_success_runner(), max_retries=0)
        q.start()
        trace = await _run_and_drain(q, ChatMessage(content="x"))
        assert trace.duration_ms is not None
        assert trace.duration_ms >= 0
        q.stop()

    @pytest.mark.asyncio
    async def test_queue_depth_zero_after_drain(self):
        q = ChatConversationQueue("s4", _make_success_runner(), max_retries=0)
        q.start()
        await _run_and_drain(q, ChatMessage(content="x"))
        await asyncio.sleep(0.1)
        assert q.queue_depth() == 0
        q.stop()


class TestFIFOOrdering:
    @pytest.mark.asyncio
    async def test_messages_processed_in_arrival_order(self):
        order_log: list[str] = []
        q = ChatConversationQueue("s-fifo", _make_ordered_runner(order_log), max_retries=0)
        q.start()

        ids = []
        for i in range(5):
            msg = ChatMessage(content=f"msg-{i}", id=f"id-{i}")
            msg_id = await q.enqueue(msg)
            ids.append(msg_id)

        # Wait for all messages
        for msg_id in ids:
            await q.await_result(msg_id, timeout=5.0)

        assert order_log == ["id-0", "id-1", "id-2", "id-3", "id-4"]
        q.stop()

    @pytest.mark.asyncio
    async def test_serial_no_concurrent_processing(self):
        """Processing must be serial: each message finishes before next starts."""
        concurrent_count = 0
        max_concurrent = 0

        async def counting_runner(msg: ChatMessage):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1
            return "ok"

        q = ChatConversationQueue("s-serial", counting_runner, max_retries=0)
        q.start()

        ids = [await q.enqueue(ChatMessage(content=f"m{i}")) for i in range(3)]
        for mid in ids:
            await q.await_result(mid, timeout=5.0)

        assert max_concurrent == 1, f"Expected max 1 concurrent, got {max_concurrent}"
        q.stop()


class TestHaltOnFailure:
    @pytest.mark.asyncio
    async def test_persistent_error_halts_queue(self):
        q = ChatConversationQueue(
            "s-halt", _make_error_runner(RuntimeError("boom")), max_retries=0
        )
        q.start()
        trace = await _run_and_drain(q, ChatMessage(content="fail"))
        assert trace.status == MessageStatus.ERROR
        assert "boom" in trace.error
        assert q.is_halted()
        q.stop()

    @pytest.mark.asyncio
    async def test_halted_queue_does_not_process_next_message(self):
        q = ChatConversationQueue(
            "s-halt2", _make_error_runner(RuntimeError("oops")), max_retries=0
        )
        q.start()
        # First message fails → halt
        m1 = await q.enqueue(ChatMessage(content="fail"))
        await q.await_result(m1, timeout=5.0)
        assert q.is_halted()

        # Second message stays QUEUED (not processed while halted)
        m2 = await q.enqueue(ChatMessage(content="second"))
        await asyncio.sleep(0.3)
        trace2 = q.get_trace(m2)
        assert trace2 is not None
        assert trace2.status == MessageStatus.QUEUED
        q.stop()

    @pytest.mark.asyncio
    async def test_clear_halt_resumes_processing(self):
        call_count = 0

        async def flaky_runner(msg: ChatMessage):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("first call fails")
            return "recovered"

        q = ChatConversationQueue("s-resume", flaky_runner, max_retries=0)
        q.start()

        m1 = await q.enqueue(ChatMessage(content="first"))
        await q.await_result(m1, timeout=5.0)
        assert q.is_halted()

        q.clear_halt()
        assert not q.is_halted()

        m2 = await q.enqueue(ChatMessage(content="second"))
        trace2 = await q.await_result(m2, timeout=5.0)
        assert trace2.status == MessageStatus.SUCCESS
        assert trace2.result == "recovered"
        q.stop()


class TestTimeoutHandling:
    @pytest.mark.asyncio
    async def test_slow_runner_triggers_timeout(self):
        q = ChatConversationQueue(
            "s-timeout",
            _make_slow_runner(10.0),  # Slow runner
            timeout_s=0.1,            # Very short timeout
            max_retries=0,
        )
        q.start()
        trace = await _run_and_drain(q, ChatMessage(content="slow"))
        assert trace.status == MessageStatus.TIMEOUT
        assert trace.error is not None
        assert q.is_halted()
        q.stop()

    @pytest.mark.asyncio
    async def test_await_result_caller_timeout(self):
        q = ChatConversationQueue(
            "s-await-timeout",
            _make_slow_runner(60.0),  # Will never finish in test
            max_retries=0,
        )
        q.start()
        msg_id = await q.enqueue(ChatMessage(content="slow"))
        # await_result times out from caller's perspective
        trace = await q.await_result(msg_id, timeout=0.1)
        assert trace.status == MessageStatus.TIMEOUT
        q.stop()

    @pytest.mark.asyncio
    async def test_await_result_unknown_id_raises(self):
        q = ChatConversationQueue("s-unknown", _make_success_runner(), max_retries=0)
        q.start()
        with pytest.raises(KeyError, match="unknown-id"):
            await q.await_result("unknown-id")
        q.stop()


class TestRetryLogic:
    @pytest.mark.asyncio
    async def test_transient_error_retried_and_succeeds(self):
        attempts = 0

        async def flaky_runner(msg: ChatMessage):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError("service unavailable — retry")
            return "finally_ok"

        q = ChatConversationQueue(
            "s-retry",
            flaky_runner,
            max_retries=3,
            backoff_base_s=0.01,
        )
        q.start()
        trace = await _run_and_drain(q, ChatMessage(content="retry_me"))
        assert trace.status == MessageStatus.SUCCESS
        assert trace.result == "finally_ok"
        assert trace.retry_count == 2
        q.stop()

    @pytest.mark.asyncio
    async def test_transient_retry_exhausted_halts_queue(self):
        async def always_transient(msg: ChatMessage):
            raise ConnectionError("rate limit 429")

        q = ChatConversationQueue(
            "s-exhaust",
            always_transient,
            max_retries=2,
            backoff_base_s=0.01,
        )
        q.start()
        trace = await _run_and_drain(q, ChatMessage(content="fail"))
        assert trace.status == MessageStatus.ERROR
        assert q.is_halted()
        q.stop()

    @pytest.mark.asyncio
    async def test_non_transient_error_not_retried(self):
        attempts = 0

        async def logic_error_runner(msg: ChatMessage):
            nonlocal attempts
            attempts += 1
            raise ValueError("business logic error")

        q = ChatConversationQueue(
            "s-no-retry",
            logic_error_runner,
            max_retries=3,
            backoff_base_s=0.01,
        )
        q.start()
        trace = await _run_and_drain(q, ChatMessage(content="x"))
        # Non-transient → should not retry (attempts stays at 1)
        assert attempts == 1
        assert trace.status == MessageStatus.ERROR
        q.stop()


class TestChatQueueManager:
    def test_singleton_returns_same_instance(self):
        m1 = ChatQueueManager.get_instance()
        m2 = ChatQueueManager.get_instance()
        assert m1 is m2

    def test_missing_runner_raises_valueerror(self):
        manager = ChatQueueManager.get_instance()
        with pytest.raises(ValueError, match="No runner registered"):
            manager.get_or_create("s-no-runner")  # No runner, not registered

    def test_register_runner_then_get_or_create(self):
        manager = ChatQueueManager.get_instance()
        manager.register_runner("s-reg", _make_success_runner())
        q = manager.get_or_create("s-reg")
        assert q is not None
        q.stop()

    def test_get_or_create_idempotent(self):
        manager = ChatQueueManager.get_instance()
        runner = _make_success_runner()
        q1 = manager.get_or_create("s-idem", runner=runner)
        q2 = manager.get_or_create("s-idem", runner=runner)
        assert q1 is q2
        q1.stop()

    def test_remove_stops_queue(self):
        manager = ChatQueueManager.get_instance()
        q = manager.get_or_create("s-remove", runner=_make_success_runner())
        manager.remove("s-remove")
        assert manager.get("s-remove") is None

    def test_active_sessions_listed(self):
        manager = ChatQueueManager.get_instance()
        manager.get_or_create("s-a", runner=_make_success_runner())
        manager.get_or_create("s-b", runner=_make_success_runner())
        sessions = manager.active_sessions()
        assert "s-a" in sessions
        assert "s-b" in sessions


class TestIsTransient:
    @pytest.mark.parametrize(
        "msg",
        [
            "service unavailable",
            "connection refused",
            "rate limit exceeded",
            "429 too many requests",
            "503 overloaded",
            "temporary failure",
        ],
    )
    def test_transient_keywords_detected(self, msg: str):
        assert _is_transient(Exception(msg)) is True

    @pytest.mark.parametrize(
        "msg",
        [
            "AttributeError: NoneType",
            "ZeroDivisionError",
            "business logic failure",
            "access denied",
            "invalid request",
        ],
    )
    def test_non_transient_not_detected(self, msg: str):
        assert _is_transient(Exception(msg)) is False
