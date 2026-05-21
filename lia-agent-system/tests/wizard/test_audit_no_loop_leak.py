"""Audit loop-leak sensor (registered 2026-05-20 — Audit E2E follow-up).

Root cause: graph.py LangGraph sync nodes call
`_asyncio.run(AuditService().log_decision(...))` from worker threads. Each
`asyncio.run()` spawns a transient loop. asyncpg connections borrowed from
the shared SQLAlchemy pool inside `log_decision` bind their internal
callbacks to this transient loop — when it closes, the connection is
returned poisoned to the pool. The next FastAPI request that borrows it
fails with "Event loop is closed" inside SET ROLE -> "RLS role enforcement
failed".

Fix surface area (preserved by this sensor):
  - app/shared/compliance/audit_service.py:
      register_main_loop(), _running_on_main_loop(), _dispatch_on_main_loop()
      log_decision() routes to main loop when called from a transient loop.

What this sensor pins:
  1. The public AuditService.log_decision symbol exists and is async.
  2. The internal `_log_decision_impl` symbol exists (split for redispatch).
  3. The `register_main_loop` / `_running_on_main_loop` / `_dispatch_on_main_loop`
     helpers exist with expected signatures.
  4. When `log_decision` is invoked from a transient loop (asyncio.run on a
     worker thread, simulating the LangGraph node pattern) WITHOUT the main
     loop registered, it does NOT raise — caller is responsible.
  5. When a main loop IS registered and `log_decision` runs on a different
     (transient) loop, the impl is redispatched onto the main loop (not the
     transient one) — pin via patching `_log_decision_impl` to capture the
     loop it executes on.
"""
from __future__ import annotations

import asyncio
import inspect
import threading
from unittest.mock import patch

import pytest

from app.shared.compliance import audit_service as audit_mod
from app.shared.compliance.audit_service import AuditService


def test_public_api_surface_preserved():
    """log_decision must remain async and accept the canonical kwargs."""
    assert inspect.iscoroutinefunction(AuditService.log_decision)
    assert inspect.iscoroutinefunction(AuditService._log_decision_impl)
    sig = inspect.signature(AuditService.log_decision)
    for p in (
        "company_id",
        "agent_name",
        "decision_type",
        "action",
        "decision",
        "reasoning",
        "criteria_used",
    ):
        assert p in sig.parameters, f"log_decision missing param {p}"


def test_loop_helpers_exist():
    """The 3 module helpers must exist with the expected interface."""
    assert callable(audit_mod.register_main_loop)
    assert callable(audit_mod._running_on_main_loop)
    assert callable(audit_mod._dispatch_on_main_loop)


def test_redispatch_routes_through_main_loop():
    """When log_decision runs on a transient loop, the impl executes on the main loop.

    Simulates the LangGraph node pattern: a worker thread calls
    `_asyncio.run(audit.log_decision(...))`. The impl MUST execute on the
    long-lived main loop, not the transient one — that's what protects the
    asyncpg pool from cross-loop poisoning.
    """
    # Snapshot current state so the test doesn't bleed into other tests
    saved = audit_mod._MAIN_LOOP
    main_loop_captured: list[asyncio.AbstractEventLoop] = []
    impl_ran_on_loop: list[asyncio.AbstractEventLoop | None] = []

    async def _start_main_loop_and_run_worker():
        """Establish the main loop, then spawn a worker thread that simulates
        a LangGraph sync node calling `asyncio.run(audit.log_decision(...))`.
        """
        audit_mod.register_main_loop()
        main_loop_captured.append(asyncio.get_running_loop())

        # Patch _log_decision_impl to capture which loop runs it.
        async def fake_impl(self, **kwargs):
            try:
                impl_ran_on_loop.append(asyncio.get_running_loop())
            except RuntimeError:
                impl_ran_on_loop.append(None)
            return "ok"

        worker_done = threading.Event()
        worker_error: list[BaseException] = []

        def _worker():
            try:
                with patch.object(AuditService, "_log_decision_impl", fake_impl):
                    asyncio.run(
                        AuditService().log_decision(
                            company_id="test-co",
                            agent_name="test:sensor",
                            decision_type="generate_jd",
                            action="x",
                            decision="ok",
                            reasoning=["sensor"],
                            criteria_used=["sensor"],
                        )
                    )
            except BaseException as exc:
                worker_error.append(exc)
            finally:
                worker_done.set()

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        # While worker runs, this main-loop coroutine must keep yielding so
        # `run_coroutine_threadsafe` can land its task.
        while not worker_done.is_set():
            await asyncio.sleep(0.01)

        if worker_error:
            raise worker_error[0]

    try:
        asyncio.run(_start_main_loop_and_run_worker())
        assert main_loop_captured, "main loop must have been captured"
        assert impl_ran_on_loop, "_log_decision_impl must have run"
        # CRITICAL invariant — impl ran on the MAIN loop, not the transient
        # asyncio.run() loop inside the worker thread.
        assert impl_ran_on_loop[0] is main_loop_captured[0], (
            "AuditService._log_decision_impl ran on the wrong loop: "
            f"expected main={id(main_loop_captured[0])}, "
            f"actual={id(impl_ran_on_loop[0]) if impl_ran_on_loop[0] else None}"
        )
    finally:
        audit_mod._MAIN_LOOP = saved


def test_no_main_loop_falls_through_to_local_impl():
    """If no main loop is registered, log_decision runs the impl locally
    (legacy behavior — no redispatch). Required so test environments and
    Celery workers without a registered main loop still function.
    """
    saved = audit_mod._MAIN_LOOP
    audit_mod._MAIN_LOOP = None

    impl_ran_on_loop: list[asyncio.AbstractEventLoop | None] = []

    async def fake_impl(self, **kwargs):
        try:
            impl_ran_on_loop.append(asyncio.get_running_loop())
        except RuntimeError:
            impl_ran_on_loop.append(None)
        return "ok"

    try:
        with patch.object(AuditService, "_log_decision_impl", fake_impl):
            asyncio.run(
                AuditService().log_decision(
                    company_id="test-co",
                    agent_name="test:sensor",
                    decision_type="generate_jd",
                    action="x",
                    decision="ok",
                    reasoning=["sensor"],
                    criteria_used=["sensor"],
                )
            )
        assert impl_ran_on_loop, "impl must have run"
        assert impl_ran_on_loop[0] is not None, "impl must have run inside SOME loop"
    finally:
        audit_mod._MAIN_LOOP = saved
