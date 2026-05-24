"""
Affirmative Action Audit Log models for compliance and tracking.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from lia_config.database import Base


class AffirmativeAuditLog(Base):
    """
    Audit log for all affirmative action related events.
    Used for LGPD compliance and internal auditing.
    """
    __tablename__ = "affirmative_audit_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(String(255), nullable=False, index=True)
    vacancy_id = Column(UUID(as_uuid=True), ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True)
    
    action = Column(String(100), nullable=False, index=True)
    
    criteria_checked = Column(JSON, default={})
    
    result = Column(Boolean, nullable=True)
    reason = Column(Text, nullable=True)
    
    performed_by = Column(String(255), nullable=True)
    performed_by_type = Column(String(50), default="system")
    
    action_metadata = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AffirmativeAuditLog {self.id} - {self.action}>"


class CandidateAffirmativeDocument(Base):
    """
    Documents uploaded by candidates for affirmative action verification.
    Tracks upload, verification status, and 24h deadline.
    """
    __tablename__ = "candidate_affirmative_documents"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    vacancy_id = Column(UUID(as_uuid=True), ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    document_type = Column(String(100), nullable=False)
    document_url = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=True)
    
    criteria_type = Column(String(50), nullable=False)
    
    status = Column(String(50), default="pending", index=True)
    
    verified_by_lia = Column(Boolean, default=False)
    lia_verification_result = Column(JSON, nullable=True)
    lia_verified_at = Column(DateTime, nullable=True)
    
    verified_by_recruiter = Column(Boolean, default=False)
    recruiter_email = Column(String(255), nullable=True)
    recruiter_verified_at = Column(DateTime, nullable=True)
    recruiter_notes = Column(Text, nullable=True)
    
    upload_deadline = Column(DateTime, nullable=True)
    is_expired = Column(Boolean, default=False)
    
    reminder_sent_at = Column(DateTime, nullable=True)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CandidateAffirmativeDocument {self.id} - {self.document_type} ({self.status})>"
