"""
Webhook — Subscriptions a eventos do Studio para integracoes externas.

Cada webhook subscreve a um conjunto de eventos. Quando um evento ocorre,
um POST e enviado ao URL com payload assinado via HMAC-SHA256.

Eventos suportados:
  - agent.execution.completed
  - agent.execution.failed
  - agent.deployment.created
  - agent.deployment.paused
  - agent.approval.requested
  - agent.approval.reviewed
"""
import enum
import uuid

from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from lia_config.database import Base


class WebhookEvent(str, PyEnum):
    AGENT_EXECUTION_COMPLETED = "agent.execution.completed"
    AGENT_EXECUTION_FAILED = "agent.execution.failed"
    AGENT_DEPLOYMENT_CREATED = "agent.deployment.created"
    AGENT_DEPLOYMENT_PAUSED = "agent.deployment.paused"
    AGENT_APPROVAL_REQUESTED = "agent.approval.requested"
    AGENT_APPROVAL_REVIEWED = "agent.approval.reviewed"
    CANDIDATE_ENRICHED = "candidate.enriched"


class WebhookStatus(str, PyEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


WEBHOOK_EVENTS = [e.value for e in WebhookEvent]


class Webhook(Base):
    __tablename__ = "studio_webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(64), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    url = Column(String(2048), nullable=False)
    events = Column(ARRAY(String), nullable=False)
    secret = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Stats
    total_deliveries = Column(Integer, default=0, nullable=False)
    total_failures = Column(Integer, default=0, nullable=False)
    last_delivery_at = Column(DateTime(timezone=True), nullable=True)
    last_status_code = Column(Integer, nullable=True)
    last_error = Column(Text, nullable=True)

    # Audit
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self, include_secret: bool = False):
        result = {
            "id": str(self.id),
            "company_id": self.company_id,
            "name": self.name,
            "url": self.url,
            "events": self.events or [],
            "is_active": self.is_active,
            "total_deliveries": self.total_deliveries,
            "total_failures": self.total_failures,
            "last_delivery_at": self.last_delivery_at.isoformat() if self.last_delivery_at else None,
            "last_status_code": self.last_status_code,
            "last_error": self.last_error,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_secret:
            result["secret"] = self.secret
        return result


class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("studio_webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
    event = Column(String(128), nullable=False)
    status = Column(Enum(WebhookStatus), default=WebhookStatus.PENDING, nullable=False)
    status_code = Column(Integer, nullable=True)
    request_body = Column(JSONB, nullable=True)
    response_body = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    attempt = Column(Integer, default=1, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "webhook_id": str(self.webhook_id),
            "event": self.event,
            "status": self.status.value if self.status else None,
            "status_code": self.status_code,
            "error": self.error,
            "attempt": self.attempt,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
