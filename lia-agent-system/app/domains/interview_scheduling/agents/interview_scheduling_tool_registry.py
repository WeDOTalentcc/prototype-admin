"""
Interview Scheduling Tool Registry — ferramentas de agendamento para o chat federado.

Expõe schedule_interview e check_interviewer_availability como ToolDefinitions
compatíveis com o recruiter_copilot (_FEDERATION_SPEC P1-6).

Fonte: app.domains.interview_scheduling.tools.scheduling_tools (LangChain @tool).
Os handlers são wrapped para garantir compatibilidade com o ToolDefinition adapter.

Multi-tenancy: schedule_interview aceita company_id via kwargs (passado pelo
tool_handler do caller). check_interviewer_availability é read-only (sem PII persistido).

SIMULAÇÃO: ambos os tools são stubs de simulação (is_simulated_calendar=True).
Em produção, substituir por integração real com Google Calendar / Outlook.

Sensor: tests/contract/test_federation_spec_completeness.py
"""
from __future__ import annotations

import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition

logger = logging.getLogger(__name__)


async def _wrap_schedule_interview(**kwargs: Any) -> dict[str, Any]:
    """Wrapper async para schedule_interview do scheduling_tools."""
    from app.domains.interview_scheduling.tools.scheduling_tools import schedule_interview

    candidate_id = kwargs.get("candidate_id", "")
    interviewer_id = kwargs.get("interviewer_id", "")
    datetime_str = kwargs.get("datetime_str", kwargs.get("datetime", ""))
    interview_type = kwargs.get("interview_type", "technical")
    meeting_url = kwargs.get("meeting_url", "")
    company_id = kwargs.get("company_id")

    try:
        # schedule_interview is an async @tool — invoke its coroutine directly
        result = await schedule_interview.coroutine(
            candidate_id=candidate_id,
            interviewer_id=interviewer_id,
            datetime_str=datetime_str,
            interview_type=interview_type,
            meeting_url=meeting_url,
            company_id=company_id,
        )
        return result if isinstance(result, dict) else {"result": result}
    except Exception as exc:
        logger.error("[interview_scheduling] schedule_interview failed: %s", exc, exc_info=True)
        raise


def _wrap_check_interviewer_availability(**kwargs: Any) -> dict[str, Any]:
    """Wrapper sync para check_interviewer_availability do scheduling_tools."""
    from app.domains.interview_scheduling.tools.scheduling_tools import check_interviewer_availability

    interviewer_id = kwargs.get("interviewer_id", "")
    date_range = kwargs.get("date_range", "")

    try:
        # check_interviewer_availability is a sync @tool — invoke its func directly
        result = check_interviewer_availability.func(
            interviewer_id=interviewer_id,
            date_range=date_range,
        )
        return result if isinstance(result, dict) else {"result": result}
    except Exception as exc:
        logger.error(
            "[interview_scheduling] check_interviewer_availability failed: %s", exc, exc_info=True
        )
        raise


_SCHEDULE_INTERVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "ID do candidato a ser entrevistado.",
        },
        "interviewer_id": {
            "type": "string",
            "description": "ID do entrevistador (recrutador ou gestor).",
        },
        "datetime_str": {
            "type": "string",
            "description": "Data e hora da entrevista (formato: YYYY-MM-DD HH:MM).",
        },
        "interview_type": {
            "type": "string",
            "enum": ["technical", "behavioral", "cultural_fit", "final"],
            "description": "Tipo da entrevista. Padrão: technical.",
        },
        "meeting_url": {
            "type": "string",
            "description": "URL da reunião (Google Meet, Teams, Zoom). Opcional.",
        },
    },
    "required": ["candidate_id", "interviewer_id", "datetime_str"],
}

_CHECK_AVAILABILITY_SCHEMA = {
    "type": "object",
    "properties": {
        "interviewer_id": {
            "type": "string",
            "description": "ID do entrevistador para verificar disponibilidade.",
        },
        "date_range": {
            "type": "string",
            "description": (
                "Intervalo de datas para verificar (formato: YYYY-MM-DD to YYYY-MM-DD). "
                "Exemplo: 2026-06-16 to 2026-06-23"
            ),
        },
    },
    "required": ["interviewer_id", "date_range"],
}


def get_interview_scheduling_tools() -> list[ToolDefinition]:
    """Retorna ToolDefinitions de agendamento de entrevistas para o chat federado.

    Dois tools:
    - schedule_interview: agendamento + persistência no DB (simulado até integração real)
    - check_interviewer_availability: leitura de agenda (simulado)

    Ambos marcados com is_simulated_calendar=True no output — frontends podem
    mostrar aviso de simulação até integração com Google Calendar / Outlook.
    """
    return [
        ToolDefinition(
            name="schedule_interview",
            description=(
                "Agendar uma entrevista entre candidato e entrevistador. "
                "Use quando o recrutador pedir para marcar/agendar entrevista com um candidato. "
                "Salva no banco de dados. NOTA: integração de calendário ainda é simulada "
                "(is_simulated_calendar=True) — o slot NÃO bloqueia a agenda real até integração "
                "com Google Calendar / Outlook ser ativada. "
                "when_to_use: agendar entrevista, marcar horário para candidato. "
                "when_not_to_use: verificar disponibilidade (use check_interviewer_availability)."
            ),
            parameters_schema=_SCHEDULE_INTERVIEW_SCHEMA,
            function=_wrap_schedule_interview,
            side_effects=["write"],
            touches_pii=True,
            affects_candidate_decision=True,
            requires_human_review=True,
        ),
        ToolDefinition(
            name="check_interviewer_availability",
            description=(
                "Verificar disponibilidade de agenda de um entrevistador em um intervalo de datas. "
                "Retorna slots disponíveis e ocupados. NOTA: simulação (dados não vêm de calendário real). "
                "when_to_use: antes de agendar entrevista, verificar quando o entrevistador está livre. "
                "when_not_to_use: agendar efetivamente (use schedule_interview)."
            ),
            parameters_schema=_CHECK_AVAILABILITY_SCHEMA,
            function=_wrap_check_interviewer_availability,
        ),
    ]
