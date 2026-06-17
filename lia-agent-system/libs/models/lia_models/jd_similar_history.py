"""JdSimilarHistory model — Sprint B Phase 1.

Aggregates JD history with pgvector embeddings for similarity-based reuse suggestion.

Activated when company has >= 10 filled vacancies (JD_SIMILAR_MIN_HISTORY threshold).
Mantém ADR-002 (modelo em lia_models package).

Schema lives in alembic/versions/106_sprint_b_learning_tables.py.
Migration 108_alter_jd_similar_pgvector.py converts jd_embedding to Vector(1536).
"""
from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from lia_config.database import Base

try:
    from pgvector.sqlalchemy import Vector  # type: ignore
    _HAS_PGVECTOR = True
except ImportError:  # pragma: no cover
    _HAS_PGVECTOR = False
    Vector = None  # type: ignore


# OpenAI text-embedding-3-small dimension. Hardcoded para consistência —
# fallback Gemini (768d) NÃO suportado nesta tabela.
JD_EMBEDDING_DIM = 1536


class JdSimilarHistory(Base):
    """Histórico de Job Descriptions enriquecidas, indexado por embedding semântico.

    Multi-tenancy: `company_id` obrigatório em toda operação (validado no repository).
    PII: `jd_enriched_json` NUNCA contém candidate data; só JD content (title, responsibilities,
    requirements). Embedding gerado de title + responsibilities apenas (ADR-006).
    """

    __tablename__ = "jd_similar_history"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenancy
    company_id = Column(String(255), nullable=False, index=True)
    job_id = Column(String(255), nullable=True, index=True)

    # Search keys
    title_normalized = Column(String(500), nullable=False, index=True)
    seniority_level = Column(String(50), nullable=True)
    department = Column(String(255), nullable=True)

    # JD content (no PII)
    jd_enriched_json = Column(JSONB, nullable=False)

    # pgvector embedding — column type set by migration 108
    if _HAS_PGVECTOR:
        jd_embedding = Column(Vector(JD_EMBEDDING_DIM), nullable=True)
    else:  # fallback for environments without pgvector loaded yet
        from sqlalchemy.dialects.postgresql import ARRAY
        from sqlalchemy import Float
        jd_embedding = Column(ARRAY(Float), nullable=True)

    # Outcome tracking
    was_filled = Column(Boolean, nullable=False, default=False)
    time_to_fill_days = Column(Integer, nullable=True)
    candidates_count = Column(Integer, nullable=False, default=0)

    # Reuse stats
    reused_count = Column(Integer, nullable=False, default=0)
    last_reused_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        """Serialize for API response (sem dados sensíveis)."""
        return {
            "id": str(self.id),
            "title_normalized": self.title_normalized,
            "department": self.department,
            "seniority_level": self.seniority_level,
            "was_filled": self.was_filled,
            "time_to_fill_days": self.time_to_fill_days,
            "candidates_count": self.candidates_count,
            "reused_count": self.reused_count,
        }
