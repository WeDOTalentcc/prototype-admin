import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Column, Date, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JobOffer(Base):
    __tablename__ = "job_offers"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: str = Column(String, nullable=False)
    job_vacancy_id: str = Column(String, nullable=False)
    candidate_id: str = Column(String, nullable=False)

    salary: Optional[Decimal] = Column(Numeric(12, 2), nullable=True)
    currency: str = Column(String(10), nullable=False, default="BRL")
    start_date: Optional[date] = Column(Date, nullable=True)
    notes: Optional[str] = Column(Text, nullable=True)

    # draft → sent → accepted | rejected | withdrawn
    status: str = Column(String(30), nullable=False, default="draft")
    sent_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    responded_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    candidate_response: Optional[str] = Column(String(30), nullable=True)
    response_notes: Optional[str] = Column(Text, nullable=True)

    created_by: Optional[str] = Column(String, nullable=True)
    requires_manager_approval: bool = Column(Boolean, nullable=False, default=False)
    manager_approved_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)

    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def is_active(self) -> bool:
        return self.status in ("draft", "sent")
