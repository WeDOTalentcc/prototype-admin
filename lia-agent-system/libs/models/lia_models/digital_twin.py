"""
SQLAlchemy models for DigitalTwin and TwinDecision.

Apply to: lia-agent-system/app/models/digital_twin.py
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid

from lia_config.database import Base


class DigitalTwin(Base):
    __tablename__ = "digital_twins"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(64), nullable=False, index=True)
    twin_name = Column(String(256), nullable=False)
    sme_user_id = Column(String(64), nullable=True)

    specialties = Column(ARRAY(String), default=list)
    description = Column(Text, nullable=True)

    decision_count = Column(Integer, default=0)
    accuracy_pct = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)

    twin_embedding = Column(Vector(768), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    decisions = relationship("TwinDecision", back_populates="twin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DigitalTwin id={self.id} name='{self.twin_name}' decisions={self.decision_count}>"


class TwinDecision(Base):
    __tablename__ = "twin_decisions"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_id = Column(UUID(as_uuid=True), ForeignKey("digital_twins.id", ondelete="CASCADE"), nullable=False)

    decision = Column(String(16), nullable=False)  # approved, rejected, maybe
    reasoning = Column(Text, nullable=False)

    candidate_snapshot = Column(JSONB, nullable=True)
    job_snapshot = Column(JSONB, nullable=True)

    embedding = Column(Vector(768), nullable=True)

    source = Column(String(32), default="ats_history")
    created_at = Column(DateTime, default=datetime.utcnow)

    twin = relationship("DigitalTwin", back_populates="decisions")

    def __repr__(self):
        return f"<TwinDecision twin={self.twin_id} decision={self.decision}>"
