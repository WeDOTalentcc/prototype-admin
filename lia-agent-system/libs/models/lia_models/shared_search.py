"""
Shared Search models for sharing candidate searches with external stakeholders.
Enables recruiters to share search results or candidate lists with hiring managers
via secure, time-limited links with optional OTP verification.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum
import uuid

from lia_config.database import Base


class ShareType(str, Enum):
    """Type of shared content."""
    search = "search"
    list = "list"


class SharedSearchStatus(str, Enum):
    """Status of a shared search link."""
    active = "active"
    expired = "expired"
    revoked = "revoked"


class FeedbackDecision(str, Enum):
    """Hiring manager feedback decision on a candidate."""
    approved = "approved"
    maybe = "maybe"
    rejected = "rejected"


class SharedSearch(Base):
    """
    Represents a shared search or candidate list that can be accessed by external stakeholders.
    
    When a recruiter shares search results or a candidate list, a snapshot of the candidates
    is stored to ensure consistent viewing even if the underlying data changes.
    """
    __tablename__ = "shared_searches"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    share_type = Column(SQLAlchemyEnum(ShareType), nullable=False, default=ShareType.search)
    source_query = Column(Text, nullable=True)
    source_list_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    expires_at = Column(DateTime, nullable=True, index=True)
    status = Column(SQLAlchemyEnum(SharedSearchStatus), nullable=False, default=SharedSearchStatus.active, index=True)
    
    snapshot_payload = Column(JSONB, nullable=False, default=dict)
    
    can_comment = Column(Boolean, nullable=False, server_default="true", default=True)
    can_rate = Column(Boolean, nullable=False, server_default="true", default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    access_records = relationship("SharedSearchAccess", back_populates="shared_search", cascade="all, delete-orphan", lazy="dynamic")
    feedback_records = relationship("SharedSearchFeedback", back_populates="shared_search", cascade="all, delete-orphan", lazy="dynamic")
    
    def __repr__(self):
        return f"<SharedSearch {self.id} - {self.title} ({self.status.value})>"


class SharedSearchAccess(Base):
    """
    Tracks individual access grants for a shared search.
    
    Each stakeholder (e.g., hiring manager) gets a unique access token for their link.
    Supports OTP verification for additional security.
    """
    __tablename__ = "shared_search_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shared_search_id = Column(UUID(as_uuid=True), ForeignKey("shared_searches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="hiring_manager")
    
    access_token = Column(String(255), nullable=False, unique=True, index=True)
    otp_hash = Column(String(255), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, nullable=False, server_default="0", default=0)

    first_accessed_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)
    total_views = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    shared_search = relationship("SharedSearch", back_populates="access_records")
    
    __table_args__ = (
        UniqueConstraint('shared_search_id', 'email', name='uq_shared_search_access_email'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<SharedSearchAccess {self.id} - {self.email} ({self.role})>"


class SharedSearchFeedback(Base):
    """
    Stores feedback from stakeholders on individual candidates within a shared search.
    
    Hiring managers can approve, reject, or mark candidates as 'maybe',
    along with optional ratings and comments.
    """
    __tablename__ = "shared_search_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shared_search_id = Column(UUID(as_uuid=True), ForeignKey("shared_searches.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    reviewer_email = Column(String(255), nullable=False, index=True)
    decision = Column(SQLAlchemyEnum(FeedbackDecision), nullable=False)
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    shared_search = relationship("SharedSearch", back_populates="feedback_records")
    
    __table_args__ = (
        UniqueConstraint('shared_search_id', 'candidate_id', 'reviewer_email', name='uq_shared_search_feedback_candidate_reviewer'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<SharedSearchFeedback {self.id} - {self.reviewer_email}: {self.decision.value}>"
