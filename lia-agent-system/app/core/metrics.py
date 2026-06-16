"""
GAP-12-011: psutil system-memory gauge + high-memory warning.

prometheus_client's default ProcessCollector already exports:
  process_resident_memory_bytes, process_virtual_memory_bytes,
  process_cpu_seconds, process_open_fds

This module adds system-wide memory visibility via psutil:
  system_memory_usage_percent — % of total RAM in use across the host

Called on every /metrics scrape; fail-open if psutil unavailable.
"""
import logging
import os

logger = logging.getLogger(__name__)

try:
    import psutil as _psutil
    from prometheus_client import Gauge as _Gauge

    _SYSTEM_MEMORY_PERCENT = _Gauge(
        "system_memory_usage_percent",
        "System-wide RAM usage as a percentage (host total)",
    )

    _MEMORY_WARNING_THRESHOLD = float(
        os.getenv("PSUTIL_MEMORY_WARNING_THRESHOLD", "80.0")
    )

    def update_process_metrics() -> None:
        """Refresh psutil gauges — called before every /metrics scrape."""
        try:
            sys_mem = _psutil.virtual_memory()
            _SYSTEM_MEMORY_PERCENT.set(sys_mem.percent)

            if sys_mem.percent >= _MEMORY_WARNING_THRESHOLD:
                logger.warning(
                    "[metrics] High system memory: %.1f%% (%.1fGB / %.1fGB)",
                    sys_mem.percent,
                    sys_mem.used / 1e9,
                    sys_mem.total / 1e9,
                )
        except Exception as exc:  # pragma: no cover
            logger.debug("[metrics] psutil update skipped (fail-open): %s", exc)

    PSUTIL_AVAILABLE = True

except ImportError:  # pragma: no cover
    PSUTIL_AVAILABLE = False

    def update_process_metrics() -> None:  # type: ignore[misc]
        """No-op: psutil not installed."""

    logger.info(
        "[metrics] psutil not installed — system_memory_usage_percent gauge disabled"
        " (add psutil>=5.9 to requirements.txt)"
    )
