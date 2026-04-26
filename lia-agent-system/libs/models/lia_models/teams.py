"""
Microsoft Teams models for bot interactions.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from lia_config.database import Base


class TeamsConversation(Base):
    """Teams conversation tracking."""
    
    __tablename__ = "teams_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Teams identifiers
    conversation_id = Column(String(255), nullable=False, unique=True, index=True)
    service_url = Column(String(500), nullable=False)
    tenant_id = Column(String(255), nullable=True)
    channel_id = Column(String(255), nullable=True)
    
    # User info
    user_id = Column(String(255), nullable=False, index=True)
    user_name = Column(String(255), nullable=True)
    user_aad_object_id = Column(String(255), nullable=True)

    # Multi-tenant boundary — populated from User.company_id via aad_object_id lookup.
    # P0-1 fix (auditoria 2026-04-26): bridge _resolve_company_id depended on this column;
    # without it, getattr fallback masked schema bug silently. Same shape as User.company_id.
    company_id = Column(String(255), nullable=True, index=True, default=None)
    
    # Conversation reference (for proactive messaging)
    conversation_reference = Column(JSON, nullable=False)
    
    # Link to internal conversation
    internal_conversation_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)


class TeamsMessage(Base):
    """Teams message log."""
    
    __tablename__ = "teams_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Teams conversation
    teams_conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Message info
    activity_id = Column(String(255), nullable=True)
    message_type = Column(String(50), nullable=False)  # message, event, invoke
    text = Column(Text, nullable=True)
    
    # Sender
    from_id = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    
    # Direction
    direction = Column(String(20), nullable=False)  # incoming, outgoing
    
    # Full activity payload
    activity_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class TeamsNotification(Base):
    """Scheduled/sent notifications via Teams."""
    
    __tablename__ = "teams_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Target
    teams_conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Notification details
    notification_type = Column(String(100), nullable=False)  # approval_needed, interview_scheduled, etc
    title = Column(String(500), nullable=True)
    message = Column(Text, nullable=False)
    
    # Adaptive card payload
    card_payload = Column(JSON, nullable=True)
    
    # Scheduling
    scheduled_for = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), default="pending")  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Related entities
    related_job_id = Column(UUID(as_uuid=True), nullable=True)
    related_candidate_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TeamsActionAuditLog(Base):
    """Audit log for Teams Adaptive Card actions."""
    
    __tablename__ = "teams_action_audit_logs"
    
    id = Column(String(255), primary_key=True)
    
    # Action information
    action = Column(String(100), nullable=False, index=True)  # approve, reject, schedule, reschedule, request_info
    source = Column(String(100), default="teams_adaptive_card")
    result = Column(String(50), nullable=False, index=True)  # success, failed, auth_failed, invalid_action
    
    # Actor information
    actor_id = Column(String(255), nullable=True, index=True)
    actor_name = Column(String(255), nullable=True)
    
    # Related entities
    candidate_id = Column(String(255), nullable=True, index=True)
    vacancy_id = Column(String(255), nullable=True, index=True)
    company_id = Column(String(255), nullable=True, index=True)
    
    # Audit details
    details = Column(JSON, nullable=False, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<TeamsActionAuditLog {self.id} - {self.action} -> {self.result}>"
    
    def to_dict(self):
        """Convert audit log to dictionary for API responses."""
        return {
            "id": self.id,
            "action": self.action,
            "source": self.source,
            "result": self.result,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "candidate_id": self.candidate_id,
            "vacancy_id": self.vacancy_id,
            "company_id": self.company_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }
