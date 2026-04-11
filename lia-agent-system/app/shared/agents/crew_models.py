"""
CrewAI-Style Delegation Models — Pydantic models for AgentCrew orchestration.

Defines:
- CrewRole: declarative role assignments (leader, researcher, executor, reviewer)
- CrewTask: individual task within a crew plan with DAG dependencies
- CrewPlan: DAG-based execution plan with sequenced tasks
- AgentCrew: crew definition with roles and shared context
- CrewExecutionResult: result of a crew execution
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CrewRoleType(StrEnum):
    LEADER = "leader"
    RESEARCHER = "researcher"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"


class CrewTaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"


class CrewExecutionStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class CrewRole(BaseModel):
    agent_name: str
    role_type: CrewRoleType
    description: str = ""
    capabilities: list[str] = Field(default_factory=list)


class CrewTask(BaseModel):
    task_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    assigned_agent: str
    action: str
    description: str = ""
    params: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    timeout_seconds: float = 30.0
    is_critical: bool = True
    max_retries: int = 1
    retry_count: int = 0
    status: CrewTaskStatus = CrewTaskStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    context_mappings: dict[str, str] = Field(default_factory=dict)

    @property
    def is_done(self) -> bool:
        return self.status in (
            CrewTaskStatus.COMPLETED,
            CrewTaskStatus.FAILED,
            CrewTaskStatus.SKIPPED,
            CrewTaskStatus.TIMED_OUT,
        )

    @property
    def duration_ms(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None


class CrewPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    description: str = ""
    tasks: list[CrewTask] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_next_tasks(self) -> list[CrewTask]:
        resolved_ids = {
            t.task_id for t in self.tasks
            if t.status in (CrewTaskStatus.COMPLETED, CrewTaskStatus.SKIPPED)
        }
        ready = []
        for task in self.tasks:
            if task.status != CrewTaskStatus.PENDING:
                continue
            if all(dep in resolved_ids for dep in task.depends_on):
                ready.append(task)
        return ready

    def get_task(self, task_id: str) -> CrewTask | None:
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    @property
    def is_complete(self) -> bool:
        return all(t.is_done for t in self.tasks)

    @property
    def has_failures(self) -> bool:
        return any(
            t.status in (CrewTaskStatus.FAILED, CrewTaskStatus.TIMED_OUT)
            for t in self.tasks
        )

    @property
    def all_succeeded(self) -> bool:
        return all(
            t.status in (CrewTaskStatus.COMPLETED, CrewTaskStatus.SKIPPED)
            for t in self.tasks
        )

    def validate_dag(self) -> list[str]:
        task_ids = {t.task_id for t in self.tasks}
        errors: list[str] = []
        for task in self.tasks:
            for dep in task.depends_on:
                if dep not in task_ids:
                    errors.append(f"Task '{task.task_id}' depends on unknown task '{dep}'")

        visited: set[str] = set()
        rec_stack: set[str] = set()
        adj: dict[str, list[str]] = {t.task_id: list(t.depends_on) for t in self.tasks}

        def _has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if _has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        for tid in task_ids:
            if tid not in visited:
                if _has_cycle(tid):
                    errors.append("Cyclic dependency detected in task DAG")
                    break

        return errors

    def get_summary(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "total_tasks": len(self.tasks),
            "completed": sum(1 for t in self.tasks if t.status == CrewTaskStatus.COMPLETED),
            "failed": sum(1 for t in self.tasks if t.status == CrewTaskStatus.FAILED),
            "skipped": sum(1 for t in self.tasks if t.status == CrewTaskStatus.SKIPPED),
            "pending": sum(1 for t in self.tasks if t.status == CrewTaskStatus.PENDING),
            "total_duration_ms": sum(t.duration_ms or 0 for t in self.tasks),
        }


class AgentCrew(BaseModel):
    crew_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    description: str = ""
    company_id: str
    roles: list[CrewRole] = Field(default_factory=list)
    plan: CrewPlan | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_role(self, agent_name: str) -> CrewRole | None:
        for r in self.roles:
            if r.agent_name == agent_name:
                return r
        return None

    def get_agents_by_role(self, role_type: CrewRoleType) -> list[str]:
        return [r.agent_name for r in self.roles if r.role_type == role_type]


class CrewExecutionResult(BaseModel):
    crew_id: str
    execution_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    company_id: str
    status: CrewExecutionStatus = CrewExecutionStatus.PENDING
    plan_summary: dict[str, Any] = Field(default_factory=dict)
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None
