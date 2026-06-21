"""
Approval Request models for workflow approvals.
Handles vacancy approvals, candidate hire approvals, and other workflow approvals.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from lia_config.database import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalType(str, enum.Enum):
    VACANCY_APPROVAL = "vacancy_approval"
    CANDIDATE_HIRE = "candidate_hire"
    OFFER_APPROVAL = "offer_approval"
    BUDGET_APPROVAL = "budget_approval"
    # Phase B (Sprint B post-audit): feature flag second-actor approval
    # workflow. Admin/DPO approves toggling sensitive learning_loops flags
    # requested by non-admin users. See app/api/v1/lia_assistant_flags.py
    # request_feature_flag_toggle / approve_feature_flag_toggle endpoints.
    FEATURE_FLAG_TOGGLE = "feature_flag_toggle"
    CUSTOM = "custom"


class ApprovalRequest(Base):
    """
    Approval requests for workflow approvals.
    Tracks the full lifecycle of approval requests with email notifications.
    """
    __tablename__ = "approval_requests"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    request_type = Column(String(50), nullable=False, default="vacancy_approval")
    
    requester_id = Column(UUID(as_uuid=True), nullable=True)
    requester_name = Column(String(255), nullable=False)
    requester_email = Column(String(255), nullable=False)
    
    target_id = Column(UUID(as_uuid=True), nullable=True)
    target_type = Column(String(50), nullable=True)
    target_name = Column(String(500), nullable=False)
    target_description = Column(Text, nullable=True)
    target_data = Column(JSON, default={})
    
    approver_id = Column(UUID(as_uuid=True), nullable=True)
    approver_name = Column(String(255), nullable=False)
    approver_email = Column(String(255), nullable=False)
    
    approval_level = Column(Integer, default=1)
    
    status = Column(String(20), nullable=False, default="pending", index=True)
    
    priority = Column(String(20), default="normal")
    
    due_date = Column(DateTime, nullable=True)
    
    approval_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    reminder_count = Column(Integer, default=0)
    last_reminder_at = Column(DateTime, nullable=True)
    
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True)
    
    expires_at = Column(DateTime, nullable=True)

    # Sprint 2 (2026-06-21): magic token para aprovacao sem login (TIPO B externo).
    magic_token = Column(String(128), nullable=True)
    magic_token_expires_at = Column(DateTime, nullable=True)
    magic_token_used = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "request_type": self.request_type,
            "requester_id": str(self.requester_id) if self.requester_id else None,
            "requester_name": self.requester_name,
            "requester_email": self.requester_email,
            "target_id": str(self.target_id) if self.target_id else None,
            "target_type": self.target_type,
            "target_name": self.target_name,
            "target_description": self.target_description,
            "target_data": self.target_data or {},
            "approver_id": str(self.approver_id) if self.approver_id else None,
            "approver_name": self.approver_name,
            "approver_email": self.approver_email,
            "approval_level": self.approval_level,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "approval_notes": self.approval_notes,
            "rejection_reason": self.rejection_reason,
            "email_sent": self.email_sent,
            "email_sent_at": self.email_sent_at.isoformat() if self.email_sent_at else None,
            "reminder_count": self.reminder_count,
            "last_reminder_at": self.last_reminder_at.isoformat() if self.last_reminder_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "magic_token": self.magic_token,
            "magic_token_expires_at": self.magic_token_expires_at.isoformat() if self.magic_token_expires_at else None,
            "magic_token_used": self.magic_token_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
