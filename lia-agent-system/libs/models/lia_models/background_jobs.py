"""
Background Jobs and Proactive Actions models for the Autonomous Agent System.

Enables LIA to:
- Run background jobs autonomously (screening, sourcing, reports, etc.)
- Schedule recurring tasks with cron expressions
- Create proactive suggestions and notifications
- Take automated actions based on patterns
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
import enum

from lia_config.database import Base


class JobStatus(str, enum.Enum):
    """Status of a background job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    """Types of background jobs LIA can execute."""
    SCREENING = "screening"
    SOURCING = "sourcing"
    REPORT_GENERATION = "report_generation"
    CANDIDATE_OUTREACH = "candidate_outreach"
    MARKET_ANALYSIS = "market_analysis"
    PATTERN_LEARNING = "pattern_learning"


class ActionType(str, enum.Enum):
    """Types of proactive actions."""
    SUGGESTION = "suggestion"
    NOTIFICATION = "notification"
    AUTO_ACTION = "auto_action"


class ActionPriority(str, enum.Enum):
    """Priority levels for proactive actions."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ActionStatus(str, enum.Enum):
    """Status of a proactive action."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


class BackgroundJob(Base):
    """
    Background jobs that run autonomously.
    
    Supports:
    - One-time execution or scheduled (cron) jobs
    - Progress tracking (0-100%)
    - Result storage and error handling
    - Execution history tracking
    """
    __tablename__ = "background_jobs"
    # QW1 audit 2026-05-22: extend_existing=True evita SQLAlchemy
    # InvalidRequestError em hot-reload do uvicorn ("Table background_jobs
    # is already defined") que causava restart-loop e 500s em cascata.
    __table_args__ = {"extend_existing": True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    job_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    status = Column(String(20), default=JobStatus.PENDING.value, index=True)
    progress = Column(Integer, default=0)
    
    config = Column(JSON, default=dict)
    schedule = Column(String(100))
    
    result = Column(JSON)
    error_message = Column(Text)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    next_run_at = Column(DateTime, index=True)
    last_run_at = Column(DateTime)
    run_count = Column(Integer, default=0)
    
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "job_type": self.job_type,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "progress": self.progress,
            "config": self.config or {},
            "schedule": self.schedule,
            "result": self.result,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "run_count": self.run_count,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def start_execution(self) -> None:
        """Mark job as started."""
        self.status = JobStatus.RUNNING.value
        self.started_at = datetime.utcnow()
        self.progress = 0
        self.error_message = None
    
    def complete_execution(self, result: dict = None) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.last_run_at = datetime.utcnow()
        self.progress = 100
        self.run_count = (self.run_count or 0) + 1
        if result:
            self.result = result
    
    def fail_execution(self, error_message: str) -> None:
        """Mark job as failed."""
        self.status = JobStatus.FAILED.value
        self.completed_at = datetime.utcnow()
        self.last_run_at = datetime.utcnow()
        self.error_message = error_message
        self.run_count = (self.run_count or 0) + 1
    
    def cancel(self) -> None:
        """Cancel the job."""
        self.status = JobStatus.CANCELLED.value
        self.updated_at = datetime.utcnow()


class ProactiveAction(Base):
    """
    Proactive actions suggested or taken by LIA.
    
    Supports:
    - Suggestions that require user approval
    - Notifications for important events
    - Auto-executable actions that LIA can perform
    - Priority levels and expiration
    """
    __tablename__ = "proactive_actions"
    # QW1 followup 2026-05-24: bug-gemeo do commit dc835da20 (BackgroundJob ja
    # tinha extend_existing=True, ProactiveAction nao). Mesmo arquivo, mesma
    # classe de bug "Table is already defined for this MetaData instance"
    # ao reimportar via paths diferentes (from lia_models.X vs from libs.models.lia_models.X).
    __table_args__ = {"extend_existing": True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    action_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(20), default=ActionPriority.NORMAL.value)
    
    related_job_id = Column(UUID(as_uuid=True), index=True)
    related_candidate_id = Column(UUID(as_uuid=True), index=True)
    trigger_reason = Column(Text)
    
    suggested_action = Column(JSON)
    auto_executable = Column(Boolean, default=False)
    
    status = Column(String(20), default=ActionStatus.PENDING.value, index=True)
    accepted_by = Column(String(100))
    accepted_at = Column(DateTime)
    executed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "action_type": self.action_type,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "related_job_id": str(self.related_job_id) if self.related_job_id else None,
            "related_candidate_id": str(self.related_candidate_id) if self.related_candidate_id else None,
            "trigger_reason": self.trigger_reason,
            "suggested_action": self.suggested_action or {},
            "auto_executable": self.auto_executable,
            "status": self.status,
            "accepted_by": self.accepted_by,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
    
    def accept(self, user_id: str) -> None:
        """Accept the proactive action."""
        self.status = ActionStatus.ACCEPTED.value
        self.accepted_by = user_id
        self.accepted_at = datetime.utcnow()
    
    def reject(self, user_id: str) -> None:
        """Reject the proactive action."""
        self.status = ActionStatus.REJECTED.value
        self.accepted_by = user_id
        self.accepted_at = datetime.utcnow()
    
    def execute(self) -> None:
        """Mark action as executed."""
        self.status = ActionStatus.EXECUTED.value
        self.executed_at = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if the action has expired."""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False
