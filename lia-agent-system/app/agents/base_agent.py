"""
Shim de retrocompatibilidade · DEPRECATED desde W1-002 (2026-05-22).

⚠️  Esse módulo é mantido APENAS pra retrocompatibilidade de imports antigos.
    Não adicione nada aqui. Migre seus imports para:

        from app.shared.agents.agent_types import AgentType, TaskPriority, ...

W1-002 deletou:
- `BaseAgent` ABC legacy com `process(intent, entities, context) -> AgentResponse`
  (todos os 21+ agents de produção usam canonical
   `lia_agents_core.agent_interface.BaseAgent` com `process(input: AgentInput)`)
- `AgentResponse` dataclass (zero consumers vivos — só estava em decorator
  `handle_agent_errors` never-applied)
- Header inversion arqueológica (Sprint I3c parou no meio).

Símbolos que sobrevivem aqui via re-export (com DeprecationWarning):
- `AgentType` (StrEnum, 13 valores — 9 ativos + 4 deprecated)
- `TaskPriority`, `TaskStatus` (StrEnum)
- `AgentAction`, `AgentTask` (dataclasses)

Sensor anti-regressão: `scripts/check_no_legacy_base_agent.py`
Pre-audit: `sprint_logs/sprint_1.2/W1-002_AUDIT.md`
"""
from __future__ import annotations

import warnings

warnings.warn(
    "`app.agents.base_agent` está depreciado desde W1-002 (2026-05-22). "
    "Use `app.shared.agents.agent_types` para AgentType, TaskPriority, "
    "TaskStatus, AgentAction, AgentTask. "
    "`BaseAgent` legacy ABC + `AgentResponse` foram deletados — agents "
    "canonical usam `lia_agents_core.agent_interface.BaseAgent`.",
    DeprecationWarning,
    stacklevel=2,
)

from app.shared.agents.agent_types import (  # noqa: E402,F401
    AgentAction,
    AgentTask,
    AgentType,
    TaskPriority,
    TaskStatus,
)

__all__ = [
    "AgentType",
    "TaskPriority",
    "TaskStatus",
    "AgentAction",
    "AgentTask",
]
