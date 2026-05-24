from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from lia_config.database import Base


class ScreeningQuestionSet(Base):
    __tablename__ = "screening_question_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_vacancy_id = Column(String(255), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    questions_hash = Column(String(64), nullable=False)
    questions_snapshot = Column(JSON, nullable=False)
    questions_count = Column(Integer, nullable=False)
    block_distribution = Column(JSON, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    source = Column(String(50), nullable=False)
    created_by = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    difficulty_coefficient = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_job_vacancy_version', 'job_vacancy_id', 'version'),
        Index('idx_job_vacancy_is_active', 'job_vacancy_id', 'is_active'),
    {"extend_existing": True}, )

    def __repr__(self):
        return f"<ScreeningQuestionSet {self.id} - job_vacancy_id: {self.job_vacancy_id}, version: {self.version}>"
