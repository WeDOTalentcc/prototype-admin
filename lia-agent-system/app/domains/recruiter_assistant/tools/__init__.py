"""Recruiter Assistant Domain - Tool definitions and executor."""
from typing import Any, Dict, List

from app.domains.base import DomainContext

RECRUITER_ASSISTANT_TOOLS = [
    {
        "tool_id": "assistant_pipeline_health",
        "name": "Saúde do Pipeline",
        "description": "Verifica a saúde geral do pipeline de recrutamento",
        "handler": "app.domains.recruiter_assistant.services.pipeline_service.pipeline_service.get_stale_candidates",
    },
    {
        "tool_id": "assistant_stale_candidates",
        "name": "Candidatos Parados",
        "description": "Encontra candidatos inativos/parados no pipeline",
        "handler": "app.domains.recruiter_assistant.services.pipeline_service.pipeline_service.get_stale_candidates",
    },
    {
        "tool_id": "assistant_move_candidate",
        "name": "Mover Candidato",
        "description": "Move candidato para uma etapa diferente do pipeline",
        "handler": "app.domains.recruiter_assistant.services.pipeline_stage_service.pipeline_stage_service.transition_candidate",
    },
    {
        "tool_id": "assistant_search_context",
        "name": "Buscar Contexto",
        "description": "Busca no histórico de conversas por contexto relevante",
        "handler": "app.domains.recruiter_assistant.services.memory_service.memory_service.search_similar_messages",
    },
    {
        "tool_id": "assistant_save_memory",
        "name": "Salvar Memória",
        "description": "Salva informação importante na memória persistente",
        "handler": "app.domains.recruiter_assistant.services.memory_service.memory_service.store_message",
    },
    {
        "tool_id": "assistant_recall_memory",
        "name": "Recuperar Memória",
        "description": "Recupera informação da memória persistente via busca semântica",
        "handler": "app.domains.recruiter_assistant.services.memory_service.memory_service.search_similar_messages",
    },
    {
        "tool_id": "assistant_conversation_summary",
        "name": "Resumo da Conversa",
        "description": "Gera resumo da conversa atual",
        "handler": "app.domains.recruiter_assistant.services.conversation_memory.ConversationMemory.update_summary",
    },
    {
        "tool_id": "assistant_kanban_analysis",
        "name": "Análise do Kanban",
        "description": "Análise por IA do quadro Kanban de recrutamento",
        "handler": "app.domains.recruiter_assistant.services.kanban_assistant_service.kanban_assistant_service.process_command",
    },
    {
        "tool_id": "assistant_send_notification",
        "name": "Enviar Notificação",
        "description": "Envia notificação proativa para o recrutador",
        "handler": "app.services.notification_service.notification_service.send_proactive_notification",
    },
    {
        "tool_id": "assistant_track_goals",
        "name": "Acompanhar Metas",
        "description": "Acompanha progresso das metas de recrutamento",
        "handler": "app.services.goal_service.goal_service.get_user_goals",
    },
]


def _get_tool_by_id(tool_id: str) -> dict | None:
    for tool in RECRUITER_ASSISTANT_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_recruiter_assistant_tool(
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
