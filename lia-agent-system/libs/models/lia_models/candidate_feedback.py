"""
Candidate Feedback Model - Tracking automatic feedback sent to candidates.

This model stores records of feedback sent to candidates, particularly for
low adherence situations where candidates receive constructive feedback
and an opportunity to resubmit their CV.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from lia_config.database import Base


class CandidateFeedback(Base):
    """
    Tracks feedback sent to candidates.
    
    Used for:
    - Recording automatic feedback for low adherence candidates
    - Tracking resubmission attempts
    - Analytics on candidate engagement
    - Audit trail for communication
    """
    __tablename__ = "candidate_feedbacks"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    candidate_id = Column(String, nullable=False, index=True)
    vacancy_id = Column(String, nullable=False, index=True)
    
    feedback_type = Column(String(50), nullable=False, index=True)
    
    adherence_score = Column(Float, nullable=True)
    
    candidate_name = Column(String(255), nullable=True)
    candidate_email = Column(String(255), nullable=True)
    candidate_phone = Column(String(50), nullable=True)
    
    vacancy_title = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    
    channels_sent = Column(JSON, default=list)
    channels_failed = Column(JSON, default=list)
    
    message_subject = Column(String(500), nullable=True)
    message_preview = Column(Text, nullable=True)
    
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    email_opened = Column(Boolean, default=False)
    email_opened_at = Column(DateTime, nullable=True)
    email_clicked = Column(Boolean, default=False)
    email_clicked_at = Column(DateTime, nullable=True)
    
    whatsapp_sent = Column(Boolean, default=False)
    whatsapp_sent_at = Column(DateTime, nullable=True)
    whatsapp_delivered = Column(Boolean, default=False)
    whatsapp_delivered_at = Column(DateTime, nullable=True)
    whatsapp_read = Column(Boolean, default=False)
    whatsapp_read_at = Column(DateTime, nullable=True)
    
    resubmit_url = Column(String(500), nullable=True)
    resubmit_token = Column(String(100), nullable=True)
    resubmit_clicked = Column(Boolean, default=False)
    resubmit_clicked_at = Column(DateTime, nullable=True)
    resubmit_completed = Column(Boolean, default=False)
    resubmit_completed_at = Column(DateTime, nullable=True)
    new_adherence_score = Column(Float, nullable=True)
    
    improvement_tips = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    matched_skills = Column(JSON, default=list)
    
    sent_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sent_by = Column(String(100), default="lia_system")
    triggered_by = Column(String(100), nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<CandidateFeedback {self.id} - {self.feedback_type} - score:{self.adherence_score}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "vacancy_id": self.vacancy_id,
            "feedback_type": self.feedback_type,
            "adherence_score": self.adherence_score,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "vacancy_title": self.vacancy_title,
            "company_name": self.company_name,
            "channels_sent": self.channels_sent,
            "channels_failed": self.channels_failed,
            "message_subject": self.message_subject,
            "message_preview": self.message_preview,
            "email_sent": self.email_sent,
            "email_opened": self.email_opened,
            "whatsapp_sent": self.whatsapp_sent,
            "whatsapp_delivered": self.whatsapp_delivered,
            "resubmit_url": self.resubmit_url,
            "resubmit_clicked": self.resubmit_clicked,
            "resubmit_completed": self.resubmit_completed,
            "new_adherence_score": self.new_adherence_score,
            "improvement_tips": self.improvement_tips,
            "missing_skills": self.missing_skills,
            "matched_skills": self.matched_skills,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FeedbackType:
    """Enum-like class for feedback types."""
    LOW_ADHERENCE = "low_adherence"
    REJECTION = "rejection"
    IMPROVEMENT_SUGGESTION = "improvement_suggestion"
    RESUBMIT_REMINDER = "resubmit_reminder"
    PROFILE_UPDATE = "profile_update"
