"""
PlannedTask Model - Database model for task planning and decomposition.

PlannedTasks are structured tasks created by the TaskPlannerAgent that support:
- Hierarchical task decomposition (parent/child relationships)
- Dependency management between tasks
- Duration estimation and tracking
- DAG-based execution planning
"""
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, JSON, ForeignKey, Boolean, Integer, Float, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from lia_config.database import Base


class PlannedTaskPriority(str, enum.Enum):
    """Priority levels for planned tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PlannedTaskStatus(str, enum.Enum):
    """Status of planned tasks."""
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlannedTask(Base):
    """
    PlannedTask model for hierarchical task planning with DAG support.
    
    Supports:
    - Parent-child relationships for task decomposition
    - Dependencies array for DAG construction
    - Estimated and actual duration tracking
    - Priority scoring based on multiple factors
    - Agent assignment for execution
    """
    __tablename__ = "planned_tasks"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    agent_type = Column(String(50), nullable=True)
    priority = Column(SQLEnum(PlannedTaskPriority), default=PlannedTaskPriority.MEDIUM)
    priority_score = Column(Float, default=0.0)
    status = Column(SQLEnum(PlannedTaskStatus), default=PlannedTaskStatus.PENDING)
    
    parent_task_id = Column(String, ForeignKey("planned_tasks.id"), nullable=True)
    
    dependencies = Column(ARRAY(String), default=list)
    
    estimated_duration = Column(Integer, nullable=True)
    actual_duration = Column(Integer, nullable=True)
    
    deadline = Column(DateTime, nullable=True)
    
    execution_level = Column(Integer, default=0)
    
    goal_id = Column(String, nullable=True)
    goal_criticality = Column(Float, default=0.5)
    
    related_job_id = Column(String, nullable=True)
    related_candidate_id = Column(String, nullable=True)
    # WT-2022 P0.PLANNED_TASK migration 166 (2026-05-21): NOT NULL aplicado no DB.
    company_id = Column(String, nullable=False)
    
    context = Column(JSON, default=dict)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    chain_of_thought = Column(JSON, default=list)
    
    created_by = Column(String, nullable=True)
    assigned_to_user_id = Column(String, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parent = relationship("PlannedTask", remote_side=[id], backref="subtasks")
    
    def to_dict(self):
        """Convert planned task to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "agent_type": self.agent_type,
            "priority": self.priority.value if self.priority else None,
            "priority_score": self.priority_score,
            "status": self.status.value if self.status else None,
            "parent_task_id": self.parent_task_id,
            "dependencies": self.dependencies or [],
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "execution_level": self.execution_level,
            "goal_id": self.goal_id,
            "goal_criticality": self.goal_criticality,
            "related_job_id": self.related_job_id,
            "related_candidate_id": self.related_candidate_id,
            "company_id": self.company_id,
            "context": self.context,
            "result": self.result,
            "error_message": self.error_message,
            "chain_of_thought": self.chain_of_thought,
            "created_by": self.created_by,
            "assigned_to_user_id": self.assigned_to_user_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_dependents_count(self, all_tasks: list) -> int:
        """Count how many tasks depend on this task."""
        count = 0
        for task in all_tasks:
            if self.id in (task.dependencies or []):
                count += 1
        return count
    
    def is_ready_to_execute(self, completed_task_ids: set) -> bool:
        """Check if all dependencies are completed."""
        if not self.dependencies:
            return True
        return all(dep_id in completed_task_ids for dep_id in self.dependencies)
    
    def __repr__(self):
        return f"<PlannedTask {self.id}: {self.title} ({self.status.value})>"


class ExecutionPlan(Base):
    """
    ExecutionPlan model for storing computed execution plans.
    
    An execution plan represents a DAG of tasks organized into
    execution levels for parallel processing.
    """
    __tablename__ = "execution_plans"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    goal_id = Column(String, nullable=True)
    root_task_id = Column(String, ForeignKey("planned_tasks.id"), nullable=True)
    
    task_ids = Column(ARRAY(String), default=list)
    
    execution_levels = Column(JSON, default=list)
    
    total_estimated_duration = Column(Integer, nullable=True)
    parallel_execution_time = Column(Integer, nullable=True)
    
    status = Column(String(50), default="pending")
    
    # WT-2022 P0.EXECUTION_PLAN migration 167 (2026-05-21): NOT NULL aplicado no DB.
    company_id = Column(String, nullable=False)
    created_by = Column(String, nullable=True)
    
    plan_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert execution plan to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "goal_id": self.goal_id,
            "root_task_id": self.root_task_id,
            "task_ids": self.task_ids or [],
            "execution_levels": self.execution_levels or [],
            "total_estimated_duration": self.total_estimated_duration,
            "parallel_execution_time": self.parallel_execution_time,
            "status": self.status,
            "company_id": self.company_id,
            "created_by": self.created_by,
            "metadata": self.plan_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<ExecutionPlan {self.id}: {self.name} ({self.status})>"
