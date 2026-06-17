import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

NPS_TOKEN_BYTES = 32
NPS_DEFAULT_TTL_HOURS = 168  # 7 days


class HiringNps(Base):
    __tablename__ = "hiring_nps"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: str = Column(String, nullable=False)
    job_vacancy_id: str = Column(String, nullable=False)
    candidate_id: Optional[str] = Column(String, nullable=True)
    respondent_type: str = Column(String(20), nullable=False)  # "candidate" | "manager"
    respondent_email: Optional[str] = Column(String(320), nullable=True)
    token: str = Column(String(64), nullable=False, unique=True,
                        default=lambda: secrets.token_urlsafe(NPS_TOKEN_BYTES))
    status: str = Column(String(20), nullable=False, default="pending")
    expires_at: datetime = Column(DateTime(timezone=True), nullable=False,
                                  default=lambda: datetime.now(timezone.utc) + timedelta(hours=NPS_DEFAULT_TTL_HOURS))
    score: Optional[int] = Column(Integer, nullable=True)
    comment: Optional[str] = Column(Text, nullable=True)
    responded_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    sent_by: Optional[str] = Column(String, nullable=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
