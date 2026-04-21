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
    # Migrated to V2 DomainAction path (actions.py).
    # Singleton instance pattern (.scheduling_service.scheduling_service.* etc.) is not
    # resolvable via dynamic import. Routes handled via scheduling_tools.py.
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
