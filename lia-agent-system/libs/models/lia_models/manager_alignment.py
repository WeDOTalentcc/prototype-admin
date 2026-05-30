"""
ManagerAlignment — tracks one-time manager approval requests for job vacancies.

Apply to: lia-agent-system/libs/models/lia_models/manager_alignment.py
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ManagerAlignment(Base):
    __tablename__ = "manager_alignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(255), nullable=False, index=True)
    job_vacancy_id = Column(String(255), nullable=False, index=True)
    manager_email = Column(String(255), nullable=False)
    manager_name = Column(String(255), nullable=True)
    # Secure random token embedded in the public /align/{token} URL
    token = Column(String(64), nullable=False, unique=True, index=True)
    # pending | approved | rejected | expired
    status = Column(String(20), nullable=False, default="pending")
    response_notes = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_manager_alignments_company_job", "company_id", "job_vacancy_id"),
    )

    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp

    def is_pending(self) -> bool:
        return self.status == "pending" and not self.is_expired()
