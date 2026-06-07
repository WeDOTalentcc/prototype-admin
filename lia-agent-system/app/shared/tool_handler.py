"""
Shared decorator for tool registry functions.
Eliminates boilerplate: tenant check + module gating + try/except/log + response formatting.

Multi-tenancy invariant (CLAUDE.md REGRA 1 + ADR-029 §3):
====================================================================
`company_id` (and other tenant keys) MUST come from the auth ContextVar
populated by middleware on JWT decode — NEVER from LLM tool-call args.

This decorator is the single canonical injection point:
1. **Strip LLM-provided tenant keys** (defense in depth — even if a tool
   schema accidentally exposes `company_id` and the LLM hallucinates a
   value, we discard it before calling the inner handler).
2. **Inject from ContextVar** (`_current_company_id` set by
   `app/middleware/auth_enforcement.py`) so handlers continue receiving
   `company_id` via kwargs without breaking signatures.
3. **Fail-closed** if neither ContextVar nor (legacy) explicit kwarg exists.

This makes ADR-029 §2 (no tenant in tool schemas) safe to enforce:
schemas can be stripped without breaking the handler contract.
"""
import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Tenant keys never trusted from LLM args; sourced exclusively from ContextVar
# Aligned with scripts/check_no_tenant_in_tool_schemas.py TENANT_KEYS
_TENANT_KEYS_LLM_FORBIDDEN = ("company_id", "tenant_id", "organization_id")

_TENANT_REQUIRED_RESPONSE: dict[str, Any] = {
    "success": False,
    "data": {},
    "message": "Tenant isolation error: 'company_id' é obrigatório. Nenhuma query de dados pode ser executada sem contexto de tenant.",
}


def _resolve_company_id_from_context() -> str:
    """Read `company_id` from auth middleware ContextVar.

    Returns empty string if not set (caller decides fail-closed behavior).
    Import is local to avoid circular import at module load time.
    """
    try:
        from app.middleware.auth_enforcement import _current_company_id
        return _current_company_id.get("") or ""
    except Exception:
        return ""


def tool_handler(domain: str, *, require_company: bool = True, module: Optional[str] = None, requires_confirmation: bool = False):
    """Decorator that wraps a tool function with tenant check + module gating + error handling.

    The decorated function should:
    - Accept **kwargs (with company_id)
    - Return the data dict directly (not wrapped in success/data/message)
    - Raise exceptions normally (they will be caught and logged)

    The decorator adds (in order):
    - **Tenant arg sanitization** (ADR-029 §2): drops LLM-supplied tenant keys;
      injects `company_id` from `_current_company_id` ContextVar (set by
      middleware on JWT decode). Defense in depth — works even if a tool
      schema accidentally still lists `company_id` as a parameter.
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
            # ── ADR-029 §2: tenant arg sanitization ─────────────────────────────
            # Drop any LLM-supplied tenant keys, then inject from ContextVar.
            # This makes it safe to strip `company_id` from tool schemas:
            # handlers continue to see `company_id` in kwargs, but its value
            # always comes from the authenticated session — never the LLM.
            _ctx_company_id = _resolve_company_id_from_context()
            for _tenant_key in _TENANT_KEYS_LLM_FORBIDDEN:
                if _tenant_key in kwargs and _tenant_key != "company_id":
                    # tenant_id / organization_id from LLM are always discarded
                    kwargs.pop(_tenant_key, None)

            if _ctx_company_id:
                # ContextVar wins over any LLM-provided value (canonical source)
                kwargs["company_id"] = _ctx_company_id
            elif "company_id" in kwargs and kwargs.get("company_id"):
                # No ContextVar but LLM provided one — log + keep for backward
                # compat during Sprint 1 migration. After Sprint 1B sensor
                # blocks LLM-provided tenant args, this branch becomes dead code.
                logger.warning(
                    "[%s] %s called with LLM-supplied company_id and no ContextVar; "
                    "honoring for backward compat (will be denied after ADR-029 §2 enforcement).",
                    domain, func.__name__,
                )

            if require_company and not kwargs.get("company_id"):
                return dict(_TENANT_REQUIRED_RESPONSE)

            # ── HITL gate (AUD-4, 2026-06-06): acao sensivel exige aprovacao ──
            # Pre-flight: BLOQUEIA o side-effect se a tool e marcada
            # requires_confirmation E nao ha aprovacao server-side (ContextVar
            # setada pelo transporte quando o USUARIO confirma — nunca pela LLM).
            # Chokepoint compartilhado -> cobre federado E supervisor. Sem
            # aprovacao -> retorna needs_confirmation, a mutacao NAO roda.
            if requires_confirmation:
                from app.shared.hitl.hitl_approval_context import is_hitl_approved
                if not is_hitl_approved():
                    logger.info(
                        "[%s] HITL gate: %s requer confirmacao do usuario (bloqueado, sem aprovacao)",
                        domain, func.__name__,
                    )
                    return {
                        "success": False,
                        "needs_confirmation": True,
                        "requires_user_input": True,
                        "message": (
                            "Esta acao precisa da sua confirmacao antes de ser "
                            "executada. Confirme para prosseguir."
                        ),
                        "hitl": {"tool": func.__name__, "domain": domain},
                    }

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
