"""
RecruiterPreferences model — Stores learned patterns and preferences for recruiters.

Used by the Pipeline Transition Agent to offer proactive suggestions based
on historical behavior (preferred platforms, time slots, actions, etc.).
"""
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class RecruiterPreference(Base):
    __tablename__ = "recruiter_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = Column(String(255), nullable=False, index=True)
    preference_key = Column(String(255), nullable=False, index=True)
    preference_value = Column(Text, nullable=False)
    frequency = Column(Integer, default=1)
    context = Column(JSON, default=dict)
    last_used = Column(DateTime, default=lambda: datetime.utcnow())
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
