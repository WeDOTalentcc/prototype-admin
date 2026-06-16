"""
Candidate List models for organizing candidates into custom collections.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class CandidateList(Base):
    """
    Represents a custom list/collection of candidates.
    Lists can be used for organizing sourcing efforts, shortlists, pools, etc.
    """
    __tablename__ = "candidate_lists"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(20), nullable=True)
    
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    is_active = Column(Boolean, default=True, index=True)
    
    members = relationship("CandidateListMember", back_populates="list", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_candidate_lists_company_name', 'company_id', 'name'),
    {"extend_existing": True}, )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
            "candidate_count": len(self.members) if self.members else 0
        }


class CandidateListMember(Base):
    """
    Represents the many-to-many relationship between lists and candidates.
    """
    __tablename__ = "candidate_list_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id = Column(UUID(as_uuid=True), ForeignKey("candidate_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    added_by = Column(String(255), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, index=True)
    notes = Column(Text, nullable=True)
    source = Column(String(50), default="manual")
    
    list = relationship("CandidateList", back_populates="members")
    
    __table_args__ = (
        UniqueConstraint('list_id', 'candidate_id', name='uq_list_candidate'),
        Index('idx_list_members_list_candidate', 'list_id', 'candidate_id'),
    {"extend_existing": True}, )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "list_id": str(self.list_id),
            "candidate_id": str(self.candidate_id),
            "added_by": self.added_by,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "notes": self.notes,
            "source": self.source
        }
