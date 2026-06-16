"""DomainEventsOutbox — outbox pattern para entrega garantida de eventos criticos.

Sprint E (2026-06-13): Guia computacional de harness.
INSERT atomico com o dominio garante que o evento nao se perde se Redis cair.
drain_to_pubsub() lê pending → publica → marca delivered.
"""
import enum
import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from lia_config.database import Base


class OutboxStatus(str, enum.Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class DomainEventsOutbox(Base):
    """
    Outbox pattern para eventos criticos de dominio.

    Garante entrega at-least-once: o evento e escrito atomicamente com a
    operacao de dominio na mesma transacao. O worker drain_to_pubsub()
    le daqui e publica no Redis pub/sub.

    Diferente de ai_consumption_outbox (billing): serve TODOS os dominios.
    """
    __tablename__ = "domain_events_outbox"
    __table_args__ = {"extend_existing": True}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    event_id = Column(String(80), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default=OutboxStatus.PENDING,
        server_default="pending",
        index=True,
    )
    correlation_id = Column(String(80), nullable=True, index=True)
    source_api = Column(String(80), nullable=True)
    version = Column(String(10), nullable=False, default="1.0", server_default="1.0")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    delivered_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, nullable=False, default=0, server_default="0")
    last_error = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DomainEventsOutbox {self.event_type} status={self.status}>"
