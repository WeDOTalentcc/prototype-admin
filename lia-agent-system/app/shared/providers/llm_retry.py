"""Transient-error retry helpers for LLM providers.

Provides exponential-backoff retry on 429 / 5xx / connection errors,
separate from the CircuitBreaker (which handles sustained outages).

Layered protection model::

    @circuit_breaker       <- long-term guard (opens after N failures)
    @_traceable            <- LangSmith trace wraps the full operation
    @llm_transient_retry   <- short-term retry (up to 3 attempts, 1-10s backoff)
       -> actual LLM call

This ordering means the CircuitBreaker counts 1 failure per user-initiated
call (not per retry attempt), preventing spurious circuit opens on transient
spikes. Retried exceptions are re-raised after exhausting attempts so the
circuit breaker still records the final failure.

Usage::

    from app.shared.providers.llm_retry import llm_transient_retry

    @circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
    @_traceable(name="...", run_type="llm")
    @llm_transient_retry
    async def generate(self, ...):
        ...
"""
from __future__ import annotations

import logging

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Transient-error predicate -- provider-agnostic, no external imports
# ---------------------------------------------------------------------------

#: Error class names that are always transient (retry without status code).
_TRANSIENT_CLASS_NAMES: frozenset[str] = frozenset({
    "RateLimitError",           # Anthropic / OpenAI 429
    "InternalServerError",      # Anthropic / OpenAI 500
    "ServiceUnavailableError",  # 503
    "APIConnectionError",       # Network-level (Anthropic SDK)
    "APITimeoutError",          # Request timeout (Anthropic SDK)
    "Timeout",                  # Requests / httpx timeout
    "TooManyRequests",          # Generic alias for 429
    "OverloadedError",          # Anthropic overload (529)
})


def _is_transient_llm_error(exc: BaseException) -> bool:
    """Return True if *exc* is a transient LLM provider error worth retrying.

    Detects by:

    1. HTTP status code attribute (429, 5xx).
    2. Exception class name for well-known transient types.

    No hard imports on provider SDKs -- works in test environments that
    do not have anthropic / openai installed.
    """
    # 1. Status-code check (works for all SDKs that expose it)
    status: int | None = (
        getattr(exc, "status_code", None)
        or getattr(exc, "status", None)
        or getattr(exc, "http_status", None)
    )
    if status is not None:
        try:
            status = int(status)
        except (ValueError, TypeError):
            status = None
    if status is not None:
        return status == 429 or (500 <= status < 600)

    # 2. Class-name fallback
    return type(exc).__name__ in _TRANSIENT_CLASS_NAMES


# ---------------------------------------------------------------------------
# Decorator -- module-level singleton, safe to use as @decorator
# ---------------------------------------------------------------------------

llm_transient_retry = retry(
    retry=retry_if_exception(_is_transient_llm_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10, jitter=2),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,  # re-raise after exhausting attempts (circuit breaker must see it)
)
"""Tenacity retry decorator for transient LLM provider errors.

Retries up to 3 times with exponential backoff (1s, 2s, ..., max 10s).
Only retries on 429 / 5xx / connection errors -- never on auth/schema errors.
"""
