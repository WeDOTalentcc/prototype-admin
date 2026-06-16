"""D.1 contract: @with_runtime_context supports positional args.

Workstream D ticket 1 (2026-05-23).

Pre-D.1 decorator only worked with **kwargs-only handlers. Voice methods
use positional args (e.g. process_audio_chunk(self, session_id, audio_data))
so they fell back to inline RuntimeContext (see F-14 historical note).

D.1: extends decorator to bind positional args via inspect.signature,
extracting requested field values whether they come positional or keyword.
Backward compat with the existing **kwargs-only call path preserved.
"""
from __future__ import annotations

import pytest

from app.shared.runtime_context import with_runtime_context


@pytest.fixture(autouse=True)
def _reset_tenant_contextvar():
    """Reset auth ContextVar before/after each test."""
    from app.middleware.auth_enforcement import _current_company_id
    token = _current_company_id.set("")
    try:
        yield
    finally:
        _current_company_id.reset(token)


def _set_company_id(value: str):
    from app.middleware.auth_enforcement import _current_company_id
    _current_company_id.set(value)


# ----------------------------------------------------------------------------
# Backward compat — kwargs-only handler still works
# ----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kwargs_only_handler_still_works():
    """D.1: existing **kwargs-only handlers must keep working (no regression)."""
    received: dict = {}

    @with_runtime_context("company_id")
    async def _handler(**kwargs):
        received.update(kwargs)
        return {"ok": True}

    _set_company_id("ctx-d1-1")
    await _handler()
    assert received.get("company_id") == "ctx-d1-1"


# ----------------------------------------------------------------------------
# New: positional-arg handler support
# ----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_decorator_supports_positional_args():
    """D.1: handler with positional params can be invoked positionally."""
    received: dict = {}

    @with_runtime_context("company_id")
    async def _handler(session_id: str, company_id: str | None = None):
        received["session_id"] = session_id
        received["company_id"] = company_id
        return {"ok": True}

    _set_company_id("ctx-d1-2")
    # invoke positionally — pre-D.1 this would raise TypeError because
    # the decorator wrapper only accepted **kwargs.
    await _handler("session-x")

    assert received["session_id"] == "session-x"
    assert received["company_id"] == "ctx-d1-2", (
        "D.1: decorator must inject company_id from ContextVar when caller "
        "did not provide it (matches kwargs-handler semantics)."
    )


@pytest.mark.asyncio
async def test_decorator_extracts_company_id_from_positional():
    """D.1: if caller passes company_id POSITIONALLY, decorator does NOT
    override (caller-wins like kwargs case)."""
    received: dict = {}

    @with_runtime_context("company_id")
    async def _handler(session_id: str, company_id: str):
        received["session_id"] = session_id
        received["company_id"] = company_id
        return {"ok": True}

    _set_company_id("ctx-d1-3")
    await _handler("session-y", "caller-tenant")

    assert received["company_id"] == "caller-tenant", (
        "D.1: caller-positional value must win over ContextVar — mirrors "
        "kwargs caller-wins semantics."
    )


@pytest.mark.asyncio
async def test_decorator_validates_required_fields_present():
    """D.1: with_runtime_context still validates field names against
    RuntimeContext dataclass — invalid name raises ValueError at decoration."""
    with pytest.raises(ValueError) as exc_info:
        @with_runtime_context("unknown_field_xyz")
        async def _h(**kwargs):
            pass
    assert "unknown" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_decorator_method_with_self_positional():
    """D.1: instance methods (self positional) still work — common case
    for voice services like VoiceCoreOrchestrator.process_audio_chunk."""
    captured: dict = {}

    class FakeService:
        @with_runtime_context("company_id")
        async def do_work(self, session_id: str, company_id: str | None = None):
            captured["session_id"] = session_id
            captured["company_id"] = company_id
            return "done"

    _set_company_id("ctx-d1-4")
    svc = FakeService()
    result = await svc.do_work("sess-A")
    assert result == "done"
    assert captured["company_id"] == "ctx-d1-4"
    assert captured["session_id"] == "sess-A"


@pytest.mark.asyncio
async def test_decorator_mixed_positional_and_kwargs():
    """D.1: handler with mixed (positional + kwarg) call style — decorator
    must inject only into the slots not occupied by caller."""
    captured: dict = {}

    @with_runtime_context("company_id")
    async def _handler(
        session_id: str,
        request_id: str,
        company_id: str | None = None,
    ):
        captured["session_id"] = session_id
        captured["request_id"] = request_id
        captured["company_id"] = company_id

    _set_company_id("ctx-d1-5")
    await _handler("sess-B", request_id="req-d1-5")

    assert captured["session_id"] == "sess-B"
    assert captured["request_id"] == "req-d1-5"
    assert captured["company_id"] == "ctx-d1-5", (
        "D.1: ContextVar fills the slot caller did not provide."
    )
