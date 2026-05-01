"""Interview & Scheduling Domain - Tool definitions and executor."""
from typing import Any, Dict, List

from app.domains.base import DomainContext
from app.domains.interview_scheduling.tools.scheduling_tools import (
    cancel_interview,
    check_interviewer_availability,
    get_interview_status,
    reschedule_interview,
    schedule_interview,
    send_interview_invitation,
)

__all__ = [
    "check_interviewer_availability",
    "schedule_interview",
    "send_interview_invitation",
    "reschedule_interview",
    "cancel_interview",
    "get_interview_status",
]

INTERVIEW_SCHEDULING_TOOLS = [
    {
        "tool_id": "scheduling_schedule_interview",
        "name": "Agendar Entrevista",
        "description": "Agenda entrevista com candidato criando evento no calendário",
        "handler": "app.domains.interview_scheduling.services.scheduling_service.scheduling_service.schedule_interview",
    },
    {
        "tool_id": "scheduling_reschedule",
        "name": "Reagendar Entrevista",
        "description": "Reagenda entrevista existente para novo horário",
        "handler": "app.domains.interview_scheduling.services.scheduling_service.scheduling_service.reschedule_interview",
    },
    {
        "tool_id": "scheduling_cancel",
        "name": "Cancelar Entrevista",
        "description": "Cancela entrevista agendada e notifica participantes",
        "handler": "app.domains.interview_scheduling.services.scheduling_service.scheduling_service.cancel_interview",
    },
    {
        "tool_id": "scheduling_check_availability",
        "name": "Verificar Disponibilidade",
        "description": "Verifica disponibilidade do entrevistador no calendário",
        "handler": "app.domains.interview_scheduling.services.calendar_service.calendar_service.check_availability",
    },
    {
        "tool_id": "scheduling_self_scheduling_link",
        "name": "Gerar Link de Auto-agendamento",
        "description": "Gera link para candidato escolher horário de entrevista",
        "handler": "app.domains.interview_scheduling.services.scheduling_service.scheduling_service.generate_self_scheduling_link",
    },
    {
        "tool_id": "scheduling_find_slots",
        "name": "Encontrar Horários Comuns",
        "description": "Encontra horários disponíveis comuns para todos os participantes",
        "handler": "app.domains.interview_scheduling.services.calendar_service.calendar_service.find_common_slots",
    },
    {
        "tool_id": "scheduling_send_reminder",
        "name": "Enviar Lembrete de Entrevista",
        "description": "Envia lembrete de entrevista para participantes",
        "handler": "app.domains.interview_scheduling.services.scheduling_service.scheduling_service.send_reminder",
    },
    {
        "tool_id": "scheduling_list_today",
        "name": "Listar Entrevistas de Hoje",
        "description": "Lista todas as entrevistas agendadas para hoje",
        "handler": "app.domains.interview_scheduling.services.scheduling_service.scheduling_service.list_today_interviews",
    },
    {
        "tool_id": "scheduling_transcribe_audio",
        "name": "Transcrever Áudio",
        "description": "Transcreve áudio de entrevista usando OpenAI Whisper STT",
        "handler": "app.services.voice_service.voice_service.transcribe_audio",
    },
    {
        "tool_id": "scheduling_analyze_voice",
        "name": "Analisar Voz",
        "description": "Analisa tom de voz e confiança do candidato na entrevista",
        "handler": "app.services.voice_service.voice_service.transcribe_audio",
    },
]


def _get_tool_by_id(tool_id: str) -> dict | None:
    for tool in INTERVIEW_SCHEDULING_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_interview_scheduling_tool(
    tool_id: str,
    parameters: dict[str, Any],
    context: DomainContext,
) -> dict[str, Any]:
    tool = _get_tool_by_id(tool_id)
    if not tool:
        return {"error": f"Tool {tool_id} not found", "status": "error"}

    handler_path = tool["handler"]
    parts = handler_path.rsplit(".", 1)
    if len(parts) != 2:
        return {"error": f"Invalid handler path: {handler_path}", "status": "error"}

    module_path, func_name = parts
    try:
        import importlib
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)
        result = await handler(**parameters) if callable(handler) else handler
        return {"status": "success", "result": result}
    except Exception as e:
        return {"error": str(e), "status": "error", "tool_id": tool_id}
