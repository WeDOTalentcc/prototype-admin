"""
Communication History Model - Tracking all candidate communications.

This model stores records of all communications sent to/from candidates,
including emails, WhatsApp messages, screening invites, and feedback.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Index
import uuid

from lia_config.database import Base


class CommunicationType:
    """Enum-like class for communication types."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    TRIAGEM_INVITE = "triagem_invite"
    AGENDAMENTO_INVITE = "agendamento_invite"
    FEEDBACK = "feedback"


class CommunicationChannel:
    """Enum-like class for communication channels."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class CommunicationDirection:
    """Enum-like class for communication direction."""
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class CommunicationStatus:
    """Enum-like class for communication status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"
    CLICKED = "clicked"
    COMPLAINED = "complained"
    UNSUBSCRIBED = "unsubscribed"


class CommunicationHistory(Base):
    """
    Communication History - Tracks all candidate communications.
    
    Used for:
    - Recording all emails sent to candidates
    - Tracking WhatsApp messages
    - Logging screening and scheduling invites
    - Storing feedback communications
    - Analytics on communication effectiveness
    - Audit trail for all candidate interactions
    """
    __tablename__ = "communication_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    candidate_id = Column(String(255), nullable=False, index=True)
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=True)
    candidate_phone = Column(String(50), nullable=True)
    
    vacancy_id = Column(String(255), nullable=True, index=True)
    vacancy_title = Column(String(255), nullable=True)
    
    communication_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), nullable=False)
    direction = Column(String(20), nullable=False)
    
    subject = Column(String(500), nullable=True)
    message_content = Column(Text, nullable=False)
    message_preview = Column(String(500), nullable=True)
    
    template_id = Column(String(255), nullable=True)
    template_name = Column(String(255), nullable=True)
    
    status = Column(String(20), nullable=False, default="pending", index=True)
    
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    extra_data = Column(JSON, default=dict)
    attachments = Column(JSON, default=list)
    
    sent_by = Column(String(255), nullable=False)
    sent_by_name = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company_id = Column(String(255), nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_comm_candidate_created', 'candidate_id', 'created_at'),
        Index('idx_comm_vacancy_type', 'vacancy_id', 'communication_type'),
        Index('idx_comm_company_created', 'company_id', 'created_at'),
        Index('idx_comm_status_created', 'status', 'created_at'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<CommunicationHistory {self.id} - {self.communication_type} via {self.channel} - {self.status}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "candidate_phone": self.candidate_phone,
            "vacancy_id": self.vacancy_id,
            "vacancy_title": self.vacancy_title,
            "communication_type": self.communication_type,
            "channel": self.channel,
            "direction": self.direction,
            "subject": self.subject,
            "message_content": self.message_content,
            "message_preview": self.message_preview,
            "template_id": self.template_id,
            "template_name": self.template_name,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "error_message": self.error_message,
            "extra_data": self.extra_data,
            "attachments": self.attachments,
            "sent_by": self.sent_by,
            "sent_by_name": self.sent_by_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "company_id": self.company_id,
        }
