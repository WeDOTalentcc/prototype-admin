"""
Versioned event schemas for WeDo Talent platform.

Sprint E (2026-06-13): formalizes and versions the event schemas
originally in app/shared/messaging/platform_events.py.
Backward compat: app/shared/messaging/platform_events.py re-exports from here.

Version convention:
  "1.0" = initial (this version)
  "1.1" = minor (additive fields, backward compat)
  "2.0" = breaking change (requires consumer migration)
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


class PlatformEvent(BaseModel):
    """Base schema for all inter-API events."""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    company_id: str
    payload: dict[str, Any]
    source_api: str
    version: str = SCHEMA_VERSION
    correlation_id: str | None = None


class JobPublishedEvent(PlatformEvent):
    event_type: str = "vagas.job.published"
    source_api: str = "api-vagas"


class JobClosedEvent(PlatformEvent):
    event_type: str = "vagas.job.closed"
    source_api: str = "api-vagas"


class CandidateMovedEvent(PlatformEvent):
    event_type: str = "funil.candidate.moved"
    source_api: str = "api-funil"


class CompanyConfiguredEvent(PlatformEvent):
    event_type: str = "onboarding.company.configured"
    source_api: str = "api-onboarding"


class ScreeningCompletedEvent(PlatformEvent):
    event_type: str = "screening.wsi.completed"
    source_api: str = "lia-agent-system"


class CandidateAppliedEvent(PlatformEvent):
    event_type: str = "candidate_applied"
    source_api: str = "lia-agent-system"


class StageChangedEvent(PlatformEvent):
    event_type: str = "stage_changed"
    source_api: str = "lia-agent-system"


class OfferSentEvent(PlatformEvent):
    """Emitido quando uma oferta e enviada ao candidato.

    Critico: deve usar outbox pattern para entrega garantida.
    EU AI Act Art.14: aprovacao humana verificada antes deste evento.
    """
    event_type: str = "offer.sent"
    source_api: str = "lia-agent-system"


# ── Registros canonicos ────────────────────────────────────────────────────────

EVENT_TYPES: dict[str, type[PlatformEvent]] = {
    "vagas.job.published":           JobPublishedEvent,
    "vagas.job.closed":              JobClosedEvent,
    "funil.candidate.moved":         CandidateMovedEvent,
    "onboarding.company.configured": CompanyConfiguredEvent,
    "screening.wsi.completed":       ScreeningCompletedEvent,
    "candidate_applied":             CandidateAppliedEvent,
    "stage_changed":                 StageChangedEvent,
    "offer.sent":                    OfferSentEvent,
}

# Eventos que DEVEM usar outbox (entrega garantida)
CRITICAL_EVENT_TYPES: frozenset[str] = frozenset({
    "stage_changed",
    "screening.wsi.completed",
    "offer.sent",
    "candidate_applied",
})
