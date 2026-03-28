import uuid
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class AgentTask:
    task_id: str
    domain_id: str
    action_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 1
    is_critical: bool = True
    context_mappings: Dict[str, str] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def is_done(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)

    @property
    def duration_ms(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "domain_id": self.domain_id,
            "action_id": self.action_id,
            "params": self.params,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "error": self.error,
            "retry_count": self.retry_count,
            "is_critical": self.is_critical,
            "duration_ms": self.duration_ms,
        }


class ExecutionPlan:
    def __init__(self, tasks: Optional[List[AgentTask]] = None, plan_id: Optional[str] = None):
        self.plan_id: str = plan_id or str(uuid.uuid4())[:8]
        self.tasks: List[AgentTask] = tasks or []
        self.status: PlanStatus = PlanStatus.PENDING
        self.context_data: Dict[str, Any] = {}
        self.created_at: datetime = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.original_query: str = ""
        self.detected_pattern: str = ""

    def add_task(self, task: AgentTask) -> None:
        self.tasks.append(task)

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    def get_next_tasks(self) -> List[AgentTask]:
        completed_ids = {t.task_id for t in self.tasks if t.status == TaskStatus.COMPLETED}
        ready = []
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            if all(dep in completed_ids for dep in task.depends_on):
                ready.append(task)
        return ready

    def update_task_result(self, task_id: str, result: Any, success: bool = True, error: Optional[str] = None) -> None:
        task = self.get_task(task_id)
        if task:
            task.result = result
            task.completed_at = datetime.utcnow()
            if success:
                task.status = TaskStatus.COMPLETED
            else:
                task.error = error
                task.status = TaskStatus.FAILED

    def inject_context(self, key: str, value: Any) -> None:
        self.context_data[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self.context_data.get(key, default)

    @property
    def is_complete(self) -> bool:
        return all(t.is_done for t in self.tasks)

    @property
    def has_failures(self) -> bool:
        return any(t.status == TaskStatus.FAILED for t in self.tasks)

    @property
    def all_succeeded(self) -> bool:
        return all(t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED) for t in self.tasks)

    def get_summary(self) -> Dict[str, Any]:
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        skipped = sum(1 for t in self.tasks if t.status == TaskStatus.SKIPPED)
        pending = sum(1 for t in self.tasks if t.status == TaskStatus.PENDING)
        total_duration = sum(t.duration_ms or 0 for t in self.tasks)

        return {
            "plan_id": self.plan_id,
            "status": self.status.value,
            "total_tasks": len(self.tasks),
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "pending": pending,
            "total_duration_ms": total_duration,
            "detected_pattern": self.detected_pattern,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    def __repr__(self) -> str:
        return f"<ExecutionPlan id={self.plan_id} tasks={len(self.tasks)} status={self.status.value}>"
