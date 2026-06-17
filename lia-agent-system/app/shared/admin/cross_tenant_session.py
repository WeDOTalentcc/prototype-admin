"""cross_tenant_session — audit-only context-manager for legitimate cross-tenant
bypass (Task #1148, ADR-030 v2 §4).

Why this exists
===============
Admin reports (monthly billing, compliance exports, platform analytics) and a
handful of Celery jobs need to read across tenants. Previously there was no
canonical helper for this, so legitimate cross-tenant bypasses:

- did not record a durable audit trail of WHO bypassed RLS, WHEN and WHY;
- did not guarantee ``RESET ROLE`` if the wrapped block raised; and
- did not require a server-side ``superadmin`` check at the endpoint layer.

S2 / S6 of the T-1129 "Multi-tenant Ownership" plan will tighten the
application-layer gates (`require_company_id`, ES tenant filter, …). Before
those land we need ONE canonical audit-emitting bypass — otherwise legitimate
admin flows will start breaking with cryptic ``InsufficientPrivilegeError`` and
nobody will have a paper trail of who bypassed what.

Contract
========
``cross_tenant_session(reason, audit_user_id)`` is an
``@asynccontextmanager`` that:

1. Verifies a previous ``require_superadmin`` dependency ran in the same
   ``contextvars`` scope (request handler / Celery task). Otherwise raises
   ``PermissionError`` BEFORE opening any DB connection.
2. Opens a fresh ``AsyncSessionLocal()`` connection, ``SET ROLE postgres`` so
   queries inside the block bypass RLS, and binds ``app.company_id`` to the
   actor's own tenant so the *audit* INSERTs themselves satisfy the
   ``audit_logs`` RLS policy.
3. Writes a "start" row to ``audit_logs`` (``decision_type='cross_tenant_bypass'``,
   ``action='start'``, ``session_id=audit_user_id``, reason in
   ``criteria_used``) and commits it. This guarantees we always have a record
   even if the wrapped block crashes the process.
4. ``yield`` the session.
5. In a ``finally``: write a matching "end" row (``action='end'``,
   ``score=duration_seconds``), increment the Prometheus counter
   ``lia_cross_tenant_session_bypass_total{reason}``, ``RESET ROLE`` and close
   the session — all under nested ``try/except`` so a failure in the audit /
   role-reset never masks the original exception or leaks a postgres-role
   connection back to the pool.

Usage
=====

.. code-block:: python

    from fastapi import APIRouter, Depends
    from app.shared.admin.cross_tenant_session import (
        cross_tenant_session, require_superadmin,
    )

    router = APIRouter()

    @router.get("/admin/billing/monthly")
    async def monthly_billing(admin = Depends(require_superadmin)):
        async with cross_tenant_session(
            reason="monthly_billing_report",
            audit_user_id=str(admin.id),
        ) as db:
            rows = await db.execute(text("SELECT company_id, ... FROM billing_ledger"))
            return rows.all()

Sentinela offline: ``tests/security/test_cross_tenant_session_audit.py``.
Runbook on-call: ``docs/runbooks/missing_tenant_context.md`` →
``CROSS_TENANT_BYPASS_SPIKE``.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, AsyncIterator

from fastapi import Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

CROSS_TENANT_BYPASS_EVENT_TYPE = "cross_tenant_bypass"


# ---------------------------------------------------------------------------
# Prometheus metric — fail-open if prometheus_client is unavailable.
# ---------------------------------------------------------------------------
try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter

    _METRIC_NAME = "lia_cross_tenant_session_bypass_total"
    if _METRIC_NAME in _PROM_REGISTRY._names_to_collectors:  # type: ignore[attr-defined]
        _BYPASS_COUNTER = _PROM_REGISTRY._names_to_collectors[_METRIC_NAME]  # type: ignore[attr-defined]
    else:
        _BYPASS_COUNTER = _PromCounter(
            _METRIC_NAME,
            "Number of legitimate cross-tenant RLS bypasses opened via cross_tenant_session.",
            ["reason"],
        )
except Exception:  # pragma: no cover — fail-open
    _BYPASS_COUNTER = None


def _emit_metric(reason: str) -> None:
    if _BYPASS_COUNTER is None:
        return
    try:
        _BYPASS_COUNTER.labels(reason=reason).inc()
    except Exception:  # pragma: no cover
        pass


# ---------------------------------------------------------------------------
# Authorization marker — set by ``require_superadmin`` dependency, read by
# ``cross_tenant_session.__aenter__``. ContextVars propagate within the same
# async task (FastAPI request handler, Celery task), so a Depends() that runs
# before the endpoint body sets the flag for the body to see — but a different
# request / handler that did NOT go through the dep gets the default ``None``.
# ---------------------------------------------------------------------------
_SUPERADMIN_CTX: ContextVar[dict[str, Any] | None] = ContextVar(
    "lia_cross_tenant_superadmin_ctx", default=None
)


def _mark_superadmin(*, user_id: str, company_id: str | None) -> None:
    """Test hook + dep helper — marks the current ContextVar scope as authorized."""
    _SUPERADMIN_CTX.set({"user_id": str(user_id), "company_id": str(company_id or "")})


def _clear_superadmin_marker() -> None:
    """Test hook — clear the marker (resets to the default ``None``)."""
    _SUPERADMIN_CTX.set(None)


def _is_superadmin_user(user: Any) -> bool:
    """Truth-table for what counts as a superadmin.

    Accepts either an explicit ``is_superadmin`` attribute (used elsewhere in
    the codebase — ``plan_limits_service``, ``trial_enforcement``) or one of
    the canonical platform-admin role strings used by the Calendar admin
    endpoints. Tenant-scoped ``UserRole.admin`` is NOT enough by design —
    superadmin must be a platform-level grant.
    """
    if getattr(user, "is_superadmin", False) is True:
        return True
    role = getattr(user, "role", None)
    role_str = getattr(role, "value", role)
    return str(role_str or "").lower() in {"super_admin", "superadmin", "platform_admin"}


# Lazy import of ``get_current_active_user`` — declared at module top so the
# Depends() default below has a stable callable even if the auth module is not
# yet importable in minimal test environments.
def _lazy_get_current_active_user():  # pragma: no cover — replaced below
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
    )


try:  # pragma: no cover — best-effort wiring
    from app.auth.dependencies import (
        get_current_active_user as _lazy_get_current_active_user,  # type: ignore[no-redef]
    )
except Exception:
    pass


async def require_superadmin(  # noqa: D401 — FastAPI dep
    current_user: Any = Depends(_lazy_get_current_active_user),
) -> Any:
    """FastAPI dependency: gate an endpoint behind a platform-level superadmin
    check AND register the caller in the ``_SUPERADMIN_CTX`` so the wrapped
    handler can later open a ``cross_tenant_session``.

    Returns the authenticated user object. Raises HTTP 403 on insufficient
    privileges (and never sets the marker in that case).
    """
    if not _is_superadmin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required.",
        )

    _mark_superadmin(
        user_id=str(getattr(current_user, "id", "") or ""),
        company_id=str(getattr(current_user, "company_id", "") or ""),
    )
    return current_user


# ---------------------------------------------------------------------------
# The context manager itself.
# ---------------------------------------------------------------------------
async def _write_audit_row(
    session: AsyncSession,
    *,
    audit_id: str,
    company_id: str,
    audit_user_id: str,
    reason: str,
    action: str,
    duration_seconds: float | None = None,
) -> None:
    """Direct INSERT into ``audit_logs`` (no ORM) to keep this helper free of
    SQLAlchemy session-state quirks under nested cross-tenant role-switches.
    """
    await session.execute(
        text(
            """
            INSERT INTO audit_logs (
                id, company_id, agent_name, decision_type, action,
                decision, reasoning, criteria_used, criteria_ignored,
                human_review_required, session_id, created_at, score
            ) VALUES (
                :id, :company_id, :agent_name, :decision_type, :action,
                :decision, CAST(:reasoning AS JSON), CAST(:criteria_used AS JSON),
                CAST(:criteria_ignored AS JSON),
                FALSE, :session_id, NOW(), :score
            )
            """
        ),
        {
            "id": audit_id,
            "company_id": company_id,
            "agent_name": "cross_tenant_session",
            "decision_type": CROSS_TENANT_BYPASS_EVENT_TYPE,
            "action": action,
            "decision": "bypass",
            "reasoning": '["cross_tenant_bypass:' + action + '"]',
            "criteria_used": '["reason:' + reason.replace('"', "'") + '","actor:' + str(audit_user_id) + '"]',
            "criteria_ignored": "[]",
            "session_id": str(audit_user_id),
            "score": duration_seconds,
        },
    )


@asynccontextmanager
async def cross_tenant_session(
    reason: str,
    audit_user_id: str,
) -> AsyncIterator[AsyncSession]:
    """Open an RLS-bypassing DB session with mandatory audit + role reset.

    Args:
        reason: short snake_case label that lands in Prometheus / audit
            (e.g. ``"monthly_billing_report"``, ``"compliance_export"``).
        audit_user_id: the platform superadmin's user id. Recorded in
            ``audit_logs.session_id`` (the canonical actor-id column per
            Task #366 workaround in ``AuditService``).

    Raises:
        PermissionError: if no ``require_superadmin`` dependency ran in this
            ContextVar scope. The block never opens a DB connection in that
            case.
        ValueError: if ``reason`` / ``audit_user_id`` are empty.
    """
    if not reason or not str(reason).strip():
        raise ValueError("cross_tenant_session: 'reason' is required.")
    if not audit_user_id or not str(audit_user_id).strip():
        raise ValueError("cross_tenant_session: 'audit_user_id' is required.")

    marker = _SUPERADMIN_CTX.get()
    if not marker:
        raise PermissionError(
            "cross_tenant_session: caller is not a verified superadmin. "
            "Apply Depends(require_superadmin) on the endpoint."
        )

    # Anti-spoofing: the caller MUST pass the same actor id that
    # ``require_superadmin`` validated. We refuse to forge audit attribution
    # for an arbitrary user_id supplied by the handler body.
    marker_user_id = str(marker.get("user_id") or "")
    if not marker_user_id or marker_user_id != str(audit_user_id):
        raise PermissionError(
            "cross_tenant_session: audit_user_id does not match the "
            "authenticated superadmin in the request scope (anti-spoofing)."
        )

    # Lazy import — avoids a top-level cycle with app.core.database, which
    # itself imports a lot of the request stack.
    from app.core.database import AsyncSessionLocal

    actor_company_id = str(marker.get("company_id") or "")
    audit_id_start = str(uuid.uuid4())
    audit_id_end = str(uuid.uuid4())
    started_at = time.monotonic()

    session: AsyncSession = AsyncSessionLocal()
    role_switched = False
    try:
        # Bind app.company_id to the actor's own tenant so the audit INSERTs
        # satisfy audit_logs' RLS policy (WITH CHECK (company_id =
        # app_current_company_id())) even before we drop to postgres.
        if actor_company_id:
            try:
                await session.execute(
                    text("SELECT set_config('app.company_id', :cid, true)"),
                    {"cid": actor_company_id},
                )
            except Exception as exc:  # pragma: no cover — best-effort
                logger.warning(
                    "[cross_tenant_session] set_config(app.company_id) failed: %s", exc
                )

        # Persist the "start" audit row first, under the default role, so RLS
        # check on audit_logs is straightforward against the actor's own tenant.
        await _write_audit_row(
            session,
            audit_id=audit_id_start,
            company_id=actor_company_id or str(uuid.UUID(int=0)),
            audit_user_id=audit_user_id,
            reason=reason,
            action="start",
        )
        await session.commit()

        # Now drop to postgres role for the actual cross-tenant work.
        await session.execute(text("SET ROLE postgres"))
        role_switched = True

        logger.warning(
            "[cross_tenant_session] BYPASS_OPENED reason=%s actor=%s actor_company=%s",
            reason,
            audit_user_id,
            actor_company_id or "<unknown>",
        )

        try:
            yield session
        finally:
            duration = time.monotonic() - started_at
            # Reset role FIRST so the "end" audit INSERT goes through under the
            # default app role (matches the "start" row's RLS context).
            if role_switched:
                try:
                    await session.execute(text("RESET ROLE"))
                except Exception as exc:  # pragma: no cover — keep going
                    logger.error(
                        "[cross_tenant_session] RESET ROLE failed: %s", exc
                    )
                role_switched = False

            try:
                # Re-bind tenant guc after RESET ROLE (it survived but be
                # defensive — connection might have been recycled).
                if actor_company_id:
                    await session.execute(
                        text("SELECT set_config('app.company_id', :cid, true)"),
                        {"cid": actor_company_id},
                    )
                await _write_audit_row(
                    session,
                    audit_id=audit_id_end,
                    company_id=actor_company_id or str(uuid.UUID(int=0)),
                    audit_user_id=audit_user_id,
                    reason=reason,
                    action="end",
                    duration_seconds=duration,
                )
                await session.commit()
            except Exception as exc:
                logger.error(
                    "[cross_tenant_session] failed to write 'end' audit row: %s",
                    exc,
                )

            _emit_metric(reason)
    finally:
        # Defense-in-depth: if we yielded before RESET ROLE in the inner finally
        # (e.g. inner finally errored), make sure the connection doesn't go
        # back to the pool stuck on postgres.
        if role_switched:
            try:
                await session.execute(text("RESET ROLE"))
            except Exception as exc:  # pragma: no cover
                logger.error(
                    "[cross_tenant_session] outer RESET ROLE failed: %s", exc
                )
        try:
            await session.close()
        except Exception:  # pragma: no cover
            pass
