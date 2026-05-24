"""
Task Model - Database model for agent-generated tasks.

Tasks are created by agents and can be assigned to other agents
or human users (recruiters).
"""
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, JSON, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from lia_config.database import Base


class TaskPriority(str, enum.Enum):
    """Priority levels for tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, enum.Enum):
    """Status of tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    """Types of tasks."""
    FEEDBACK_PENDING = "feedback_pending"
    INTERVIEW_SCHEDULE = "interview_schedule"
    CV_REVIEW = "cv_review"
    SEND_REPORT = "send_report"
    SOURCING = "sourcing"
    ALERT = "alert"
    FOLLOW_UP = "follow_up"
    GENERAL = "general"


class Task(Base):
    """
    Task model for tracking agent and user tasks.
    """
    __tablename__ = "tasks"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    task_type = Column(SQLEnum(TaskType), default=TaskType.GENERAL)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    
    # WT-2022 P0.TASK cross-tenant fix (2026-05-21): tenant scoping column.
    # TODO migration próxima sprint: backfill por assigned_to_user_id->users.company_id
    # e then ALTER COLUMN nullable=False. Por ora nullable=True para não quebrar rows legacy,
    # MAS repo SEMPRE filtra por company_id (defense in depth via Depends(require_company_id)).
    # WT-2022 P0.TASK migration 161 (2026-05-21): NOT NULL aplicado no DB. Python model alinhado.
    company_id = Column(String(255), nullable=False, index=True)

    created_by_agent = Column(String(50), nullable=True)
    assigned_to_agent = Column(String(50), nullable=True)
    assigned_to_user_id = Column(String, nullable=True)
    
    related_job_id = Column(String, nullable=True)
    related_candidate_id = Column(String, nullable=True)
    
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    context = Column(JSON, default=dict)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    is_automated = Column(Boolean, default=False)
    requires_confirmation = Column(Boolean, default=False)
    
    reminder_sent = Column(Boolean, default=False)
    reminder_count = Column(Integer, default=0)
    
    confirmed_by = Column(String, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    rejected_by = Column(String, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    escalated_to = Column(String, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    escalation_reason = Column(Text, nullable=True)
    escalation_level = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type.value if self.task_type else None,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "created_by_agent": self.created_by_agent,
            "assigned_to_agent": self.assigned_to_agent,
            "assigned_to_user_id": self.assigned_to_user_id,
            "related_job_id": self.related_job_id,
            "related_candidate_id": self.related_candidate_id,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "context": self.context,
            "is_automated": self.is_automated,
            "requires_confirmation": self.requires_confirmation,
            "reminder_sent": self.reminder_sent,
            "reminder_count": self.reminder_count,
            "confirmed_by": self.confirmed_by,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "rejected_by": self.rejected_by,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_reason": self.rejection_reason,
            "escalated_to": self.escalated_to,
            "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
            "escalation_reason": self.escalation_reason,
            "escalation_level": self.escalation_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Task {self.id}: {self.title} ({self.status.value})>"


class TaskTemplate(Base):
    """
    Task template for common recurring tasks.
    """
    __tablename__ = "task_templates"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    task_type = Column(SQLEnum(TaskType), default=TaskType.GENERAL)
    default_priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    
    title_template = Column(String(255), nullable=False)
    description_template = Column(Text, nullable=True)
    
    default_due_days = Column(Integer, nullable=True)
    
    assigned_agent = Column(String(50), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    context_schema = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value if self.task_type else None,
            "default_priority": self.default_priority.value if self.default_priority else None,
            "title_template": self.title_template,
            "description_template": self.description_template,
            "default_due_days": self.default_due_days,
            "assigned_agent": self.assigned_agent,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
