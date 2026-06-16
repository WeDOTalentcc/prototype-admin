"""Sprint R.2 sensor — aio_pika cross-loop close leak guard.

Validates the harness fix in `app/shared/messaging/rabbitmq_producer.py`:

  1. When `publish_to_exchange()` runs on the registered main loop, it
     publishes directly via the singleton (no per-call connect/close).
  2. When invoked from a transient worker loop (`asyncio.run` on a thread),
     it MUST redispatch onto the registered main loop via
     `asyncio.run_coroutine_threadsafe(...)` — NOT call `asyncio.run` again
     or open a fresh `connect_robust()` per call.
  3. No `_GatheringFuture pending attached to a different loop` traceback
     is emitted when the worker-loop path is exercised.

Pattern mirrors the audit_service loop-leak fix sensor methodology.
No real RabbitMQ broker — the singleton `rabbitmq_producer.publish_topic`
is mocked, the loop-dispatch behaviour is verified by intercepting
`asyncio.run_coroutine_threadsafe`.
"""
from __future__ import annotations

import asyncio
import io
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import pytest

from app.shared.messaging import rabbitmq_producer as mq


@pytest.fixture(autouse=True)
def _reset_main_loop():
    """Reset module-level _MAIN_LOOP between tests."""
    saved = mq._MAIN_LOOP
    mq._MAIN_LOOP = None
    yield
    mq._MAIN_LOOP = saved


def test_register_main_loop_captures_running_loop():
    """register_main_loop() with no arg captures the current running loop."""
    async def _go():
        mq.register_main_loop()
        return mq._MAIN_LOOP

    captured = asyncio.run(_go())
    assert captured is not None
    # The captured loop is closed by asyncio.run; that's fine — the assertion
    # is that something was captured at all.


def test_running_on_main_loop_true_when_same_loop():
    """_running_on_main_loop is True when current loop is the registered one."""
    async def _go():
        mq.register_main_loop()
        return mq._running_on_main_loop()

    assert asyncio.run(_go()) is True


def test_publish_on_main_loop_calls_singleton_directly():
    """When on main loop, publish_to_exchange invokes rabbitmq_producer.publish_topic
    directly (no run_coroutine_threadsafe redispatch)."""
    calls: list[tuple] = []

    async def _fake_publish_topic(exchange, routing_key, message):
        calls.append((exchange, routing_key, message))

    with patch.object(mq.rabbitmq_producer, "publish_topic", _fake_publish_topic):
        with patch.object(mq, "settings") as fake_settings:
            fake_settings.RABBITMQ_URL = "amqp://test"
            with patch.object(mq._asyncio_loop_mod, "run_coroutine_threadsafe") as mocked_dispatch:
                async def _go():
                    mq.register_main_loop()
                    await mq.publish_to_exchange("ex", "rk", {"a": 1})

                asyncio.run(_go())

                mocked_dispatch.assert_not_called()

    assert calls == [("ex", "rk", {"a": 1})]


def test_publish_from_worker_thread_dispatches_via_run_coroutine_threadsafe():
    """When publish_to_exchange runs on a transient worker-thread loop, it MUST
    redispatch via asyncio.run_coroutine_threadsafe to the registered main loop —
    not call asyncio.run / open a fresh connection.

    We spin up a *real* main loop in a dedicated thread (mirroring how FastAPI
    runs the main loop in the uvicorn thread) and exercise the publish from a
    second worker thread that owns its own transient `asyncio.run` loop.
    `asyncio.run_coroutine_threadsafe` is the only safe transfer mechanism —
    if the fix regresses to `asyncio.run`/per-call connect, this test fails.
    """
    main_loop = asyncio.new_event_loop()
    loop_ready = threading.Event()

    def _main_loop_thread():
        asyncio.set_event_loop(main_loop)
        loop_ready.set()
        main_loop.run_forever()

    main_thread = threading.Thread(target=_main_loop_thread, daemon=True)
    main_thread.start()
    loop_ready.wait(timeout=2.0)
    mq._MAIN_LOOP = main_loop

    received: list[tuple] = []
    received_lock = threading.Lock()

    async def _fake_publish_topic(exchange, routing_key, message):
        with received_lock:
            received.append((exchange, routing_key, message))

    dispatch_calls: list[asyncio.AbstractEventLoop] = []
    real_run_coroutine_threadsafe = mq._asyncio_loop_mod.run_coroutine_threadsafe

    def _spy_run_coroutine_threadsafe(coro, loop):
        dispatch_calls.append(loop)
        return real_run_coroutine_threadsafe(coro, loop)

    try:
        with patch.object(mq.rabbitmq_producer, "publish_topic", _fake_publish_topic), \
             patch.object(mq._asyncio_loop_mod, "run_coroutine_threadsafe",
                          _spy_run_coroutine_threadsafe), \
             patch.object(mq, "settings") as fake_settings:
            fake_settings.RABBITMQ_URL = "amqp://test"

            stderr_capture = io.StringIO()
            stdout_capture = io.StringIO()
            worker_error: list[BaseException] = []

            def _worker():
                # Fresh transient loop — simulates LangGraph/Celery worker.
                try:
                    with redirect_stderr(stderr_capture), redirect_stdout(stdout_capture):
                        asyncio.run(mq.publish_to_exchange("ex", "rk", {"a": 2}))
                except BaseException as e:  # noqa: BLE001
                    worker_error.append(e)

            t = threading.Thread(target=_worker)
            t.start()
            t.join(timeout=5.0)
            assert not t.is_alive(), "worker thread hung"
            assert not worker_error, f"worker raised: {worker_error[0]!r}"

            # Assert dispatch path was taken (not in-place await on worker loop).
            assert len(dispatch_calls) == 1, (
                f"expected exactly 1 dispatch to main loop, got {len(dispatch_calls)}"
            )
            assert dispatch_calls[0] is main_loop

            # Assert the publish landed on the singleton, on the main loop.
            assert received == [("ex", "rk", {"a": 2})]

            # Assert no cross-loop traceback was emitted to stderr/stdout.
            combined = stderr_capture.getvalue() + stdout_capture.getvalue()
            assert "attached to a different loop" not in combined, (
                f"Cross-loop close leak detected in test output: {combined}"
            )
            assert "_GatheringFuture" not in combined
    finally:
        main_loop.call_soon_threadsafe(main_loop.stop)
        main_thread.join(timeout=2.0)
        main_loop.close()


def test_dispatch_raises_when_main_loop_not_registered():
    """If main loop was never registered, _dispatch_on_main_loop raises a clean
    RuntimeError instead of silently failing."""
    assert mq._MAIN_LOOP is None
    with pytest.raises(RuntimeError, match="main loop not registered"):
        mq._dispatch_on_main_loop(lambda: asyncio.sleep(0), timeout=1.0)
