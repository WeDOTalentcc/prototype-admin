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
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from lia_config.database import Base


class Webhook(Base):
    __tablename__ = "webhooks"

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
