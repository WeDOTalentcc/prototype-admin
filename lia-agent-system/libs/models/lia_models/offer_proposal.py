"""
OfferProposal model — canonical hybrid schema.

Sprint F.4 (#42/#46) canonical resolution: hybrid schema — DB canonical
(multi-round, approval workflow, multi-channel send, analytical events,
rendered letter content) + 4 ADDITIONS from new version
(LGPD snapshots, Numeric salary, status CHECK, cancellation tracking).
"""
from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index,
    LargeBinary, Numeric, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from lia_config.database import Base
from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin


class OfferProposal(EncryptedFieldMixin, Base):
    """Carta-oferta estruturada — canonical hybrid (DB-canonical + 4 additions).

    Schema source of truth: tabela ``offer_proposals`` no Postgres (canonical).
    Suporta multi-round negotiation, approval workflow, multi-channel send,
    eventos analiticos (E11/E12), e conteudo renderizado da carta.

    Sprint F.4 additions (non-destructive, mantidas do "new version" anterior):
      1. ``job_data_snapshot`` / ``candidate_data_snapshot`` JSONB NOT NULL DEFAULT '{}'
         — snapshot LGPD imutavel apos status=sent (ADR-LGPD-001 Art. 12).
      2. ``salary`` declarado Numeric(12, 2) (DB migrado de double precision).
      3. CHECK constraint ``chk_offer_status`` no DB nivel.
      4. ``cancelled_at`` / ``cancelled_by_user_id`` para tracking de cancelamento.
    """
    __tablename__ = "offer_proposals"
    __table_args__ = (
        Index("ix_offer_proposals_candidate_id", "candidate_id"),
        Index("ix_offer_proposals_company_id", "company_id"),
        Index("ix_offer_proposals_job_vacancy_id", "job_vacancy_id"),
        Index("ix_offer_proposals_status", "status"),
        Index("ix_offer_proposals_vacancy_candidate_id", "vacancy_candidate_id"),
        # Camada 3 Item 3 (2026-05-22, migration 172): composite index
        # for per-department approver lookup hot path in
        # OfferService._has_eligible_approver_for_amount.
        Index("ix_offer_proposals_company_department", "company_id", "department_id"),
        CheckConstraint(
            "status IN ('draft','sent','accepted','declined','expired','cancelled')",
            name="chk_offer_status",
        ),
    {"extend_existing": True}, )

    # P0.B (audit 2026-05-21, migration 160): candidate_email encrypted at rest
    # via EncryptedFieldMixin canonical. Caller-side: zero mudanca.
    _pii_encrypt_fields = [
        ("_candidate_email_raw", "_candidate_email_encrypted", "candidate_email_hash"),
    ]

    # Identidade + tenancy
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False)

    # FKs (job + candidato + vacancy_candidate)
    job_vacancy_id = Column(UUID(as_uuid=True), nullable=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True)
    vacancy_candidate_id = Column(UUID(as_uuid=True), nullable=True)

    # Camada 3 Item 3 (2026-05-22, migration 172): per-department approver
    # routing. NULL = offer sem associacao explicita de departamento
    # (backward-compat). Hot-path indexed em __table_args__ acima
    # (ix_offer_proposals_company_department).
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Display denormalizado (cache para listagens / cartas)
    candidate_name = Column(String(255), nullable=False)
    # P0.B (migration 160): plaintext column kept para dual-write transition.
    # Access via hybrid_property ``candidate_email`` registered by mixin.
    _candidate_email_raw = Column("candidate_email", String(255), nullable=True)
    _candidate_email_encrypted = Column("candidate_email_encrypted", LargeBinary, nullable=True)
    candidate_email_hash = Column(String(64), nullable=True, index=True)
    job_title = Column(String(255), nullable=True)

    # Compensacao
    currency = Column(String(8), nullable=True, default="BRL")
    salary = Column(Numeric(12, 2), nullable=True)
    bonus_pct = Column(Numeric, nullable=True)  # double precision in DB; Numeric ok
    bonus_target = Column(Numeric, nullable=True)
    benefits = Column(JSONB, nullable=True, default=list)

    # Datas
    start_date = Column(DateTime, nullable=True)
    response_deadline = Column(DateTime, nullable=True)

    # Clausulas customizadas + conteudo renderizado da carta
    custom_clauses = Column(JSONB, nullable=True, default=list)
    letter_markdown = Column(Text, nullable=True)
    letter_html = Column(Text, nullable=True)
    template_version = Column(String(32), nullable=True)
    llm_provider = Column(String(32), nullable=True)
    llm_model = Column(String(64), nullable=True)

    # Estado + multi-round negotiation
    status = Column(String(32), nullable=False, default="draft")
    current_round = Column(Numeric, nullable=True, default=0)
    rounds = Column(JSONB, nullable=True, default=list)

    # Approval workflow
    approval_request_id = Column(UUID(as_uuid=True), nullable=True)
    approval_required_level = Column(String(32), nullable=True)

    # Envio multi-canal + resposta
    sent_at = Column(DateTime, nullable=True)
    sent_via = Column(JSONB, nullable=True, default=list)
    candidate_responded_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    decline_reason = Column(Text, nullable=True)

    # Eventos analiticos
    e11_triggered = Column(Boolean, nullable=True, default=False)
    e12_triggered = Column(Boolean, nullable=True, default=False)

    # Audit
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # === Sprint F.4 ADDITIONS (4 non-destructive) ===
    # 1. LGPD snapshots (ADR-LGPD-001 Art. 12 — imutaveis apos status=sent)
    job_data_snapshot = Column(JSONB, nullable=False, default=dict, server_default="{}")
    candidate_data_snapshot = Column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    # 4. Cancellation tracking
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by_user_id = Column(String(255), nullable=True)


    # === Migration 266 ADDITIONS — offer portal + negotiation (Phase 1) ===
    # Portal access (N1 candidate-facing)
    candidate_token = Column(UUID(as_uuid=True), nullable=True, unique=True, index=True)
    acceptance_url = Column(Text, nullable=True)
    offer_link_sent_at = Column(DateTime, nullable=True)

    # Portal engagement tracking
    candidate_viewed_at = Column(DateTime, nullable=True)
    candidate_response_notes = Column(Text, nullable=True)

    # Internal negotiation context (N2/N3 concierge — never exposed to candidate)
    negotiation_context_notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<OfferProposal {self.id} candidate={self.candidate_id} "
            f"status={self.status}>"
        )
