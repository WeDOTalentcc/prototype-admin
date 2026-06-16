"""
TenantAwareTask — canonical Celery base for tenant propagation.

Task #1145 (Multi-tenant Ownership — Celery tenant propagation).

Why this exists
===============
Celery workers historically ran the task body in a process whose DB session
opens with the default Postgres role (``postgres`` superuser), so the RLS
policies installed in migration ``068_rls_deny_by_default`` (103 tables) were
silently **bypassed** for every async job — even though the request that
enqueued the job had a perfectly valid JWT.

This base class makes it impossible to enqueue a tenant-bound job without a
valid ``company_id`` AND guarantees the DB session inside the worker runs as
``lia_app`` with ``app.company_id`` set — i.e., the same RLS contract the
HTTP layer already enforces via :func:`lia_config.database.get_db`.

How enforcement works
---------------------
* Producer side — :meth:`TenantAwareTask.apply_async` validates ``company_id``
  via :class:`CompanyId.parse` BEFORE the job is enqueued. In strict mode,
  missing/invalid raises; in legacy retrocompat mode (7d window per T-1129
  D2/R4), warns + emits a Prometheus metric.
* Worker side — Celery calls :meth:`before_start` BEFORE the task body and
  :meth:`after_return` AFTER it. These set/reset the worker ContextVar and
  mirror to the HTTP middleware ContextVar. :meth:`__call__` is also wrapped
  for eager-mode parity (unit tests, ``task.apply()``).
* DB-session side — a single canonical SQLAlchemy ``after_begin`` listener
  is installed on the global ``Session`` class. It runs ``SET LOCAL ROLE
  lia_app`` + ``SELECT set_config('app.company_id', :cid, true)`` on **every
  transaction** opened while the worker ContextVar is set. That closes the
  RLS bypass globally: it does not matter whether the task body uses
  :func:`tenant_aware_session`, the raw ``AsyncSessionLocal()``, or any
  legacy ``async_session_factory()`` callsite — RLS is enforced.

Modes
-----
* ``LIA_CELERY_TENANT_STRICT=true`` — strict: ``apply_async`` without a
  valid ``company_id`` raises :class:`MissingTenantContextError` /
  :class:`InvalidCompanyIdError` **before** the job hits the broker.
* default (legacy retrocompat) — warn + emit
  ``lia_celery_task_tenant_outcome_total{outcome=missing|invalid}`` metric,
  enqueue continues. Stays default for ~7d (T-1129 D2/R4) to drain the
  legacy queue, then ops flips strict on in production.

See also
--------
* ``app/shared/value_objects/company_id.py`` — canonical parser (T-A).
* ``app/middleware/auth_enforcement.py`` — HTTP-side ContextVar.
* ``lia-agent-system/libs/config/lia_config/database.py`` — RLS wire-up.
* ``.local/tasks/task-1145.md``
* ``.local/tasks/T-1129-multi-tenant-ownership-plan.md`` §S4
"""
from __future__ import annotations

import inspect
import logging
import os
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, AsyncIterator

import sqlalchemy as sa
from sqlalchemy import event as _sa_event
from sqlalchemy.orm import Session as _SyncSession

from app.shared.exceptions.tenant_errors import (
    InvalidCompanyIdError,
    MissingTenantContextError,
)
from app.shared.value_objects.company_id import CompanyId
from lia_config.celery_app import LIATask

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# ContextVar — worker-local tenant for the current task execution.
# ----------------------------------------------------------------------
# Sub-services (e.g. ``resolve_tenant_snippet_for_non_react``) read this when
# their explicit ``company_id_raw`` argument is None / empty, so legacy code
# invoked from inside a task automatically inherits the tenant.
_celery_company_id: ContextVar[str] = ContextVar(
    "_celery_company_id", default=""
)


# ----------------------------------------------------------------------
# Strict-mode flag — distinct from LIA_AGENT_TENANT_STRICT.
# ----------------------------------------------------------------------
_STRICT_TRUTHY = frozenset({"1", "true", "yes", "on"})
_STRICT_FALSY = frozenset({"0", "false", "no", "off"})


