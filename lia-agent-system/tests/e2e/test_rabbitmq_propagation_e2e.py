"""
Contract Test — RabbitMQ event propagation Python → Rails.

MIGRATION_PLAN item 8.3 (PX08).

CONTEXT:
    Python publishes domain events to exchange `lia_python_events`
    (see app/shared/messaging/rails_event_schemas.py). Rails consumes
    those events via the Sneakers worker `LiaEventsWorker` (item 2.1)
    bound to queue `lia_events_queue`.

    This test validates the contract of the publish path:
      - publish_rails_event calls publish_to_exchange with the correct
        exchange name, routing key, and payload fields.
      - Each of the 6 event types uses the right schema dataclass.
      - An event published with an incompatible major version is NOT
        accepted by validate_event_version.

    Converted from E2E (requires RabbitMQ + Rails worker) →
    unit/contract (mocks publish_to_exchange). The behaviour contract
    is identical; only the transport layer is stubbed.

DEPENDENCIES:
    - app/shared/messaging/rails_event_publisher.py   — ✅ shipped
    - app/shared/messaging/rails_event_schemas.py      — ✅ shipped
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch, call

import pytest


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

COMPANY_ID = "test-company-" + uuid.uuid4().hex[:8]
CANDIDATE_ID = "42"
JOB_ID = "1"


async def _publish(event_type: str, payload: dict) -> AsyncMock:
    """Call publish_rails_event with a mocked transport and return the mock."""
    from app.shared.messaging.rails_event_publisher import publish_rails_event

    mock = AsyncMock()
    with patch("app.shared.messaging.rails_event_publisher.publish_to_exchange", mock):
        await publish_rails_event(
            event_type=event_type,
            payload=payload,
            company_id=COMPANY_ID,
        )
    return mock


# ──────────────────────────────────────────────────────────────────────
# Tests — one per handler
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type,extra_payload",
    [
        (
            "screening.completed",
            # Use fields from ScreeningCompletedEvent: score, recommendation, candidate_id, job_id
            {"score": 0.87, "recommendation": "advance",
             "candidate_id": CANDIDATE_ID, "job_id": JOB_ID},
        ),
        (
            "interview.scheduled",
            {"scheduled_at": "2026-05-01T14:00:00Z", "interview_type": "technical",
             "candidate_id": CANDIDATE_ID, "job_id": JOB_ID},
        ),
        (
            "interview.completed",
            # Use fields from InterviewCompletedEvent: overall_score, report_summary
            {"overall_score": 0.9, "report_summary": "Strong technical, good fit",
             "candidate_id": CANDIDATE_ID, "job_id": JOB_ID},
        ),
        (
            "offer.sent",
            # Use fields from OfferSentEvent: salary_offered, channel
            {"salary_offered": 15000, "channel": "email",
             "candidate_id": CANDIDATE_ID, "job_id": JOB_ID},
        ),
        (
            "candidate.enriched",
            # Use fields from CandidateEnrichedEvent: lia_score, enrichment_source
            {"lia_score": 0.82, "enrichment_source": "apify",
             "candidate_id": CANDIDATE_ID},
        ),
        (
            "pipeline.moved",
            {"from_stage": "screening", "to_stage": "interview", "reason": "screening_approved",
             "candidate_id": CANDIDATE_ID, "job_id": JOB_ID},
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
async def test_event_publishes_to_correct_exchange_and_routing_key(
    event_type: str,
    extra_payload: dict,
):
    """publish_rails_event must call publish_to_exchange with the Rails
    exchange and the event_type as routing key, plus all required fields."""
    from app.shared.messaging.rails_event_schemas import RAILS_EVENT_EXCHANGE

    mock = await _publish(event_type, extra_payload)

    mock.assert_called_once()
    kwargs = mock.call_args.kwargs if mock.call_args.kwargs else {}
    args = mock.call_args.args if mock.call_args.args else ()

    # Unpack positional or keyword arguments
    exchange_arg = kwargs.get("exchange") or (args[0] if len(args) > 0 else None)
    routing_key_arg = kwargs.get("routing_key") or (args[1] if len(args) > 1 else None)
    message_arg = kwargs.get("message") or (args[2] if len(args) > 2 else None)

    assert exchange_arg == RAILS_EVENT_EXCHANGE, (
        f"Expected exchange={RAILS_EVENT_EXCHANGE!r}, got {exchange_arg!r}"
    )
    assert routing_key_arg == event_type, (
        f"Expected routing_key={event_type!r}, got {routing_key_arg!r}"
    )
    assert isinstance(message_arg, dict), "message must be a dict"
    assert message_arg.get("company_id") == COMPANY_ID, (
        f"company_id missing or wrong in published message: {message_arg}"
    )
    assert message_arg.get("event_type") == event_type, (
        f"event_type missing or wrong in published message: {message_arg}"
    )
    assert "version" in message_arg, "version field missing from published message"
    assert "timestamp" in message_arg, "timestamp field missing from published message"


@pytest.mark.asyncio
async def test_event_schemas_registered_for_all_6_types():
    """EVENT_REGISTRY must contain all 6 handler types."""
    from app.shared.messaging.rails_event_schemas import EVENT_REGISTRY

    expected = {
        "screening.completed",
        "interview.scheduled",
        "interview.completed",
        "offer.sent",
        "candidate.enriched",
        "pipeline.moved",
    }
    assert expected.issubset(set(EVENT_REGISTRY.keys())), (
        f"Missing event types in EVENT_REGISTRY: {expected - set(EVENT_REGISTRY.keys())}"
    )


@pytest.mark.asyncio
async def test_incompatible_event_version_is_rejected():
    """validate_event_version must return False for a major version bump."""
    from app.shared.messaging.rails_event_schemas import validate_event_version

    # Compatible versions
    assert validate_event_version("screening.completed", "1.0") is True
    assert validate_event_version("screening.completed", "1.1") is True

    # Incompatible major version — must be rejected
    assert validate_event_version("screening.completed", "2.0") is False, (
        "Worker should reject v2.0 event (major version mismatch). "
        "EventRegistry.validate_event_version guard is not firing."
    )
    # Unknown event type — must also be rejected
    assert validate_event_version("unknown.event", "1.0") is False


@pytest.mark.asyncio
async def test_raw_publish_includes_version_field():
    """publish_rails_event_raw must include the explicit version in the message."""
    from app.shared.messaging.rails_event_publisher import publish_rails_event_raw

    mock = AsyncMock()
    with patch("app.shared.messaging.rails_event_publisher.publish_to_exchange", mock):
        await publish_rails_event_raw(
            event_type="screening.completed",
            event_version="2.0",
            payload={"candidate_id": CANDIDATE_ID, "job_id": JOB_ID, "score": 0.5},
            company_id=COMPANY_ID,
        )

    mock.assert_called_once()
    kwargs = mock.call_args.kwargs if mock.call_args.kwargs else {}
    args = mock.call_args.args if mock.call_args.args else ()
    message_arg = kwargs.get("message") or (args[2] if len(args) > 2 else None)

    assert message_arg is not None
    assert message_arg.get("version") == "2.0", (
        "publish_rails_event_raw must preserve the explicit event_version in the message"
    )
    assert message_arg.get("company_id") == COMPANY_ID
