"""
Webhook model for external integrations.

Supports outbound webhooks to notify external systems about events:
- candidate.created
- candidate.stage_changed
- interview.scheduled
- offer.sent
- hire.completed
"""
import uuid
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


class WebhookEvent(StrEnum):
    """Supported webhook events."""
    CANDIDATE_CREATED = "candidate.created"
    CANDIDATE_STAGE_CHANGED = "candidate.stage_changed"
    INTERVIEW_SCHEDULED = "interview.scheduled"
    OFFER_SENT = "offer.sent"
    HIRE_COMPLETED = "hire.completed"
    CANDIDATE_REJECTED = "candidate.rejected"
    APPLICATION_RECEIVED = "application.received"
    SCREENING_COMPLETED = "screening.completed"
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"


class WebhookStatus(StrEnum):
    """Webhook delivery status."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class Webhook(Base):
    """
    Webhook configuration model.
    
    Stores webhook endpoints that should be notified when specific events occur.
    """
    __tablename__ = "webhooks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(255), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(2000), nullable=False)
    
    events = Column(JSON, default=list)
    
    secret_key = Column(String(255), nullable=True)
    
    headers = Column(JSON, default=dict)
    
    is_active = Column(Boolean, default=True)
    
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "events": self.events,
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
    
    def to_dict_full(self) -> dict[str, Any]:
        """Convert to dictionary with full details (including secret)."""
        result = self.to_dict()
        result["secret_key"] = self.secret_key
        result["headers"] = self.headers
        return result


class WebhookLog(Base):
    """
    Webhook delivery log.
    
    Tracks each webhook delivery attempt for debugging and auditing.
    """
    __tablename__ = "webhook_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = Column(String, nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    event = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    
    status = Column(String(50), default=WebhookStatus.PENDING.value)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    attempt_number = Column(Integer, default=1)
    
    triggered_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "company_id": self.company_id,
            "event": self.event,
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


WEBHOOK_EVENTS = [
    {
        "event": WebhookEvent.CANDIDATE_CREATED.value,
        "description": "Triggered when a new candidate is created in the system",
        "payload_example": {
            "event": "candidate.created",
            "candidate_id": "uuid",
            "name": "John Doe",
            "email": "john@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        }
    },
    {
        "event": WebhookEvent.CANDIDATE_STAGE_CHANGED.value,
        "description": "Triggered when a candidate moves to a different recruitment stage",
        "payload_example": {
            "event": "candidate.stage_changed",
            "candidate_id": "uuid",
            "job_vacancy_id": "uuid",
            "previous_stage": "screening",
            "new_stage": "interview",
            "changed_at": "2024-01-01T00:00:00Z"
        }
    },
    {
        "event": WebhookEvent.INTERVIEW_SCHEDULED.value,
        "description": "Triggered when an interview is scheduled with a candidate",
        "payload_example": {
            "event": "interview.scheduled",
            "interview_id": "uuid",
            "candidate_id": "uuid",
            "job_vacancy_id": "uuid",
            "scheduled_at": "2024-01-01T10:00:00Z",
            "interviewer": "Jane Smith"
        }
    },
    {
        "event": WebhookEvent.OFFER_SENT.value,
        "description": "Triggered when a job offer is sent to a candidate",
        "payload_example": {
            "event": "offer.sent",
            "candidate_id": "uuid",
            "job_vacancy_id": "uuid",
            "offer_id": "uuid",
            "sent_at": "2024-01-01T00:00:00Z"
        }
    },
    {
        "event": WebhookEvent.HIRE_COMPLETED.value,
        "description": "Triggered when a candidate is officially hired",
        "payload_example": {
            "event": "hire.completed",
            "candidate_id": "uuid",
            "job_vacancy_id": "uuid",
            "start_date": "2024-02-01",
            "hired_at": "2024-01-01T00:00:00Z"
        }
    },
    {
        "event": WebhookEvent.CANDIDATE_REJECTED.value,
        "description": "Triggered when a candidate is rejected from a position",
        "payload_example": {
            "event": "candidate.rejected",
            "candidate_id": "uuid",
            "job_vacancy_id": "uuid",
            "reason": "Not a good fit",
            "rejected_at": "2024-01-01T00:00:00Z"
        }
    },
    {
        "event": WebhookEvent.APPLICATION_RECEIVED.value,
        "description": "Triggered when a new application is received",
        "payload_example": {
            "event": "application.received",
            "candidate_id": "uuid",
            "job_vacancy_id": "uuid",
            "source": "linkedin",
            "received_at": "2024-01-01T00:00:00Z"
        }
    },
    {
        "event": WebhookEvent.SCREENING_COMPLETED.value,
        "description": "Triggered when candidate screening is completed",
        "payload_example": {
            "event": "screening.completed",
            "candidate_id": "uuid",
            "job_vacancy_id": "uuid",
            "score": 85,
            "recommendation": "proceed",
            "completed_at": "2024-01-01T00:00:00Z"
        }
    },
    {
        "event": WebhookEvent.TASK_CREATED.value,
        "description": "Triggered when a new task is created",
        "payload_example": {
            "event": "task.created",
            "task_id": "uuid",
            "title": "Review candidate",
            "assignee": "recruiter@company.com",
            "due_date": "2024-01-05",
            "created_at": "2024-01-01T00:00:00Z"
        }
    },
    {
        "event": WebhookEvent.TASK_COMPLETED.value,
        "description": "Triggered when a task is completed",
        "payload_example": {
            "event": "task.completed",
            "task_id": "uuid",
            "title": "Review candidate",
            "completed_by": "recruiter@company.com",
            "completed_at": "2024-01-01T00:00:00Z"
        }
    },
]
