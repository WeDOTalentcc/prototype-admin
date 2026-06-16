"""Canonical RuntimeContext for tool/handler dependency injection.

ADR-029 §3 — RuntimeContext Wrapper
====================================================================

Sprint 1B installed ContextVar-based tenant injection at the
`tool_handler` decorator level. Sprint 3 formalizes the pattern:

  - Typed access: `ctx.company_id` instead of `kwargs.get("company_id")`
  - Single source of truth for runtime context fields
  - Future-proof: easy to add user_id/request_id/db when middleware
    populates them

This module is the canonical entrypoint. Tool handlers should NOT
read `_current_company_id` ContextVar directly — use `RuntimeContext`
or `with_runtime_context` decorator.

Usage:
    from app.shared.runtime_context import RuntimeContext, with_runtime_context

    # Direct access
    ctx = RuntimeContext.from_contextvars()
    if not ctx.company_id:
        raise RuntimeError("...")

    # Decorator (typed injection)
    @with_runtime_context("company_id")
    @tool_handler("my_domain")
    async def my_tool(*, company_id: str, **kwargs):
        ...
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, fields
import inspect
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """Per-request runtime context.

    All fields come from canonical ContextVars set by middleware
    (`app/middleware/auth_enforcement.py`). Frozen to prevent mutation
    after construction; build a new instance to override.

    Sprint 3 MVP: only `company_id` is wired. Adding more fields
    requires:
      1. ContextVar declaration in `auth_enforcement.py`
      2. Middleware setter logic
      3. Field below + `from_contextvars()` mapping
    """

    company_id: str = ""

    # Reserved for future expansion (see ADR-029 §3 candidates):
    # user_id: str = ""
    # user_role: str = ""
    # request_id: str = ""
    # db: Any = None  # set by FastAPI Depends, not ContextVar

    @classmethod
    def from_contextvars(cls) -> "RuntimeContext":
        """Build a RuntimeContext from the current request's ContextVars.

        Returns empty/default values if not inside a request context
        (e.g., test fixture without middleware). Caller should validate
        required fields.
        """
        # Lazy import to avoid circular at module load time
        try:
            from app.middleware.auth_enforcement import _current_company_id
            company_id = _current_company_id.get("") or ""
        except Exception as exc:
            logger.warning("[RuntimeContext] failed to read ContextVar: %s", exc)
            company_id = ""

        return cls(company_id=company_id)

    def is_complete(self, required_fields: tuple[str, ...]) -> bool:
        """Returns True iff every requested field is non-empty."""
        for fname in required_fields:
            value = getattr(self, fname, None)
            if not value:
                return False
        return True

    def as_kwargs(self, fields_subset: tuple[str, ...] | None = None) -> dict[str, Any]:
        """Return a dict of field -> value for kwarg injection.

        Args:
            fields_subset: only include these fields (default: all non-empty)
        """
        out: dict[str, Any] = {}
        for f in fields(self):
            if fields_subset is not None and f.name not in fields_subset:
                continue
            value = getattr(self, f.name)
            if value:  # only inject non-empty values
                out[f.name] = value
        return out


def with_runtime_context(*field_names: str) -> Callable[[Callable], Callable]:
    """Decorator: inject specified RuntimeContext fields into kwargs.

    Stacks above `tool_handler` (so the inner handler still receives
    the validated kwargs). Companion to Sprint 1B's tool_handler
    ContextVar injection — this version is more explicit and typed.

    Args:
        *field_names: which fields to inject. E.g.
            @with_runtime_context("company_id")

    Behavior:
        - Builds RuntimeContext from current ContextVars
        - For each requested field: if non-empty in ctx AND not already
          in kwargs, inject it
        - kwargs already containing the field WIN (caller override —
          unlike Sprint 1B's tool_handler decorator which always wins
          for security reasons)

    NOTE: This decorator does NOT enforce fail-closed. For tenant
    enforcement, stack `tool_handler` underneath:

        @with_runtime_context("company_id")
        @tool_handler("my_domain")  # this enforces fail-closed
        async def handler(...): ...
    """
    if not field_names:
        raise ValueError(
            "with_runtime_context requires at least 1 field name "
            "(e.g. with_runtime_context('company_id'))"
        )

    valid = {f.name for f in fields(RuntimeContext)}
    invalid = [n for n in field_names if n not in valid]
    if invalid:
        raise ValueError(
            f"with_runtime_context: unknown field(s) {invalid}. "
            f"Valid: {sorted(valid)}"
        )

    def decorator(fn: Callable) -> Callable:
        # D.1 (Workstream D ticket 1, 2026-05-23): bind via inspect.signature so
        # the wrapper accepts positional args + self for methods + mixed call
        # styles. Pre-D.1 the wrapper only accepted **kwargs which forced voice
        # services with positional args to fall back to inline RuntimeContext.
        sig = inspect.signature(fn)

        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = RuntimeContext.from_contextvars()

            try:
                # Bind args+kwargs to signature so we can see which fields the
                # caller already populated (positionally or by keyword) and
                # only inject into the empty slots.
                bound = sig.bind_partial(*args, **kwargs)
            except TypeError:
                # Fallback: signature binding failed (e.g. fn uses **kwargs
                # only and inspect couldn't fully resolve). Behave like the
                # legacy kwargs-only wrapper.
                for fname in field_names:
                    if fname not in kwargs or not kwargs.get(fname):
                        value = getattr(ctx, fname, None)
                        if value:
                            kwargs[fname] = value
                return await fn(*args, **kwargs)

            # Detect a possible VAR_KEYWORD param (e.g. **kwargs); its name
            # is whatever the function called it (commonly "kwargs"). We use
            # this both to allow ContextVar injection through it AND to honor
            # caller-supplied values stuffed into it.
            var_keyword_name: str | None = None
            for pname, p in sig.parameters.items():
                if p.kind == inspect.Parameter.VAR_KEYWORD:
                    var_keyword_name = pname
                    break

            def _caller_already_set(field_name: str) -> bool:
                # Direct positional/keyword slot (e.g. company_id is a real param).
                if field_name in bound.arguments and bound.arguments.get(field_name):
                    return True
                # Hidden inside **kwargs (e.g. handler signature is
                # ``async def h(**kwargs)`` and caller passed company_id=...).
                if var_keyword_name and var_keyword_name in bound.arguments:
                    var_dict = bound.arguments.get(var_keyword_name) or {}
                    if isinstance(var_dict, dict) and var_dict.get(field_name):
                        return True
                # Caller-supplied via raw kwargs to wrapper (in case bind
                # missed it for some signature corner case).
                if field_name in kwargs and kwargs.get(field_name):
                    return True
                return False

            for fname in field_names:
                # Caller-wins.
                if _caller_already_set(fname):
                    continue
                # ContextVar fallback: inject if the field is a known param OR
                # if the function accepts **kwargs (VAR_KEYWORD absorbs any name).
                if fname not in sig.parameters and var_keyword_name is None:
                    continue
                value = getattr(ctx, fname, None)
                if value:
                    kwargs[fname] = value

            return await fn(*args, **kwargs)

        # Mark for sensor introspection
        wrapper._runtime_context_fields = field_names  # type: ignore[attr-defined]
        return wrapper

    return decorator
