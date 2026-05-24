"""
AgentVersionSnapshot — historico de versoes de Custom Agents.

Cada PATCH a um agent cria um snapshot do estado anterior antes de aplicar
a mudanca. Permite timeline visual, diff, e revert.
"""
import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from lia_config.database import Base


class AgentVersionSnapshot(Base):
    __tablename__ = "agent_version_snapshots"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    version = Column(Integer, nullable=False)

    # Snapshot completo do estado anterior
    snapshot_data = Column(JSONB, nullable=False)

    # Campos que mudaram nesta revisao
    changed_fields = Column(ARRAY(String), default=[])
    change_reason = Column(Text, nullable=True)

    changed_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "company_id": self.company_id,
            "version": self.version,
            "snapshot_data": self.snapshot_data or {},
            "changed_fields": self.changed_fields or [],
            "change_reason": self.change_reason,
            "changed_by": self.changed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def summary(self):
        """Lightweight summary for list view (without full snapshot)."""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "version": self.version,
            "changed_fields": self.changed_fields or [],
            "change_reason": self.change_reason,
            "changed_by": self.changed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
