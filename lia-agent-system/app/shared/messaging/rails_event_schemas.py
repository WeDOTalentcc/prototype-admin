"""
Rails Integration Event Schemas — events published by the fork for Rails to consume.

These events are published to RabbitMQ exchange 'lia_rails_events' (direct).
The Rails ats_api would consume these via Sneakers workers.

Event Flow:
  Fork (FastAPI) → RabbitMQ → Rails (Sneakers worker)

  Example: After LIA completes a screening, it publishes a
  'screening.completed' event. Rails picks it up and updates
  the apply status in the selective_process pipeline.

Schema aligned with Rails models:
  - candidate_id, job_id, apply_id match Rails IDs
  - selective_process_id matches Rails pipeline stage IDs
"""
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

RAILS_EVENT_EXCHANGE = "lia_rails_events"


@dataclass
class BaseRailsEvent:
    """Base event schema for Rails integration.

    Field ordering note: event_type and company_id have defaults here so that
    subclasses can override event_type with a concrete default without violating
    the 'non-default argument follows default argument' rule.  Both fields are
    required in practice — callers must always pass company_id explicitly.
    """
    event_type: str = ""
    company_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    source: str = "lia-agent-system"
    version: str = "1.0"

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScreeningCompletedEvent(BaseRailsEvent):
    """Published when LIA completes a candidate screening."""
    event_type: str = "screening.completed"
    apply_id: int | None = None
    candidate_id: int | None = None
    job_id: int | None = None
    score: float | None = None  # 0.0 - 10.0
    recommendation: str | None = None  # "advance", "hold", "decline"
    reasoning: str | None = None
    bias_flags: list[str] = field(default_factory=list)


@dataclass
class InterviewScheduledEvent(BaseRailsEvent):
    """Published when LIA schedules an interview."""
    event_type: str = "interview.scheduled"
    apply_id: int | None = None
    candidate_id: int | None = None
    job_id: int | None = None
    scheduled_at: str | None = None
    channel: str | None = None  # "whatsapp", "teams", "email"
    interview_type: str | None = None  # "technical", "behavioral", "wsi"


@dataclass
class InterviewCompletedEvent(BaseRailsEvent):
    """Published when LIA completes an interview evaluation."""
    event_type: str = "interview.completed"
    apply_id: int | None = None
    candidate_id: int | None = None
    job_id: int | None = None
    competency_scores: dict[str, float] = field(default_factory=dict)
    overall_score: float | None = None
    report_summary: str | None = None


@dataclass
class OfferSentEvent(BaseRailsEvent):
    """Published when LIA sends an offer to a candidate."""
    event_type: str = "offer.sent"
    apply_id: int | None = None
    candidate_id: int | None = None
    job_id: int | None = None
    salary_offered: float | None = None
    channel: str | None = None


@dataclass
class CandidateEnrichedEvent(BaseRailsEvent):
    """Published when LIA enriches a candidate profile with AI data."""
    event_type: str = "candidate.enriched"
    candidate_id: int | None = None
    lia_score: float | None = None
    skills_match_pct: float | None = None
    cultural_fit: float | None = None
    seniority_detected: str | None = None
    enrichment_source: str | None = None  # "cv_parsing", "linkedin", "screening"


@dataclass
class PipelineMovedEvent(BaseRailsEvent):
    """Published when LIA moves a candidate in the pipeline."""
    event_type: str = "pipeline.moved"
    apply_id: int | None = None
    candidate_id: int | None = None
    job_id: int | None = None
    from_stage: str | None = None
    to_stage: str | None = None
    reason: str | None = None


# Registry of all event types for documentation/validation
EVENT_REGISTRY = {
    "screening.completed": ScreeningCompletedEvent,
    "interview.scheduled": InterviewScheduledEvent,
    "interview.completed": InterviewCompletedEvent,
    "offer.sent": OfferSentEvent,
    "candidate.enriched": CandidateEnrichedEvent,
    "pipeline.moved": PipelineMovedEvent,
}


# ---------------------------------------------------------------------------
# LIA-E03: Event version registry for forward/backward compat
# ---------------------------------------------------------------------------

EVENT_VERSIONS = {
    "screening.completed": "1.0",
    "interview.scheduled": "1.0",
    "interview.completed": "1.0",
    "offer.sent": "1.0",
    "candidate.enriched": "1.0",
    "pipeline.moved": "1.0",
    "agent.execution.completed": "1.0",
    "agent.execution.failed": "1.0",
    "agent.deployment.created": "1.0",
    "agent.deployment.paused": "1.0",
    "agent.approval.requested": "1.0",
    "agent.approval.reviewed": "1.0",
}


def validate_event_version(event_type: str, received_version: str) -> bool:
    """Check if a received event version is compatible with the current schema.

    Simple MAJOR version compat: "1.0" and "1.1" are compatible, "2.0" is not.
    """
    current = EVENT_VERSIONS.get(event_type)
    if not current:
        return False  # Unknown event type
    try:
        current_major = int(current.split(".")[0])
        received_major = int(received_version.split(".")[0])
        return current_major == received_major
    except (ValueError, IndexError):
        return False
