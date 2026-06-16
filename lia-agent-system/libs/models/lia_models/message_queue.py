"""
Message Queue Model - Queue for outbound communications with retry logic.

This model manages pending messages with:
- Retry logic with exponential backoff (up to 3 attempts)
- Status tracking (pending, sent, delivered, failed, bounced)
- Priority-based ordering
- LGPD consent tracking
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, Index, Float
import uuid

from lia_config.database import Base


class MessagePriority:
    """Priority levels for message queue."""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class MessageStatus:
    """Status of queued messages."""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class MessageChannel:
    """Communication channels."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"


class MessageQueue(Base):
    """
    Message Queue - Manages outbound communications with retry logic.
    
    Features:
    - Up to 3 retry attempts with exponential backoff
    - Priority-based processing
    - LGPD consent verification
    - Delivery status tracking
    - Bulk communication support
    """
    __tablename__ = "message_queue"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    company_id = Column(String(255), nullable=False, index=True)
    
    candidate_id = Column(String(255), nullable=False, index=True)
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=True)
    candidate_phone = Column(String(50), nullable=True)
    
    vacancy_id = Column(String(255), nullable=True, index=True)
    vacancy_title = Column(String(255), nullable=True)
    
    channel = Column(String(20), nullable=False, index=True)
    message_type = Column(String(50), nullable=False, index=True)
    priority = Column(Integer, default=MessagePriority.NORMAL, index=True)
    
    subject = Column(String(500), nullable=True)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    
    template_id = Column(String(255), nullable=True)
    template_name = Column(String(255), nullable=True)
    template_variables = Column(JSON, default=dict)
    
    status = Column(String(20), nullable=False, default=MessageStatus.PENDING, index=True)
    
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime, nullable=True, index=True)
    last_retry_at = Column(DateTime, nullable=True)
    
    provider_message_id = Column(String(255), nullable=True)
    provider_response = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    
    consent_verified = Column(Boolean, default=False)
    consent_type = Column(String(50), nullable=True)
    consent_verified_at = Column(DateTime, nullable=True)
    
    bulk_id = Column(String(255), nullable=True, index=True)
    bulk_sequence = Column(Integer, nullable=True)
    
    scheduled_at = Column(DateTime, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    extra_data = Column(JSON, default=dict)
    
    __table_args__ = (
        Index('idx_mq_status_priority', 'status', 'priority', 'created_at'),
        Index('idx_mq_company_status', 'company_id', 'status'),
        Index('idx_mq_retry', 'status', 'next_retry_at'),
        Index('idx_mq_bulk', 'bulk_id', 'bulk_sequence'),
        Index('idx_mq_scheduled', 'status', 'scheduled_at'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<MessageQueue {self.id} - {self.channel} to {self.candidate_name} ({self.status})>"
    
    def calculate_next_retry(self) -> datetime:
        """Calculate next retry time with exponential backoff."""
        if self.retry_count >= self.max_retries:
            return None
        base_delay = 60
        delay = base_delay * (2 ** self.retry_count)
        max_delay = 3600
        delay = min(delay, max_delay)
        return datetime.utcnow() + timedelta(seconds=delay)
    
    def should_retry(self) -> bool:
        """Check if message should be retried."""
        return (
            self.status in [MessageStatus.FAILED, MessageStatus.PENDING] and
            self.retry_count < self.max_retries
        )
    
    def mark_sent(self, provider_message_id: str = None, provider_response: dict = None):
        """Mark message as sent."""
        self.status = MessageStatus.SENT
        self.sent_at = datetime.utcnow()
        if provider_message_id:
            self.provider_message_id = provider_message_id
        if provider_response:
            self.provider_response = provider_response
    
    def mark_delivered(self):
        """Mark message as delivered."""
        self.status = MessageStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str):
        """Mark message as failed and schedule retry if possible."""
        self.last_retry_at = datetime.utcnow()
        self.retry_count += 1
        self.error_message = error_message
        
        if self.should_retry():
            self.status = MessageStatus.PENDING
            self.next_retry_at = self.calculate_next_retry()
        else:
            self.status = MessageStatus.FAILED
            self.failed_at = datetime.utcnow()
    
    def mark_blocked(self, reason: str):
        """Mark message as blocked (consent issues, opt-out, etc)."""
        self.status = MessageStatus.BLOCKED
        self.error_message = reason
        self.failed_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "candidate_phone": self.candidate_phone,
            "vacancy_id": self.vacancy_id,
            "vacancy_title": self.vacancy_title,
            "channel": self.channel,
            "message_type": self.message_type,
            "priority": self.priority,
            "subject": self.subject,
            "template_id": self.template_id,
            "template_name": self.template_name,
            "status": self.status,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "consent_verified": self.consent_verified,
            "bulk_id": self.bulk_id,
            "bulk_sequence": self.bulk_sequence,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "error_message": self.error_message,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
