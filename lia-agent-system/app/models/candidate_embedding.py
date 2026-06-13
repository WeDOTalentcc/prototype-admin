"""CandidateEmbedding SQLAlchemy model — pgvector embeddings de candidatos."""
from datetime import datetime
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, Float, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from lia_config.database import Base

EMBEDDING_DIMENSION = 768


class CandidateEmbedding(Base):
    __tablename__ = "candidate_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    skills = Column(ARRAY(String), default=list)
    experience_summary = Column(Text, nullable=True)

    embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=True)
    embedding_text = Column(Text, nullable=True)
    embedding_provider = Column(String(50), nullable=True)
    embedding_model = Column(String(100), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_candidate_embedding_company", "company_id", "is_active"),
        Index("uq_candidate_embedding_cid", "company_id", "candidate_id", unique=True),
        {"extend_existing": True},
    )
