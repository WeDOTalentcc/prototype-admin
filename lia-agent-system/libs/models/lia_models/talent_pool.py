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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(BigInteger, nullable=False, index=True)
    ideal_profile_id = Column(UUID(as_uuid=True), nullable=True)
    created_by_user_id = Column(BigInteger, nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")  # active/paused/archived
    screening_questions = Column(JSON, default=list)
    screening_config = Column(JSON, default=dict)
    screening_approved = Column(Boolean, default=False)
    agent_sourcing_enabled = Column(Boolean, default=False)
    agent_config = Column(JSON, default=dict)
    candidates_count = Column(Integer, default=0)
    screened_count = Column(Integer, default=0)
    ready_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "account_id": self.account_id,
            "ideal_profile_id": str(self.ideal_profile_id) if self.ideal_profile_id else None,
            "created_by_user_id": self.created_by_user_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "screening_questions": self.screening_questions or [],
            "screening_config": self.screening_config or {},
            "screening_approved": self.screening_approved,
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
    stage = Column(String, nullable=False, default="discovered")  # discovered/contacted/screening/screened/ready
    origin = Column(String, nullable=False, default="manual")  # agent/manual/import/search
    fit_score = Column(Float, nullable=True)
    screening_data = Column(JSON, default=dict)
    match_criteria = Column(JSON, default=dict)
    moved_to_job_id = Column(BigInteger, nullable=True)
    moved_at = Column(DateTime, nullable=True)
    moved_to_stage = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("talent_pool_id", "candidate_id", name="uq_talent_pool_candidate"),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "talent_pool_id": str(self.talent_pool_id),
            "candidate_id": self.candidate_id,
            "stage": self.stage,
            "origin": self.origin,
            "fit_score": self.fit_score,
            "screening_data": self.screening_data or {},
            "match_criteria": self.match_criteria or {},
            "moved_to_job_id": self.moved_to_job_id,
            "moved_at": self.moved_at.isoformat() if self.moved_at else None,
            "moved_to_stage": self.moved_to_stage,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
