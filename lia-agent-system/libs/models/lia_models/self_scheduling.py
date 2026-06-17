"""
Self-Scheduling Link models for candidate interview self-service.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
import secrets

from lia_config.database import Base


class SelfSchedulingLink(Base):
    """
    Self-scheduling links allow candidates to choose their preferred interview time.
    """
    __tablename__ = "self_scheduling_links"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    
    candidate_id = Column(UUID(as_uuid=True), nullable=True)
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False)
    
    job_vacancy_id = Column(UUID(as_uuid=True), nullable=True)
    job_title = Column(String(255), nullable=True)
    
    interviewer_emails = Column(JSON, default=[])
    organizer_email = Column(String(255), nullable=True)
    
    interview_type = Column(String(50), default="hr")
    interview_mode = Column(String(50), default="video")
    duration_minutes = Column(Integer, default=60)
    
    available_slots = Column(JSON, default=[])
    
    selected_slot = Column(JSON, nullable=True)
    interview_id = Column(UUID(as_uuid=True), nullable=True)
    
    status = Column(String(50), default="pending", index=True)
    
    expires_at = Column(DateTime, nullable=False)
    
    max_uses = Column(Integer, default=1)
    use_count = Column(Integer, default=0)
    
    notes = Column(Text, nullable=True)
    extra_data = Column(JSON, default={})
    
    created_by = Column(String(255), nullable=False, default="system")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)
    
    def is_valid(self) -> bool:
        """Check if link is still valid."""
        if self.status not in ("pending", "active"):
            return False
        if self.expires_at < datetime.utcnow():
            return False
        if self.use_count >= self.max_uses:
            return False
        return True
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "token": self.token,
            "candidate_id": str(self.candidate_id) if self.candidate_id else None,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "job_vacancy_id": str(self.job_vacancy_id) if self.job_vacancy_id else None,
            "job_title": self.job_title,
            "interviewer_emails": self.interviewer_emails,
            "interview_type": self.interview_type,
            "interview_mode": self.interview_mode,
            "duration_minutes": self.duration_minutes,
            "available_slots": self.available_slots,
            "selected_slot": self.selected_slot,
            "interview_id": str(self.interview_id) if self.interview_id else None,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_valid": self.is_valid(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<SelfSchedulingLink {self.token[:8]}... for {self.candidate_name}>"


class RescheduleHistory(Base):
    """
    Track interview rescheduling history for limits and auditing.
    """
    __tablename__ = "reschedule_history"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    interview_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    job_vacancy_id = Column(UUID(as_uuid=True), nullable=True)
    
    original_start_time = Column(DateTime, nullable=False)
    original_end_time = Column(DateTime, nullable=False)
    
    new_start_time = Column(DateTime, nullable=False)
    new_end_time = Column(DateTime, nullable=False)
    
    reason = Column(Text, nullable=True)
    requested_by = Column(String(50), nullable=False)
    
    reschedule_number = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "interview_id": str(self.interview_id),
            "candidate_id": str(self.candidate_id) if self.candidate_id else None,
            "original_start_time": self.original_start_time.isoformat(),
            "new_start_time": self.new_start_time.isoformat(),
            "reason": self.reason,
            "requested_by": self.requested_by,
            "reschedule_number": self.reschedule_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InterviewReminder(Base):
    """
    Scheduled interview reminders for candidates and interviewers.
    """
    __tablename__ = "interview_reminders"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    interview_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    reminder_type = Column(String(50), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    recipient_type = Column(String(50), nullable=False)
    
    scheduled_for = Column(DateTime, nullable=False, index=True)
    hours_before = Column(Integer, nullable=False)
    
    status = Column(String(50), default="pending", index=True)
    sent_at = Column(DateTime, nullable=True)
    send_error = Column(Text, nullable=True)
    
    channels = Column(JSON, default=["email"])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "interview_id": str(self.interview_id),
            "reminder_type": self.reminder_type,
            "recipient_email": self.recipient_email,
            "recipient_type": self.recipient_type,
            "scheduled_for": self.scheduled_for.isoformat(),
            "hours_before": self.hours_before,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }
