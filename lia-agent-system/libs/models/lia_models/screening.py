from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from lia_config.database import Base


class ScreeningTask(Base):
    __tablename__ = "screening_tasks"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(String(255), nullable=False, index=True)
    job_id = Column(String(255), nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    source = Column(String(50), nullable=False)
    resume_text = Column(Text, nullable=True)
    resume_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "company_id": self.company_id,
            "status": self.status,
            "source": self.source,
            "resume_url": self.resume_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
