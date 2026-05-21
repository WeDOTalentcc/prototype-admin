"""
LIA-E01: Standard API Response Envelope
LIA-E02: Opt-in decorator for gradual migration

Provides consistent success and error response shapes for the LIA API.
Endpoints can opt-in via:
  1. Direct usage: return APIResponse.ok(data={...})
  2. Decorator: @api_envelope (wraps any dict return in an envelope)

Existing endpoints continue to work unchanged. Migration is gradual.
"""
import functools
import time
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar, Optional, List

from fastapi import Request
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIMetadata(BaseModel):
    """Standard metadata attached to API responses."""
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    api_version: str = "v1"
    duration_ms: Optional[float] = None
    pagination: Optional[dict] = None


class APIError(BaseModel):
    """Standard error detail."""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[dict] = None


# DUPLICATE_OF_INTENT: app/shared/api/response.py:25 — legacy envelope success/message/data; canonical is modern ok/data/error/meta
class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope.

    Success shape:
        {"success": true, "message": "...", "data": {...}, "metadata": {...}, "errors": null}

    Error shape:
        {"success": false, "message": "...", "data": null, "metadata": {...}, "errors": [...]}
    """
    success: bool = True
    message: str = ""
    data: Optional[T] = None
    metadata: APIMetadata = Field(default_factory=APIMetadata)
    errors: Optional[List[APIError]] = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "", metadata: Optional[APIMetadata] = None) -> "APIResponse":
        """Convenience factory for success responses."""
        return cls(
            success=True,
            message=message,
            data=data,
            metadata=metadata or APIMetadata(),
            errors=None,
        )

    @classmethod
    def fail(cls, message: str, errors: Optional[List[APIError]] = None, metadata: Optional[APIMetadata] = None) -> "APIResponse":
        """Convenience factory for error responses."""
        return cls(
            success=False,
            message=message,
            data=None,
            metadata=metadata or APIMetadata(),
            errors=errors or [APIError(code="error", message=message)],
        )


# Convenience alias
APIEnvelope = APIResponse


# ---------------------------------------------------------------------------
# LIA-E02: Opt-in decorator for gradual migration
# ---------------------------------------------------------------------------

def api_envelope(message: str = "OK"):
    """Decorator that wraps a handler's return value in an APIResponse envelope.

    Usage:
        @router.get("/items")
        @api_envelope(message="Items retrieved")
        async def list_items():
            return [...]  # becomes APIResponse(data=[...])
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()

            # Find request object if passed
            request = None
            for arg in list(args) + list(kwargs.values()):
                if isinstance(arg, Request):
                    request = arg
                    break

            try:
                result = await func(*args, **kwargs)

                # If already wrapped, return as-is
                if isinstance(result, APIResponse):
                    return result

                duration_ms = (time.perf_counter() - start) * 1000
                metadata = APIMetadata(
                    request_id=getattr(request.state, "request_id", None) if request else None,
                    duration_ms=round(duration_ms, 2),
                )
                return APIResponse.ok(data=result, message=message, metadata=metadata)
            except Exception:
                # Let FastAPI's exception handlers deal with it
                raise

        return wrapper

    return decorator
