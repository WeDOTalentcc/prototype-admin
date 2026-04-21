"""ATS Integration Domain - Tool definitions and executor."""
from typing import Any, Dict, List

from app.domains.base import DomainContext

ATS_INTEGRATION_TOOLS = [
    # Migrated to V2 DomainAction path (actions.py).
    # Singleton instance pattern (.ats_sync_service.ats_sync_service.*) is not
    # resolvable via dynamic import. Routes handled by PipelineTransitionAgent.
]


def _get_tool_by_id(tool_id: str) -> dict | None:
    for tool in ATS_INTEGRATION_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_ats_integration_tool(
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
        handler = resolve_handler_path(handler_path)
        if not callable(handler):
            return {"error": f"Handler not callable: {handler_path}", "status": "error", "tool_id": tool_id}
        result = await handler(**parameters) if _is_awaitable_callable(handler) else handler(**parameters)
        if _is_awaitable(result):
            result = await result
        return {"status": "success", "result": result}
    except Exception as e:
        return {"error": str(e), "status": "error", "tool_id": tool_id}


def _is_awaitable_callable(fn) -> bool:
    import asyncio
    return asyncio.iscoroutinefunction(fn)


def _is_awaitable(value) -> bool:
    import inspect
    return inspect.isawaitable(value)
