"""
Agent Types — Definições canônicas de tipos de agentes LIA.

Extraído de app/agents/base_agent.py como parte da consolidação de legacy (Sprint I3c).
Este é agora o local canônico para AgentType, AgentTask, AgentResponse e BaseAgent.

app/agents/base_agent.py é mantido como shim de retrocompatibilidade.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
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
    """Represents an action that an agent can perform."""
    name: str
    description: str
    handler: str
    requires_confirmation: bool = False
    estimated_duration_seconds: int = 0
    tags: list[str] = field(default_factory=list)


@dataclass
class AgentTask:
    """Represents a task created by an agent."""
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


@dataclass
class AgentResponse:
    """Standard response structure from an agent."""
    success: bool
    message: str
    data: dict[str, Any] | None = None
    next_actions: list[str] = field(default_factory=list)
    tasks_created: list[AgentTask] = field(default_factory=list)
    requires_user_input: bool = False
    suggested_prompts: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Classe base abstrata para todos os agentes especializados LIA.

    Migrada de app/agents/base_agent.py (I3c — Sprint I3).
    Local canônico: app/shared/agents/agent_types.py
    app/agents/base_agent.py mantido como shim de retrocompatibilidade.
    """

    def __init__(self):
        self._actions: dict[str, AgentAction] = {}
        self._register_actions()

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def capabilities(self) -> list[str]:
        return [action.name for action in self._actions.values()]

    @abstractmethod
    def _register_actions(self) -> None:
        pass

    def register_action(self, action: AgentAction) -> None:
        self._actions[action.name] = action

    def get_actions(self) -> list[AgentAction]:
        return list(self._actions.values())

    def get_action(self, action_name: str) -> AgentAction | None:
        return self._actions.get(action_name)

    def can_handle(self, intent: str, entities: dict[str, Any]) -> float:
        return 0.0

    @abstractmethod
    async def process(
        self,
        intent: str,
        entities: dict[str, Any],
        context: dict[str, Any],
    ) -> AgentResponse:
        pass


# Re-export para facilitar imports
__all__ = [
    "AgentType",
    "TaskPriority",
    "TaskStatus",
    "AgentAction",
    "AgentTask",
    "AgentResponse",
    "BaseAgent",
]
