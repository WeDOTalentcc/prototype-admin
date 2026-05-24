"""Bug C Red test: _is_async_method must detect AsyncAnthropic.messages.create as async.

When this returns False, _patch_messages_api routes to the sync wrapper that
calls _enforce_credit_gate_sync, which raises RuntimeError("called from
running event loop") and fails 100% of LLM calls in async context (chat,
orchestrator, every async path).

This is the root cause of the "Demo User, estou com dificuldade..."
surfacing in production (the catch-all in main_orchestrator.process
swallows the RuntimeError into a friendly message).

Pin: AsyncAnthropic.messages.create MUST be detected as async by all 3
detection cascades (iscoroutinefunction, __wrapped__, class name fallback).
"""
from __future__ import annotations

import inspect
import os

import pytest

from app.shared.llm_bootstrap import _is_async_method


def test_is_async_method_detects_async_anthropic_messages_create():
    """RED if Anthropic SDK wrapper decorator hides the async nature.

    If this fails, _patch_messages_api routes AsyncAnthropic through the
    sync wrapper → RuntimeError on every async LLM call.
    """
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        pytest.skip("anthropic SDK not installed in this env")

    # Construct without making any network call. Key may be invalid; we only
    # need the messages.create method handle.
    client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "sk-test"))
    create_method = client.messages.create

    is_async = _is_async_method(create_method)
    assert is_async, (
        f"AsyncAnthropic.messages.create was NOT detected as async. "
        f"This means _patch_messages_api will install the SYNC wrapper, "
        f"which calls _enforce_credit_gate_sync — that raises "
        f"RuntimeError when called from a running event loop. Every "
        f"async LLM call will fail.\n\n"
        f"Diagnostic:\n"
        f"  inspect.iscoroutinefunction(create_method) = "
        f"{inspect.iscoroutinefunction(create_method)}\n"
        f"  hasattr __wrapped__ = {hasattr(create_method, '__wrapped__')}\n"
        f"  __wrapped__ iscoroutinefunction = "
        f"{inspect.iscoroutinefunction(getattr(create_method, '__wrapped__', None))}\n"
        f"  __self__ class name = "
        f"{type(getattr(create_method, '__self__', None)).__name__}\n"
    )


def test_is_async_method_detects_async_anthropic_messages_stream():
    """Stream API has the same detection requirement (line 607 sync gate)."""
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        pytest.skip("anthropic SDK not installed")

    client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "sk-test"))
    if not hasattr(client.messages, "stream"):
        pytest.skip("messages.stream not exposed in this SDK version")
    stream_method = client.messages.stream
    is_async = _is_async_method(stream_method)
    assert is_async, (
        f"AsyncAnthropic.messages.stream was NOT detected as async — "
        f"same defect pattern as create. See create test for diagnostics."
    )


def test_is_async_method_rejects_sync_anthropic_messages_create():
    """Negative case: sync client must NOT be flagged as async."""
    try:
        from anthropic import Anthropic
    except ImportError:
        pytest.skip("anthropic SDK not installed")

    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "sk-test"))
    create_method = client.messages.create
    is_async = _is_async_method(create_method)
    assert not is_async, (
        f"Sync Anthropic.messages.create was incorrectly flagged as async. "
        f"This would route to the async wrapper that uses async gate — "
        f"would deadlock in sync caller (asyncio.run inside no-loop)."
    )
