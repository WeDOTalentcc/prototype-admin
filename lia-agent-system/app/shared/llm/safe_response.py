"""
safe_llm_with_flag — canonical helper for LLM-touching handlers.

REGRA 4 (CLAUDE.md): handlers tocando LLM/encryption/critical IO MUST fail-loud.

This helper enforces an explicit envelope contract:

    envelope = safe_llm_with_flag(my_llm_call, *args, **kwargs)
    envelope.success          # True if call succeeded
    envelope.data             # the actual result (None on failure)
    envelope.fallback_used    # explicit flag — NEVER hidden
    envelope.failure_mode     # enum (LLMFailureMode) explaining failure
    envelope.error_message    # human-readable
    envelope.needs_manual_review  # explicit ops signal

A handler can then return the envelope as-is to the API, which makes the
failure VISIBLE in the response. The previous anti-pattern was:

    try:
        return llm_call(...)        # success path
    except Exception:
        return template_fallback   # SILENT — caller can't tell
                                    # this was a fallback. Looks like success.

That is exactly the F6.B3 pattern caught in the 2026-05-20 audit
(analyze_company_culture, get_llm_config). The helper makes it impossible
to silently mask LLM failure.

Usage:
    from app.shared.llm import safe_llm_with_flag, LLMFailureMode

    @router.post("/analyze")
    async def analyze(payload):
        envelope = await safe_llm_with_flag(
            llm_analyze_culture,
            payload=payload,
        )
        # Frontend gets {"success": False, "fallback_used": True, ...}
        # if LLM failed — not a fake "success" with empty strings.
        return envelope.to_dict()
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LLMFailureMode(str, Enum):
    """Explicit categories of LLM call failure."""

    SUCCESS = "success"
    PARSE_ERROR = "parse_error"           # JSON parse, schema validation
    PROVIDER_ERROR = "provider_error"     # OpenAI 500, Anthropic timeout
    AUTH_ERROR = "auth_error"             # bad API key, quota
    NETWORK_ERROR = "network_error"       # connection refused, DNS
    UNKNOWN = "unknown"                   # catch-all (still explicit)


@dataclass
class LLMResponseEnvelope:
    """Explicit envelope — replaces silent fallback."""

    success: bool
    data: Any = None
    fallback_used: bool = False
    failure_mode: LLMFailureMode = LLMFailureMode.SUCCESS
    error_message: str | None = None
    needs_manual_review: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "fallback_used": self.fallback_used,
            "failure_mode": self.failure_mode.value,
            "error_message": self.error_message,
            "needs_manual_review": self.needs_manual_review,
            "metadata": self.metadata,
        }


def _classify_exception(exc: Exception) -> LLMFailureMode:
    """Best-effort classification — duck-types on exc name."""
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if any(t in name for t in ("json", "validation", "pydantic", "parse")):
        return LLMFailureMode.PARSE_ERROR
    if any(t in name for t in ("timeout", "connection", "network")):
        return LLMFailureMode.NETWORK_ERROR
    if any(t in name for t in ("auth", "permission", "quota")):
        return LLMFailureMode.AUTH_ERROR
    if any(t in msg for t in ("api key", "unauthorized", "401")):
        return LLMFailureMode.AUTH_ERROR
    if any(t in msg for t in ("503", "502", "500", "provider")):
        return LLMFailureMode.PROVIDER_ERROR
    return LLMFailureMode.UNKNOWN


def safe_llm_with_flag(
    func: Callable[..., T],
    *args: Any,
    fallback_data: Any = None,
    needs_manual_review_on_fail: bool = False,
    **kwargs: Any,
) -> LLMResponseEnvelope:
    """
    Call `func(*args, **kwargs)` and wrap in canonical envelope (sync version).

    On exception:
    - Log full traceback
    - Return envelope with success=False, fallback_used=True, classified failure_mode
    - NEVER raise (caller decides how to handle envelope)

    For async functions, use `safe_llm_with_flag_async`.
    """
    try:
        result = func(*args, **kwargs)
        return LLMResponseEnvelope(success=True, data=result)
    except Exception as exc:
        mode = _classify_exception(exc)
        logger.exception(
            "safe_llm_with_flag caught %s (%s) in %s",
            type(exc).__name__,
            mode.value,
            getattr(func, "__name__", repr(func)),
        )
        return LLMResponseEnvelope(
            success=False,
            data=fallback_data,
            fallback_used=True,
            failure_mode=mode,
            error_message=str(exc),
            needs_manual_review=needs_manual_review_on_fail,
        )


async def safe_llm_with_flag_async(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    fallback_data: Any = None,
    needs_manual_review_on_fail: bool = False,
    **kwargs: Any,
) -> LLMResponseEnvelope:
    """Async version of safe_llm_with_flag."""
    try:
        result = await func(*args, **kwargs)
        return LLMResponseEnvelope(success=True, data=result)
    except Exception as exc:
        mode = _classify_exception(exc)
        logger.exception(
            "safe_llm_with_flag_async caught %s (%s) in %s",
            type(exc).__name__,
            mode.value,
            getattr(func, "__name__", repr(func)),
        )
        return LLMResponseEnvelope(
            success=False,
            data=fallback_data,
            fallback_used=True,
            failure_mode=mode,
            error_message=str(exc),
            needs_manual_review=needs_manual_review_on_fail,
        )
