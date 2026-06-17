"""
HITL Models — Human-in-the-Loop persistence (Sprint F1).

Dois modelos:
  HITLPendingAction — estado atual de cada aprovação pendente/resolvida
  HITLAuditTrail   — log imutável de todas as resoluções (SOX / BCB 498)

Redis permanece como cache fast-path (TTL 24h).
DB é source of truth persistente.
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

try:
    from app.core.database import Base
except ImportError:
    from lia_config.database import Base


class HITLPendingAction(Base):
    """
    Representa uma solicitação de aprovação HITL.
    status: pending | approved | rejected | expired
    """
    __tablename__ = "hitl_pending_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: HITLPendingAction inclui admin overrides system-level (cross-tenant)
    company_id = Column(String(255), nullable=True, index=True)
    thread_id = Column(String(255), nullable=False)
    pending_id = Column(String(255), nullable=False, unique=True)
    domain = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    data = Column(JSONB, nullable=True, default=dict)
    agent_input = Column(JSONB, nullable=True, default=dict)
    ws_session_id = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    approved = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_hitl_pending_thread_id", "thread_id"),
        Index("ix_hitl_pending_status", "status"),
        Index("ix_hitl_pending_expires_at", "expires_at"),
    {"extend_existing": True}, )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "thread_id": self.thread_id,
            "pending_id": self.pending_id,
            "domain": self.domain,
            "action": self.action,
            "description": self.description,
            "data": self.data or {},
            "agent_input": self.agent_input or {},
            "ws_session_id": self.ws_session_id,
            "status": self.status,
            "approved": self.approved,
            "comment": self.comment,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class HITLAuditTrail(Base):
    """
    Log imutável de resoluções HITL.
    Nunca atualizado após insert — auditoria SOX/BCB 498.
    """
    __tablename__ = "hitl_audit_trail"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: HITLAuditTrail cross-tenant compliance log (auditor WeDOTalent)
    company_id = Column(String(255), nullable=True, index=True)
    thread_id = Column(String(255), nullable=False)
    pending_id = Column(String(255), nullable=False)
    domain = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    approved = Column(Boolean, nullable=False)
    comment = Column(Text, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_hitl_audit_thread_id", "thread_id"),
        Index("ix_hitl_audit_pending_id", "pending_id"),
        Index("ix_hitl_audit_resolved_at", "resolved_at"),
    {"extend_existing": True}, )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "thread_id": self.thread_id,
            "pending_id": self.pending_id,
            "domain": self.domain,
            "action": self.action,
            "approved": self.approved,
            "comment": self.comment,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
