"""
E2E Test — Email delivery + template resolution.

MIGRATION_PLAN item 8.4 (PX08).

CONTEXT:
    The communication agent fires email via the Mailgun provider (item 0.7)
    using templates stored in the `recruitment_email_templates` table.
    This suite validates the full path:

        1. Template lookup by company_id + channel=email + template_key
        2. Variable substitution ({{candidate_name}}, {{job_title}}, etc.)
        3. Consent gate check (INV-L02 / item 3.5) — no send without consent
        4. Actual email delivery via Mailgun sandbox
        5. Delivery receipt / message-id captured back in CommunicationHistory

    The Mailgun sandbox accepts mail for whitelisted recipients only, so
    we direct the test to a fixture email address that's pre-whitelisted
    in the sandbox config. In production this test runs against a real
    Mailgun domain with a catch-all inbox that the teardown polls.

DEPENDENCIES:
    - 0.7 (MAILGUN_API_KEY configured)        — ⏳ MANUAL (devops)
    - 3.5 (Consent check in communication)     — ✅ shipped (Wave 1)
    - Recruitment email templates seeded       — fixture

SKIP BEHAVIOR:
    Skipped unless E2E_EMAIL_AVAILABLE=true AND a Mailgun sandbox or
    real key is configured. When MAILGUN_API_KEY is empty, the test
    automatically skips with a clear reason — no fake pass.

PROMPT REFERENCE (PX08 parameters):
    resource       = email send path (template → Mailgun → delivery receipt)
    rails_path     = /v1/communication_history (verification)
    bloqueador     = any regression in consent gate or template engine
    independente_de = 8.1, 8.2, 8.3
"""
from __future__ import annotations

import asyncio
import os
import time
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("E2E_EMAIL_AVAILABLE", "false").lower() not in {"1", "true", "yes"}
    or not os.environ.get("MAILGUN_API_KEY"),
    reason="Requires MAILGUN_API_KEY set + E2E_EMAIL_AVAILABLE=true (item 0.7 deployed)",
)


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def python_api_url() -> str:
    return os.environ.get("PYTHON_API_URL", "http://localhost:8001")


@pytest.fixture
def recruiter_token() -> str:
    return os.environ["E2E_RECRUITER_A_TOKEN"]


@pytest.fixture
def company_id() -> str:
    return os.environ["E2E_ACCOUNT_A_ID"]


@pytest.fixture
def test_inbox_email() -> str:
    """Pre-whitelisted recipient in the Mailgun sandbox."""
    return os.environ.get("E2E_TEST_INBOX_EMAIL", "e2e-test@wedotalent.cc")


@pytest.fixture
def candidate_with_consent() -> str:
    """Candidate seeded with active email consent (INV-L02)."""
    return os.environ["E2E_CANDIDATE_WITH_EMAIL_CONSENT"]


@pytest.fixture
def candidate_without_consent() -> str:
    """Candidate without email consent — send must be blocked."""
    return os.environ["E2E_CANDIDATE_WITHOUT_CONSENT"]


@pytest.fixture
def seed_template_key() -> str:
    """Pre-seeded template like 'screening_invite' that has placeholders."""
    return os.environ.get("E2E_TEMPLATE_KEY", "screening_invite")


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

async def _poll_communication_history(
    python_api_url: str,
    recruiter_token: str,
    correlation_id: str,
    timeout_seconds: float = 15.0,
) -> dict | None:
    """Poll CommunicationHistory for the record with our correlation_id."""
    from httpx import AsyncClient

    deadline = time.time() + timeout_seconds
    headers = {"Authorization": f"Bearer {recruiter_token}"}

    async with AsyncClient(base_url=python_api_url, timeout=10.0) as client:
        while time.time() < deadline:
            resp = await client.get(
                "/api/v1/communication/history",
                params={"correlation_id": correlation_id, "limit": 5},
                headers=headers,
            )
            if resp.status_code == 200:
                rows = resp.json().get("data") or []
                for row in rows:
                    if row.get("correlation_id") == correlation_id:
                        return row
            await asyncio.sleep(0.5)

    return None


