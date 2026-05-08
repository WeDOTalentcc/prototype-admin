"""
LLM Provider Metrics — in-memory fallback and circuit breaker counters.

Production: swap out with Prometheus client or LangSmith spans without
breaking the call signature.
"""
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

_fallback_counter: dict[str, int] = {}
_circuit_counter: dict[str, int] = {}
_fallback_timestamps: list[tuple[str, str, str, float]] = []  # (primary, fallback, tenant, ts)


def record_fallback(primary: str, fallback_provider: str, tenant_id: Optional[str] = None) -> None:
    """Record a provider fallback event."""
    key = f"{primary}→{fallback_provider}"
    _fallback_counter[key] = _fallback_counter.get(key, 0) + 1
    _fallback_timestamps.append((primary, fallback_provider, tenant_id or "", time.time()))
    # Keep only last 1000 events
    if len(_fallback_timestamps) > 1000:
        _fallback_timestamps.pop(0)
    logger.info(
        "[LLM-Metrics] fallback event: primary=%s → fallback=%s tenant=%s total=%d",
        primary,
        fallback_provider,
        tenant_id,
        _fallback_counter[key],
    )


def record_circuit_open(provider: str) -> None:
    """Record a circuit breaker open event."""
    _circuit_counter[provider] = _circuit_counter.get(provider, 0) + 1
    logger.warning(
        "[LLM-Metrics] circuit_open: provider=%s total=%d",
        provider,
        _circuit_counter[provider],
    )


def get_metrics() -> dict:
    """Return current metric snapshot for dashboard/health endpoints."""
    return {
        "fallback_total": dict(_fallback_counter),
        "circuit_open_total": dict(_circuit_counter),
        "recent_fallbacks": len(_fallback_timestamps),
    }
