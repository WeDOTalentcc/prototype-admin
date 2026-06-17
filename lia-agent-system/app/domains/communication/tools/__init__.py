"""Communication Domain - Tool definitions and executor."""
from typing import Any, Dict, List

from app.domains.base import DomainContext

COMMUNICATION_TOOLS = [
    {
        "tool_id": "communication_send_email",
        "name": "Enviar Email",
        "description": "Envia email individual usando template ou conteúdo customizado",
        "handler": "app.domains.communication.services.email_service.email_service.send_email",
    },
    {
        "tool_id": "communication_send_bulk",
        "name": "Enviar Email em Massa",
        "description": "Envia emails para múltiplos destinatários",
        "handler": "app.domains.communication.services.email_service.email_service.send_bulk_email",
    },
    {
        "tool_id": "communication_send_whatsapp",
        "name": "Enviar WhatsApp",
        "description": "Envia mensagem WhatsApp para candidato via provider configurado",
        "handler": "app.domains.communication.services.whatsapp_service.send_whatsapp_message",
    },
    {
        "tool_id": "communication_send_teams",
        "name": "Enviar Teams",
        "description": "Envia mensagem via Microsoft Teams",
        "handler": "app.domains.communication.services.teams_service.send_teams_message",
    },
    {
        "tool_id": "communication_create_template",
        "name": "Criar Template de Email",
        "description": "Cria novo template de email/comunicação",
        "handler": "app.domains.communication.services.email_service.email_service.create_template",
    },
    {
        "tool_id": "communication_list_templates",
        "name": "Listar Templates",
        "description": "Lista templates de comunicação disponíveis",
        "handler": "app.domains.communication.services.email_service.email_service.list_templates",
    },
    {
        "tool_id": "communication_preview_template",
        "name": "Preview de Template",
        "description": "Visualiza template renderizado com dados do candidato",
        "handler": "app.domains.communication.services.email_service.email_service.preview_template",
    },
    {
        "tool_id": "communication_get_history",
        "name": "Histórico de Comunicação",
        "description": "Consulta histórico de comunicações com candidato",
        "handler": "app.domains.communication.services.communication_history_service.get_history",
    },
    {
        "tool_id": "communication_manage_webhook",
        "name": "Gerenciar Webhook",
        "description": "Configura e gerencia webhooks de comunicação",
        "handler": "app.domains.communication.services.webhook_service.manage_webhook",
    },
    {
        "tool_id": "communication_data_request",
        "name": "Solicitação de Dados",
        "description": "Processa solicitações de dados LGPD",
        "handler": "app.domains.communication.services.data_request_service.handle_request",
    },
]


def _get_tool_by_id(tool_id: str) -> dict | None:
    for tool in COMMUNICATION_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_communication_tool(
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
