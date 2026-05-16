"""
webhook_ownership — canonical per-tenant ownership validator for inbound webhooks.

Why this exists (Task #1146 — Multi-tenant Ownership — Webhook validators)
=========================================================================
The 6 external webhooks ingested by the platform (Teams, OpenMic, Merge,
Twilio, WhatsApp, Mailgun) used to validate HMAC signatures against a single
global secret per provider:

- ``TEAMS_WEBHOOK_SECRET``
- ``OPENMIC_WEBHOOK_SECRET``
- ``MERGE_WEBHOOK_SECRET``
- ``TWILIO_AUTH_TOKEN``
- ``MAILGUN_WEBHOOK_SIGNING_KEY``

Any party that compromises the global secret can forge a payload for ANY
tenant and move candidates, change interview state, or trigger billing.
The companion gap is that nothing was cross-checking the ``candidate_id`` /
``job_id`` / ``session_id`` cited inside the payload against the
``company_id`` declared in the same payload (or in headers like
``X-Company-ID``).

This module closes both gaps:

1. **Per-tenant HMAC secret**, stored encrypted in
   ``company_webhook_secrets`` (migration ``131_company_webhook_secrets``).
   Each ``(company_id, provider)`` row carries its own Fernet-encrypted
   secret. During the 90-day rollout we accept BOTH the per-tenant secret
   AND the global one (``dual_validate=True``); after D+90 the runbook
   ``docs/runbooks/webhook_secret_rotation.md`` flips dual-validate off.
2. **Cross-tenant ownership check** — the helper queries
   ``candidates`` / ``job_vacancies`` (already RLS-protected) and confirms
   the referenced rows belong to the resolved ``company_id``. A mismatch
   is HTTP 403 with audit row ``decision='owner_mismatch'``.
3. **Audit trail** — every call writes one ``audit_logs`` row with
   ``decision_type=GENERATE_FEEDBACK`` and
   ``action='webhook_ownership_verified'`` so SOX/EU AI Act trails carry
   provider, resolved tenant, decision, and PII-masked context.
4. **Prometheus metric** — ``lia_webhook_ownership_outcome_total`` with
   labels ``{provider, outcome}`` for canary alerting.

Usage
=====
::

    from app.shared.security.webhook_ownership import (
        verify_webhook_owner,
        WebhookOwnershipError,
    )

    @router.post("/webhooks/merge")
    async def handle(request: Request):
        raw = await request.body()
        payload = json.loads(raw)
        signature = request.headers.get("X-Merge-Signature")
        try:
            company_id = await verify_webhook_owner(
                provider="merge",
                raw_body=raw,
                signature=signature,
                declared_company_id=payload.get("linked_account", {}).get(
                    "end_user_origin_id"
                ),
                candidate_id=payload.get("data", [{}])[0].get("candidate"),
                job_id=payload.get("data", [{}])[0].get("job"),
            )
        except WebhookOwnershipError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc))

See also
========
- ``alembic/versions/131_company_webhook_secrets.py`` — schema + RLS.
- ``app/shared/security/redis_crypto.py`` — Fernet wrapper (shared key).
- ``docs/runbooks/webhook_secret_rotation.md`` — 90-day rollout runbook.
- ``tests/security/test_webhook_ownership_crossvalidation.py`` — 24-test
  red-team suite (4 scenarios × 6 providers).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from app.shared.exceptions.tenant_errors import InvalidCompanyIdError
from app.shared.value_objects.company_id import CompanyId

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = frozenset(
    {"teams", "openmic", "merge", "twilio", "whatsapp", "mailgun"}
)

# Global-secret env var per provider (legacy / dual-validate fallback).
_GLOBAL_SECRET_ENV: Mapping[str, str] = {
    "teams": "TEAMS_WEBHOOK_SECRET",
    "openmic": "OPENMIC_WEBHOOK_SECRET",
    "merge": "MERGE_WEBHOOK_SECRET",
    "twilio": "TWILIO_AUTH_TOKEN",
    "whatsapp": "TWILIO_AUTH_TOKEN",
    "mailgun": "MAILGUN_WEBHOOK_SIGNING_KEY",
}

# ── Prometheus counter — fail-open if prometheus_client is unavailable ───────
try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter

    _METRIC_NAME = "lia_webhook_ownership_outcome_total"
    if _METRIC_NAME in _PROM_REGISTRY._names_to_collectors:  # type: ignore[attr-defined]
        _OUTCOME_COUNTER = _PROM_REGISTRY._names_to_collectors[_METRIC_NAME]  # type: ignore[attr-defined]
    else:
        _OUTCOME_COUNTER = _PromCounter(
            _METRIC_NAME,
            "Outcome of per-tenant webhook ownership validation.",
            ["provider", "outcome"],
        )
except Exception:  # pragma: no cover — fail-open
    _OUTCOME_COUNTER = None


def _emit(provider: str, outcome: str) -> None:
    if _OUTCOME_COUNTER is None:
        return
    try:
        _OUTCOME_COUNTER.labels(provider=provider, outcome=outcome).inc()
    except Exception:  # pragma: no cover
        pass


# ── Public errors ────────────────────────────────────────────────────────────


class WebhookOwnershipError(Exception):
    """Raised when webhook ownership validation fails.

    Attributes:
        status_code: HTTP status the caller should propagate (default 403).
        outcome: machine-readable outcome label
            (``signature_invalid`` | ``owner_mismatch`` | ``unknown_tenant`` |
            ``provider_unsupported`` | ``missing_secret``).
    """

    def __init__(self, message: str, *, status_code: int = 403, outcome: str = "owner_mismatch"):
        super().__init__(message)
        self.status_code = status_code
        self.outcome = outcome


# ── Provider-specific signature verification ─────────────────────────────────


def _hmac_sha256_hex(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _hmac_sha1_b64(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha1).digest()
    return base64.b64encode(digest).decode("utf-8")


def _verify_signature(provider: str, secret: str, raw_body: bytes, signature: str | None) -> bool:
    """Per-provider HMAC verification with constant-time comparison.

    Twilio uses HMAC-SHA1 + base64 (over URL+sorted-params, normally — here
    we constant-time the body for parity with the test surface); the others
    use HMAC-SHA256 hex.
    """
    if not signature or not secret:
        return False
    sig = signature
    if sig.startswith("sha256="):
        sig = sig[len("sha256=") :]

    if provider in {"twilio", "whatsapp"}:
        expected = _hmac_sha1_b64(secret, raw_body)
    else:
        expected = _hmac_sha256_hex(secret, raw_body)

    return hmac.compare_digest(expected, sig)


# ── Per-tenant secret resolver (DB-backed, dual-validate) ────────────────────


# Lookup signature kept dependency-injectable so tests can override without
# spinning up Postgres. Default impl reads from ``company_webhook_secrets``
# via a tenant-scoped session.
TenantSecretLookup = Callable[[str, str], "Awaitable[str | None]"]  # noqa: F821


async def _default_tenant_secret_lookup(provider: str, company_id: str) -> str | None:
    """Read ``company_webhook_secrets.secret_encrypted`` for (company, provider).

    Decrypts via ``RedisCrypto`` (same Fernet key as ``REDIS_ENCRYPTION_KEY``).
    Returns ``None`` when no active row exists (caller falls back to global
    secret during the 90-day dual-validate window).
    """
    # Task #1146 — open a fresh ``AsyncSessionLocal`` with explicit
    # ``SET ROLE lia_app`` + ``set_tenant_context(company_id)`` so RLS
    # restricts visible rows to the declared tenant. (We CANNOT use
    # ``get_tenant_db`` here — that dependency takes a FastAPI
    # ``Request`` and reads ``request.state.company_id``, which is not
    # available inside the webhook ownership helper.)
    try:
        import sqlalchemy as sa
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal, set_tenant_context
        from app.shared.security.redis_crypto import get_redis_crypto

        async with AsyncSessionLocal() as session:
            try:
                await session.execute(sa.text("SET ROLE lia_app"))
            except Exception as role_err:
                logger.error(
                    "[webhook_ownership] SET ROLE lia_app failed: %s", role_err
                )
                return None
            await set_tenant_context(session, company_id)
            try:
                row = await session.execute(
                    text(
                        """
                        SELECT secret_encrypted
                        FROM company_webhook_secrets
                        WHERE provider = :provider
                          AND status = 'active'
                        LIMIT 1
                        """
                    ),
                    {"provider": provider},
                )
                value = row.scalar_one_or_none()
                if not value:
                    return None
                return get_redis_crypto().decrypt(value)
            finally:
                try:
                    await session.execute(sa.text("RESET ROLE"))
                except Exception:
                    pass
    except Exception as exc:  # pragma: no cover — fail to global fallback
        logger.warning(
            "[webhook_ownership] tenant secret lookup failed provider=%s err=%s",
            provider,
            exc,
        )
        return None


# ── Ownership cross-check (candidate / job belongs to tenant) ────────────────


OwnershipLookup = Callable[[str, str | None, str | None, str | None], "Awaitable[bool]"]  # noqa: F821


async def _default_ownership_lookup(
    company_id: str,
    candidate_id: str | None,
    job_id: str | None,
    session_id: str | None,
) -> bool:
    """Confirm referenced rows belong to ``company_id``.

    Queries ``candidates`` / ``job_vacancies`` through a tenant-scoped
    session — RLS already restricts the rows visible. Returns ``True`` when
    every supplied id is found (i.e. owned by the tenant); ``False`` when
    any id exists in the DB but for a different tenant (RLS hides it ⇒
    ``NOT FOUND`` for THIS tenant).
    """
    if not any([candidate_id, job_id, session_id]):
        return True
    # Task #1146 — same rationale as ``_default_tenant_secret_lookup``:
    # open a fresh tenant-bound session and let RLS hide rows from other
    # tenants. ``NOT FOUND`` ⇒ cross-tenant reference ⇒ owner_mismatch.
    try:
        import sqlalchemy as sa
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal, set_tenant_context

        async with AsyncSessionLocal() as session:
            try:
                await session.execute(sa.text("SET ROLE lia_app"))
            except Exception as role_err:
                logger.error(
                    "[webhook_ownership] SET ROLE lia_app failed in ownership lookup: %s",
                    role_err,
                )
                return False
            await set_tenant_context(session, company_id)
            try:
                if candidate_id:
                    hit = await session.execute(
                        text("SELECT 1 FROM candidates WHERE id = :id LIMIT 1"),
                        {"id": candidate_id},
                    )
                    if hit.scalar_one_or_none() is None:
                        return False
                if job_id:
                    hit = await session.execute(
                        text("SELECT 1 FROM job_vacancies WHERE id = :id LIMIT 1"),
                        {"id": job_id},
                    )
                    if hit.scalar_one_or_none() is None:
                        return False
                # ``session_id`` is provider-specific (Twilio call SID /
                # OpenMic call_id) — out of scope for SQL cross-check
                # until we wire the voice tables here.
                return True
            finally:
                try:
                    await session.execute(sa.text("RESET ROLE"))
                except Exception:
                    pass
    except Exception as exc:  # pragma: no cover — fail-closed
        logger.warning(
            "[webhook_ownership] ownership lookup failed company=%s err=%s",
            company_id,
            exc,
        )
        return False


# ── Audit trail ──────────────────────────────────────────────────────────────


AuditEmitter = Callable[
    ["WebhookOwnershipAudit"], "Awaitable[None]"  # noqa: F821
]


@dataclass(frozen=True, slots=True)
class WebhookOwnershipAudit:
    provider: str
    company_id: str | None
    decision: str  # 'ok' | 'owner_mismatch' | 'signature_invalid' | 'unknown_tenant' | 'missing_secret'
    candidate_id: str | None = None
    job_id: str | None = None
    session_id: str | None = None
    secret_source: str = "unknown"  # 'tenant' | 'global' | 'none'


def _sentry_capture_mismatch(
    *,
    provider: str,
    decision: str,
    company_id: str | None,
    candidate_id: str | None = None,
    job_id: str | None = None,
    session_id: str | None = None,
    error: str | None = None,
) -> None:
    """Explicit Sentry capture with canonical fingerprint for ownership
    mismatches. Wires SEV-1 PagerDuty alerting via the
    ``WEBHOOK_OWNERSHIP_MISMATCH`` fingerprint configured upstream
    (Task #1146 — Sentry → PagerDuty integration).

    Fails silently if Sentry SDK is not installed so the webhook path
    never breaks on telemetry.
    """
    try:
        import sentry_sdk  # type: ignore

        with sentry_sdk.push_scope() as scope:
            scope.fingerprint = ["WEBHOOK_OWNERSHIP_MISMATCH", provider, decision]
            scope.level = "error"
            scope.set_tag("webhook_provider", provider)
            scope.set_tag("ownership_decision", decision)
            scope.set_tag("severity", "sev-1")
            scope.set_tag("alert_route", "pagerduty")
            scope.set_context(
                "webhook_ownership",
                {
                    "provider": provider,
                    "decision": decision,
                    "company_id": company_id or "<anon>",
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "session_id": session_id,
                    "error": error,
                },
            )
            sentry_sdk.capture_message(
                f"WEBHOOK_OWNERSHIP_MISMATCH provider={provider} decision={decision}",
                level="error",
            )
    except Exception:
        pass


# Sentinel "system tenant" UUID used when a webhook arrives that cannot be
# bound to any real tenant (signature_invalid in anonymous fallback,
# unknown_tenant, unresolved_tenant, malformed_payload, timestamp_expired,
# skipped before tenant resolution). Required because ``audit_logs`` has
# FORCE ROW LEVEL SECURITY with WITH CHECK ``company_id = app_current_company_id()``
# (migration 068) — an empty/NULL company_id would fail INSERT, dropping
# exactly the high-risk audit rows the reviewer flagged. The constant is
# the documented system-tenant address from ``replit.md`` §Multi-tenant
# Companies Schema, last byte ``FF`` to disambiguate from the Demo Company
# (``…01``).
SYSTEM_WEBHOOK_TENANT_ID = "00000000-0000-4000-a000-0000000000ff"


async def _default_audit_emitter(record: WebhookOwnershipAudit) -> None:
    """Write the canonical ``webhook_ownership_verified`` audit row.

    Task #1146 — **fail-closed guarantee**: every received webhook MUST
    produce exactly one ``audit_logs`` row. We use a sentinel system
    tenant when ``record.company_id`` is unresolved so the RLS WITH
    CHECK on ``audit_logs`` cannot reject the INSERT, and we re-raise
    on persistence failure so the caller returns 500 (provider retries)
    instead of silently dropping the forensic trail.
    """
    from app.shared.compliance.audit_service import AuditService

    effective_company_id = record.company_id or SYSTEM_WEBHOOK_TENANT_ID
    try:
        await AuditService().log_decision(
            company_id=effective_company_id,
            agent_name=f"webhook:{record.provider}",
            decision_type="webhook_ownership_verified",
            action="webhook_ownership_verified",
            decision=record.decision,
            reasoning=[
                f"provider={record.provider}",
                f"secret_source={record.secret_source}",
                f"declared_company_id={record.company_id or 'none'}",
            ],
            criteria_used=["hmac_signature", "tenant_binding", "ownership_crosscheck"],
            candidate_id=record.candidate_id,
            job_vacancy_id=record.job_id,
            human_review_required=record.decision
            not in ("ok", "ok_anonymous_global", "skipped"),
        )
    except Exception as exc:
        # Fail-CLOSED — surface the forensic gap as a 500 to the
        # provider (which will retry per its webhook contract) rather
        # than swallowing the missing audit row.
        logger.error(
            "[webhook_ownership] AUDIT PERSISTENCE FAILED provider=%s decision=%s "
            "effective_company_id=%s err=%s — re-raising (fail-closed)",
            record.provider,
            record.decision,
            effective_company_id,
            exc,
        )
        raise


async def emit_ownership_audit(
    *,
    provider: str,
    decision: str,
    company_id: str | None,
    candidate_id: str | None = None,
    job_id: str | None = None,
    session_id: str | None = None,
    secret_source: str = "none",
    error: str | None = None,
    audit_emitter: AuditEmitter | None = None,
) -> None:
    """Emit the canonical ``webhook_ownership_verified`` audit row + metric.

    Used by callers that reject a request BEFORE invoking
    ``verify_webhook_owner`` (e.g. Teams JWT-vs-payload tenant mismatch)
    so the canonical audit cardinality is preserved: exactly one audit
    row per inbound webhook request, regardless of outcome.
    """
    _emit(provider, decision)
    audit = audit_emitter or _default_audit_emitter
    await audit(
        WebhookOwnershipAudit(
            provider=provider,
            company_id=company_id,
            decision=decision,
            candidate_id=candidate_id,
            job_id=job_id,
            session_id=session_id,
            secret_source=secret_source,
        )
    )
    # Fire SEV-1 Sentry capture for any non-OK decision so PagerDuty
    # routing picks it up via the WEBHOOK_OWNERSHIP_MISMATCH fingerprint.
    if decision not in ("ok", "skipped"):
        _sentry_capture_mismatch(
            provider=provider,
            decision=decision,
            company_id=company_id,
            candidate_id=candidate_id,
            job_id=job_id,
            session_id=session_id,
            error=error,
        )
        logger.warning(
            "[webhook_ownership] WEBHOOK_OWNERSHIP_MISMATCH provider=%s tenant=%s outcome=%s error=%s",
            provider,
            company_id or "anon",
            decision,
            error,
        )


# ── Public entrypoint ────────────────────────────────────────────────────────


async def verify_webhook_owner(
    *,
    provider: str,
    raw_body: bytes,
    signature: str | None,
    declared_company_id: str | None,
    candidate_id: str | None = None,
    job_id: str | None = None,
    session_id: str | None = None,
    signature_payload: bytes | None = None,
    enforce_ownership: bool = True,
    allow_anonymous_global: bool = False,
    dual_validate: bool = True,
    tenant_secret_lookup: TenantSecretLookup | None = None,
    ownership_lookup: OwnershipLookup | None = None,
    audit_emitter: AuditEmitter | None = None,
) -> CompanyId | None:
    """Validate signature + ownership for an inbound webhook payload.

    Args:
        provider: one of ``SUPPORTED_PROVIDERS``.
        raw_body: exact request body bytes (HMAC input).
        signature: HMAC value from the provider header.
        declared_company_id: tenant id extracted from the payload / header
            (``linked_account.end_user_origin_id`` for Merge,
            ``metadata.company_id`` for OpenMic, ``X-Company-ID`` for Teams).
            May be ``None`` for providers whose payloads don't carry a tenant
            (Mailgun delivery events, Twilio status callbacks) — caller must
            then set ``allow_anonymous_global=True`` so the helper falls back
            to global signature validation without enforcing ownership.
        candidate_id / job_id / session_id: optional ids to cross-check.
        signature_payload: when set, HMAC is computed over THIS byte string
            instead of ``raw_body``. Required for providers whose canonical
            signing input is not the raw body — Twilio (URL + sorted params)
            and Mailgun (``f"{ts}{token}"``).
        enforce_ownership: when ``False``, skips the candidate/job
            cross-tenant check. Used by providers whose payloads only carry
            recipient ids (Mailgun message-id, Twilio CallSid) where the
            tenant is already authoritatively recovered via repo lookup.
        allow_anonymous_global: when ``True`` AND ``declared_company_id`` is
            ``None``, accepts a valid global signature, returns ``None``,
            audits ``decision='ok_anonymous_global'``, and skips ownership.
            Used by Mailgun/Twilio status-callback endpoints where the
            payload doesn't carry tenant context.
        dual_validate: when True (default through D+90), accept either the
            per-tenant secret OR the global env secret. After the runbook
            window closes, pass ``False`` to enforce per-tenant only.
        tenant_secret_lookup / ownership_lookup / audit_emitter: injection
            seams for tests.

    Returns:
        Resolved ``CompanyId`` — or ``None`` in the ``allow_anonymous_global``
        success path (no tenant in payload, global signature valid).

    Raises:
        WebhookOwnershipError: any failure (signature, mismatch, missing
            secret). The caller MUST translate to ``HTTPException``.
    """
    if provider not in SUPPORTED_PROVIDERS:
        _emit(provider, "provider_unsupported")
        raise WebhookOwnershipError(
            f"unsupported provider: {provider!r}",
            status_code=400,
            outcome="provider_unsupported",
        )

    secret_lookup = tenant_secret_lookup or _default_tenant_secret_lookup
    owner_lookup = ownership_lookup or _default_ownership_lookup
    audit = audit_emitter or _default_audit_emitter
    sig_body = signature_payload if signature_payload is not None else raw_body

    # --- Step 1: parse / validate declared company_id --------------------
    if not declared_company_id:
        # Anonymous-tenant fallback for providers (Mailgun delivery events,
        # Twilio status callbacks) whose payloads have no tenant identifier.
        if allow_anonymous_global:
            global_secret = os.getenv(_GLOBAL_SECRET_ENV.get(provider, ""), "")
            if global_secret and _verify_signature(provider, global_secret, sig_body, signature):
                _emit(provider, "ok_anonymous_global")
                await audit(
                    WebhookOwnershipAudit(
                        provider=provider,
                        company_id=None,
                        decision="ok_anonymous_global",
                        candidate_id=candidate_id,
                        job_id=job_id,
                        session_id=session_id,
                        secret_source="global",
                    )
                )
                return None
            _emit(provider, "signature_invalid")
            await audit(
                WebhookOwnershipAudit(
                    provider=provider,
                    company_id=None,
                    decision="signature_invalid",
                    candidate_id=candidate_id,
                    job_id=job_id,
                    session_id=session_id,
                    secret_source="global" if global_secret else "none",
                )
            )
            _sentry_capture_mismatch(
                provider=provider,
                decision="signature_invalid",
                company_id=None,
                candidate_id=candidate_id,
                job_id=job_id,
                session_id=session_id,
                error="anonymous-tenant fallback HMAC verification failed",
            )
            logger.error(
                "[webhook_ownership] WEBHOOK_OWNERSHIP_MISMATCH provider=%s tenant=anon outcome=signature_invalid",
                provider,
            )
            raise WebhookOwnershipError(
                "webhook signature invalid (anonymous-tenant fallback)",
                status_code=403,
                outcome="signature_invalid",
            )

        _emit(provider, "unknown_tenant")
        await audit(
            WebhookOwnershipAudit(
                provider=provider,
                company_id=None,
                decision="unknown_tenant",
                candidate_id=candidate_id,
                job_id=job_id,
                session_id=session_id,
            )
        )
        _sentry_capture_mismatch(
            provider=provider,
            decision="unknown_tenant",
            company_id=None,
            candidate_id=candidate_id,
            job_id=job_id,
            session_id=session_id,
            error="payload missing tenant identifier",
        )
        raise WebhookOwnershipError(
            "webhook payload missing tenant identifier",
            status_code=403,
            outcome="unknown_tenant",
        )

    try:
        company = CompanyId.parse(declared_company_id)
    except InvalidCompanyIdError as exc:
        _emit(provider, "unknown_tenant")
        await audit(
            WebhookOwnershipAudit(
                provider=provider,
                company_id=str(declared_company_id),
                decision="unknown_tenant",
                candidate_id=candidate_id,
                job_id=job_id,
                session_id=session_id,
            )
        )
        _sentry_capture_mismatch(
            provider=provider,
            decision="unknown_tenant",
            company_id=str(declared_company_id),
            candidate_id=candidate_id,
            job_id=job_id,
            session_id=session_id,
            error=f"invalid tenant identifier: {exc}",
        )
        raise WebhookOwnershipError(
            f"invalid tenant identifier in webhook payload: {exc}",
            status_code=403,
            outcome="unknown_tenant",
        ) from exc

    company_str = company.as_str()

    # --- Step 2: resolve secret (per-tenant first, then global fallback) -
    secret_source = "none"
    tenant_secret = await secret_lookup(provider, company_str)
    valid_signature = False

    if tenant_secret:
        secret_source = "tenant"
        valid_signature = _verify_signature(provider, tenant_secret, sig_body, signature)

    if not valid_signature and dual_validate:
        global_secret = os.getenv(_GLOBAL_SECRET_ENV.get(provider, ""), "")
        if global_secret:
            if _verify_signature(provider, global_secret, sig_body, signature):
                valid_signature = True
                # Honest telemetry: when the per-tenant secret was PRESENT but
                # didn't verify (e.g. mid-rotation, drift), surface that fact
                # as a distinct secret_source so the rollout dashboard does
                # NOT silently absorb the failure into a "tenant" verdict.
                if tenant_secret:
                    secret_source = "global_after_tenant_failed"
                else:
                    secret_source = "global"

    if not valid_signature:
        outcome = "signature_invalid" if (tenant_secret or os.getenv(_GLOBAL_SECRET_ENV.get(provider, ""), "")) else "missing_secret"
        _emit(provider, outcome)
        await audit(
            WebhookOwnershipAudit(
                provider=provider,
                company_id=company_str,
                decision=outcome,
                candidate_id=candidate_id,
                job_id=job_id,
                session_id=session_id,
                secret_source=secret_source,
            )
        )
        _sentry_capture_mismatch(
            provider=provider,
            decision=outcome,
            company_id=company_str,
            candidate_id=candidate_id,
            job_id=job_id,
            session_id=session_id,
            error=f"secret_source={secret_source}",
        )
        logger.error(
            "[webhook_ownership] WEBHOOK_OWNERSHIP_MISMATCH provider=%s tenant=%s outcome=%s",
            provider,
            company_str,
            outcome,
        )
        raise WebhookOwnershipError(
            "webhook signature invalid for declared tenant",
            status_code=403,
            outcome=outcome,
        )

    # --- Step 3: cross-tenant ownership of referenced ids ----------------
    if enforce_ownership and any([candidate_id, job_id, session_id]):
        owned = await owner_lookup(company_str, candidate_id, job_id, session_id)
        if not owned:
            _emit(provider, "owner_mismatch")
            await audit(
                WebhookOwnershipAudit(
                    provider=provider,
                    company_id=company_str,
                    decision="owner_mismatch",
                    candidate_id=candidate_id,
                    job_id=job_id,
                    session_id=session_id,
                    secret_source=secret_source,
                )
            )
            _sentry_capture_mismatch(
                provider=provider,
                decision="owner_mismatch",
                company_id=company_str,
                candidate_id=candidate_id,
                job_id=job_id,
                session_id=session_id,
                error="cross-tenant entity reference",
            )
            logger.error(
                "[webhook_ownership] WEBHOOK_OWNERSHIP_MISMATCH provider=%s tenant=%s "
                "candidate=%s job=%s outcome=owner_mismatch",
                provider,
                company_str,
                candidate_id,
                job_id,
            )
            raise WebhookOwnershipError(
                "webhook payload references entities owned by another tenant",
                status_code=403,
                outcome="owner_mismatch",
            )

    # --- Step 4: success audit + metric ----------------------------------
    _emit(provider, "ok")
    await audit(
        WebhookOwnershipAudit(
            provider=provider,
            company_id=company_str,
            decision="ok",
            candidate_id=candidate_id,
            job_id=job_id,
            session_id=session_id,
            secret_source=secret_source,
        )
    )
    return company


__all__ = [
    "SUPPORTED_PROVIDERS",
    "WebhookOwnershipAudit",
    "WebhookOwnershipError",
    "verify_webhook_owner",
]
