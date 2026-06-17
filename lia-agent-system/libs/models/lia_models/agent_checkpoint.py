"""
Agent Checkpoint model — persistent state for LangGraph-style agents.

Allows any agent's state dict to be saved and restored by session_id,
providing fault tolerance when the process restarts between user turns.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

from lia_config.database import Base


class AgentCheckpoint(Base):
    """
    Stores serialized agent state per session.

    One row per (session_id, agent_type) — upserted on each completed
    graph execution. When the process restarts, the agent restores state
    from this row instead of starting from scratch.
    """
    __tablename__ = "agent_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identifies the ongoing conversation / wizard session
    session_id = Column(String(255), nullable=False, index=True)

    # Which agent owns this checkpoint (job_wizard, pipeline, etc.)
    agent_type = Column(String(100), nullable=False)

    # Multi-tenant isolation
    # TENANT-EXEMPT: checkpoints de agentes system-level (orchestrator global)
    company_id = Column(String(255), nullable=True, index=True)

    # The full serialized state (TypedDict → JSON)
    state_json = Column(JSON, nullable=False, default={})

    # Housekeeping
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_agent_checkpoints_session_type", "session_id", "agent_type", unique=True),
    {"extend_existing": True}, )

    def __repr__(self):
        return f"<AgentCheckpoint session={self.session_id} agent={self.agent_type}>"
