"""
CandidateJob — canonical SQLAlchemy model.
Migrated from app/models/candidate_job.py as part of Phase 3 consolidation.

Lightweight join-table tracking a candidates application to a job vacancy.
Distinct from VacancyCandidate (which manages pipeline stages); CandidateJob
records the raw application event with source metadata.
"""
from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class CandidateJob(Base):
    """
    Records a candidates application to a specific job vacancy.

    Used by the WhatsApp conversation flow (_create_candidate_from_conversation)
    to log the raw application event before a full VacancyCandidate record is
    created.
    """
    __tablename__ = "candidate_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_vacancy_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Application metadata
    status = Column(String(50), default="Novo", index=True)
    source = Column(String(100), nullable=True)       # e.g. "whatsapp_lia", "manual"
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_candidate_job_cand_vac", "candidate_id", "job_vacancy_id"),
    {"extend_existing": True}, )

    def __repr__(self):
        return f"<CandidateJob candidate:{self.candidate_id} vacancy:{self.job_vacancy_id} status:{self.status}>"


__all__ = ["CandidateJob"]
