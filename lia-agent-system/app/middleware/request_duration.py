"""
GAP-12-008: HTTP request duration tracking with slow-request alerting.

Complements StructuredLoggingMiddleware (which logs every request) by:
  1. Adding X-Response-Time-Ms header for client-side visibility.
  2. Logging slow requests as WARNING (structured, with request_id).
  3. Exposing a Prometheus histogram (http_request_duration_seconds)
     when prometheus_client is installed.

Mount AFTER RequestIdMiddleware so request.state.request_id is available.
"""
import logging
import os
import time
from collections.abc import Callable

# GAP-12-006: N+1 query detection helpers (no-op if not in dev mode)
try:
    from lia_config.database import (
        N_PLUS_ONE_ENABLED,
        N_PLUS_ONE_THRESHOLD,
        get_request_query_count,
        reset_request_query_count,
    )
except ImportError:
    N_PLUS_ONE_ENABLED = False
    N_PLUS_ONE_THRESHOLD = 10
    def get_request_query_count(): return 0
    def reset_request_query_count(): pass


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("lia.slow_request")

SLOW_REQUEST_THRESHOLD_MS: float = float(
    os.getenv("SLOW_REQUEST_THRESHOLD_MS", "3000")
)

# ---------------------------------------------------------------------------
# Optional Prometheus histogram — fail-open if prometheus_client not installed
# ---------------------------------------------------------------------------
try:
    from prometheus_client import Histogram

    REQUEST_DURATION_HISTOGRAM: Histogram | None = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "status_code"],
        buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    )
except ImportError:  # pragma: no cover
    REQUEST_DURATION_HISTOGRAM = None


# Paths excluded from slow-request alerting (health checks, metrics, SSE streams)
_EXCLUDED_PREFIXES = ("/health", "/metrics", "/api/v1/lia-assistant/sse")


class RequestDurationMiddleware(BaseHTTPMiddleware):
    """Tracks HTTP request duration, exposes header + histogram + slow alert."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()

        # GAP-12-006: reset SQL counter for this request scope (dev only)
        if N_PLUS_ONE_ENABLED:
            reset_request_query_count()

        response = await call_next(request)

        duration_s = time.perf_counter() - start
        duration_ms = duration_s * 1000

        # GAP-12-006: attach query count header + N+1 warning (dev only)
        if N_PLUS_ONE_ENABLED:
            _qcount = get_request_query_count()
            response.headers["X-Query-Count"] = str(_qcount)
            path = request.url.path
            if (
                _qcount > N_PLUS_ONE_THRESHOLD
                and not any(path.startswith(p) for p in _EXCLUDED_PREFIXES)
            ):
                _req_id = getattr(request.state, "request_id", "unknown")
                logging.getLogger("lia.n_plus_one").warning(
                    "[N+1] %d SQL queries for %s %s (threshold %d) — possible N+1 issue",
                    _qcount,
                    request.method,
                    path,
                    N_PLUS_ONE_THRESHOLD,
                    extra={"request_id": _req_id, "query_count": _qcount, "path": path},
                )

        # 1. Response header for client visibility
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.0f}"

        path = request.url.path

        # 2. Prometheus histogram (label cardinality kept low — no raw path)
        if REQUEST_DURATION_HISTOGRAM is not None:
            REQUEST_DURATION_HISTOGRAM.labels(
                method=request.method,
                status_code=str(response.status_code),
            ).observe(duration_s)

        # 3. Slow-request warning (skip excluded paths)
        if duration_ms > SLOW_REQUEST_THRESHOLD_MS and not any(
            path.startswith(p) for p in _EXCLUDED_PREFIXES
        ):
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(
                "Slow request: %s %s took %.0fms (threshold: %.0fms)",
                request.method,
                path,
                duration_ms,
                SLOW_REQUEST_THRESHOLD_MS,
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration_ms, 1),
                    "path": path,
                    "method": request.method,
                    "status_code": response.status_code,
                },
            )

        return response
