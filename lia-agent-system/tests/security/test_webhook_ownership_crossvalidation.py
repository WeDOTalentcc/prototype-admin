"""
Red-team — Multi-tenant Ownership of Inbound Webhooks (Task #1146).

Covers 4 attack scenarios × 6 providers = 24 tests against
``app.shared.security.webhook_ownership.verify_webhook_owner``:

    (a) correct per-tenant secret + correct payload   → returns CompanyId
    (b) signature signed with tenant B's secret while
        declared_company_id = tenant A                 → HTTP 403 signature_invalid
    (c) declared_company_id is invalid / unknown      → HTTP 403 unknown_tenant
    (d) candidate_id belongs to a different tenant    → HTTP 403 owner_mismatch

The helper is exercised in isolation: the DB-backed secret lookup,
ownership lookup, and audit emitter are injected as awaitables so the
tests don't need Postgres. Audit emissions are captured into a list so
each scenario asserts the canonical ``webhook_ownership_verified`` row
landed with the right ``decision``.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import uuid

import pytest

from app.shared.security.webhook_ownership import (
    SUPPORTED_PROVIDERS,
    WebhookOwnershipAudit,
    WebhookOwnershipError,
    verify_webhook_owner,
)

# ── Test fixtures (deterministic UUID v4 tenants + secrets) ──────────────────

TENANT_A = "11111111-1111-4111-a111-111111111111"
TENANT_B = "22222222-2222-4222-a222-222222222222"
SECRET_A = "tenant-a-secret"
SECRET_B = "tenant-b-secret"
BODY = b'{"event":"call_completed","payload":1}'
CANDIDATE_OK = str(uuid.uuid4())
CANDIDATE_OTHER = str(uuid.uuid4())

PROVIDERS = sorted(SUPPORTED_PROVIDERS)


def _sign(provider: str, secret: str, body: bytes) -> str:
    """Mirror the helper's per-provider signing scheme."""
    if provider in {"twilio", "whatsapp"}:
        digest = hmac.new(secret.encode(), body, hashlib.sha1).digest()
        return base64.b64encode(digest).decode()
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _secret_lookup_factory(secret_by_tenant: dict[str, str]):
    async def _lookup(provider: str, company_id: str) -> str | None:
        return secret_by_tenant.get(company_id)

    return _lookup


def _ownership_lookup_factory(owned_candidates: dict[str, set[str]]):
    async def _lookup(
        company_id: str,
        candidate_id: str | None,
        job_id: str | None,
        session_id: str | None,
    ) -> bool:
        if candidate_id is None:
            return True
        return candidate_id in owned_candidates.get(company_id, set())

    return _lookup


@pytest.fixture
def captured_audits():
    records: list[WebhookOwnershipAudit] = []

    async def _audit(record: WebhookOwnershipAudit) -> None:
        records.append(record)

    return records, _audit


