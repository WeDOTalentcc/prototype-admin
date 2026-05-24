"""
LGPD reference tables: LegalBasis and ConsentVersion.
Used by Candidate to record the legal ground for data processing (LGPD Art.7+18).
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class LegalBasis(Base):
    """
    LGPD Art.7 legal bases for data processing.
    Examples: consent, legitimate_interest, contract, legal_obligation
    """
    __tablename__ = "lgpd_legal_bases"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), nullable=False, unique=True)  # e.g. "consent", "legitimate_interest"
    description_pt = Column(Text, nullable=False)  # in Portuguese for DPO
    lgpd_article = Column(String(50), nullable=True)  # e.g. "Art. 7, inciso I"
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<LegalBasis {self.code}: {self.lgpd_article}>"


class ConsentVersion(Base):
    """
    Versions of the consent form presented to candidates.
    When a candidate gives consent, we record which version they agreed to.
    """
    __tablename__ = "lgpd_consent_versions"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(50), nullable=False, unique=True)  # e.g. "v1.0", "v2.3"
    effective_from = Column(DateTime(timezone=True), nullable=False)
    content_hash = Column(String(64), nullable=True)  # SHA-256 of the consent text
    changes_summary = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ConsentVersion {self.version}>"