def is_celery_tenant_strict_mode() -> bool:
    """Resolve ``LIA_CELERY_TENANT_STRICT`` at runtime.

    Default is **off** for the 7-day retrocompat window. Flip to ``true`` once
    the legacy queue has drained and the
    ``lia_celery_task_tenant_outcome_total{outcome=missing}`` rate falls to 0.
    """
    raw = os.getenv("LIA_CELERY_TENANT_STRICT", "").strip().lower()
    if raw in _STRICT_TRUTHY:
        return True
    if raw in _STRICT_FALSY:
        return False
    return False


# ----------------------------------------------------------------------
# Public ContextVar accessors.
# ----------------------------------------------------------------------
def get_celery_company_id() -> str:
    """Return the tenant ContextVar set by the active Celery task, or ``""``."""
    return _celery_company_id.get("")


def set_celery_company_id_context(company_id: str):
    """Set the tenant ContextVar for the current task execution.

    Mirrors the value into ``app.middleware.auth_enforcement._current_company_id``
    too, because :func:`lia_config.database.get_db` reads the latter to inject
    RLS — so any FastAPI-style session opened inside the task body still
    benefits from the same contract.

    Returns an opaque token pair, passable back to
    :func:`reset_celery_company_id_context`.
    """
    cid = str(company_id or "")
    token = _celery_company_id.set(cid)
    mw_token = None
    try:
        from app.middleware.auth_enforcement import (
            _current_company_id as _mw_var,
        )

        mw_token = _mw_var.set(cid)
    except Exception:  # pragma: no cover — defense-in-depth
        mw_token = None
    return (token, mw_token)


def reset_celery_company_id_context(tokens) -> None:
    """Reverse :func:`set_celery_company_id_context`. Safe to call twice."""
    if tokens is None:
        return
    token, mw_token = tokens
    try:
        _celery_company_id.reset(token)
    except (LookupError, ValueError):  # pragma: no cover
        pass
    if mw_token is not None:
        try:
            from app.middleware.auth_enforcement import (
                _current_company_id as _mw_var,
            )

            _mw_var.reset(mw_token)
        except (LookupError, ValueError, Exception):  # pragma: no cover
            pass


# ----------------------------------------------------------------------
# Prometheus counter.
# ----------------------------------------------------------------------
try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter

    _METRIC_NAME = "lia_celery_task_tenant_outcome_total"
    _existing = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(
        _METRIC_NAME
    )
    if _existing is not None:
        _OUTCOME_COUNTER = _existing
    else:
        _OUTCOME_COUNTER = _PromCounter(
            _METRIC_NAME,
            "TenantAwareTask outcomes (Task #1145).",
            labelnames=("task", "outcome"),
        )
except Exception:  # pragma: no cover — fail-open if prometheus is missing
    _OUTCOME_COUNTER = None


def _emit(task: str, outcome: str) -> None:
    if _OUTCOME_COUNTER is None:
        return
    try:
        _OUTCOME_COUNTER.labels(task=task, outcome=outcome).inc()
    except Exception:  # pragma: no cover
        pass


# ----------------------------------------------------------------------
# Global session listener — RLS enforcement on EVERY transaction opened
# while a Celery TenantAwareTask is executing.
# ----------------------------------------------------------------------
# Single canonical hook. Fires for both sync sessions and the inner sync
# session inside SQLAlchemy AsyncSession. Gated by the ContextVar so the
# HTTP path (which already runs its own SET ROLE / set_config inside
# ``get_db``) is untouched: when the request is HTTP-served, the Celery
# ContextVar is empty so this listener short-circuits.
_LISTENER_INSTALLED = False


def _install_session_tenant_listener() -> None:
    global _LISTENER_INSTALLED
    if _LISTENER_INSTALLED:
        return

    @_sa_event.listens_for(_SyncSession, "after_begin")
    def _set_tenant_on_session_begin(session, transaction, connection):  # noqa: ARG001
        cid = _celery_company_id.get("")
        if not cid:
            return
        try:
            connection.execute(sa.text("SET LOCAL ROLE lia_app"))
            connection.execute(
                sa.text("SELECT set_config('app.company_id', :cid, true)"),
                {"cid": cid},
            )
        except Exception as exc:  # pragma: no cover — defense-in-depth
            logger.error(
                "[TenantAwareTask] failed to bind RLS context "
                "(cid=%s) on session begin: %s",
                cid,
                exc,
            )
            raise

    _LISTENER_INSTALLED = True


_install_session_tenant_listener()