# ── 4 scenarios × 6 providers ────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", PROVIDERS)
async def test_a_correct_secret_and_payload_returns_company(provider, captured_audits):
    records, audit = captured_audits

    company = await verify_webhook_owner(
        provider=provider,
        raw_body=BODY,
        signature=_sign(provider, SECRET_A, BODY),
        declared_company_id=TENANT_A,
        candidate_id=CANDIDATE_OK,
        dual_validate=False,
        tenant_secret_lookup=_secret_lookup_factory({TENANT_A: SECRET_A}),
        ownership_lookup=_ownership_lookup_factory({TENANT_A: {CANDIDATE_OK}}),
        audit_emitter=audit,
    )

    assert company.as_str() == TENANT_A
    assert len(records) == 1
    assert records[0].decision == "ok"
    assert records[0].provider == provider
    assert records[0].company_id == TENANT_A
    assert records[0].secret_source == "tenant"


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", PROVIDERS)
async def test_b_secret_from_other_tenant_is_rejected(provider, captured_audits):
    """Attacker signs payload with tenant B's secret but declares tenant A."""
    records, audit = captured_audits

    with pytest.raises(WebhookOwnershipError) as exc:
        await verify_webhook_owner(
            provider=provider,
            raw_body=BODY,
            signature=_sign(provider, SECRET_B, BODY),
            declared_company_id=TENANT_A,
            candidate_id=CANDIDATE_OK,
            dual_validate=False,
            tenant_secret_lookup=_secret_lookup_factory(
                {TENANT_A: SECRET_A, TENANT_B: SECRET_B}
            ),
            ownership_lookup=_ownership_lookup_factory({TENANT_A: {CANDIDATE_OK}}),
            audit_emitter=audit,
        )

    assert exc.value.status_code == 403
    assert exc.value.outcome == "signature_invalid"
    assert len(records) == 1
    assert records[0].decision == "signature_invalid"
    assert records[0].company_id == TENANT_A


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", PROVIDERS)
async def test_c_invalid_declared_company_id_is_rejected(provider, captured_audits):
    """``X-Company-ID``-style override carrying a reserved/empty literal."""
    records, audit = captured_audits

    with pytest.raises(WebhookOwnershipError) as exc:
        await verify_webhook_owner(
            provider=provider,
            raw_body=BODY,
            signature=_sign(provider, SECRET_A, BODY),
            declared_company_id="default",  # reserved literal — must be rejected
            candidate_id=CANDIDATE_OK,
            dual_validate=False,
            tenant_secret_lookup=_secret_lookup_factory({TENANT_A: SECRET_A}),
            ownership_lookup=_ownership_lookup_factory({TENANT_A: {CANDIDATE_OK}}),
            audit_emitter=audit,
        )

    assert exc.value.status_code == 403
    assert exc.value.outcome == "unknown_tenant"
    assert len(records) == 1
    assert records[0].decision == "unknown_tenant"


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", PROVIDERS)
async def test_d_candidate_owned_by_other_tenant_is_rejected(provider, captured_audits):
    """Signature passes; the cited candidate belongs to tenant B."""
    records, audit = captured_audits

    with pytest.raises(WebhookOwnershipError) as exc:
        await verify_webhook_owner(
            provider=provider,
            raw_body=BODY,
            signature=_sign(provider, SECRET_A, BODY),
            declared_company_id=TENANT_A,
            candidate_id=CANDIDATE_OTHER,
            dual_validate=False,
            tenant_secret_lookup=_secret_lookup_factory({TENANT_A: SECRET_A}),
            ownership_lookup=_ownership_lookup_factory(
                {TENANT_B: {CANDIDATE_OTHER}}  # owned by B, not A
            ),
            audit_emitter=audit,
        )

    assert exc.value.status_code == 403
    assert exc.value.outcome == "owner_mismatch"
    assert len(records) == 1
    assert records[0].decision == "owner_mismatch"
    assert records[0].candidate_id == CANDIDATE_OTHER


# ── Sanity: the test matrix really covers 24 cases ───────────────────────────


def test_matrix_coverage_is_24():
    """Sentinel: 4 scenarios × 6 providers = 24 — fails if a provider is dropped."""
    assert len(PROVIDERS) == 6
    assert set(PROVIDERS) == {
        "teams",
        "openmic",
        "merge",
        "twilio",
        "whatsapp",
        "mailgun",
    }


# ── Endpoint-level wiring sanity (Task #1146 — addressing review feedback) ───
#
# These tests don't spin up FastAPI / Postgres — they assert each of the 6
# integrated webhook handlers imports & calls ``verify_webhook_owner`` (i.e.
# the helper is the single authoritative verifier and no legacy global-secret
# pre-check survives ahead of it).


