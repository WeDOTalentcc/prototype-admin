"""
AgentApprovalRequest — Workflow de aprovacao para Studio agents.

Enterprise requirement: manager/admin aprova antes do agent ir para producao.
Flow: draft -> pending_approval -> approved/rejected -> active
"""
import enum
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from lia_config.database import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AgentApprovalRequest(Base):
    __tablename__ = "agent_approval_requests"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("custom_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    requested_by = Column(String(128), nullable=False)
    reviewed_by = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    review_notes = Column(Text, nullable=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # GAP-4 fix: ORM relationship para cascade delete automatico (migration 285)
    agent = relationship("CustomAgent", back_populates="approval_requests", foreign_keys=[agent_id])

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "company_id": self.company_id,
            "requested_by": self.requested_by,
            "reviewed_by": self.reviewed_by,
            "status": self.status,
            "review_notes": self.review_notes,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
