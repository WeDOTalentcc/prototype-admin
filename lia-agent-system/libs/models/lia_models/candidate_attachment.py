"""
Candidate Attachment Model - Tracking all candidate file attachments.

This model stores records of all files attached to candidates,
including CVs, documents, certificates, videos, transcripts, and other files.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, Index
import uuid

from lia_config.database import Base


class AttachmentType:
    """Enum-like class for attachment types."""
    CV = "cv"
    DOCUMENT = "document"
    CERTIFICATE = "certificate"
    VIDEO = "video"
    TRANSCRIPT = "transcript"
    OTHER = "other"


class UploadSource:
    """Enum-like class for upload sources."""
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"
    LIA = "lia"
    ATS = "ats"


class CandidateAttachment(Base):
    """
    Candidate Attachment - Tracks all candidate file attachments.
    
    Used for:
    - Storing CVs and resumes
    - Recording documents uploaded by candidates or recruiters
    - Tracking certificates and credentials
    - Storing video introductions or interviews
    - Keeping transcripts and screening records
    - Linking files to interviews, screenings, or communications
    """
    __tablename__ = "candidate_attachments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    candidate_id = Column(String(255), nullable=False, index=True)
    candidate_name = Column(String(255), nullable=False)
    
    file_name = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False, index=True)
    file_url = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256 hex digest for file-level dedup (GAP-05-006)
    
    upload_source = Column(String(50), nullable=False, index=True)
    
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(String(255), nullable=True)
    
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True, index=True)
    
    company_id = Column(String(255), nullable=False, index=True)
    
    uploaded_by = Column(String(255), nullable=False)
    uploaded_by_name = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_attach_candidate_created', 'candidate_id', 'created_at'),
        Index('idx_attach_candidate_type', 'candidate_id', 'file_type'),
        Index('idx_attach_company_created', 'company_id', 'created_at'),
        Index('idx_attach_related_entity', 'related_entity_type', 'related_entity_id'),
        Index("idx_attach_file_hash_company", "file_hash", "company_id"),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<CandidateAttachment {self.id} - {self.file_name} ({self.file_type})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_url": self.file_url,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "upload_source": self.upload_source,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "description": self.description,
            "is_active": self.is_active,
            "company_id": self.company_id,
            "uploaded_by": self.uploaded_by,
            "uploaded_by_name": self.uploaded_by_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