def test_all_six_endpoints_call_verify_webhook_owner():
    """Sentinel: every one of the 6 webhook routes uses the canonical helper."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2] / "app" / "api" / "v1"
    targets = {
        "teams.py": "teams",
        "openmic_webhook.py": "openmic",
        "merge_webhooks.py": "merge",
        "mailgun_webhooks.py": "mailgun",
        "twilio_voice.py": "twilio",
        "whatsapp_webhook.py": "whatsapp",
    }
    for filename, provider in targets.items():
        src = (root / filename).read_text(encoding="utf-8")
        assert "verify_webhook_owner" in src, (
            f"{filename} must call verify_webhook_owner (Task #1146 "
            f"requires single authoritative verifier per webhook)"
        )
        assert f'provider="{provider}"' in src, (
            f"{filename} must invoke verify_webhook_owner with "
            f'provider="{provider}"'
        )


def test_legacy_global_hmac_pre_check_removed_from_three_endpoints():
    """teams/merge/openmic must NOT execute global-secret HMAC before helper.

    These three are the cross-tenant-sensitive endpoints whose payloads carry
    a candidate/job id. The reviewer flagged that a pre-helper global gate
    would short-circuit the per-tenant secret path. This sentinel asserts the
    pre-checks have been removed (or commented as Task #1146 deprecated).
    """
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2] / "app" / "api" / "v1"

    # teams.py: _verify_teams_webhook_signature must not be called inside the
    # webhook endpoint anymore (helper string defined elsewhere is fine).
    teams_src = (root / "teams.py").read_text(encoding="utf-8")
    assert "if not _verify_teams_webhook_signature(raw_body" not in teams_src

    # merge_webhooks.py: verify_merge_signature(body, ...) call removed.
    merge_src = (root / "merge_webhooks.py").read_text(encoding="utf-8")
    assert "if not verify_merge_signature(body" not in merge_src

    # openmic_webhook.py: openmic_service.validate_webhook_signature call removed
    # from the request handler (the import may still exist for backfill scripts).
    openmic_src = (root / "openmic_webhook.py").read_text(encoding="utf-8")
    assert "openmic_service.validate_webhook_signature(" not in openmic_src


@pytest.mark.asyncio
async def test_anonymous_global_fallback_accepts_valid_mailgun_signature():
    """Mailgun/Twilio status callbacks have no tenant in payload — the
    ``allow_anonymous_global`` branch must accept a globally-valid signature
    and audit ``decision='ok_anonymous_global'``."""
    import os

    ts = "1700000000"
    token = "token-xyz"
    payload = f"{ts}{token}".encode("utf-8")
    global_secret = "global-mailgun-key"
    sig = hmac.new(global_secret.encode(), payload, hashlib.sha256).hexdigest()

    records: list[WebhookOwnershipAudit] = []

    async def _audit(rec: WebhookOwnershipAudit) -> None:
        records.append(rec)

    async def _empty_secret(provider: str, company_id: str) -> str | None:
        return None

    os.environ["MAILGUN_WEBHOOK_SIGNING_KEY"] = global_secret
    try:
        result = await verify_webhook_owner(
            provider="mailgun",
            raw_body=b"",
            signature=sig,
            signature_payload=payload,
            declared_company_id=None,
            allow_anonymous_global=True,
            enforce_ownership=False,
            tenant_secret_lookup=_empty_secret,
            audit_emitter=_audit,
        )
    finally:
        os.environ.pop("MAILGUN_WEBHOOK_SIGNING_KEY", None)

    assert result is None
    assert len(records) == 1
    assert records[0].decision == "ok_anonymous_global"
    assert records[0].secret_source == "global"


@pytest.mark.asyncio
async def test_anonymous_global_fallback_rejects_bad_signature():
    """Anonymous fallback path must still 403 on invalid signature."""
    import os

    os.environ["MAILGUN_WEBHOOK_SIGNING_KEY"] = "real-key"
    try:
        with pytest.raises(WebhookOwnershipError) as exc:
            await verify_webhook_owner(
                provider="mailgun",
                raw_body=b"",
                signature="deadbeef",
                signature_payload=b"1700000000token",
                declared_company_id=None,
                allow_anonymous_global=True,
                enforce_ownership=False,
                tenant_secret_lookup=lambda *_a, **_kw: _async_none(),
            )
    finally:
        os.environ.pop("MAILGUN_WEBHOOK_SIGNING_KEY", None)

    assert exc.value.status_code == 403
    assert exc.value.outcome == "signature_invalid"


async def _async_none():
    return None
