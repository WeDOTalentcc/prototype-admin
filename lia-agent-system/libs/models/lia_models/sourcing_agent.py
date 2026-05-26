"""
SQLAlchemy models for SourcingAgent and SourcingAgentSignal.

Apply to: lia-agent-system/app/models/sourcing_agent.py
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class SourcingAgent(Base):
    __tablename__ = "sourcing_agents"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(64), nullable=False, index=True)
    job_id = Column(String(64), nullable=True)
    talent_pool_id = Column(UUID(as_uuid=True), nullable=True)
    agent_template_id = Column(String(255), ForeignKey("agent_templates.id", ondelete="SET NULL"), nullable=True)

    agent_name = Column(String(256), nullable=False)
    status = Column(String(16), nullable=False, default="active")  # active, paused, completed
    calibration_v = Column(Integer, nullable=False, default=0)

    search_strategy = Column(JSONB, nullable=False, default=dict)
    preferences = Column(JSONB, nullable=False, default=dict)
    outreach_config = Column(JSONB, nullable=False, default=dict)

    profiles_viewed = Column(Integer, default=0)
    profiles_approved = Column(Integer, default=0)
    profiles_rejected = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    signals = relationship("SourcingAgentSignal", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SourcingAgent id={self.id} name='{self.agent_name}' status={self.status} v{self.calibration_v}>"


class SourcingAgentSignal(Base):
    __tablename__ = "sourcing_agent_signals"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Sprint 7B-3a Part 1.5 v2 (migration 209): agent_id → NULLABLE.
    # Signals históricos pré-Sprint 7A preservados (calibração). Signals novos
    # (Part 2 full) usam custom_agent_id canonical-only fail-closed.
    agent_id = Column(UUID(as_uuid=True), ForeignKey("sourcing_agents.id", ondelete="CASCADE"), nullable=True)
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

    agent = relationship("SourcingAgent", back_populates="signals")
    custom_agent = relationship("CustomAgent", back_populates="signals")
    assignment = relationship("PoolAgentAssignment", back_populates="signals")

    def __repr__(self):
        return f"<Signal custom_agent={self.custom_agent_id} type={self.signal_type} criteria={self.criteria_extracted}>"
