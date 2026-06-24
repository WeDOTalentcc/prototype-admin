"""
GAP-12-011: psutil system-memory gauge + high-memory warning.
GAP-12-009: tracemalloc periodic snapshot para detectar memory leaks.

prometheus_client's default ProcessCollector already exports:
  process_resident_memory_bytes, process_virtual_memory_bytes,
  process_cpu_seconds, process_open_fds

This module adds system-wide memory visibility via psutil:
  system_memory_usage_percent — % of total RAM in use across the host

Called on every /metrics scrape; fail-open if psutil unavailable.
"""
import logging
import os
import tracemalloc as _tracemalloc

logger = logging.getLogger(__name__)

# GAP-12-009: tracemalloc snapshot — opt-in via env var (default off to avoid perf impact)
_TRACEMALLOC_ENABLED = os.getenv("TRACEMALLOC_ENABLED", "false").lower() == "true"
_TRACEMALLOC_SNAPSHOT_INTERVAL = int(os.getenv("TRACEMALLOC_SNAPSHOT_INTERVAL", "60"))
_TRACEMALLOC_TOP_N = int(os.getenv("TRACEMALLOC_TOP_N", "5"))
_tracemalloc_call_count = 0

if _TRACEMALLOC_ENABLED:
    _tracemalloc.start(10)  # keep 10 frames of traceback
    logger.info("[metrics] tracemalloc started — snapshot every %d scrapes", _TRACEMALLOC_SNAPSHOT_INTERVAL)


def _take_tracemalloc_snapshot() -> None:
    """Log top N memory allocations. Called periodically. Fail-open."""
    if not _TRACEMALLOC_ENABLED or not _tracemalloc.is_tracing():
        return
    try:
        snapshot = _tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")[:_TRACEMALLOC_TOP_N]
        logger.info("[metrics][tracemalloc] Top %d memory allocations:", _TRACEMALLOC_TOP_N)
        for idx, stat in enumerate(top_stats, 1):
            logger.info(
                "[metrics][tracemalloc]  #%d: %s — %.1f KiB",
                idx, stat.traceback.format()[0] if stat.traceback else "unknown",
                stat.size / 1024,
            )
    except Exception as exc:
        logger.debug("[metrics] tracemalloc snapshot failed (fail-open): %s", exc)


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
        """Refresh psutil gauges and optionally log tracemalloc snapshot."""
        global _tracemalloc_call_count
        _tracemalloc_call_count += 1
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

        # GAP-12-009: periodic tracemalloc snapshot
        if _TRACEMALLOC_ENABLED and _tracemalloc_call_count % _TRACEMALLOC_SNAPSHOT_INTERVAL == 0:
            _take_tracemalloc_snapshot()

    PSUTIL_AVAILABLE = True

except ImportError:  # pragma: no cover
    PSUTIL_AVAILABLE = False

    def update_process_metrics() -> None:  # type: ignore[misc]
        """No-op: psutil not installed. tracemalloc snapshot still runs if enabled."""
        global _tracemalloc_call_count
        _tracemalloc_call_count += 1
        if _TRACEMALLOC_ENABLED and _tracemalloc_call_count % _TRACEMALLOC_SNAPSHOT_INTERVAL == 0:
            _take_tracemalloc_snapshot()

    logger.info(
        "[metrics] psutil not installed — system_memory_usage_percent gauge disabled"
        " (add psutil>=5.9 to requirements.txt)"
    )
