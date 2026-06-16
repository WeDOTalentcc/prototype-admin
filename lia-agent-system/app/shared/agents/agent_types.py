"""
Agent Types — Definições canônicas de tipos de agentes LIA.

Canonical location pós W1-002 (2026-05-22):
- Esse arquivo é a SINGLE SOURCE OF TRUTH para AgentType, TaskPriority,
  TaskStatus, AgentAction (dataclass legacy), AgentTask (dataclass legacy).
- `app/agents/base_agent.py` é shim de retrocompat com DeprecationWarning.

W1-002 cleanup (pre-audit em sprint_logs/sprint_1.2/W1-002_AUDIT.md):
- Antes do W1-002: esse arquivo era `from app.agents.base_agent import *`
  (shim REVERSO — header dizia canonical, mas conteúdo era re-export).
- Depois do W1-002: conteúdo inline aqui, shim invertido.

NOTA: `BaseAgent` ABC legacy com `process(intent, entities, context)` foi
**deletada** — todos os 21+ agents de produção usam canonical
`lia_agents_core.agent_interface.BaseAgent` com `process(input: AgentInput)`.
`AgentResponse` legacy também foi removida (não tinha consumers vivos).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class AgentType(StrEnum):
    """
    Types of specialized agents in the LIA system.

    Architecture: 9 agents (1 orchestrator + 8 specialized)
    Based on WeDOTalent Multi-Agent Architecture v2.2
    """
    # Agente 0: Orquestrador Central
    ORCHESTRATOR = "orchestrator"

    # Agente 1: Planejador de Vaga (ex-Job Intake)
    JOB_PLANNER = "job_planner"

    # Agente 2: Sourcing e Atração
    SOURCING = "sourcing"

    # Agente 3: Triagem Curricular (extraído do Screening)
    CV_SCREENING = "cv_screening"

    # Agente 4: Entrevistador WhatsApp/Voz (extraído do Screening)
    INTERVIEWER = "interviewer"

    # Agente 5: Avaliador WSI (extraído do Screening)
    WSI_EVALUATOR = "wsi_evaluator"

    # Agente 6: Agendador
    SCHEDULING = "scheduling"

    # Agente 7: Analista e Feedback (merge Communication + Analytics)
    ANALYST_FEEDBACK = "analyst_feedback"

    # Agente 8: Integrador ATS
    ATS_INTEGRATOR = "ats_integrator"

    # Agente Especial: Assistente Pessoal do Recrutador
    RECRUITER_ASSISTANT = "recruiter_assistant"

    # Agente 9: Planejador de Tarefas (Task Planner)
    TASK_PLANNER = "task_planner"

    # DEPRECATED — mantidos para retrocompatibilidade durante migração
    JOB_INTAKE = "job_intake"       # Use JOB_PLANNER
    SCREENING = "screening"          # Use CV_SCREENING, INTERVIEWER, ou WSI_EVALUATOR
    COMMUNICATION = "communication"  # Use ANALYST_FEEDBACK
    ANALYTICS = "analytics"          # Use ANALYST_FEEDBACK


class TaskPriority(StrEnum):
    """Priority levels for agent tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(StrEnum):
    """Status of agent-generated tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentAction:
    """
    Represents an action that an agent can perform.

    DEPRECATED — Mantida apenas pra retrocompat de scaffolding antigo.
    Canonical em `lia_agents_core.agent_interface.AgentAction` (pydantic
    `action_type, params, requires_confirmation`).
    """
    name: str
    description: str
    handler: str
    requires_confirmation: bool = False
    estimated_duration_seconds: int = 0
    tags: list[str] = field(default_factory=list)


@dataclass
class AgentTask:
    """
    Represents a task created by an agent.

    Usado em `app/domains/automation/services/task_service.py` pra criar
    tasks de DB. Não tem equivalente canonical em `lia_agents_core` —
    mantido aqui como modelo de domínio de automation.
    """
    id: str
    title: str
    description: str
    created_by_agent: AgentType
    assigned_to_agent: AgentType | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    due_date: datetime | None = None
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


__all__ = [
    "AgentType",
    "TaskPriority",
    "TaskStatus",
    "AgentAction",
    "AgentTask",
]
