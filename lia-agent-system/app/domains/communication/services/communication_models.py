"""
SQLAlchemy models for the communication domain.

Extracted from communication_service.py to reduce file size and improve maintainability.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


class PendingApproval(Base):
    """Pending approval requests for communications requiring human review."""
    __tablename__ = "pending_approvals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False, index=True)
    
    candidate_id = Column(String, nullable=False, index=True)
    candidate_name = Column(String(255), nullable=True)
    candidate_email = Column(String(255), nullable=True)
    candidate_phone = Column(String(50), nullable=True)
    
    job_id = Column(String, nullable=True, index=True)
    job_title = Column(String(255), nullable=True)
    
    message_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), nullable=False, default="email")
    
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    body_html = Column(Text, nullable=True)
    
    ai_personalization = Column(Text, nullable=True)
    personalization_context = Column(JSON, default=dict)
    
    status = Column(String(20), default="pending", index=True)
    
    requested_by = Column(String(255), nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    modified_subject = Column(String(500), nullable=True)
    modified_body = Column(Text, nullable=True)
    
    priority = Column(String(20), default="normal")
    expires_at = Column(DateTime, nullable=True)
    
    communication_log_id = Column(String, nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "candidate_phone": self.candidate_phone,
            "job_id": self.job_id,
            "job_title": self.job_title,
            "message_type": self.message_type,
            "channel": self.channel,
            "subject": self.subject,
            "body": self.body,
            "body_html": self.body_html,
            "ai_personalization": self.ai_personalization,
            "personalization_context": self.personalization_context,
            "status": self.status,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes,
            "modified_subject": self.modified_subject,
            "modified_body": self.modified_body,
            "priority": self.priority,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "communication_log_id": self.communication_log_id,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CommunicationLog(Base):
    """Audit log for all communications sent."""
    __tablename__ = "communication_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False, index=True)
    
    candidate_id = Column(String, nullable=False, index=True)
    candidate_email = Column(String(255), nullable=True)
    candidate_phone = Column(String(50), nullable=True)
    
    job_id = Column(String, nullable=True, index=True)
    
    message_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), nullable=False, index=True)
    
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    body_html = Column(Text, nullable=True)
    
    status = Column(String(20), default="pending", index=True)
    
    sent_at = Column(DateTime, nullable=True, index=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    provider_name = Column(String(50), nullable=True)
    provider_message_id = Column(String(255), nullable=True)
    provider_response = Column(JSON, default=dict)
    
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    approval_id = Column(String, nullable=True)
    approved_by = Column(String(255), nullable=True)
    
    sent_by = Column(String(255), nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "candidate_email": self.candidate_email,
            "candidate_phone": self.candidate_phone,
            "job_id": self.job_id,
            "message_type": self.message_type,
            "channel": self.channel,
            "subject": self.subject,
            "body": self.body,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "provider_name": self.provider_name,
            "provider_message_id": self.provider_message_id,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "approval_id": self.approval_id,
            "approved_by": self.approved_by,
            "sent_by": self.sent_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CandidateOptOut(Base):
    """LGPD-compliant opt-out tracking for candidates."""
    __tablename__ = "candidate_opt_outs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False, index=True)
    
    candidate_id = Column(String, nullable=False, index=True)
    candidate_email = Column(String(255), nullable=True, index=True)
    candidate_phone = Column(String(50), nullable=True, index=True)
    
    channel = Column(String(20), nullable=False, index=True)
    
    opt_out_type = Column(String(50), nullable=False, default="all")
    opt_out_reason = Column(Text, nullable=True)
    
    opted_out_at = Column(DateTime, default=datetime.utcnow, index=True)
    opted_out_via = Column(String(50), nullable=True)
    
    is_active = Column(Boolean, default=True)
    reactivated_at = Column(DateTime, nullable=True)
    reactivated_by = Column(String(255), nullable=True)
    
    consent_given_at = Column(DateTime, nullable=True)
    consent_ip_address = Column(String(50), nullable=True)
    consent_user_agent = Column(String(500), nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "candidate_email": self.candidate_email,
            "candidate_phone": self.candidate_phone,
            "channel": self.channel,
            "opt_out_type": self.opt_out_type,
            "opt_out_reason": self.opt_out_reason,
            "opted_out_at": self.opted_out_at.isoformat() if self.opted_out_at else None,
            "is_active": self.is_active,
            "consent_given_at": self.consent_given_at.isoformat() if self.consent_given_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CandidateQuarantine(Base):
    """Quarantine tracking for rejected candidates (3 months no-contact)."""
    __tablename__ = "candidate_quarantines"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False, index=True)
    
    candidate_id = Column(String, nullable=False, index=True)
    job_id = Column(String, nullable=True, index=True)
    
    reason = Column(String(100), nullable=False, default="rejection")
    
    quarantine_start = Column(DateTime, default=datetime.utcnow, index=True)
    quarantine_end = Column(DateTime, nullable=False, index=True)
    quarantine_days = Column(Integer, default=90)
    
    is_active = Column(Boolean, default=True, index=True)
    lifted_at = Column(DateTime, nullable=True)
    lifted_by = Column(String(255), nullable=True)
    lift_reason = Column(Text, nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "reason": self.reason,
            "quarantine_start": self.quarantine_start.isoformat() if self.quarantine_start else None,
            "quarantine_end": self.quarantine_end.isoformat() if self.quarantine_end else None,
            "quarantine_days": self.quarantine_days,
            "is_active": self.is_active,
            "lifted_at": self.lifted_at.isoformat() if self.lifted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
