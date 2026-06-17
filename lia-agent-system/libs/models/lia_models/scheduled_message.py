"""ScheduledMessage Model — GAP-07-007.

Stores recruiter-initiated messages for future delivery.
Celery task `send_scheduled_messages` polls for `status='pending'` rows
where `send_at <= now()` and dispatches them via CommunicationService.

LGPD: message_content is PII; lgpd_expiry enforces 90-day retention (Art. 15).
Multi-tenancy: company_id is indexed and NEVER nullable.
"""
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Index, String, Text
from lia_config.database import Base


class ScheduledMessageStatus:
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledMessage(Base):
    """Scheduled future message for a candidate — recruiter-initiated."""

    __tablename__ = "scheduled_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    company_id = Column(String(255), nullable=False, index=True)
    recruiter_id = Column(String(255), nullable=True, index=True)  # user who scheduled
    candidate_id = Column(String(255), nullable=False, index=True)
    candidate_name = Column(String(255), nullable=True)
    vacancy_id = Column(String(255), nullable=True)

    channel = Column(String(20), nullable=False)  # email | whatsapp
    message_content = Column(Text, nullable=False)
    subject = Column(String(500), nullable=True)  # for email

    send_at = Column(DateTime, nullable=False, index=True)

    status = Column(String(20), nullable=False, default=ScheduledMessageStatus.PENDING, index=True)
    error_detail = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    # LGPD Art. 15 — data retention: auto-expire 90 days after send_at
    lgpd_expiry = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_sched_msg_pending_send_at", "status", "send_at"),
        Index("idx_sched_msg_company_created", "company_id", "created_at"),
        Index("idx_sched_msg_candidate", "candidate_id", "status"),
        {"extend_existing": True},
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "recruiter_id": self.recruiter_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "vacancy_id": self.vacancy_id,
            "channel": self.channel,
            "message_content": self.message_content,
            "subject": self.subject,
            "send_at": self.send_at.isoformat() if self.send_at else None,
            "status": self.status,
            "error_detail": self.error_detail,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "lgpd_expiry": self.lgpd_expiry.isoformat() if self.lgpd_expiry else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
