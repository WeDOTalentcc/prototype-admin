"""
Sentinel — TenantAwareTask propagates company_id end-to-end.

Task #1145 (Multi-tenant Ownership — Celery tenant propagation).

Covers the canonical invariants:

1. **Producer-side, strict, missing company_id** — ``apply_async`` raises
   :class:`MissingTenantContextError` BEFORE the job is enqueued.
2. **Producer-side, strict, invalid company_id** — ``apply_async`` raises
   :class:`InvalidCompanyIdError` for the forbidden literal ``"default"``.
3. **Producer-side, legacy (default)** — ``apply_async`` warns + emits the
   ``outcome=missing`` metric but still enqueues.
4. **Worker-side ContextVar lifecycle** — within the task body,
   :func:`get_celery_company_id` returns the parsed/normalized ``company_id``;
   after return it is reset to ``""``, even if the task raised. Both the
   eager ``__call__`` path AND the production
   ``before_start`` / ``after_return`` lifecycle path are exercised.
5. **Sub-service fallback** — :func:`resolve_tenant_snippet_for_non_react`
   reads the worker ContextVar when its explicit ``company_id_raw`` is None,
   so legacy code invoked from inside a task automatically inherits tenant.
6. **DB session enforcement (RLS)** — when ``LIA_CELERY_TEST_DB_URL`` (or
   ``DATABASE_URL``) is available, opening a session inside the task body
   automatically runs ``SET LOCAL ROLE lia_app`` + ``set_config('app.company_id',
   :cid, true)`` via the global ``after_begin`` listener; a query for
   ``current_setting('app.company_id', true)`` returns the injected value.
"""
from __future__ import annotations

import asyncio
import os
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.jobs.tenant_aware_task import (
    TenantAwareTask,
    get_celery_company_id,
    reset_celery_company_id_context,
    set_celery_company_id_context,
)
from app.shared.exceptions.tenant_errors import (
    InvalidCompanyIdError,
    MissingTenantContextError,
)
from lia_config.celery_app import celery_app


CANONICAL_UUID = "00000000-0000-4000-a000-000000000001"


# ---------------------------------------------------------------------------
# Fixtures — a real Celery task running in EAGER mode (no broker required).
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def eager_task():
    """Register a TenantAwareTask under eager mode so .apply runs sync."""
    captured: dict = {}

    @celery_app.task(
        name="tests._t1145.echo_tenant",
        bind=True,
        base=TenantAwareTask,
    )
    def _echo_tenant(self, payload: str, company_id: str) -> dict:
        captured["company_id"] = get_celery_company_id()
        captured["payload"] = payload
        return {"company_id_seen": get_celery_company_id()}

    _echo_tenant._captured = captured  # type: ignore[attr-defined]
    return _echo_tenant


@pytest.fixture
def strict_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LIA_CELERY_TENANT_STRICT", "true")
    yield


@pytest.fixture
def legacy_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LIA_CELERY_TENANT_STRICT", "false")
    yield


# ---------------------------------------------------------------------------
# 1 + 2 — Producer-side, strict.
# ---------------------------------------------------------------------------
def test_apply_async_strict_missing_company_id_raises(eager_task, strict_mode):
    with pytest.raises(MissingTenantContextError) as exc_info:
        eager_task.apply_async(args=("hello",), kwargs={})
    details = exc_info.value.details
    assert details["task"] == "tests._t1145.echo_tenant"
    assert details["tenant_source"] == "celery.apply_async"


def test_apply_async_strict_invalid_company_id_raises(eager_task, strict_mode):
    with pytest.raises(InvalidCompanyIdError):
        eager_task.apply_async(args=("hello", "default"), kwargs={})


def test_apply_async_strict_invalid_kwarg_raises(eager_task, strict_mode):
    with pytest.raises(InvalidCompanyIdError):
        eager_task.apply_async(
            args=("hello",), kwargs={"company_id": "default"}
        )


# ---------------------------------------------------------------------------
# 3 — Producer-side, legacy retrocompat — no raise, metric emitted.
# ---------------------------------------------------------------------------
def test_apply_async_legacy_missing_warns_but_enqueues(
    eager_task, legacy_mode, caplog
):
    with patch(
        "lia_config.celery_app.LIATask.apply_async", autospec=True
    ) as parent:
        parent.return_value = "stub-async-result"
        with caplog.at_level("WARNING"):
            result = eager_task.apply_async(args=("hello",), kwargs={})
        assert result == "stub-async-result"
        assert parent.called
    assert any(
        "TenantAwareTask" in rec.message and "outcome=missing" in rec.message
        for rec in caplog.records
    )


# ---------------------------------------------------------------------------
# 4 — Worker-side ContextVar lifecycle.
# ---------------------------------------------------------------------------
def test_worker_eager_call_sets_and_resets_context_var(eager_task):
    assert get_celery_company_id() == ""

    result = eager_task(payload="ping", company_id=CANONICAL_UUID)
    assert result["company_id_seen"] == CANONICAL_UUID
    assert eager_task._captured["company_id"] == CANONICAL_UUID

    # ContextVar reset after return.
    assert get_celery_company_id() == ""


