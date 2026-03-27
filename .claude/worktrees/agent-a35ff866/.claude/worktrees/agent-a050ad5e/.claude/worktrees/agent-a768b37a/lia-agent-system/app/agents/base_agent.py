"""
DEPRECATED — Shim de retrocompatibilidade (Sprint I3c).

Local canônico: app/shared/agents/agent_types.py

Este arquivo re-exporta todas as definições para manter compatibilidade
com imports existentes (app.agents.base_agent.*).
Não adicionar nova lógica aqui.
"""
from app.shared.agents.agent_types import (  # noqa: F401
    AgentType,
    TaskPriority,
    TaskStatus,
    AgentAction,
    AgentTask,
    AgentResponse,
    BaseAgent,
)

__all__ = [
    "AgentType",
    "TaskPriority",
    "TaskStatus",
    "AgentAction",
    "AgentTask",
    "AgentResponse",
    "BaseAgent",
]
