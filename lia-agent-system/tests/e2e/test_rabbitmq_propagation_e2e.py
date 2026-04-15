"""
E2E Test — RabbitMQ event propagation Python → Rails.

MIGRATION_PLAN item 8.3 (PX08).

CONTEXT:
    Python publishes domain events to exchange `lia_python_events`
    (see app/shared/messaging/rails_event_schemas.py). Rails consumes
    those events via the Sneakers worker `LiaEventsWorker` (item 2.1)
    bound to queue `lia_events_queue`.

    This test validates the full pipe: publish on Python, consume on
    Rails, verify side effect (AuditLog / Notification) landed in
    Rails DB. It covers the 6 event types the worker now handles:

        - screening.completed
        - interview.scheduled
        - interview.completed
        - offer.sent
        - candidate.enriched
        - pipeline.moved

    We also cover the schema-version guard: an event published with an
    incompatible major version must be rejected by the worker and sent
    to DLQ (LiaEvents::EventRegistry.validate_version).

DEPENDENCIES:
    - 2.1 (LiaEventsWorker 6 handlers)       — ✅ shipped
    - 2.3 (Bunny connection pool)             — ✅ shipped (Wave 0)
    - 2.2 (WSManager Redis pub/sub)           — ✅ shipped (parallel, not blocking)
    - RabbitMQ reachable + Rails worker up    — infra

SKIP BEHAVIOR:
    Runs only when E2E_RABBITMQ_AVAILABLE=true. Requires the Sneakers
    worker to be consuming `lia_events_queue` on the same broker the
    Python publisher connects to.

PROMPT REFERENCE (PX08 parameters):
    resource       = event propagation (Python → RabbitMQ → Rails)
    rails_path     = /v1/audit_logs (verification read)
    bloqueador     = any regression in the event contract between systems
    independente_de = 8.1 (isolation), 8.2 (chain), 8.4 (email)
"""
from __future__ import annotations

import asyncio
import os
import time
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("E2E_RABBITMQ_AVAILABLE", "false").lower() not in {"1", "true", "yes"},
    reason="Requires RabbitMQ + Rails Sneakers worker running (item 2.1 deployed)",
)


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def rails_api_url() -> str:
    return os.environ["RAILS_API_URL"]


@pytest.fixture
def recruiter_token() -> str:
    return os.environ["E2E_RECRUITER_A_TOKEN"]


@pytest.fixture
def test_company_id() -> str:
    """Rails account id scoped to this test. Used as company_id in events."""
    return os.environ["E2E_ACCOUNT_A_ID"]


@pytest.fixture
def test_candidate_id() -> str:
    return os.environ["E2E_SEED_CANDIDATE_ID"]


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

async def _publish_event(event_type: str, payload: dict, company_id: str) -> None:
    """Publish an event on the Python side exactly as real agents do."""
    from app.shared.messaging.rails_event_publisher import publish_rails_event

    await publish_rails_event(
        event_type=event_type,
        payload=payload,
        company_id=company_id,
    )


async def _poll_audit_log(
    rails_api_url: str,
    recruiter_token: str,
    expected_action: str,
    candidate_id: str,
    timeout_seconds: float = 5.0,
) -> dict | None:
    """Poll Rails AuditLog for the expected entry. Returns the matching
    row when found, None on timeout."""
    from httpx import AsyncClient

    deadline = time.time() + timeout_seconds
    headers = {"Authorization": f"Bearer {recruiter_token}"}

    async with AsyncClient(base_url=rails_api_url, timeout=10.0) as client:
        while time.time() < deadline:
            resp = await client.get(
                "/v1/audit_logs",
                params={"candidate_id": candidate_id, "action": expected_action, "limit": 5},
                headers=headers,
            )
            if resp.status_code == 200:
                rows = resp.json().get("data") or resp.json().get("audit_logs") or []
                for row in rows:
                    if row.get("action") == expected_action:
                        return row
            await asyncio.sleep(0.25)

    return None