def test_worker_production_lifecycle_hooks_set_and_reset_context_var(eager_task):
    """Production worker path: before_start → __call__ (no re-entry) → after_return."""
    assert get_celery_company_id() == ""

    eager_task.before_start("task-id-1145", ("ping", CANONICAL_UUID), {})
    # ContextVar must be set after before_start so DB sessions opened by the
    # task body inherit the tenant via the global session listener.
    assert get_celery_company_id() == CANONICAL_UUID

    # The body running through __call__ must NOT re-enter the context.
    result = eager_task(payload="ping", company_id=CANONICAL_UUID)
    assert result["company_id_seen"] == CANONICAL_UUID
    # Still set — only after_return resets it in the production path.
    assert get_celery_company_id() == CANONICAL_UUID

    eager_task.after_return(
        "SUCCESS", result, "task-id-1145", ("ping", CANONICAL_UUID), {}, None
    )
    assert get_celery_company_id() == ""


def test_worker_resets_context_var_even_on_exception():
    captured: dict = {}

    @celery_app.task(
        name="tests._t1145.boom_tenant",
        bind=True,
        base=TenantAwareTask,
    )
    def _boom(self, company_id: str) -> dict:
        captured["company_id"] = get_celery_company_id()
        raise RuntimeError("simulated failure")

    with pytest.raises(RuntimeError, match="simulated failure"):
        _boom(company_id=CANONICAL_UUID)

    assert captured["company_id"] == CANONICAL_UUID
    # ContextVar reset even though the body raised.
    assert get_celery_company_id() == ""


def test_worker_normalizes_company_id_via_company_id_parse():
    captured: dict = {}

    @celery_app.task(
        name="tests._t1145.uppercase_uuid",
        bind=True,
        base=TenantAwareTask,
    )
    def _norm(self, company_id: str) -> dict:
        captured["seen"] = get_celery_company_id()
        return {}

    upper = CANONICAL_UUID.upper()
    _norm(company_id=upper)
    # CompanyId.parse lower-cases UUIDs canonically.
    assert captured["seen"] == CANONICAL_UUID


# ---------------------------------------------------------------------------
# 5 — Sub-service fallback via ContextVar.
# ---------------------------------------------------------------------------
def test_resolve_tenant_snippet_for_non_react_reads_context_var(monkeypatch):
    """The legacy helper must inherit ``company_id`` from the worker
    ContextVar when its explicit ``company_id_raw`` arg is None.
    """
    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")
    from app.shared.agents.tenant_aware_agent import (
        resolve_tenant_snippet_for_non_react,
    )

    tokens = set_celery_company_id_context(CANONICAL_UUID)
    try:
        with pytest.raises(MissingTenantContextError) as exc_info:
            resolve_tenant_snippet_for_non_react(
                ctx={}, agent_name="t1145_helper"
            )
        details = exc_info.value.details
        # The ContextVar value propagated to the error details.
        assert CANONICAL_UUID in details["company_id_raw"]
    finally:
        reset_celery_company_id_context(tokens)
    assert get_celery_company_id() == ""


# ---------------------------------------------------------------------------
# 6 — apply_async with VALID company_id passes through.
# ---------------------------------------------------------------------------
def test_apply_async_valid_company_id_passes_through(eager_task, strict_mode):
    with patch(
        "lia_config.celery_app.LIATask.apply_async", autospec=True
    ) as parent:
        parent.return_value = "stub-async-result"
        result = eager_task.apply_async(
            args=("hello", CANONICAL_UUID), kwargs={}
        )
        assert result == "stub-async-result"
        assert parent.called

    fresh_uuid = str(uuid4())
    with patch(
        "lia_config.celery_app.LIATask.apply_async", autospec=True
    ) as parent:
        parent.return_value = "stub-async-result"
        eager_task.apply_async(
            args=("hello",), kwargs={"company_id": fresh_uuid}
        )
        assert parent.called


# ---------------------------------------------------------------------------
# 7 — DB session enforcement (RLS). Verifies the global after_begin listener
# binds ``app.company_id`` on EVERY session opened during a task — including
# the raw ``AsyncSessionLocal()`` path used by legacy code, not just the
# opt-in :func:`tenant_aware_session` sugar.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    not (os.getenv("LIA_CELERY_TEST_DB_URL") or os.getenv("DATABASE_URL")),
    reason="no DB URL configured for RLS session-binding test",
)
def test_worker_db_session_binds_app_company_id():
    """Inside the task body, ``current_setting('app.company_id', true)``
    must return the company_id we enqueued the task with — proving the
    global ``after_begin`` listener wired in :mod:`app.jobs.tenant_aware_task`
    bound the RLS context, regardless of which session helper the task body
    chose to use.
    """
    import sqlalchemy as sa
    from app.core.database import AsyncSessionLocal

    captured: dict = {}

    @celery_app.task(
        name="tests._t1145.db_echo",
        bind=True,
        base=TenantAwareTask,
    )
    def _db_echo(self, company_id: str) -> dict:
        async def _inner():
            # Raw session — exactly the path legacy task bodies use.
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    row = await session.execute(
                        sa.text(
                            "SELECT current_setting('app.company_id', true)"
                        )
                    )
                    captured["app_company_id"] = row.scalar()
                    role = await session.execute(
                        sa.text("SELECT current_user")
                    )
                    captured["role"] = role.scalar()
            return captured

        return asyncio.get_event_loop().run_until_complete(_inner())

    _db_echo(company_id=CANONICAL_UUID)
    assert captured.get("app_company_id") == CANONICAL_UUID, (
        f"RLS binding failed: app.company_id={captured.get('app_company_id')!r}"
    )
    assert captured.get("role") == "lia_app", (
        f"SET LOCAL ROLE lia_app failed: current_user={captured.get('role')!r}"
    )
