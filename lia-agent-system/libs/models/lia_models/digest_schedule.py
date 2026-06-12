"""Model: DigestSchedulePreference — per-user + company-default digest frequency.

Fatia 2 (2026-06-12): user_id IS NULL = padrão da empresa.
                       user_id = UUID  = override pessoal do recrutador.

Unique constraint via partial indexes (migration 262):
  uq_digest_schedule_company_default : UNIQUE(company_id) WHERE user_id IS NULL
  uq_digest_schedule_user_override   : UNIQUE(company_id, user_id) WHERE user_id IS NOT NULL
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from lia_config.database import Base


class DigestSchedulePreference(Base):
    """Per-user digest frequency preference (or company default when user_id IS NULL)."""

    __tablename__ = "digest_schedule_preferences"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True)   # NULL = company default

    # Frequências canônicas: daily | twice_daily | weekly | monthly
    frequency = Column(String(20), nullable=False, default="weekly")

    # Optional timing (UTC "HH:MM")
    preferred_time_morning = Column(String(5), nullable=True)
    preferred_time_afternoon = Column(String(5), nullable=True)  # segunda entrega twice_daily

    # Quiet hours (local 0-23); dispatch é ignorado nesse intervalo
    quiet_hours_start = Column(Integer, nullable=True)
    quiet_hours_end = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "frequency": self.frequency,
            "preferred_time_morning": self.preferred_time_morning,
            "preferred_time_afternoon": self.preferred_time_afternoon,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "is_active": self.is_active,
            "source": "user" if self.user_id else "company_default",
        }
