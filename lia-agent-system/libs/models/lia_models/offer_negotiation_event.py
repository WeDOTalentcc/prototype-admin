"""OfferNegotiationEvent — modelo canônico de log de eventos de proposta.

Armazena cada interação significativa no ciclo de vida de uma OfferProposal:
envio, visualização, aceite, recusa, rodadas de negociação, touchpoints do concierge.

FairnessGuard snapshot obrigatório em toda criação (campo fairness_snapshot).
Dados anonimizados em aprendizado: MIN_SAMPLES = 10 (ADR-LGPD-001 Art. 12 §1).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint, Column, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from lia_config.database import Base


VALID_EVENT_TYPES = frozenset({
    "sent", "viewed", "accepted", "declined", "counter_proposed",
    "concierge_touchpoint", "negotiation_round", "approved_by_manager",
    "expired", "cancelled",
})

VALID_ACTORS = frozenset({"candidate", "recruiter", "lia", "manager"})


class OfferNegotiationEvent(Base):
    """Log imutável de eventos no ciclo de vida de uma proposta de oferta.

    Regras de escrita:
    - Nunca atualizar eventos existentes (append-only).
    - `fairness_snapshot` obrigatório (pode ser {"check": "not_applicable"}).
    - `company_id` indexado para isolamento multi-tenant.
    """

    __tablename__ = "offer_negotiation_events"
    __table_args__ = (
        Index("ix_offer_neg_events_offer_id", "offer_id"),
        Index("ix_offer_neg_events_company", "company_id", "created_at"),
        CheckConstraint(
            "event_type IN ("
            "'sent','viewed','accepted','declined','counter_proposed',"
            "'concierge_touchpoint','negotiation_round','approved_by_manager',"
            "'expired','cancelled')",
            name="chk_offer_neg_event_type",
        ),
        CheckConstraint(
            "actor IN ('candidate','recruiter','lia','manager')",
            name="chk_offer_neg_actor",
        ),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("offer_proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id = Column(String(255), nullable=False)
    event_type = Column(String(64), nullable=False)
    round_number = Column(Integer(), nullable=False, default=0)
    actor = Column(String(32), nullable=False)

    salary_proposed = Column(Numeric(12, 2), nullable=True)
    salary_counter = Column(Numeric(12, 2), nullable=True)
    benefits_snapshot = Column(JSONB(), nullable=True, default=dict)
    notes = Column(Text(), nullable=True)
    fairness_snapshot = Column(JSONB(), nullable=True, default=dict)

    created_at = Column(DateTime(), nullable=False, default=datetime.utcnow)
