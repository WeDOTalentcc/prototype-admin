"""
Tenant Demo Fallback Guard (Task #991 / T4).

Canonical defense against the "ID estranho 00000000... aparece como
minha empresa" + "salvou mas não persistiu" bug class. Before T4, two
endpoints in :mod:`app.api.v1.company` silently fell back to the Demo
Company profile (``CompanyProfile.is_default = True``, canonical UUID
``00000000-0000-4000-a000-000000000001``) whenever an authenticated
user had a ``company_id`` but no profile linked to it:

- ``GET  /company/profile`` (line 557 of company.py)
- ``POST /company/onboarding`` (line 186 of company.py)

Symptom on the platform: a real-tenant recruiter would log in, edit
``Minha Empresa`` cards, and the writes would land on the Demo Company
profile — visible to every other tenant that hit the same fallback.
This violates tenant isolation (``threat_model.md`` — Elevation of
Privilege + Information Disclosure) and LGPD Art. 5 V (segurança).

This module centralises:

1. The Demo Company canonical UUID and a predicate to recognise
   legitimate Demo callers (dev-mode user, no auth, or Demo tenant).
2. A Prometheus counter ``lia_tenant_demo_fallback_total{reason}`` that
   tracks every place a fallback *would* have happened. In production
   this counter must stay flat — any increase triggers a Sentry alert.
3. A Sentry capture helper with stable fingerprint
   ``TENANT_DEMO_FALLBACK_PROD`` so on-call gets a single grouped issue
   per drift, not one issue per affected user.

It is the moral sibling of ``app.shared.agents.tenant_aware_agent``
(T-A canary) — same pattern, different layer (HTTP route vs. agent
prompt).
"""
from __future__ import annotations

import logging
import os
import time
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)

# Canonical Demo Company UUID (T-C — see replit.md "Multi-tenant
# Companies Schema"). The slug ``"demo_company"`` was retired in T-C
# but the literal value still appears in the seeded demo *user*
# (``app/auth/dependencies.py:261``) — so callers must accept both.
DEMO_COMPANY_UUID = "00000000-0000-4000-a000-000000000001"
DEMO_COMPANY_SLUG = "demo_company"
_DEMO_COMPANY_VALUES: frozenset[str] = frozenset({DEMO_COMPANY_UUID, DEMO_COMPANY_SLUG})

# Sentry fingerprint — keep in lockstep with the runbook + alerting
# rules. Changing this string silently breaks paging.
SENTRY_FINGERPRINT = "TENANT_DEMO_FALLBACK_PROD"


def is_demo_caller(company_id: Any) -> bool:
    """Return True when the caller is legitimately the Demo tenant.

    Used to decide whether falling back to ``CompanyProfile.is_default``
    is acceptable (Demo user reading Demo data) or a tenant-isolation
    breach (real user reading Demo data).
    """
    if company_id is None:
        return False
    try:
        normalized = str(company_id).strip().lower()
    except Exception:
        return False
    return normalized in _DEMO_COMPANY_VALUES


# ── Prometheus counter ────────────────────────────────────────────────
# Mirrors the ``lia_agent_tenant_context_resolved_total`` pattern from
# tenant_aware_agent.py: optional dep, idempotent registration so
# uvicorn auto-reload does not raise ``ValueError: Duplicated``.
_FALLBACK_COUNTER: Any = None
try:  # pragma: no cover — exercised via integration
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter

    _METRIC_NAME = "lia_tenant_demo_fallback_total"
    _existing = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(_METRIC_NAME)
    if _existing is not None:
        _FALLBACK_COUNTER = _existing
    else:
        _FALLBACK_COUNTER = _PromCounter(
            _METRIC_NAME,
            (
                "Total de quedas no fallback Demo Company por reason "
                "(T4 #991). Em produção esse contador deve ficar plano — "
                "qualquer crescimento indica vazamento entre tenants."
            ),
            labelnames=("reason", "endpoint"),
        )
except Exception:  # pragma: no cover — defensive
    _FALLBACK_COUNTER = None

# In-memory snapshot mirror — exposed via /health/compliance/bypass-status
# alongside the Prometheus counter. Per-process (not authoritative in
# multi-instance prod) but useful for smoke checks and dev.
_LOCAL_SNAPSHOT: dict[str, int] = {}

