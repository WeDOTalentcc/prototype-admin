"""
Agent Activity Database Model
Tracks all activities performed by AI agents in the system.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, JSON, Float, Index, Enum as SQLEnum
import enum

from lia_config.database import Base


class ActivityStatus(str, enum.Enum):
    """Status of agent activities."""
    SUCCESS = "success"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    ERROR = "error"


class AgentActivity(Base):
    """
    Agent Activity - Tracks individual actions performed by agents.
    Used in the Agent Control Center for activity feed and metrics.
    """
    __tablename__ = "agent_activities"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    agent_id = Column(String(50), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    agent_icon = Column(String(10), nullable=True, default="🤖")
    
    activity_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    status = Column(SQLEnum(ActivityStatus), default=ActivityStatus.PENDING, index=True)
    
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    duration_seconds = Column(Float, nullable=True)
    
    sla_breach = Column(Boolean, default=False)
    sla_deadline = Column(DateTime, nullable=True)
    
    related_job_id = Column(String(255), nullable=True, index=True)
    related_candidate_id = Column(String(255), nullable=True, index=True)
    # TENANT-EXEMPT: agent activity log inclui system agents (cross-tenant analytics, ADR-LGPD-001)
    company_id = Column(String(255), nullable=True, index=True)
    
    activity_metadata = Column(JSON, default=dict)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_agent_activity_agent_date', 'agent_id', 'started_at'),
        Index('idx_agent_activity_status_date', 'status', 'started_at'),
        {"extend_existing": True},
    )
    
    def __repr__(self):
        return f"<AgentActivity {self.agent_id} - {self.activity_type}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_icon": self.agent_icon,
            "type": self.activity_type,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "sla_breach": self.sla_breach,
            "related_job_id": self.related_job_id,
            "related_candidate_id": self.related_candidate_id,
            "metadata": self.activity_metadata,
            "result_data": self.result_data,
            "error_message": self.error_message,
        }


class AgentMetricsSnapshot(Base):
    """
    Hourly snapshot of agent metrics for trend visualization.
    Stores aggregated metrics per agent per hour.
    """
    __tablename__ = "agent_metrics_snapshots"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    agent_id = Column(String(50), nullable=False, index=True)
    snapshot_hour = Column(DateTime, nullable=False, index=True)
    
    actions_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    avg_response_time = Column(Float, nullable=True)
    
    sla_breaches = Column(Integer, default=0)
    
    utilization_pct = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_metrics_agent_hour', 'agent_id', 'snapshot_hour', unique=True),
        {"extend_existing": True},
    )
    
    def __repr__(self):
        return f"<AgentMetricsSnapshot {self.agent_id} - {self.snapshot_hour}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "agent_id": self.agent_id,
            "snapshot_hour": self.snapshot_hour.isoformat() if self.snapshot_hour else None,
            "actions_count": self.actions_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "avg_response_time": self.avg_response_time,
            "sla_breaches": self.sla_breaches,
            "utilization_pct": self.utilization_pct,
        }
