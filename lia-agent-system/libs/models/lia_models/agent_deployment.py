"""
AgentDeployment — Binds a Studio agent to a target (job, talent pool, pipeline stage, list).

An agent without a deployment is a draft/template. Deployments connect agents to
the real recruiting flow, enabling automatic execution via automation triggers.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from lia_config.database import Base


class DeploymentTargetType(str, enum.Enum):
    JOB = "job"
    TALENT_POOL = "talent_pool"
    PIPELINE_STAGE = "pipeline_stage"
    CANDIDATE_LIST = "candidate_list"


class DeploymentTriggerMode(str, enum.Enum):
    MANUAL = "manual"
    ON_NEW_CANDIDATE = "on_new_candidate"
    ON_STAGE_CHANGE = "on_stage_change"
    SCHEDULED = "scheduled"


class AgentDeployment(Base):
    """Binds a CustomAgent to a target environment for execution."""

    __tablename__ = "agent_deployments"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("custom_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)

    # WHERE the agent operates
    target_type = Column(String(32), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    target_name = Column(String(512), nullable=True)

    # WHEN the agent runs
    trigger_mode = Column(String(32), nullable=False, default="manual")
    schedule_cron = Column(String(128), nullable=True)

    # CONFIG
    is_active = Column(Boolean, default=True, nullable=False)
    config_overrides = Column(JSONB, default={})

    # METRICS
    execution_count = Column(Integer, default=0, nullable=False)
    last_execution_at = Column(DateTime(timezone=True), nullable=True)
    candidates_processed = Column(Integer, default=0, nullable=False)

    # AUDIT
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # GAP-4 fix: ORM relationship para cascade delete automatico (migration 285)
    agent = relationship("CustomAgent", back_populates="deployments", foreign_keys=[agent_id])

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "company_id": self.company_id,
            "target_type": self.target_type,
            "target_id": str(self.target_id),
            "target_name": self.target_name,
            "trigger_mode": self.trigger_mode,
            "schedule_cron": self.schedule_cron,
            "is_active": self.is_active,
            "config_overrides": self.config_overrides or {},
            "execution_count": self.execution_count,
            "last_execution_at": self.last_execution_at.isoformat() if self.last_execution_at else None,
            "candidates_processed": self.candidates_processed,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
