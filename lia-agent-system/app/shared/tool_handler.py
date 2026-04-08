"""
Shared decorator for tool registry functions.
Eliminates boilerplate: tenant check + try/except/log + response formatting.
"""
import asyncio
import logging
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

_TENANT_REQUIRED_RESPONSE: dict[str, Any] = {
    "success": False,
    "data": {},
    "message": "Tenant isolation error: 'company_id' é obrigatório. Nenhuma query de dados pode ser executada sem contexto de tenant.",
}


def tool_handler(domain: str, *, require_company: bool = True):
    """Decorator that wraps a tool function with tenant check + error handling.

    The decorated function should:
    - Accept **kwargs (with company_id)
    - Return the data dict directly (not wrapped in success/data/message)
    - Raise exceptions normally (they will be caught and logged)

    The decorator adds:
    - company_id presence check (fail-closed) — skip with require_company=False
    - try/except with logger.error
    - Standard response formatting {"success": True/False, "data": ..., "message": ...}

    If the inner function returns a dict that already contains a "success" key,
    the decorator passes it through untouched.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(**kwargs: Any) -> dict[str, Any]:
            # --- tenant guard ---
            if require_company and not kwargs.get("company_id"):
                return dict(_TENANT_REQUIRED_RESPONSE)
            try:
                # support both sync and async callables
                result = func(**kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                # pass-through already-formatted responses
                if isinstance(result, dict) and "success" in result:
                    return result
                return {"success": True, "data": result, "message": "OK"}
            except Exception as exc:
                logger.error("[%s] %s error: %s", domain, func.__name__, exc, exc_info=True)
                return {"success": False, "data": {}, "message": str(exc)}

        return wrapper

    return decorator
