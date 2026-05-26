"""
Canonical schema para timeline de eventos de Agent Studio (sourcing/screening).

Registrado 2026-05-26 — Sprint 7B-3b Part 1 Fase B.

Eventos heterogêneos (sourcing signals positive/negative, calibration, dispatch,
feedback). Fields comuns tipados; campos específicos vão em `payload` dict pra
flexibilidade entre tipos de evento.

Origem dos dados: `SourcingAgentOrchestrator.get_agent_timeline()` que serializa
linhas da tabela `sourcing_agent_signals` (custom_agent_id canonical).

WeDoBaseModel canonical (REGRA 1 Pydantic conventions): `extra='forbid'` força
HTTP 422 explícito se backend mandar fields fantasma — protege contrato.
"""
from __future__ import annotations

from typing import Any, Literal

from app.shared.types import WeDoBaseModel


# Literal aligned com get_agent_timeline() shape real (sourcing signals):
# - "positive" → recruiter aprovou candidato
# - "negative" → recruiter rejeitou candidato
# Outros tipos (calibration, dispatch) reservados para extensão futura sem
# breaking changes — payload dict acomoda extras.
AgentTimelineEventType = Literal["positive", "negative", "calibration", "dispatch", "feedback"]


class AgentTimelineEventResponse(WeDoBaseModel):
    """Evento individual da timeline canonical de Agent Studio.

    Shape derivado de `get_agent_timeline()` em sourcing_agent_orchestrator.py:
        {
            "id": str,
            "icon": str (emoji),
            "type": "positive" | "negative",
            "reason": str,
            "criteria": list[str],
            "candidate_id": str,
            "created_at": str (ISO 8601),
        }

    Fields opcionais permitem cobrir variações entre tipos de evento sem quebrar
    consumers existentes (payload dict é catch-all canonical).
    """

    id: str
    icon: str
    type: AgentTimelineEventType
    reason: str | None = None
    criteria: list[str] = []
    candidate_id: str | None = None
    created_at: str | None = None
    payload: dict[str, Any] = {}
