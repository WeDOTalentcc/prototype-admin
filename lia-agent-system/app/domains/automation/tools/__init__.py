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
    # Migrated to V2 DomainAction path (actions.py).
    # Singleton instance pattern (.task_service.task_service.* etc.) is not
    # resolvable via dynamic import. Routes handled via automation_tools.py.
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
    try:
        from app.shared.tool_handler import resolve_handler_path
        import asyncio, inspect
        handler = resolve_handler_path(handler_path)
        if not callable(handler):
            return {"error": f"Handler not callable: {handler_path}", "status": "error", "tool_id": tool_id}
        result = await handler(**parameters) if asyncio.iscoroutinefunction(handler) else handler(**parameters)
        if inspect.isawaitable(result):
            result = await result
        return {"status": "success", "result": result}
    except Exception as e:
        return {"error": str(e), "status": "error", "tool_id": tool_id}