# T4 #991 — sliding window of event timestamps for the canonical
# ``last_24h_count`` health field. Bounded deque; entries older than
# 24h are evicted lazily on read/write.
_TWENTY_FOUR_HOURS = 24 * 60 * 60
_EVENT_TIMESTAMPS: "deque[float]" = deque(maxlen=10_000)


def _evict_old_events(now: float | None = None) -> None:
    cutoff = (now if now is not None else time.time()) - _TWENTY_FOUR_HOURS
    while _EVENT_TIMESTAMPS and _EVENT_TIMESTAMPS[0] < cutoff:
        _EVENT_TIMESTAMPS.popleft()


def _record_local(reason: str, endpoint: str) -> None:
    key = f"{endpoint}:{reason}"
    _LOCAL_SNAPSHOT[key] = _LOCAL_SNAPSHOT.get(key, 0) + 1
    now = time.time()
    _EVENT_TIMESTAMPS.append(now)
    _evict_old_events(now)


def get_demo_fallback_snapshot() -> dict[str, int]:
    """Return a copy of the per-process counter for /health exposure."""
    return dict(_LOCAL_SNAPSHOT)


def get_last_24h_count() -> int:
    """Number of fallback events in the last 24h (sliding window)."""
    _evict_old_events()
    return len(_EVENT_TIMESTAMPS)


def reset_demo_fallback_snapshot() -> None:
    """Reset used by tests."""
    _LOCAL_SNAPSHOT.clear()
    _EVENT_TIMESTAMPS.clear()


# ── Sentry capture ────────────────────────────────────────────────────
def _capture_sentry(reason: str, endpoint: str, extra: dict[str, Any]) -> None:
    """Capture a Sentry message with stable fingerprint when in prod.

    Dev/staging logs CRITICAL but skips Sentry to avoid noise.
    """
    # T4 #991 — canary capture covers prod + staging (mirrors the T-A
    # ``_prod_like`` env list used by the bypass-status endpoint).
    env = os.getenv("APP_ENV", "development").lower()
    if env not in ("production", "prod", "staging"):
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            # T4 #991 — fingerprint MUST be exactly the canonical
            # constant (single-element list). Appending endpoint/reason
            # would split issues per route and defeat the on-call
            # contract of "one grouped Sentry issue per drift". Endpoint
            # and reason live in tags/extras for filtering instead.
            scope.fingerprint = [SENTRY_FINGERPRINT]
            scope.set_tag("event_key", SENTRY_FINGERPRINT)
            scope.set_tag("endpoint", endpoint)
            scope.set_tag("reason", reason)
            scope.set_extra("runbook", "docs/runbooks/missing_tenant_context.md")
            scope.set_extra("payload", extra)
            sentry_sdk.capture_message(SENTRY_FINGERPRINT, level="error")
    except Exception:  # pragma: no cover — defensive
        pass


def record_demo_fallback(
    *,
    endpoint: str,
    reason: str,
    user_company_id: Any = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Telemetry sink for any place a Demo fallback was prevented.

    Call this BEFORE raising the 404/403, not after, so the counter
    captures the would-be drift even if the response handling errors.

    Args:
        endpoint: Route identifier (e.g. ``"get_company_profile"``).
        reason: Short stable label (e.g. ``"missing_profile"``,
            ``"non_demo_user_targeting_demo"``).
        user_company_id: The caller's company_id — included in the
            Sentry payload, never logged in plain text outside the
            PII-masked logger.
        extra: Additional structured context for Sentry.
    """
    if _FALLBACK_COUNTER is not None:
        try:
            _FALLBACK_COUNTER.labels(reason=reason, endpoint=endpoint).inc()
        except Exception:  # pragma: no cover — defensive
            pass
    _record_local(reason, endpoint)

    payload: dict[str, Any] = {
        "endpoint": endpoint,
        "reason": reason,
        "user_company_id": str(user_company_id) if user_company_id else None,
    }
    if extra:
        payload.update(extra)

    logger.warning(
        "[TENANT_DEMO_FALLBACK] endpoint=%s reason=%s user_company_id=%s",
        endpoint,
        reason,
        user_company_id,
    )
    _capture_sentry(reason, endpoint, payload)
