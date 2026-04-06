# LIA-R03 — MultiDomainPlan: plano de execução cross-domain para o orchestrator
# Permite que o orchestrator execute tarefas que requerem múltiplos domínios.
# Ex: "triagem de CV + agendamento de entrevista" → cv_screening + interview_scheduling

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import Any


class PlanStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    step_id: str
    domain: str
    action: str
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    status: PlanStepStatus = PlanStepStatus.PENDING
    depends_on: list[str] = field(default_factory=list)  # step_ids
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class MultiDomainPlan:
    """Execution plan spanning multiple LIA domains.
    
    LIA-R03: O orchestrator usa MultiDomainPlan para coordenar tarefas
    que cruzam fronteiras de domínio, mantendo rastreabilidade e auditoria.
    """
    plan_id: str = field(default_factory=lambda: f"plan-{str(uuid.uuid4())[:8]}")
    user_id: str = ""
    original_intent: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_step(
        self,
        domain: str,
        action: str,
        input_data: dict[str, Any] | None = None,
        depends_on: list[str] | None = None,
    ) -> PlanStep:
        step = PlanStep(
            step_id=f"step-{len(self.steps)+1}",
            domain=domain,
            action=action,
            input_data=input_data or {},
            depends_on=depends_on or [],
        )
        self.steps.append(step)
        return step
    
    def get_ready_steps(self) -> list[PlanStep]:
        """Returns steps whose dependencies are all completed."""
        completed_ids = {
            s.step_id for s in self.steps if s.status == PlanStepStatus.COMPLETED
        }
        return [
            s for s in self.steps
            if s.status == PlanStepStatus.PENDING
            and all(dep in completed_ids for dep in s.depends_on)
        ]
    
    def mark_step_done(self, step_id: str, output: dict[str, Any]) -> None:
        for step in self.steps:
            if step.step_id == step_id:
                step.status = PlanStepStatus.COMPLETED
                step.output_data = output
                step.completed_at = datetime.now(UTC)
                return
    
    def mark_step_failed(self, step_id: str, error: str) -> None:
        for step in self.steps:
            if step.step_id == step_id:
                step.status = PlanStepStatus.FAILED
                step.error = error
                step.completed_at = datetime.now(UTC)
                return
    
    @property
    def is_complete(self) -> bool:
        return all(
            s.status in (PlanStepStatus.COMPLETED, PlanStepStatus.SKIPPED, PlanStepStatus.FAILED)
            for s in self.steps
        )
    
    @property
    def has_failures(self) -> bool:
        return any(s.status == PlanStepStatus.FAILED for s in self.steps)
    
    def summary(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "intent": self.original_intent,
            "total_steps": len(self.steps),
            "completed": sum(1 for s in self.steps if s.status == PlanStepStatus.COMPLETED),
            "failed": sum(1 for s in self.steps if s.status == PlanStepStatus.FAILED),
            "pending": sum(1 for s in self.steps if s.status == PlanStepStatus.PENDING),
            "is_complete": self.is_complete,
        }
