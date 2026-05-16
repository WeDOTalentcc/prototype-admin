"""
Tenant Redis Namespace — canonical helper for tenant-namespaced Redis keys.

Task #1144 — Multi-tenant Ownership / Cache Redis tenant-namespaced.

Every Redis key emitted by the backend must embed ``company_id`` so that
two tenants asking the same question (e.g. "criar vaga de backend") never
share a cached response. This module is the single source of truth for:

* ``tenant_namespaced_key(prefix, company_id, suffix)`` — build a canonical
  ``<prefix>:<company_id>:<suffix>`` key, validating ``company_id`` via
  :class:`app.shared.value_objects.company_id.CompanyId` (rejects ``""``,
  ``"default"``, ``"none"``, etc.).
* ``record_namespace_violation(module)`` — increment the Prometheus counter
  ``lia_redis_tenant_namespace_violation_total{module}`` and, in production,
  fail loud with :class:`RuntimeError` (sentinel S9 in the Sealing task
  guarantees zero occurrence).

The helper is intentionally tiny and dependency-light so it can be imported
from cache, queue, rate-limit, session and tracing modules without creating
import cycles.
"""
from __future__ import annotations

import logging
import os
from typing import Final

from app.shared.exceptions.tenant_errors import InvalidCompanyIdError
from app.shared.value_objects.company_id import CompanyId

logger = logging.getLogger(__name__)

_PROD_ENVS: Final[frozenset[str]] = frozenset({"production", "prod"})


def _is_production() -> bool:
    return os.getenv("ENVIRONMENT", "").lower() in _PROD_ENVS


try:  # Prometheus is optional — keep helper usable in tests without it.
    from prometheus_client import Counter

    _VIOLATION_COUNTER: Counter | None = Counter(
        "lia_redis_tenant_namespace_violation_total",
        "Redis keys emitted without a tenant namespace (sentinel S9 must keep this at 0).",
        ["module"],
    )
except Exception:  # pragma: no cover - prometheus_client absent in some envs
    _VIOLATION_COUNTER = None


def normalize_company_id(company_id: str | CompanyId | None) -> str:
    """Validate and return the canonical string form of ``company_id``.

    Raises :class:`InvalidCompanyIdError` for ``None``, ``""``, ``"default"``,
    etc. This is the single gate every Redis-touching module must call before
    composing a key.
    """
    if isinstance(company_id, CompanyId):
        return company_id.as_str()
    return CompanyId.parse(company_id).as_str()


def tenant_namespaced_key(
    prefix: str,
    company_id: str | CompanyId | None,
    suffix: str,
) -> str:
    """Return ``<prefix>:<company_id>:<suffix>`` with validated ``company_id``.

    The output is the only Redis-key shape accepted across the backend after
    Task #1144. Pass ``suffix`` already hashed/encoded as needed by the caller.
    The ``prefix`` may itself contain ``:`` (e.g. ``"lia:session"``); the
    canonical shape places ``company_id`` immediately AFTER the prefix.
    """
    if not prefix:
        raise ValueError("prefix must be non-empty")
    if not suffix:
        raise ValueError("suffix must be non-empty")
    cid = normalize_company_id(company_id)
    key = f"{prefix}:{cid}:{suffix}"
    # Defensive re-check via the central gate. Passing ``company_id`` and
    # ``prefix`` separately avoids ambiguity when ``prefix`` contains ``:``
    # (e.g. ``"lia:session"`` — parts[1] would be ``"session"``, not the cid).
    assert_tenant_namespaced_key(
        key, module=f"tenant_namespaced_key.{prefix}", company_id=cid, prefix=prefix
    )
    return key


def assert_tenant_namespaced_key(
    key: str,
    *,
    module: str,
    company_id: str | CompanyId,
    prefix: str | None = None,
) -> None:
    """Validate that ``key`` is ``<prefix>:<company_id>:<suffix>``.

    Centralised contract enforcement: every Redis key emitted by the backend
    MUST be passed through either :func:`tenant_namespaced_key` (which calls
    this internally) or this assertion directly before the SET/GET/DEL.

    The caller supplies the expected ``company_id`` (and optionally the
    ``prefix``) so the validator works correctly even when ``prefix``
    itself contains ``:`` (e.g. ``"lia:session"``).

    A failure increments
    ``lia_redis_tenant_namespace_violation_total{module=<module>}`` and, in
    production, raises :class:`RuntimeError` via
    :func:`record_namespace_violation`. In dev/test the call is logged at
    CRITICAL so unit tests can observe it.
    """
    try:
        cid = normalize_company_id(company_id)
    except InvalidCompanyIdError:
        record_namespace_violation(module)
        return
    if not key:
        record_namespace_violation(module)
        return
    if prefix is not None:
        expected = f"{prefix}:{cid}:"
        if not key.startswith(expected):
            record_namespace_violation(module)
        return
    # No prefix hint — fall back to substring check (cid must appear as a
    # standalone segment somewhere after the first ``:``).
    if f":{cid}:" not in key and not key.endswith(f":{cid}"):
        record_namespace_violation(module)


def record_namespace_violation(module: str) -> None:
    """Record a Redis key emitted without tenant namespace.

    * Production: increments Prometheus counter AND raises ``RuntimeError`` so
      the caller can never silently leak across tenants.
    * Dev / test: increments counter + emits ``CRITICAL`` log (fail-loud but
      non-blocking, to let sentinel S9 enumerate violations).
    """
    if _VIOLATION_COUNTER is not None:
        try:
            _VIOLATION_COUNTER.labels(module=module).inc()
        except Exception:  # pragma: no cover
            pass
    msg = (
        f"[tenant_redis_namespace] Redis key emitted without company_id by "
        f"module={module!r}. Task #1144 contract violated."
    )
    if _is_production():
        logger.critical(msg)
        raise RuntimeError(msg)
    logger.critical(msg)


__all__ = [
    "normalize_company_id",
    "tenant_namespaced_key",
    "record_namespace_violation",
]
