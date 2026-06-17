"""TDD: RuntimeContext + with_runtime_context decorator (Sprint 3 ADR-029 §3).

Sprint 1B installed ContextVar injection at tool_handler level. Sprint 3
formalizes via typed RuntimeContext + explicit decorator.

Tests cover:
  1. RuntimeContext dataclass typing + factory
  2. is_complete / as_kwargs helpers
  3. with_runtime_context decorator: injects from ContextVar
  4. Caller-provided kwargs win over ContextVar (unlike tool_handler)
  5. Invalid field name raises at decoration time
  6. Missing field name argument raises
  7. Decorator is composable with tool_handler

Skill: tdd-workflow + canonical-fix.
"""
from __future__ import annotations

import pytest

from app.shared.runtime_context import (
    RuntimeContext,
    with_runtime_context,
)


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


# ──────────────────────────────────────────────────────────────────────
# RuntimeContext dataclass
# ──────────────────────────────────────────────────────────────────────


def test_runtime_context_default_empty():
    """No ContextVar set → empty fields."""
    ctx = RuntimeContext.from_contextvars()
    assert ctx.company_id == ""


def test_runtime_context_reads_company_id_from_contextvar():
    _set_company_id("tenant-A")
    ctx = RuntimeContext.from_contextvars()
    assert ctx.company_id == "tenant-A"


def test_runtime_context_is_frozen():
    """Immutability prevents accidental mutation downstream."""
    ctx = RuntimeContext(company_id="tenant-A")
    with pytest.raises((AttributeError, Exception)):  # FrozenInstanceError
        ctx.company_id = "tenant-B"


def test_is_complete_returns_true_when_all_fields_set():
    ctx = RuntimeContext(company_id="tenant-A")
    assert ctx.is_complete(("company_id",)) is True


def test_is_complete_returns_false_when_field_empty():
    ctx = RuntimeContext(company_id="")
    assert ctx.is_complete(("company_id",)) is False


def test_as_kwargs_returns_only_non_empty():
    ctx = RuntimeContext(company_id="tenant-A")
    kw = ctx.as_kwargs()
    assert kw == {"company_id": "tenant-A"}


def test_as_kwargs_with_empty_field_skips():
    ctx = RuntimeContext(company_id="")
    kw = ctx.as_kwargs()
    assert kw == {}


def test_as_kwargs_subset_filtering():
    ctx = RuntimeContext(company_id="tenant-A")
    kw = ctx.as_kwargs(fields_subset=())  # exclude all
    assert kw == {}


# ──────────────────────────────────────────────────────────────────────
# with_runtime_context decorator
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decorator_injects_company_id_when_kwargs_omit_it():
    received: dict = {}

    @with_runtime_context("company_id")
    async def _handler(**kwargs):
        received.update(kwargs)
        return {"ok": True}

    _set_company_id("ctx-tenant")
    result = await _handler()  # no kwargs

    assert result["ok"] is True
    assert received["company_id"] == "ctx-tenant"


@pytest.mark.asyncio
async def test_decorator_does_not_override_caller_supplied_field():
    """Unlike tool_handler (security-fail-closed), with_runtime_context
    is a softer "default value" pattern — caller wins."""
    received: dict = {}

    @with_runtime_context("company_id")
    async def _handler(**kwargs):
        received.update(kwargs)
        return {"ok": True}

    _set_company_id("ctx-tenant")
    await _handler(company_id="caller-override")

    assert received["company_id"] == "caller-override", (
        "with_runtime_context should not override caller — that's tool_handler's job"
    )


@pytest.mark.asyncio
async def test_decorator_skips_when_contextvar_empty_and_no_kwarg():
    received: dict = {}

    @with_runtime_context("company_id")
    async def _handler(**kwargs):
        received.update(kwargs)
        return {"ok": True}

    # ContextVar is empty (fixture reset)
    await _handler()
    # Field should NOT be injected when both are empty
    assert "company_id" not in received


def test_decorator_with_empty_args_raises():
    with pytest.raises(ValueError, match="at least 1 field name"):
        with_runtime_context()


def test_decorator_with_invalid_field_name_raises():
    with pytest.raises(ValueError, match="unknown field"):
        with_runtime_context("nonexistent_field")


def test_decorator_marks_function_for_introspection():
    """Sensor `check_tool_handlers_use_runtime_context.py` (Sprint 3.4)
    will look for this attribute."""
    @with_runtime_context("company_id")
    async def _handler(**kwargs):
        return {}

    assert hasattr(_handler, "_runtime_context_fields")
    assert _handler._runtime_context_fields == ("company_id",)


# ──────────────────────────────────────────────────────────────────────
# Composability with tool_handler (Sprint 1B)
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decorator_composes_with_tool_handler():
    """with_runtime_context (outer) + tool_handler (inner) work together."""
    from app.shared.tool_handler import tool_handler

    received: dict = {}

    @with_runtime_context("company_id")
    @tool_handler("test_domain")
    async def _handler(**kwargs):
        received.update(kwargs)
        return {"ok": True}

    _set_company_id("ctx-tenant")
    result = await _handler()

    assert result.get("success") is True
    assert received.get("company_id") == "ctx-tenant"