# ----------------------------------------------------------------------
# company_id resolution from a (args, kwargs) call payload.
# ----------------------------------------------------------------------
def _resolve_company_id_from_call(
    run_fn, args: tuple, kwargs: dict
) -> Any | None:
    """Return the raw ``company_id`` provided to the task, or ``None``.

    Looks first in ``kwargs['company_id']``; otherwise inspects the run
    function signature for a ``company_id`` parameter and matches it
    positionally against ``args`` (skipping the bound ``self``).
    """
    if "company_id" in kwargs:
        return kwargs.get("company_id")
    if run_fn is None:
        return None
    try:
        sig = inspect.signature(run_fn)
    except (TypeError, ValueError):
        return None
    params = [p for p in sig.parameters.values() if p.name != "self"]
    for idx, p in enumerate(params):
        if p.name == "company_id":
            if idx < len(args):
                return args[idx]
            return None
    return None


# ----------------------------------------------------------------------
# Base class.
# ----------------------------------------------------------------------
class TenantAwareTask(LIATask):
    """Canonical Celery base for tenant-bound tasks.

    Subclass / use via the ``base=TenantAwareTask`` decorator kwarg::

        @celery_app.task(
            name="agents.wizard.execute",
            bind=True,
            base=TenantAwareTask,
            max_retries=2,
            queue="vagas_normal",
        )
        def execute_wizard_task(self, payload, session_id, company_id, ...):
            ...

    Tasks that legitimately have **no tenant** (cluster-wide cron such as
    ``health.check_dlq_health`` or ``rls.health_check``) may still use
    ``base=TenantAwareTask``; the legacy retrocompat path treats the missing
    ``company_id`` as outcome=``missing`` (metric only, no raise). When strict
    mode is flipped on in production, those tasks should switch back to
    ``LIATask`` or explicitly pass a sentinel.
    """

    abstract = True

    # Attribute used to stash ContextVar tokens between
    # ``before_start`` / ``__call__`` and ``after_return`` so the lifecycle
    # is reentrancy-safe across the (before_start → __call__ → after_return)
    # chain Celery runs in workers and the (__call__) call done in tests.
    _TOKENS_ATTR = "_tenant_aware_tokens"

    # ------------------------------------------------------------------
    # Internals.
    # ------------------------------------------------------------------
    def _task_name(self) -> str:
        return getattr(self, "name", None) or self.__class__.__name__

    def _bound_run(self):
        return getattr(self, "run", None)

    def _enter_tenant_context(self, args: tuple, kwargs: dict):
        """Resolve company_id, set both ContextVars, return tokens or None."""
        raw = _resolve_company_id_from_call(self._bound_run(), args, kwargs)
        if raw in (None, ""):
            return None
        try:
            cid = CompanyId.parse(raw).as_str()
        except InvalidCompanyIdError:
            _emit(self._task_name(), "invalid")
            if is_celery_tenant_strict_mode():
                raise
            logger.warning(
                "[TenantAwareTask] task=%s started with invalid "
                "company_id=%r; running without ContextVar (legacy mode).",
                self._task_name(),
                raw,
            )
            return None
        return set_celery_company_id_context(cid)

    # ------------------------------------------------------------------
    # Producer-side guard.
    # ------------------------------------------------------------------
    def apply_async(self, args=None, kwargs=None, **options):  # type: ignore[override]
        args = tuple(args or ())
        kwargs = dict(kwargs or {})
        task_name = self._task_name()
        raw = _resolve_company_id_from_call(self._bound_run(), args, kwargs)

        outcome = "ok"
        if raw is None or raw == "":
            outcome = "missing"
        else:
            try:
                CompanyId.parse(raw)
            except InvalidCompanyIdError:
                outcome = "invalid"

        _emit(task_name, outcome)
        if outcome != "ok":
            if is_celery_tenant_strict_mode():
                if outcome == "missing":
                    raise MissingTenantContextError(
                        f"Celery task '{task_name}' enqueued without company_id "
                        "(LIA_CELERY_TENANT_STRICT=true)",
                        details={
                            "task": task_name,
                            "tenant_source": "celery.apply_async",
                            "company_id_raw": repr(raw),
                        },
                    )
                raise InvalidCompanyIdError(
                    f"Celery task '{task_name}' enqueued with invalid "
                    f"company_id: {raw!r}",
                    details={
                        "task": task_name,
                        "tenant_source": "celery.apply_async",
                        "company_id_raw": repr(raw),
                    },
                )
            logger.warning(
                "[TenantAwareTask] task=%s enqueued without valid company_id "
                "(outcome=%s, raw=%r). Set LIA_CELERY_TENANT_STRICT=true to "
                "enforce fail-closed.",
                task_name,
                outcome,
                raw,
            )

        return super().apply_async(args=args, kwargs=kwargs, **options)

    # ------------------------------------------------------------------
    # Worker-side lifecycle hooks.
    # ------------------------------------------------------------------
    # Celery's trace pipeline calls these around the task body:
    #
    #   before_start → __call__ (which delegates to run) → after_return
    #
    # In eager mode (``task.apply()``) and unit tests, only ``__call__`` is
    # invoked. We set/reset in both places, guarded by an attribute on the
    # bound task so we never enter the context twice for the same execution.
    def before_start(self, task_id, args, kwargs):  # type: ignore[override]
        try:
            super().before_start(task_id, args, kwargs)
        except AttributeError:
            # Older Celery versions don't define before_start on Task.
            pass
        if getattr(self, self._TOKENS_ATTR, None) is None:
            tokens = self._enter_tenant_context(tuple(args or ()), dict(kwargs or {}))
            setattr(self, self._TOKENS_ATTR, tokens or "noop")

    def after_return(self, status, retval, task_id, args, kwargs, einfo):  # type: ignore[override]
        try:
            tokens = getattr(self, self._TOKENS_ATTR, None)
            if tokens not in (None, "noop"):
                reset_celery_company_id_context(tokens)
        finally:
            try:
                delattr(self, self._TOKENS_ATTR)
            except AttributeError:
                pass
            try:
                super().after_return(status, retval, task_id, args, kwargs, einfo)
            except AttributeError:
                pass

    def __call__(self, *args, **kwargs):  # type: ignore[override]
        """Worker-side entrypoint — also covers eager-mode (``apply``)."""
        # If before_start already ran (production worker path),
        # _TOKENS_ATTR is set and we skip re-entering.
        entered_here = False
        if getattr(self, self._TOKENS_ATTR, None) is None:
            tokens = self._enter_tenant_context(args, kwargs)
            setattr(self, self._TOKENS_ATTR, tokens or "noop")
            entered_here = True
        try:
            return super().__call__(*args, **kwargs)
        finally:
            if entered_here:
                tokens = getattr(self, self._TOKENS_ATTR, None)
                if tokens not in (None, "noop"):
                    reset_celery_company_id_context(tokens)
                try:
                    delattr(self, self._TOKENS_ATTR)
                except AttributeError:
                    pass


