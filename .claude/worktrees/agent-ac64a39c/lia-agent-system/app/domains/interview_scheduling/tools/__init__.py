"""Interview & Scheduling Domain - Tool definitions and executor."""
from typing import Dict, Any, List

from app.domains.base import DomainContext

INTERVIEW_SCHEDULING_TOOLS = [
    {
        "tool_id": "scheduling_schedule_interview",
        "name": "Agendar Entrevista",
        "description": "Agenda entrevista com candidato criando evento no calendário",
        "handler": "app.services.scheduling_service.scheduling_service.schedule_interview",
    },
    {
        "tool_id": "scheduling_reschedule",
        "name": "Reagendar Entrevista",
        "description": "Reagenda entrevista existente para novo horário",
        "handler": "app.services.scheduling_service.scheduling_service.reschedule_interview",
    },
    {
        "tool_id": "scheduling_cancel",
        "name": "Cancelar Entrevista",
        "description": "Cancela entrevista agendada e notifica participantes",
        "handler": "app.services.scheduling_service.scheduling_service.cancel_interview",
    },
    {
        "tool_id": "scheduling_check_availability",
        "name": "Verificar Disponibilidade",
        "description": "Verifica disponibilidade do entrevistador no calendário",
        "handler": "app.services.calendar_service.calendar_service.check_availability",
    },
    {
        "tool_id": "scheduling_self_scheduling_link",
        "name": "Gerar Link de Auto-agendamento",
        "description": "Gera link para candidato escolher horário de entrevista",
        "handler": "app.services.scheduling_service.scheduling_service.generate_self_scheduling_link",
    },
    {
        "tool_id": "scheduling_find_slots",
        "name": "Encontrar Horários Comuns",
        "description": "Encontra horários disponíveis comuns para todos os participantes",
        "handler": "app.services.calendar_service.calendar_service.find_common_slots",
    },
    {
        "tool_id": "scheduling_send_reminder",
        "name": "Enviar Lembrete de Entrevista",
        "description": "Envia lembrete de entrevista para participantes",
        "handler": "app.services.scheduling_service.scheduling_service.send_reminder",
    },
    {
        "tool_id": "scheduling_list_today",
        "name": "Listar Entrevistas de Hoje",
        "description": "Lista todas as entrevistas agendadas para hoje",
        "handler": "app.services.scheduling_service.scheduling_service.list_today_interviews",
    },
    {
        "tool_id": "scheduling_transcribe_audio",
        "name": "Transcrever Áudio",
        "description": "Transcreve áudio de entrevista usando Deepgram Nova-2",
        "handler": "app.services.deepgram_service.deepgram_service.transcribe_audio_url",
    },
    {
        "tool_id": "scheduling_analyze_voice",
        "name": "Analisar Voz",
        "description": "Analisa tom de voz e confiança do candidato na entrevista",
        "handler": "app.services.deepgram_service.deepgram_service.transcribe_audio_url",
    },
]


def _get_tool_by_id(tool_id: str) -> dict | None:
    for tool in INTERVIEW_SCHEDULING_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_interview_scheduling_tool(
    tool_id: str,
    parameters: Dict[str, Any],
    context: DomainContext,
) -> Dict[str, Any]:
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
