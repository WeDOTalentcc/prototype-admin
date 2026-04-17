"""
Shared decorator for tool registry functions.
Eliminates boilerplate: tenant check + module gating + try/except/log + response formatting.
"""
import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

_TENANT_REQUIRED_RESPONSE: dict[str, Any] = {
    "success": False,
    "data": {},
    "message": "Tenant isolation error: 'company_id' é obrigatório. Nenhuma query de dados pode ser executada sem contexto de tenant.",
}


def tool_handler(domain: str, *, require_company: bool = True, module: Optional[str] = None):
    """Decorator that wraps a tool function with tenant check + module gating + error handling.

    The decorated function should:
    - Accept **kwargs (with company_id)
    - Return the data dict directly (not wrapped in success/data/message)
    - Raise exceptions normally (they will be caught and logged)

    The decorator adds:
    - company_id presence check (fail-closed) — skip with require_company=False
    - Module gating check when `module` is specified (fail-closed: denied when context missing or check errors)
    - try/except with logger.error
    - Standard response formatting {"success": True/False, "data": ..., "message": ...}

    If the inner function returns a dict that already contains a "success" key,
    the decorator passes it through untouched.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(**kwargs: Any) -> dict[str, Any]:
            if require_company and not kwargs.get("company_id"):
                # Fallback 1: _context object (AgenticLoop/ToolExecutor path)
                _ctx = kwargs.get("_context")
                _resolved = getattr(_ctx, "company_id", "") if _ctx else ""
                # Fallback 2: contextvar set by AuthEnforcementMiddleware (LangGraph path)
                if not _resolved:
                    try:
                        from app.shared.tenant_llm_context import get_current_llm_tenant
                        _resolved = get_current_llm_tenant()
                    except Exception:
                        pass
                if not _resolved:
                    return dict(_TENANT_REQUIRED_RESPONSE)
                kwargs["company_id"] = _resolved

            access_result = None

            if module:
                company_id = kwargs.get("company_id")
                db = kwargs.get("db")

                if not company_id or not db:
                    from app.shared.module_gating import build_degraded_response
                    logger.warning(
                        "[%s] Module gating fail-closed: missing context for %s (company_id=%s, db=%s)",
                        domain, func.__name__, bool(company_id), bool(db),
                    )
                    return build_degraded_response(func.__name__, module)

                if company_id and db:
                    try:
                        from app.shared.module_gating import (
                            check_tool_module_access,
                            build_degraded_response,
                            build_beta_response,
                            PREMIUM_GATED_TOOLS,
                            TASTING_TOOLS,
                        )
                        access_result = await check_tool_module_access(
                            func.__name__, company_id, db
                        )

                        if not access_result["allowed"]:
                            if func.__name__ in TASTING_TOOLS:
                                try:
                                    result = func(**kwargs)
                                    if asyncio.iscoroutine(result):
                                        result = await result
                                    if isinstance(result, dict):
                                        from app.shared.module_gating import _extract_tasting_data
                                        tasting = _extract_tasting_data(
                                            result if "data" not in result else {"data": result.get("data", result)}
                                        )
                                        return build_degraded_response(func.__name__, module, partial_data=tasting)
                                except Exception:
                                    pass
                            return build_degraded_response(func.__name__, module)

                    except Exception as exc:
                        from app.shared.module_gating import build_degraded_response
                        logger.warning(
                            "[%s] Module gating fail-closed on error for %s: %s",
                            domain, func.__name__, exc,
                        )
                        return build_degraded_response(func.__name__, module)

            try:
                result = func(**kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                if isinstance(result, dict) and "success" in result:
                    _result = result
                else:
                    _result = {"success": True, "data": result, "message": "OK"}

                if access_result and access_result.get("status") == "beta" and isinstance(_result, dict):
                    from app.shared.module_gating import build_beta_response
                    _result = build_beta_response(_result, module)

                return _result
            except Exception as exc:
                logger.error("[%s] %s error: %s", domain, func.__name__, exc, exc_info=True)
                return {"success": False, "data": {}, "message": str(exc)}

        wrapper._module_gated = module
        return wrapper

    return decorator