# ──────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_email_with_template_delivers_successfully(
    python_api_url: str,
    recruiter_token: str,
    candidate_with_consent: str,
    seed_template_key: str,
    test_inbox_email: str,
):
    """Happy path: render template, pass consent gate, send via Mailgun,
    capture delivery receipt."""
    from httpx import AsyncClient

    correlation_id = f"e2e-email-{uuid.uuid4().hex[:8]}"
    headers = {
        "Authorization": f"Bearer {recruiter_token}",
        "X-Correlation-Id": correlation_id,
    }

    async with AsyncClient(base_url=python_api_url, timeout=30.0) as client:
        resp = await client.post(
            "/api/v1/communication/send-email",
            headers=headers,
            json={
                "candidate_id": candidate_with_consent,
                "template_key": seed_template_key,
                "variables": {
                    "candidate_name": "Ana Souza",
                    "job_title": "Engenheira Backend Python",
                    "interview_link": "https://wedotalent.cc/i/abc123",
                },
                "to_override": test_inbox_email,  # direct to sandbox inbox
            },
        )

    assert resp.status_code in {200, 202}, (
        f"Send failed: {resp.status_code} {resp.text[:300]}"
    )
    body = resp.json()
    assert body.get("message_id"), "Mailgun did not return a message_id"

    # Verify CommunicationHistory was persisted + delivery tracked
    record = await _poll_communication_history(
        python_api_url=python_api_url,
        recruiter_token=recruiter_token,
        correlation_id=correlation_id,
        timeout_seconds=15.0,
    )
    assert record is not None, "CommunicationHistory row not written"
    assert record.get("status") in {"sent", "delivered"}, (
        f"Communication status was {record.get('status')}, expected sent/delivered"
    )
    # Template rendering: the rendered body must have substituted variables
    rendered = record.get("rendered_body", "")
    assert "Ana Souza" in rendered, "Template did not substitute {{candidate_name}}"
    assert "Engenheira Backend Python" in rendered, "Template did not substitute {{job_title}}"
    assert "{{" not in rendered, "Rendered body still contains unsubstituted placeholders"


@pytest.mark.asyncio
async def test_send_without_consent_is_blocked(
    python_api_url: str,
    recruiter_token: str,
    candidate_without_consent: str,
    seed_template_key: str,
    test_inbox_email: str,
):
    """INV-L02: sending to a candidate without email consent must be
    blocked by the ConsentGate (item 3.5), fail-closed."""
    from httpx import AsyncClient

    async with AsyncClient(base_url=python_api_url, timeout=15.0) as client:
        resp = await client.post(
            "/api/v1/communication/send-email",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={
                "candidate_id": candidate_without_consent,
                "template_key": seed_template_key,
                "variables": {"candidate_name": "Test", "job_title": "X"},
                "to_override": test_inbox_email,
            },
        )

    # ConsentGate must return 403 (or 451 Unavailable For Legal Reasons)
    assert resp.status_code in {403, 451}, (
        f"Consent gate allowed send without consent! Got {resp.status_code}. "
        f"This is a LGPD compliance regression (INV-L02, Sprint 3.5)."
    )
    error_body = resp.json()
    error_code = error_body.get("error") or error_body.get("detail", {}).get("error", "")
    assert "consent" in str(error_code).lower() or "lgpd" in str(error_code).lower(), (
        f"Response does not cite consent/lgpd as the reason: {error_body}"
    )


@pytest.mark.asyncio
async def test_template_not_found_returns_422(
    python_api_url: str,
    recruiter_token: str,
    candidate_with_consent: str,
    test_inbox_email: str,
):
    """Unknown template key must 422, not silently fall through to a
    default template or, worse, send empty email."""
    from httpx import AsyncClient

    async with AsyncClient(base_url=python_api_url, timeout=15.0) as client:
        resp = await client.post(
            "/api/v1/communication/send-email",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={
                "candidate_id": candidate_with_consent,
                "template_key": "non_existent_template_xyz",
                "variables": {},
                "to_override": test_inbox_email,
            },
        )

    assert resp.status_code == 422, (
        f"Unknown template did not return 422: got {resp.status_code}. "
        "Template-not-found must be explicit, not silent."
    )


@pytest.mark.asyncio
async def test_missing_variables_returns_422_not_partial_send(
    python_api_url: str,
    recruiter_token: str,
    candidate_with_consent: str,
    seed_template_key: str,
    test_inbox_email: str,
):
    """A template referencing {{job_title}} with job_title missing from
    variables must fail validation, never send a half-rendered email."""
    from httpx import AsyncClient

    async with AsyncClient(base_url=python_api_url, timeout=15.0) as client:
        resp = await client.post(
            "/api/v1/communication/send-email",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={
                "candidate_id": candidate_with_consent,
                "template_key": seed_template_key,
                "variables": {"candidate_name": "Only"},  # job_title missing
                "to_override": test_inbox_email,
            },
        )

    assert resp.status_code == 422, (
        f"Template with missing variables rendered anyway: {resp.status_code}. "
        "Strict variable validation is required."
    )
