"""
SQLAlchemy model for SourcingAgentSignal (canonical).

Sprint 8 (2026-05-26): DELETED class SourcingAgent + tabela sourcing_agents.
Migration 211 dropou sourcing_agents + sourcing_agent_signals.agent_id +
custom_agents.legacy_sourcing_agent_id. CustomAgent (category='sourcing') eh
canonical para agentes; SourcingAgentSignal preservado pra signals canonical
(custom_agent_id NOT NULL fail-closed per Sprint 7B-3a Part 1.5 v2).

Apply to: lia-agent-system/app/models/sourcing_agent.py (shim re-export).
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class SourcingAgentSignal(Base):
    __tablename__ = "sourcing_agent_signals"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Sprint 7B-3a Part 1.5 v2: canonical write path. NOT NULL = fail-closed.
    custom_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Sprint 7A migration 202: opcional, liga signal a um assignment talent_pool×agent.
    assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pool_agent_assignments.id", ondelete="SET NULL"),
        nullable=True,
    )
    signal_type = Column(String(16), nullable=False)  # positive, negative
    candidate_id = Column(String(64), nullable=True)
    reason = Column(Text, nullable=False)
    criteria_extracted = Column(ARRAY(String), default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Sprint 8 (migration 211): relationship .agent removida (SourcingAgent class deletada)
    custom_agent = relationship("CustomAgent", back_populates="signals")
    assignment = relationship("PoolAgentAssignment", back_populates="signals")

    def __repr__(self):
        return f"<Signal custom_agent={self.custom_agent_id} type={self.signal_type} criteria={self.criteria_extracted}>"
