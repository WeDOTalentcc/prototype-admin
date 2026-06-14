"""SQLAlchemy model for FairnessGuard audit log (EU AI Act compliance)."""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from lia_config.database import Base


class FairnessAuditLog(Base):
    """
    Records every FairnessGuard check that blocked a query or generated warnings.

    Used for:
    - EU AI Act transparency requirements (temporal audit trail)
    - Recruiter coaching (which categories trigger most blocks)
    - Company-level bias pattern analysis
    """

    __tablename__ = "fairness_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: FairnessAuditLog cross-tenant analytics (ADR-LGPD-001 anonimizacao agregada)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    recruiter_id = Column(UUID(as_uuid=True), nullable=True)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True)

    # SHA-256 of the original query — allows dedup without storing PII
    query_hash = Column(String(64), nullable=False)

    # Bias category detected (genero | raca_etnia | idade | ...)
    category = Column(String(50), nullable=True, index=True)

    # JSON array of matched discriminatory terms
    blocked_terms = Column(JSONB, nullable=True)

    # Confidence score from pattern matching
    confidence = Column(Float, nullable=True)

    # True = request was blocked; False = only soft warnings
    is_blocked = Column(Boolean, nullable=False, default=False, index=True)

    # Where in the system the check was triggered: pipeline | wizard | sourcing | search
    context = Column(String(100), nullable=True)

    # FAR-5: Soft warnings gerados pelo Layer 2 (léxico implícito) — nullable para compatibilidade
    soft_warnings = Column(JSONB, nullable=True)

    # Fix D: correlaciona com sessao SSE para trail de observabilidade
    session_id = Column(String(100), nullable=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_fairness_company_date", "company_id", "created_at"),
    {"extend_existing": True}, )

    def __repr__(self) -> str:
        return (
            f"<FairnessAuditLog id={self.id} category={self.category} "
            f"is_blocked={self.is_blocked} context={self.context}>"
        )
