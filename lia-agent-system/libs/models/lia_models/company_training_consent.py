"""T-11 B.1.2: CompanyTrainingConsent canonical model.

Tenant-level opt-in para training data export (ADR-RLHF-001 + ADR-LGPD-002).
Empresa admin opta in/out para que conversations da LIA com seus recrutadores
sejam usadas em fine-tune Anthropic Claude via AWS Bedrock.

Diferença vs LGPDConsent/ConsentRecord:
- ConsentRecord/LGPDConsent: candidate-level (consent do candidato)
- CompanyTrainingConsent: tenant-level (consent da empresa via admin)

Refs:
- ADR-RLHF-001 (T-11 Bedrock fine-tune pipeline)
- ADR-LGPD-002 (training data anonymizer)
- LGPD Art. 7 §I (consentimento) + Art. 33 (cross-border)
- BLOCKING_PURPOSES inclui "training_data" (T-11 B.1.1)
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class CompanyTrainingConsent(Base):
    """Tenant-level training data export consent (T-11 ADR-RLHF-001).

    Unique constraint canonical: 1 record per company_id (UPSERT pattern).
    Lifecycle:
    1. INSERT default (consent_given=False) on company creation (event-driven)
    2. UPDATE consent_given=True + granted_at quando admin opta in via UI
    3. UPDATE revoked_at + revoke_reason quando admin revoga
       (training_data em BLOCKING_PURPOSES — revoke cascata erasure cross-border)

    Erasure cascade canonical:
    - revoked_at SET → list_quality_feedback retorna [] para company_id
    - existing fine-tuned models NÃO são afetados retroativamente
      (modelos already-trained vivem na conta AWS Bedrock WeDOTalent)
    - novos exports BLOCKED (fail-CLOSED via filter B.1.3)
    """

    __tablename__ = "company_training_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Consent state
    consent_given = Column(Boolean, default=False, nullable=False, index=True)
    granted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True, index=True)

    # Versioning canonical (ADR-LGPD-002 anonymizer version compat)
    version = Column(String(20), default="1.0", nullable=False)
    legal_basis = Column(String(50), default="LGPD_ART_7_I", nullable=False)

    # Audit trail
    consent_source = Column(String(50), nullable=True)  # admin_ui, api, csv_import
    consent_text = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_id_granted = Column(String(100), nullable=True)  # admin who opted in
    user_id_revoked = Column(String(100), nullable=True)  # admin who opted out
    revoke_reason = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Constraint canonical: 1 active consent per company
    __table_args__ = (
        UniqueConstraint(
            "company_id", name="uq_company_training_consents_company_id"
        ),
        Index(
            "idx_company_training_consents_active",
            "company_id",
            "consent_given",
            "revoked_at",
        ),
    {"extend_existing": True}, )

    def __repr__(self):
        state = "granted" if self.consent_given and not self.revoked_at else "denied"
        return f"<CompanyTrainingConsent {self.company_id} - {state}>"

    @property
    def is_active(self) -> bool:
        """Canonical active check: consent_given=True AND not revoked."""
        return bool(self.consent_given) and self.revoked_at is None

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "consent_given": self.consent_given,
            "is_active": self.is_active,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "version": self.version,
            "legal_basis": self.legal_basis,
            "consent_source": self.consent_source,
            "user_id_granted": self.user_id_granted,
            "user_id_revoked": self.user_id_revoked,
            "revoke_reason": self.revoke_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
