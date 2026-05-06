"""Tests for the ADR-029 §2 ContextVar injection in `tool_handler`.

The decorator (`app.shared.tool_handler.tool_handler`) injects `company_id`
from the auth-middleware `ContextVar` (`_current_company_id`) before
invoking the wrapped tool function. This makes it safe to strip
`company_id` from JSON tool schemas: the LLM stops asking for it (UX),
and the value still reaches the handler via kwargs (operational).

Tests in `test_tool_handler_isolation.py` cover the fail-closed path
(no ContextVar, no kwargs → tenant error). These tests cover the
positive paths and the LLM-supplied-tenant defense-in-depth.

Skill: tdd-workflow (red→green→refactor).
"""
from __future__ import annotations

import pytest

from app.shared.tool_handler import (
    _TENANT_KEYS_LLM_FORBIDDEN,
    _resolve_company_id_from_context,
    tool_handler,
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


def _set_company_id_ctx(value: str):
    """Helper: set the auth ContextVar inline."""
    from app.middleware.auth_enforcement import _current_company_id
    _current_company_id.set(value)


# ──────────────────────────────────────────────────────────────────────
# Positive path: ContextVar populated, no LLM-supplied company_id
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_context_var_injects_company_id_when_kwargs_omit_it():
    """When LLM doesn't send company_id (because schema-stripped) but the
    ContextVar is set, handler receives company_id via kwargs."""
    received: dict = {}

    @tool_handler("test_domain")
    async def _handler(**kwargs):
        received.update(kwargs)
        return {"ok": True}

    _set_company_id_ctx("ctx-tenant-123")
    result = await _handler()  # NO company_id kwarg — simulates stripped schema

    assert result["success"] is True, f"expected success, got {result}"
    assert received.get("company_id") == "ctx-tenant-123", (
        f"ContextVar value should be injected into kwargs; got {received}"
    )


@pytest.mark.asyncio
async def test_context_var_wins_over_llm_supplied_company_id():
    """If LLM hallucinated a company_id arg AND the ContextVar is set,
    ContextVar wins. Defense in depth against tenant escalation."""
    received: dict = {}

    @tool_handler("test_domain")
    async def _handler(**kwargs):
        received.update(kwargs)
        return {"ok": True}

    _set_company_id_ctx("auth-tenant-A")
    # LLM tries to escalate to tenant B — should be overwritten
    result = await _handler(company_id="malicious-tenant-B", other_arg="value")

    assert result["success"] is True
    assert received.get("company_id") == "auth-tenant-A", (
        "ContextVar must override LLM-supplied company_id (tenant-escalation defense)"
    )
    assert received.get("other_arg") == "value", (
        "Non-tenant kwargs should pass through unchanged"
    )


# ──────────────────────────────────────────────────────────────────────
# Defense in depth: LLM-supplied tenant_id / organization_id always dropped
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_llm_supplied_tenant_id_is_stripped_from_kwargs():
    """LLM-supplied `tenant_id` / `organization_id` are never passed to handlers,
    even when the auth ContextVar is set. They have no canonical source in
    this codebase — only `company_id` does."""
    received: dict = {}

    @tool_handler("test_domain")
    async def _handler(**kwargs):
        received.update(kwargs)
        return {"ok": True}

    _set_company_id_ctx("auth-tenant")
    await _handler(
        tenant_id="llm-injected-tenant",
        organization_id="llm-injected-org",
        legitimate_arg="kept",
    )

    assert "tenant_id" not in received, "LLM-supplied tenant_id must be stripped"
    assert "organization_id" not in received, "LLM-supplied organization_id must be stripped"
    assert received.get("legitimate_arg") == "kept", "Non-tenant kwargs preserved"
    assert received.get("company_id") == "auth-tenant", "Authentic company_id injected"


# ──────────────────────────────────────────────────────────────────────
# Backward compat: legacy LLM-supplied company_id without ContextVar
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_llm_supplied_company_id_honored_when_no_context_var(caplog):
    """Sprint 1 transitional: if no ContextVar BUT LLM supplied a value,
    honor it for backward compat + log a warning. After ADR-029 §2 sensor
    is blocking, schemas are clean and this branch becomes unreachable."""
    received: dict = {}

    @tool_handler("test_domain")
    async def _handler(**kwargs):
        received.update(kwargs)
        return {"ok": True}

    # ContextVar empty (default), LLM provides legacy company_id
    import logging
    with caplog.at_level(logging.WARNING):
        result = await _handler(company_id="legacy-tenant-X")

    assert result["success"] is True
    assert received.get("company_id") == "legacy-tenant-X"
    # Warning surfaced for audit trail
    assert any("LLM-supplied company_id" in rec.message for rec in caplog.records), (
        "Backward-compat branch must log a warning to surface migration debt"
    )


# ──────────────────────────────────────────────────────────────────────
# Constants + helpers
# ──────────────────────────────────────────────────────────────────────


def test_tenant_keys_constant_includes_canonical_three():
    """Pin the constant — sensor + decorator must agree on the set."""
    assert "company_id" in _TENANT_KEYS_LLM_FORBIDDEN
    assert "tenant_id" in _TENANT_KEYS_LLM_FORBIDDEN
    assert "organization_id" in _TENANT_KEYS_LLM_FORBIDDEN


def test_resolve_company_id_from_context_returns_empty_when_unset():
    """Helper must return empty string (not None) when ContextVar absent;
    callers rely on truthiness check."""
    assert _resolve_company_id_from_context() == ""


def test_resolve_company_id_from_context_returns_set_value():
    _set_company_id_ctx("hello-tenant")
    assert _resolve_company_id_from_context() == "hello-tenant"