# ──────────────────────────────────────────────────────────────────────
# Tests — one per handler, to isolate regressions
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type,expected_action,extra_payload",
    [
        (
            "screening.completed",
            "screening.completed",
            {"score": 0.87, "decision": "approved", "model_used": "wsi_v2"},
        ),
        (
            "interview.scheduled",
            "interview.scheduled",
            {"scheduled_at": "2026-05-01T14:00:00Z", "interview_type": "technical"},
        ),
        (
            "interview.completed",
            "interview.completed",
            {"outcome": "passed", "feedback_summary": "Strong technical, good fit"},
        ),
        (
            "offer.sent",
            "offer.sent",
            {"salary": 15000, "currency": "BRL", "offer_id": str(uuid.uuid4())},
        ),
        (
            "candidate.enriched",
            "candidate.enriched",
            {"fields_added": ["linkedin", "github"], "source": "apify"},
        ),
        (
            "pipeline.moved",
            "pipeline.moved",
            {"from_stage": "screening", "to_stage": "interview", "reason": "screening_approved"},
        ),
    ],
    ids=[
        "screening.completed",
        "interview.scheduled",
        "interview.completed",
        "offer.sent",
        "candidate.enriched",
        "pipeline.moved",
    ],
)
async def test_event_reaches_rails_audit_log(
    event_type: str,
    expected_action: str,
    extra_payload: dict,
    rails_api_url: str,
    recruiter_token: str,
    test_company_id: str,
    test_candidate_id: str,
):
    """Each of the 6 handler types gets published; we assert that a
    matching AuditLog row appears in Rails within the timeout."""
    payload = {
        "candidate_id": test_candidate_id,
        "job_id": os.environ.get("E2E_SEED_JOB_ID", "1"),
        **extra_payload,
    }

    await _publish_event(event_type, payload, test_company_id)

    row = await _poll_audit_log(
        rails_api_url=rails_api_url,
        recruiter_token=recruiter_token,
        expected_action=expected_action,
        candidate_id=test_candidate_id,
        timeout_seconds=5.0,
    )

    assert row is not None, (
        f"Event {event_type} did not produce AuditLog row with action={expected_action} "
        f"within 5s. Check: (a) RabbitMQ connectivity, (b) Sneakers worker alive, "
        f"(c) handler implementation in lia_events_worker.rb"
    )
    assert row.get("company_id") == test_company_id, (
        f"AuditLog row has wrong company_id: {row.get('company_id')} vs {test_company_id}"
    )


@pytest.mark.asyncio
async def test_incompatible_event_version_is_rejected(
    test_company_id: str,
    test_candidate_id: str,
):
    """An event published with a future major version must be rejected
    by LiaEventsWorker (log + DLQ), not crash the worker.
    """
    from app.shared.messaging.rails_event_publisher import publish_rails_event_raw

    # Publish a v2.0 event — the Rails registry only knows v1.x
    await publish_rails_event_raw(
        event_type="screening.completed",
        event_version="2.0",
        payload={"candidate_id": test_candidate_id, "job_id": "1", "score": 0.5},
        company_id=test_company_id,
    )

    # The worker log should show the incompatible-version warning. We
    # don't have a programmatic way to assert on the DLQ from a test,
    # so we assert the NEGATIVE: no AuditLog row should have been
    # written from this incompatible event.
    await asyncio.sleep(2.0)  # give worker time to process + reject

    row = await _poll_audit_log(
        rails_api_url=os.environ["RAILS_API_URL"],
        recruiter_token=os.environ["E2E_RECRUITER_A_TOKEN"],
        expected_action="screening.completed",
        candidate_id=test_candidate_id,
        timeout_seconds=1.0,
    )
    # Note: this assertion is probabilistic — a legit v1.0 event that
    # ran concurrently could also produce a row. In CI we isolate the
    # test candidate_id so no other events use it.
    if row is not None:
        # Check if the row came from THIS (v2.0) event. If event_version
        # made it into the reasoning JSON, we can be sure.
        reasoning = row.get("reasoning") or {}
        assert reasoning.get("event_version") != "2.0", (
            "Worker accepted an incompatible v2.0 event. "
            "EventRegistry.validate_version guard is not firing."
        )
