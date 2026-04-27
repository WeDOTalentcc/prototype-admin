"""
OfferProposal model — carta-oferta estruturada com LGPD-compliant snapshots.
"""
from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Index,
    Integer, Numeric, String, Text, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from lia_config.database import Base


class OfferProposal(Base):
    """
    Carta-oferta estruturada enviada a um candidato.

    Snapshots JSONB de job_data e candidate_data sao imutaveis apos
    status=sent para garantir rastreabilidade LGPD da proposta enviada.
    """
    __tablename__ = "offer_proposals"
    __table_args__ = (
        Index("ix_offer_proposals_company", "company_id"),
        Index("ix_offer_proposals_candidate", "candidate_id"),
        Index("ix_offer_proposals_job", "job_id"),
        Index("ix_offer_proposals_status", "status"),
        Index("ix_offer_proposals_company_candidate", "company_id", "candidate_id"),
        CheckConstraint(
            "status IN ('draft','sent','accepted','declined','expired','cancelled')",
            name="chk_offer_status",
        ),
        CheckConstraint(
            "send_mode IN ('auto','manual') OR send_mode IS NULL",
            name="chk_offer_send_mode",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)

    candidate_id = Column(String(255), nullable=False)
    job_id = Column(UUID(as_uuid=True), nullable=False)

    # FK para email_templates (template usado para o envio)
    template_id = Column(UUID(as_uuid=True), nullable=True)

    # Snapshots imutaveis (LGPD: dados da epoca do envio)
    job_data_snapshot = Column(JSONB, nullable=False, default=dict)
    candidate_data_snapshot = Column(JSONB, nullable=False, default=dict)

    # Campos estruturados da carta-oferta
    offered_salary = Column(Numeric(12, 2), nullable=True)
    offered_salary_currency = Column(String(10), default="BRL")
    offered_bonus_admission = Column(Numeric(12, 2), nullable=True)
    offered_bonus_variable = Column(JSONB, nullable=True)
    offered_benefits = Column(JSONB, nullable=True)
    offered_start_date = Column(Date, nullable=True)
    validity_days = Column(Integer, default=7)
    expires_at = Column(DateTime, nullable=True)

    # Notas livres do recrutador (nao enviadas ao candidato)
    recruiter_notes = Column(Text, nullable=True)

    # Estado da proposta
    status = Column(String(20), nullable=False, default="draft", index=True)
    send_mode = Column(String(20), nullable=True)  # 'auto' | 'manual'

    # Referencia ao log de email (preenchida apos send_auto)
    email_log_id = Column(UUID(as_uuid=True), nullable=True)

    # Resposta do candidato
    candidate_response_at = Column(DateTime, nullable=True)
    candidate_response_message = Column(Text, nullable=True)
    declined_reason = Column(String(50), nullable=True)

    # Audit trail
    created_by_user_id = Column(String(255), nullable=False)
    sent_by_user_id = Column(String(255), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by_user_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<OfferProposal {self.id} candidate={self.candidate_id} status={self.status}>"
