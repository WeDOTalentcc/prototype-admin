"""Recruiter Assistant Domain - Tool definitions and executor."""
from typing import Any, Dict, List

from app.domains.base import DomainContext

RECRUITER_ASSISTANT_TOOLS = [
    # Migrated to V2 DomainAction path.
    # Singleton instance pattern not resolvable via dynamic import.
    # Routes handled by KanbanAgent and PolicyAgent.
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
