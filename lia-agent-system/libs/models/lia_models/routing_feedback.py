"""RoutingFeedback — stores routing correction signals for adaptive learning."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class RoutingFeedback(Base):
    __tablename__ = "routing_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=True)
    message_hash = Column(String(64), nullable=False)  # MD5 of original message
    routed_domain = Column(String(100), nullable=False)   # what router chose
    actual_domain = Column(String(100), nullable=True)    # what was correct
    corrected = Column(String(5), nullable=True)          # "true" if correction
    corrected_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_routing_feedback_company_domain', 'company_id', 'routed_domain'),
        Index('ix_routing_feedback_corrected_at', 'corrected_at'),
    {"extend_existing": True}, )

    @staticmethod
    def hash_message(message: str) -> str:
        return hashlib.md5(message.encode()).hexdigest()