# ----------------------------------------------------------------------
# RLS-bound DB session sugar (optional — the global listener above already
# enforces the same contract on every session opened during a task).
# ----------------------------------------------------------------------
@asynccontextmanager
async def tenant_aware_session() -> AsyncIterator[Any]:
    """Open a tenant-bound :class:`AsyncSession` for use in Celery tasks.

    Mostly redundant now that the global ``after_begin`` listener enforces
    RLS on every session opened while the worker ContextVar is set — but
    kept as a clear, opinionated factory for new task bodies (auto-commit
    on exit, auto-rollback on exception, explicit RESET ROLE on close).

    Raises :class:`MissingTenantContextError` when no tenant ContextVar is
    set (caller forgot to use ``base=TenantAwareTask`` or pass ``company_id``).
    """
    from app.core.database import AsyncSessionLocal

    cid = get_celery_company_id()
    if not cid:
        try:
            from app.middleware.auth_enforcement import (
                _current_company_id as _mw_var,
            )

            cid = _mw_var.get("") or ""
        except Exception:  # pragma: no cover
            cid = ""

    if not cid:
        raise MissingTenantContextError(
            "tenant_aware_session() called without tenant ContextVar set — "
            "ensure the task uses base=TenantAwareTask and was enqueued with "
            "a valid company_id.",
            details={"tenant_source": "celery_worker"},
        )

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            try:
                await session.execute(sa.text("RESET ROLE"))
            except Exception:
                pass
            await session.close()


__all__ = [
    "TenantAwareTask",
    "get_celery_company_id",
    "set_celery_company_id_context",
    "reset_celery_company_id_context",
    "is_celery_tenant_strict_mode",
    "tenant_aware_session",
]
