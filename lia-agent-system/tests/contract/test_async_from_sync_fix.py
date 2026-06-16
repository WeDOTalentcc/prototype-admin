"""Contract tests — P0 async-from-sync gate routing fix (2026-05-22).

Validates the harness fix in `app.shared.llm_bootstrap._patch_messages_api`:
* AsyncAnthropic.messages.create receives an ASYNC wrapper that routes through
  `_enforce_credit_gate_async`.
* Anthropic (sync).messages.create receives a SYNC wrapper that routes through
  `_enforce_credit_gate_sync`.
* Calling the sync gate from a running event loop now FAIL-LOUDLY (REGRA 4)
  instead of silently swallowing the RuntimeError into a fail-safe ALLOW.
* `inspect.iscoroutinefunction` is the canonical discriminator.

Tests the SHIM, not the real SDK. We construct fake client objects with
`messages.create` set to either an async or sync callable to validate the
patching dispatch.
"""
from __future__ import annotations

import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.middleware.auth_enforcement import _current_company_id
from app.shared.llm_bootstrap import (
    _enforce_credit_gate_async,
    _enforce_credit_gate_sync,
    _patch_messages_api,
    install_llm_guards,
)
from app.shared.services.ai_credit_gate import AICreditExhausted


# Ensure bootstrap is installed once for module — same idempotent path as prod.
install_llm_guards()


COMPANY_OK = "test-company-uuid-async-routing"


# ----------------------------------------------------------------------
# 1. inspect.iscoroutinefunction detects sync vs async correctly.
# ----------------------------------------------------------------------

def test_inspect_iscoroutinefunction_detects_correctly():
    """The discriminator the patcher uses returns True only for async def."""

    def sync_fn():
        return 1

    async def async_fn():
        return 1

    assert inspect.iscoroutinefunction(sync_fn) is False
    assert inspect.iscoroutinefunction(async_fn) is True

    # AsyncMock is also recognized as a coroutine function.
    assert inspect.iscoroutinefunction(AsyncMock()) is True
    # MagicMock is NOT.
    assert inspect.iscoroutinefunction(MagicMock()) is False


# ----------------------------------------------------------------------
# 2. AsyncAnthropic-shaped client gets an ASYNC patched create.
# ----------------------------------------------------------------------

def _make_async_client():
    """Mimic AsyncAnthropic shape: client.messages.create is `async def`."""
    async def _orig_create(*args, **kwargs):
        # Return a typed-ish response shape used by reconcile path.
        resp = MagicMock()
        resp.usage = MagicMock()
        resp.usage.input_tokens = 10
        resp.usage.output_tokens = 5
        return resp

    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = _orig_create
    # Strip the auto _lia_patched sentinel possibly inherited from MagicMock.
    if hasattr(client.messages, "_lia_patched"):
        try:
            del client.messages._lia_patched
        except AttributeError:
            pass
    return client


def _make_sync_client():
    """Mimic Anthropic (sync) shape: client.messages.create is `def`."""

    def _orig_create(*args, **kwargs):
        resp = MagicMock()
        resp.usage = MagicMock()
        resp.usage.input_tokens = 10
        resp.usage.output_tokens = 5
        return resp

    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = _orig_create
    if hasattr(client.messages, "_lia_patched"):
        try:
            del client.messages._lia_patched
        except AttributeError:
            pass
    return client


def test_async_anthropic_gets_async_patched_create():
    """AsyncAnthropic-shaped client: patched create must be a coroutine fn."""
    client = _make_async_client()
    _patch_messages_api(client, "anthropic-async-test-1")
    assert inspect.iscoroutinefunction(client.messages.create), (
        "Async client must receive async-patched create (P0 fix)"
    )


def test_sync_anthropic_gets_sync_patched_create():
    """Anthropic (sync) client: patched create must be a regular fn."""
    client = _make_sync_client()
    _patch_messages_api(client, "anthropic-sync-test-1")
    assert not inspect.iscoroutinefunction(client.messages.create), (
        "Sync client must receive sync-patched create"
    )


# ----------------------------------------------------------------------
# 3. Async caller from async context goes through async gate — no RuntimeError.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_caller_from_async_context_no_runtime_error():
    """The whole point of the P0 fix: AsyncAnthropic.messages.create called
    from within asyncio.run / pytest-asyncio context must NOT raise
    RuntimeError ('Cannot run the event loop while another loop is running').

    The patched async create goes through _enforce_credit_gate_async which
    awaits cleanly inside the existing event loop.
    """
    client = _make_async_client()
    _patch_messages_api(client, "anthropic-async-routing-test")

    # Capture which gate helper got called.
    async_gate_called = {"value": False}

    async def _fake_async_gate(provider, kwargs, *, estimator):
        async_gate_called["value"] = True
        return None

    token = _current_company_id.set(COMPANY_OK)
    try:
        with patch(
            "app.shared.llm_bootstrap._enforce_credit_gate_async",
            new=_fake_async_gate,
        ):
            # This used to blow up with RuntimeError when the sync gate
            # tried run_until_complete inside a running loop.
            await client.messages.create(
                model="claude-sonnet-4",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10,
            )

        assert async_gate_called["value"] is True, (
            "Async gate should have been hit by async-patched create"
        )
    finally:
        _current_company_id.reset(token)


# ----------------------------------------------------------------------
# 4. Sync gate called from a running loop now FAIL-LOUDS (REGRA 4).
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sync_gate_called_from_running_loop_raises_runtime_error():
    """Direct invocation of _enforce_credit_gate_sync from a running event
    loop must raise RuntimeError (no silent swallow → no fail-safe ALLOW).

    This is the canonical guard against future regressions in
    _patch_messages_api: if anyone (re)introduces a sync wrapper on an
    async SDK seam, the moment the gate is hit from async context, this
    error fires loudly.
    """
    token = _current_company_id.set(COMPANY_OK)
    try:
        with pytest.raises(RuntimeError, match="running event loop"):
            _enforce_credit_gate_sync(
                "anthropic-sync-from-async",
                {"messages": [{"role": "user", "content": "x"}], "max_tokens": 5},
                estimator=lambda k: 5,
            )
    finally:
        _current_company_id.reset(token)


# ----------------------------------------------------------------------
# 5. _is_async_method handles SDK wrappers (Anthropic decorator) correctly.
# ----------------------------------------------------------------------

def test_is_async_method_detects_anthropic_async_decorator():
    """Real-world regression: Anthropic SDK wraps `async def create` with
    `@_utils.required_args(...)` which hides the coroutine status from
    `inspect.iscoroutinefunction`. `_is_async_method` must look through
    `__wrapped__` (or fall back to class name `AsyncMessages`).
    """
    try:
        from anthropic.resources.messages import AsyncMessages, Messages
    except ImportError:
        pytest.skip("anthropic SDK not installed in this environment")

    from app.shared.llm_bootstrap import _is_async_method

    # Bare functions still defeat iscoroutinefunction but pass _is_async_method
    # via __wrapped__.
    assert _is_async_method(AsyncMessages.create) is True, (
        "Anthropic AsyncMessages.create should be detected via __wrapped__"
    )
    assert _is_async_method(Messages.create) is False, (
        "Anthropic Messages.create (sync) should NOT be detected as async"
    )


def test_is_async_method_handles_plain_callables():
    """Sanity: plain def, async def, and lambda all classified correctly."""
    from app.shared.llm_bootstrap import _is_async_method

    def sync_fn():
        return 1

    async def async_fn():
        return 1

    assert _is_async_method(sync_fn) is False
    assert _is_async_method(async_fn) is True
    assert _is_async_method(lambda: 1) is False
