"""Canonical helpers for tool context extraction.

G2 canonical fix (2026-05-24): replaces the recurring antipattern
    company_id = context.company_id if context else None
which causes silent fallback to WHERE company_id = NULL → 0 rows.

Per CLAUDE.md REGRA 4 (no silent fallback in critical AI paths) and
ADR-001 §3 (multi-tenancy fail-closed at producer).
"""
from __future__ import annotations

from typing import Any


class ToolContextMissingError(RuntimeError):
    """Raised when a tool is invoked without proper tenant context.

    This is ALWAYS an orchestrator-level bug — the executor MUST inject
    `_context: ToolExecutionContext` into kwargs before dispatching. If
    this exception is raised, look upstream (agentic_loop, tool_executor,
    main_orchestrator route).
    """


def require_company_id_from_context(kwargs: dict[str, Any], tool_name: str) -> str:
    """Extract company_id from kwargs["_context"]. Fail-loud if missing.

    Side effect: pops `_context` from kwargs (matching `_extract_context`
    contract of legacy tools).

    Raises:
        ToolContextMissingError: when _context is missing or its
            company_id is empty. The error message names the tool and
            points the operator to the orchestrator (not to retry).

    Returns:
        Non-empty company_id (str / UUID-as-str).

    Usage:
        async def search_jobs(..., **kwargs):
            company_id = require_company_id_from_context(kwargs, "search_jobs")
            # ... safe to use in WHERE clause
    """
    context = kwargs.pop("_context", None)
    if context is None:
        raise ToolContextMissingError(
            f"Tool '{tool_name}' invoked without _context. The agentic_loop "
            f"or tool_executor must inject ToolExecutionContext before "
            f"dispatch — see app/tools/executor.py. Silent fail-open would "
            f"return all-zero or cross-tenant rows."
        )
    # TENANT-FALLBACK-OK: this is the canonical helper itself — the if-not-cid raise below converts the None into a loud failure.
    # TENANT-FALLBACK-OK: this is the canonical helper itself — the
    # if-not-cid raise below converts None into a loud failure.
    # TENANT-FALLBACK-OK: canonical helper itself — `if not cid` raise below converts None to loud failure
    cid = getattr(context, "company_id", None)
    if not cid:
        raise ToolContextMissingError(
            f"Tool '{tool_name}' received ToolExecutionContext with empty "
            f"company_id (user_id={getattr(context, 'user_id', '?')}). "
            f"Multi-tenancy fail-closed per CLAUDE.md REGRA 4 + ADR-001."
        )
    return str(cid)


def context_or_raise(kwargs: dict[str, Any], tool_name: str):
    """Return the ToolExecutionContext or raise. Use when callers need
    user_id, permissions, session_id, not just company_id."""
    context = kwargs.pop("_context", None)
    if context is None:
        raise ToolContextMissingError(
            f"Tool '{tool_name}' invoked without _context — see "
            f"require_company_id_from_context docstring."
        )
    return context


def require_company_id_from_obj(context: Any, tool_name: str) -> str:
    """Validate company_id on an already-extracted context object.

    Sprint 2 (G2 batch migration): tools that need BOTH company_id AND user_id
    use `context_or_raise` to get the context, then this helper to validate
    company_id. Avoids popping `_context` twice from kwargs.

    Raises:
        ToolContextMissingError: when company_id is empty.

    Usage:
        context = context_or_raise(kwargs, "tool_name")
        company_id = require_company_id_from_obj(context, "tool_name")
        user_id = context.user_id
    """
    # TENANT-FALLBACK-OK: canonical helper itself — `if not cid` raise below converts None to loud failure
    cid = getattr(context, "company_id", None)
    if not cid:
        raise ToolContextMissingError(
            f"Tool '{tool_name}' received ToolExecutionContext with empty "
            f"company_id (user_id={getattr(context, 'user_id', '?')}). "
            f"Multi-tenancy fail-closed per CLAUDE.md REGRA 4 + ADR-001."
        )
    return str(cid)



def normalize_wrapper_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Normalize tool wrapper kwargs to canonical `_context`-in-kwargs form.

    Converges TWO dispatch paths into a single canonical kwargs shape so that
    downstream tool handlers can rely on `kwargs["_context"]`:

    - Path A (Global ToolExecutor): `app/tools/executor.py:281` (Sprint 8
      NS-2, commit 06b199d4, 2026-05-24) injects
      ``handler_kwargs["_context"] = ToolExecutionContext(...)`` before
      dispatching. The wrapper just needs to forward.

    - Path B (Domain ReAct agents via `tool_handler` decorator): the
      decorator extracts company_id/user_id from the
      `_current_company_id` / `_current_user_id` ContextVars and injects
      them as regular kwargs (NOT _context). The wrapper must build
      `_context` from those before forwarding.

    Defensive contract:
    - If Path A already supplied a non-empty `_context`, keep it.
    - Otherwise, pop `company_id`/`user_id` and synthesize a SimpleNamespace.
    - Never silently drop tenant: empty company_id passes through so the
      canonical handler can fail-loud via require_company_id_from_context.

    Sensor 3 (registered 2026-05-24, see scripts/check_wrappers_prefer_context.py)
    blocks wrapper code that pops company_id without delegating to this helper.
    """
    from types import SimpleNamespace

    existing = kwargs.get("_context")
    if existing is not None and getattr(existing, "company_id", ""):
        # Path A — executor already injected valid context. Forward as-is.
        return kwargs

    # Path B — build _context from explicit kwargs (tool_handler ContextVar pattern).
    company_id = kwargs.pop("company_id", "") or ""
    user_id = kwargs.pop("user_id", "") or ""
    kwargs["_context"] = SimpleNamespace(company_id=company_id, user_id=user_id)
    return kwargs
