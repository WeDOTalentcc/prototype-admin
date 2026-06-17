from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Text
import uuid

from lia_config.database import Base


class SearchFeedback(Base):
    __tablename__ = "search_feedbacks"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Multi-tenancy: company_id alimenta a RLS deny-by-default (migration 222).
    # varchar pra casar com app_current_company_id()::text + padrao candidates.
    company_id = Column(String, nullable=False, index=True)

    candidate_id = Column(String, nullable=False, index=True)
    job_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=False, index=True)

    search_query = Column(String, nullable=True)
    # Fase 2: ancora o feedback aos CRITERIOS da busca (query+filtros). Re-hidrata
    # ao re-executar/resgatar a busca (historico/lista/pool). Calculado no backend.
    search_fingerprint = Column(String, nullable=True, index=True)
    feedback_type = Column(String(20), nullable=False)
    candidate_score = Column(Float, nullable=True)
    candidate_name = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SearchFeedback {self.id} - {self.feedback_type} - candidate:{self.candidate_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "user_id": self.user_id,
            "search_query": self.search_query,
            "search_fingerprint": self.search_fingerprint,
            "feedback_type": self.feedback_type,
            "candidate_score": self.candidate_score,
            "candidate_name": self.candidate_name,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
