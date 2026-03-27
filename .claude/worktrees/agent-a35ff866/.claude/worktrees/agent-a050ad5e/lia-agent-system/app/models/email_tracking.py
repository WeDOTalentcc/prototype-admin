"""
EmailTrackingEvent model — COMP-7.

LGPD Art. 7 VI: base legal = interesse legítimo (disclosure-based).
IP e email são armazenados apenas como SHA256 hash (não reversíveis).
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class EmailTrackingEvent(Base):
    __tablename__ = "email_tracking_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(String(255), nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True, index=True)
    event_type = Column(String(50), nullable=False)   # "open" | "click"
    recipient_hash = Column(String(64), nullable=True)  # SHA256
    ip_hash = Column(String(64), nullable=True)          # SHA256
    user_agent = Column(Text, nullable=True)
    link_url = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_ = Column("metadata", JSONB, nullable=True)

    __table_args__ = (
        Index("ix_email_tracking_notification_type", "notification_id", "event_type"),
    )
