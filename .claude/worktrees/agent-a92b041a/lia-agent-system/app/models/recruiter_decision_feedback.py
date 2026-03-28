"""
RecruiterDecisionFeedback — D6 (ML Feedback Loop)

Armazena decisões dos recrutadores sobre candidatos para calibração adaptativa.
"""
from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class RecruiterDecision(str, enum.Enum):
    approved = "approved"
    rejected = "rejected"
    shortlisted = "shortlisted"
    override_approve = "override_approve"
    override_reject = "override_reject"


class RecruiterDecisionFeedback(Base):
    __tablename__ = "recruiter_decision_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    job_id = Column(String(255), nullable=False, index=True)
    candidate_id = Column(String(255), nullable=False, index=True)
    lia_score = Column(Float, nullable=True)
    decision = Column(SAEnum(RecruiterDecision), nullable=False)
    decision_by = Column(String(255), nullable=True)   # user_id
    decision_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_rdf_company_job", "company_id", "job_id"),
        Index("ix_rdf_decision_at", "company_id", "decision_at"),
    )
