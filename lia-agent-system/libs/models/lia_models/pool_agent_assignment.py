"""SQLAlchemy model for PoolAgentAssignment — Sub-sprint 7A canonical M2M.

Tabela `pool_agent_assignments` criada na migration 202.
Source of truth pra assignment talent_pool <-> custom_agent.

Multi-tenancy invariant: company_id redundante com pool.company_id e agent.company_id.
Repo `PoolAgentAssignmentRepository` enforca consistency em insert.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from lia_config.database import Base


class PoolAgentAssignment(Base):
    __tablename__ = "pool_agent_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(36), nullable=False, index=True)

    talent_pool_id = Column(
        UUID(as_uuid=True),
        ForeignKey("talent_pools.id", ondelete="CASCADE"),
        nullable=False,
    )
    custom_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False,
    )

    status = Column(String(16), nullable=False, default="active")
    config_overrides = Column(JSONB, nullable=False, default=dict)
    schedule_type = Column(String(16), nullable=False, default="on_demand")
    schedule_config = Column(JSONB, nullable=False, default=dict)

    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_run_status = Column(String(16), nullable=True)
    runtime_metrics = Column(JSONB, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    created_by = Column(String(36), nullable=False)

    # Sprint 7B-3a Part 1.5 v2 (2026-05-26): reverse relationship opcional pra SourcingAgentSignal.
    # assignment_id no signal é nullable (ON DELETE SET NULL), então cascade NÃO é delete-orphan.
    signals = relationship(
        "SourcingAgentSignal",
        back_populates="assignment",
    )

    __table_args__ = (
        UniqueConstraint("talent_pool_id", "custom_agent_id", name="uq_pool_agent"),
        CheckConstraint(
            "schedule_type IN ('on_demand','cron','event_driven')",
            name="chk_paa_schedule_type",
        ),
        CheckConstraint(
            "status IN ('active','paused','completed','error')",
            name="chk_paa_status",
        ),
        Index("idx_paa_company", "company_id"),
        Index("idx_paa_pool", "talent_pool_id"),
        Index("idx_paa_agent", "custom_agent_id"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return (
            f"<PoolAgentAssignment id={self.id} pool={self.talent_pool_id} "
            f"agent={self.custom_agent_id} schedule={self.schedule_type} status={self.status}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "talent_pool_id": str(self.talent_pool_id),
            "custom_agent_id": str(self.custom_agent_id),
            "status": self.status,
            "config_overrides": self.config_overrides or {},
            "schedule_type": self.schedule_type,
            "schedule_config": self.schedule_config or {},
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_run_status": self.last_run_status,
            "runtime_metrics": self.runtime_metrics or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }
