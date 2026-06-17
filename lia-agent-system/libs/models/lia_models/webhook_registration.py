"""
Webhook Registration model for job status change notifications.

Stores webhook configurations for external systems to receive
notifications when job vacancy statuses change.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
import hmac
import hashlib
import secrets


from lia_config.database import Base


class WebhookRegistration(Base):
    """
    Webhook Registration for job status change notifications.
    
    Companies can register webhook URLs to receive notifications
    when job vacancy statuses change.
    """
    __tablename__ = "webhook_registrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(2000), nullable=False)
    
    event_types = Column(JSON, default=list)
    
    secret_key = Column(String(255), nullable=False, default=lambda: WebhookRegistration.generate_secret_key())  # P1-W3-11
    
    headers = Column(JSON, default=dict)
    
    is_active = Column(Boolean, default=True, index=True)
    
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)
    
    last_triggered_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    last_failure_reason = Column(Text, nullable=True)
    
    total_triggers = Column(Integer, default=0)
    total_successes = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_webhook_reg_company_active', 'company_id', 'is_active'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<WebhookRegistration {self.id} - {self.name} - {self.url}>"
    
    @staticmethod
    def generate_secret_key() -> str:
        """Generate a secure secret key for HMAC signing."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_signature(payload: str, secret_key: str) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload.
        
        Args:
            payload: JSON payload string
            secret_key: Secret key for signing
            
        Returns:
            Hex-encoded HMAC signature prefixed with 'sha256='
        """
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    @staticmethod
    def verify_signature(payload: str, signature: str, secret_key: str) -> bool:
        """
        Verify HMAC-SHA256 signature.
        
        Args:
            payload: JSON payload string
            signature: Signature to verify (with or without 'sha256=' prefix)
            secret_key: Secret key used for signing
            
        Returns:
            True if signature is valid
        """
        expected = WebhookRegistration.generate_signature(payload, secret_key)
        actual = signature if signature.startswith('sha256=') else f"sha256={signature}"
        return hmac.compare_digest(expected, actual)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (masks sensitive data)."""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "event_types": self.event_types or [],
            "secret_key": "***" if self.secret_key else None,
            "headers": {k: "***" for k in (self.headers or {}).keys()},
            "is_active": self.is_active,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "last_failure_reason": self.last_failure_reason,
            "total_triggers": self.total_triggers,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_dict_full(self) -> Dict[str, Any]:
        """Convert to dictionary with full details (including secrets)."""
        result = self.to_dict()
        result["secret_key"] = self.secret_key
        result["headers"] = self.headers
        return result


class WebhookDeliveryLog(Base):
    """
    Log of webhook delivery attempts.
    
    Tracks each delivery attempt for debugging and auditing.
    """
    __tablename__ = "webhook_delivery_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    
    status = Column(String(50), default="pending")
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    attempt_number = Column(Integer, default=1)
    
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_webhook_delivery_webhook', 'webhook_id', 'triggered_at'),
        Index('idx_webhook_delivery_company', 'company_id', 'triggered_at'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "webhook_id": str(self.webhook_id),
            "company_id": self.company_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "status": self.status,
            "status_code": self.status_code,
            "response_body": self.response_body[:500] if self.response_body else None,
            "error_message": self.error_message,
            "attempt_number": self.attempt_number,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
        }


JOB_STATUS_WEBHOOK_EVENTS = [
    {
        "event": "job.status_changed",
        "description": "Triggered when a job vacancy status changes",
        "payload_example": {
            "event": "job.status_changed",
            "job_id": "uuid",
            "old_status": "Rascunho",
            "new_status": "Ativa",
            "changed_at": "2024-01-01T00:00:00Z",
            "changed_by": "user@example.com"
        }
    },
    {
        "event": "job.created",
        "description": "Triggered when a new job vacancy is created",
        "payload_example": {
            "event": "job.created",
            "job_id": "uuid",
            "title": "Software Engineer",
            "status": "Rascunho",
            "created_at": "2024-01-01T00:00:00Z",
            "created_by": "user@example.com"
        }
    },
    {
        "event": "job.published",
        "description": "Triggered when a job vacancy is published",
        "payload_example": {
            "event": "job.published",
            "job_id": "uuid",
            "title": "Software Engineer",
            "published_at": "2024-01-01T00:00:00Z",
            "published_by": "user@example.com"
        }
    },
    {
        "event": "job.closed",
        "description": "Triggered when a job vacancy is closed or completed",
        "payload_example": {
            "event": "job.closed",
            "job_id": "uuid",
            "title": "Software Engineer",
            "final_status": "Concluída",
            "closed_at": "2024-01-01T00:00:00Z",
            "closed_by": "user@example.com"
        }
    },
]
