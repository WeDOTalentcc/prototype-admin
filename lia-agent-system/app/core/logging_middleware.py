"""
StructuredLoggingMiddleware — Per-request structured log entry.

Emits one JSON-compatible log record per request containing:
  request_id, method, path, status_code, duration_ms,
  company_id (from auth header if present), user_id, tier

Tier classification:
  - "agent"      paths under /api/v1/lia-assistant or /api/v1/agent
  - "management" paths under /api/v1/admin or /api/v1/compliance
  - "data"       everything else under /api/v1

Usage (in main.py):
    from app.core.logging_middleware import StructuredLoggingMiddleware
    app.add_middleware(StructuredLoggingMiddleware)
"""
import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("lia.request")


def _classify_tier(path: str) -> str:
    if any(seg in path for seg in ("/lia-assistant", "/agent", "/wsi", "/wizard")):
        return "agent"
    if any(seg in path for seg in ("/admin", "/compliance", "/audit", "/drift", "/bias")):
        return "management"
    return "data"


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Adds a structured log line for every HTTP request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()

        # Extract identifiers from request state (set by RequestIdMiddleware / auth)
        request_id: str = getattr(request.state, "request_id", "-")

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        # User/company info may be set on state by auth dependencies after call_next
        user_id: str = getattr(request.state, "user_id", "-")
        company_id: str = getattr(request.state, "company_id", "-")

        tier = _classify_tier(request.url.path)

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "company_id": company_id,
                "user_id": user_id,
                "tier": tier,
            },
        )

        return response
