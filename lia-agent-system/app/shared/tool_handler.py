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


def resolve_handler_path(handler_path: str) -> Any:
    """Resolve a dotted handler path progressively.

    Supports both module-level callables (`pkg.mod.func`) and
    class/singleton method paths (`pkg.mod.singleton.method`,
    `pkg.mod.Class.classmethod`). Mirrors the strategy used by
    `tests/test_chat_capabilities_smoke.py::_resolve_handler` so the
    runtime tool registry agrees with the smoke gate.

    Fail-closed: when a handler resolves to an *unbound* instance method
    (i.e. a class accessor like `pkg.mod.Service.method` whose first
    parameter is `self`), this resolver looks for a sibling singleton on
    the same module and binds against it. If no singleton exists, raises
    `TypeError` so the caller surfaces a real error instead of silently
    calling `func(**parameters)` and exploding with
    "missing 1 required positional argument: 'self'".

    Raises ImportError, AttributeError or TypeError on failure (caller
    wraps in its own response shape).
    """
    import importlib
    import inspect

    parts = handler_path.split(".")
    last_err: Exception | None = None
    for i in range(len(parts), 0, -1):
        try:
            module = importlib.import_module(".".join(parts[:i]))
        except ImportError as exc:
            last_err = exc
            continue
        obj: Any = module
        owner: Any = module
        try:
            for attr in parts[i:]:
                owner = obj
                obj = getattr(obj, attr)
        except AttributeError as exc:
            last_err = exc
            continue
        # Detect "unbound" class methods: callable whose immediate owner is
        # a class and whose first positional param is `self`. Try to find
        # an instance to bind on the same module.
        if (
            callable(obj)
            and inspect.isclass(owner)
            and not inspect.ismethod(obj)
            and not isinstance(obj, (staticmethod, classmethod))
        ):
            try:
                sig_params = list(inspect.signature(obj).parameters.values())
            except (TypeError, ValueError):
                sig_params = []
            if sig_params and sig_params[0].name == "self":
                instance = _find_singleton_for_class(module, owner)
                if instance is not None:
                    return getattr(instance, parts[-1])
                raise TypeError(
                    f"Handler '{handler_path}' resolves to an unbound method on "
                    f"{owner.__name__}; register the singleton path "
                    f"(e.g. '{owner.__module__}.<singleton>.{parts[-1]}') instead."
                )
        return obj
    raise (last_err or ImportError(f"Could not resolve handler: {handler_path}"))


def _find_singleton_for_class(module: Any, cls: Any) -> Any:
    """Return the first module-level attribute that is an instance of `cls`."""
    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            value = getattr(module, name)
        except Exception:
            continue
        if isinstance(value, cls) and value is not cls:
            return value
    return None
