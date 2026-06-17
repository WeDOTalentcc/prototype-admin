"""lia-events — versioned Pydantic event schemas for WeDo Talent platform."""
from lia_events.schemas import (
    PlatformEvent,
    JobPublishedEvent,
    JobClosedEvent,
    CandidateMovedEvent,
    CandidateAppliedEvent,
    StageChangedEvent,
    ScreeningCompletedEvent,
    CompanyConfiguredEvent,
    OfferSentEvent,
    EVENT_TYPES,
    CRITICAL_EVENT_TYPES,
)

__all__ = [
    "PlatformEvent",
    "JobPublishedEvent",
    "JobClosedEvent",
    "CandidateMovedEvent",
    "CandidateAppliedEvent",
    "StageChangedEvent",
    "ScreeningCompletedEvent",
    "CompanyConfiguredEvent",
    "OfferSentEvent",
    "EVENT_TYPES",
    "CRITICAL_EVENT_TYPES",
]
