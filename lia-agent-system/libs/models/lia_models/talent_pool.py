"""
Talent Pool Models - Database models for the Talent Pool feature.

Talent Pools allow companies to maintain curated groups of candidates
independently of specific job vacancies, with screening and sourcing
capabilities.
"""
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from lia_config.database import Base


class TalentPool(Base):
    """A curated pool of candidates managed by a company."""
    __tablename__ = "talent_pools"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")
    archetype_id = Column(String, nullable=True)
    screening_questions = Column(JSON, default=list)
    screening_config = Column(JSON, default=dict)
    agent_sourcing_enabled = Column(Boolean, default=False)
    agent_config = Column(JSON, default=dict)
    candidates_count = Column(Integer, default=0)
    screened_count = Column(Integer, default=0)
    ready_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def account_id(self):
        return self.company_id

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "archetype_id": self.archetype_id,
            "screening_questions": self.screening_questions or [],
            "screening_config": self.screening_config or {},
            "agent_sourcing_enabled": self.agent_sourcing_enabled,
            "agent_config": self.agent_config or {},
            "candidates_count": self.candidates_count,
            "screened_count": self.screened_count,
            "ready_count": self.ready_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TalentPoolCandidate(Base):
    """A candidate within a talent pool."""
    __tablename__ = "talent_pool_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_pool_id = Column(
        UUID(as_uuid=True),
        ForeignKey("talent_pools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id = Column(BigInteger, nullable=False, index=True)
    candidate_uuid = Column(UUID(as_uuid=True), nullable=True, index=True)
    stage = Column(String, nullable=False, default="discovered")  # discovered/contacted/screening/screened/ready
    origin = Column(String, nullable=False, default="manual")  # agent/manual/import/search
    fit_score = Column(Float, nullable=True)
    screening_data = Column(JSON, default=dict)
    match_criteria = Column(JSON, default=dict)
    moved_to_job_id = Column(BigInteger, nullable=True)
    moved_to_job_uuid = Column(UUID(as_uuid=True), nullable=True, index=True)
    moved_at = Column(DateTime, nullable=True)
    moved_to_stage = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("talent_pool_id", "candidate_id", name="uq_talent_pool_candidate"),
    {"extend_existing": True}, )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "talent_pool_id": str(self.talent_pool_id),
            "candidate_id": self.candidate_id,
            "candidate_uuid": str(self.candidate_uuid) if self.candidate_uuid else None,
            "stage": self.stage,
            "origin": self.origin,
            "fit_score": self.fit_score,
            "screening_data": self.screening_data or {},
            "match_criteria": self.match_criteria or {},
            "moved_to_job_id": self.moved_to_job_id,
            "moved_to_job_uuid": str(self.moved_to_job_uuid) if self.moved_to_job_uuid else None,
            "moved_at": self.moved_at.isoformat() if self.moved_at else None,
            "moved_to_stage": self.moved_to_stage,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
