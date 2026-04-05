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
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import json


RAILS_EVENT_EXCHANGE = "lia_rails_events"


@dataclass
class BaseRailsEvent:
    """Base event schema for Rails integration."""
    event_type: str
    company_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "lia-agent-system"
    version: str = "1.0"

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScreeningCompletedEvent(BaseRailsEvent):
    """Published when LIA completes a candidate screening."""
    event_type: str = "screening.completed"
    apply_id: Optional[int] = None
    candidate_id: Optional[int] = None
    job_id: Optional[int] = None
    score: Optional[float] = None  # 0.0 - 10.0
    recommendation: Optional[str] = None  # "advance", "hold", "decline"
    reasoning: Optional[str] = None
    bias_flags: List[str] = field(default_factory=list)


@dataclass
class InterviewScheduledEvent(BaseRailsEvent):
    """Published when LIA schedules an interview."""
    event_type: str = "interview.scheduled"
    apply_id: Optional[int] = None
    candidate_id: Optional[int] = None
    job_id: Optional[int] = None
    scheduled_at: Optional[str] = None
    channel: Optional[str] = None  # "whatsapp", "teams", "email"
    interview_type: Optional[str] = None  # "technical", "behavioral", "wsi"


@dataclass
class InterviewCompletedEvent(BaseRailsEvent):
    """Published when LIA completes an interview evaluation."""
    event_type: str = "interview.completed"
    apply_id: Optional[int] = None
    candidate_id: Optional[int] = None
    job_id: Optional[int] = None
    competency_scores: Dict[str, float] = field(default_factory=dict)
    overall_score: Optional[float] = None
    report_summary: Optional[str] = None


@dataclass
class OfferSentEvent(BaseRailsEvent):
    """Published when LIA sends an offer to a candidate."""
    event_type: str = "offer.sent"
    apply_id: Optional[int] = None
    candidate_id: Optional[int] = None
    job_id: Optional[int] = None
    salary_offered: Optional[float] = None
    channel: Optional[str] = None


@dataclass
class CandidateEnrichedEvent(BaseRailsEvent):
    """Published when LIA enriches a candidate profile with AI data."""
    event_type: str = "candidate.enriched"
    candidate_id: Optional[int] = None
    lia_score: Optional[float] = None
    skills_match_pct: Optional[float] = None
    cultural_fit: Optional[float] = None
    seniority_detected: Optional[str] = None
    enrichment_source: Optional[str] = None  # "cv_parsing", "linkedin", "screening"


@dataclass
class PipelineMovedEvent(BaseRailsEvent):
    """Published when LIA moves a candidate in the pipeline."""
    event_type: str = "pipeline.moved"
    apply_id: Optional[int] = None
    candidate_id: Optional[int] = None
    job_id: Optional[int] = None
    from_stage: Optional[str] = None
    to_stage: Optional[str] = None
    reason: Optional[str] = None


# Registry of all event types for documentation/validation
EVENT_REGISTRY = {
    "screening.completed": ScreeningCompletedEvent,
    "interview.scheduled": InterviewScheduledEvent,
    "interview.completed": InterviewCompletedEvent,
    "offer.sent": OfferSentEvent,
    "candidate.enriched": CandidateEnrichedEvent,
    "pipeline.moved": PipelineMovedEvent,
}
