"""
DomainEvent — immutable event store for SOX-compliant audit replay.

Invariants:
  - NO UPDATE or DELETE operations allowed — append-only
  - sequence_number is auto-incremented per (aggregate_type, aggregate_id)
  - event_data is JSONB — arbitrary structure per event_type
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class DomainEvent(Base):
    __tablename__ = "domain_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type = Column(String(100), nullable=False)  # "candidate" | "job" | "pipeline"
    aggregate_id = Column(String(255), nullable=False)    # UUID of the entity
    event_type = Column(String(100), nullable=False)      # "CandidateMoved" | "JobCreated" | etc.
    event_data = Column(JSONB, nullable=False, default=dict)
    company_id = Column(String(255), nullable=False)
    created_by = Column(String(255), nullable=True)       # user_id or agent_name
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sequence_number = Column(BigInteger, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('aggregate_type', 'aggregate_id', 'sequence_number',
                         name='uq_domain_events_sequence'),
        Index('ix_domain_events_aggregate', 'aggregate_type', 'aggregate_id', 'created_at'),
        Index('ix_domain_events_company', 'company_id', 'created_at'),
        Index('ix_domain_events_event_type', 'event_type'),
    {"extend_existing": True}, )
