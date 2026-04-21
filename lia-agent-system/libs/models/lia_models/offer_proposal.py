"""
Offer Proposal models for E10 (Proposta & Negociação).

Stores the lifecycle of a hire proposal: draft, internally approved,
sent to the candidate, negotiated through one or more rounds, and
finally accepted or declined.

Each negotiation event is appended to ``rounds`` (JSON) as an audit
trail; high-level status transitions live on the parent row.
"""
from datetime import datetime
import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class OfferStatus(str, enum.Enum):
    DRAFT = "draft"                       # carta gerada, ainda não foi para aprovação interna
    PENDING_APPROVAL = "pending_approval" # em aprovação interna (ApprovalChain)
    APPROVED = "approved"                 # aprovada internamente, pronta para envio
    REJECTED = "rejected"                 # aprovação interna negada (chain rejeitou)
    SENT = "sent"                         # enviada ao candidato
    NEGOTIATING = "negotiating"           # candidato pediu contraproposta
    ACCEPTED = "accepted"                 # candidato aceitou → trigger E11
    DECLINED = "declined"                 # candidato recusou → trigger E12
    EXPIRED = "expired"                   # prazo de resposta venceu
    WITHDRAWN = "withdrawn"               # empresa retirou a proposta


class OfferRoundType(str, enum.Enum):
    INITIAL = "initial"
    COUNTER_FROM_CANDIDATE = "counter_from_candidate"
    COUNTER_FROM_COMPANY = "counter_from_company"
    ACCEPT = "accept"
    DECLINE = "decline"
    WITHDRAW = "withdraw"
    APPROVAL = "approval"
    REJECTION = "rejection"
    NOTE = "note"


class OfferProposal(Base):
    """
    Carta-proposta com histórico estruturado de negociação.

    ``rounds`` é a fonte de verdade do audit trail por rodada. Cada
    item tem o shape:

        {
          "round": int,
          "type": "initial|counter_from_candidate|...",
          "actor": "company|candidate|approver",
          "actor_name": str,
          "actor_email": str,
          "salary": float | null,
          "bonus_pct": float | null,
          "currency": str,
          "benefits": [str],
          "message": str,
          "created_at": iso8601,
        }
    """
    __tablename__ = "offer_proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)

    # Vínculos com o resto do pipeline
    job_vacancy_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    vacancy_candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Snapshot do candidato (para evitar quebras se o candidato for removido)
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)

    # Termos da proposta (valores correntes — última rodada efetiva)
    currency = Column(String(8), default="BRL")
    salary = Column(Float, nullable=True)
    bonus_pct = Column(Float, nullable=True)
    bonus_target = Column(Float, nullable=True)
    benefits = Column(JSON, default=list)
    start_date = Column(DateTime, nullable=True)
    response_deadline = Column(DateTime, nullable=True)
    custom_clauses = Column(JSON, default=list)

    # Carta gerada (Markdown + HTML) e meta do template
    letter_markdown = Column(Text, nullable=True)
    letter_html = Column(Text, nullable=True)
    template_version = Column(String(32), nullable=True)
    llm_provider = Column(String(32), nullable=True)
    llm_model = Column(String(64), nullable=True)

    # Lifecycle
    status = Column(String(32), nullable=False, default=OfferStatus.DRAFT.value, index=True)
    current_round = Column(Float, default=0)
    rounds = Column(JSON, default=list)

    # Aprovação interna
    approval_request_id = Column(UUID(as_uuid=True), nullable=True)
    approval_required_level = Column(String(32), nullable=True)  # manager | director | vp_or_cfo

    # Comunicação
    sent_at = Column(DateTime, nullable=True)
    sent_via = Column(JSON, default=list)  # ["email", "whatsapp"]
    candidate_responded_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    decline_reason = Column(Text, nullable=True)

    # Triggers downstream
    e11_triggered = Column(Boolean, default=False)
    e12_triggered = Column(Boolean, default=False)

    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "job_vacancy_id": str(self.job_vacancy_id) if self.job_vacancy_id else None,
            "candidate_id": str(self.candidate_id) if self.candidate_id else None,
            "vacancy_candidate_id": str(self.vacancy_candidate_id) if self.vacancy_candidate_id else None,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "job_title": self.job_title,
            "currency": self.currency,
            "salary": self.salary,
            "bonus_pct": self.bonus_pct,
            "bonus_target": self.bonus_target,
            "benefits": self.benefits or [],
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "response_deadline": self.response_deadline.isoformat() if self.response_deadline else None,
            "custom_clauses": self.custom_clauses or [],
            "letter_markdown": self.letter_markdown,
            "letter_html": self.letter_html,
            "template_version": self.template_version,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "status": self.status,
            "current_round": int(self.current_round or 0),
            "rounds": self.rounds or [],
            "approval_request_id": str(self.approval_request_id) if self.approval_request_id else None,
            "approval_required_level": self.approval_required_level,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "sent_via": self.sent_via or [],
            "candidate_responded_at": self.candidate_responded_at.isoformat() if self.candidate_responded_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "declined_at": self.declined_at.isoformat() if self.declined_at else None,
            "decline_reason": self.decline_reason,
            "e11_triggered": bool(self.e11_triggered),
            "e12_triggered": bool(self.e12_triggered),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
