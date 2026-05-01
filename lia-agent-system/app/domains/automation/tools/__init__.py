"""Automation & Tasks Domain - Tool definitions and executor."""
from typing import Any, Dict, List

from app.domains.automation.tools.automation_tools import (
    bulk_send_notifications,
    get_automation_logs,
    schedule_reminder,
    send_automated_email,
    trigger_workflow,
    update_candidate_status,
)
from app.domains.base import DomainContext

__all__ = [
    "trigger_workflow",
    "send_automated_email",
    "update_candidate_status",
    "bulk_send_notifications",
    "schedule_reminder",
    "get_automation_logs",
]

AUTOMATION_TOOLS = [
    {
        "tool_id": "automation_create_task",
        "name": "Criar Tarefa",
        "description": "Cria uma nova tarefa para execução",
        "handler": "app.domains.automation.services.task_service.TaskService.create_task",
    },
    {
        "tool_id": "automation_list_tasks",
        "name": "Listar Tarefas",
        "description": "Lista tarefas e seus status atuais",
        "handler": "app.domains.automation.services.task_service.TaskService.list_tasks",
    },
    {
        "tool_id": "automation_complete_task",
        "name": "Concluir Tarefa",
        "description": "Marca uma tarefa como concluída",
        "handler": "app.domains.automation.services.task_service.TaskService.complete_task",
    },
    {
        "tool_id": "automation_cancel_task",
        "name": "Cancelar Tarefa",
        "description": "Cancela uma tarefa pendente",
        "handler": "app.domains.automation.services.task_service.TaskService.cancel_task",
    },
    {
        "tool_id": "automation_create_rule",
        "name": "Criar Regra de Automação",
        "description": "Cria uma nova regra de automação",
        "handler": "app.domains.automation.services.automation_service.AutomationService.create_automation",
    },
    {
        "tool_id": "automation_list_rules",
        "name": "Listar Regras de Automação",
        "description": "Lista regras de automação configuradas",
        "handler": "app.domains.automation.services.automation_service.AutomationService.list_automations",
    },
    {
        "tool_id": "automation_enable_rule",
        "name": "Ativar Automação",
        "description": "Ativa uma regra de automação",
        "handler": "app.domains.automation.services.automation_service.AutomationService.enable_automation",
    },
    {
        "tool_id": "automation_disable_rule",
        "name": "Desativar Automação",
        "description": "Desativa uma regra de automação",
        "handler": "app.domains.automation.services.automation_service.AutomationService.disable_automation",
    },
    {
        "tool_id": "automation_trigger",
        "name": "Disparar Automação",
        "description": "Dispara manualmente uma automação configurada",
        "handler": "app.domains.automation.services.automation_trigger_service.AutomationTriggerService.trigger",
    },
    {
        "tool_id": "automation_view_log",
        "name": "Ver Log de Execução",
        "description": "Visualiza histórico de execução de automações",
        "handler": "app.domains.automation.services.automation_service.AutomationService.get_execution_log",
    },
]


def _get_tool_by_id(tool_id: str) -> dict | None:
    for tool in AUTOMATION_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_automation_tool(
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
