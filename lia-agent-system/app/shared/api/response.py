import os
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ResponseMeta(BaseModel):
    request_id: str | None = None
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = APP_VERSION


class APIResponse(BaseModel):
    ok: bool
    data: Any | None = None
    error: ErrorDetail | None = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


def _extract_request_id(request: Request | None) -> str | None:
    if request is None:
        return None
    return getattr(request.state, "request_id", None)


def ok_response(
    data: Any,
    status_code: int = 200,
    request: Request | None = None,
) -> JSONResponse:
    meta = ResponseMeta(request_id=_extract_request_id(request))
    body: dict[str, Any] = {
        "ok": True,
        "data": data,
        "meta": meta.model_dump(),
    }
    return JSONResponse(content=body, status_code=status_code)


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
) -> JSONResponse:
    meta = ResponseMeta(request_id=_extract_request_id(request))
    body: dict[str, Any] = {
        "ok": False,
        "error": ErrorDetail(code=code, message=message, details=details).model_dump(),
        "meta": meta.model_dump(),
    }
    return JSONResponse(content=body, status_code=status_code)


def not_found(resource: str, request: Request | None = None) -> JSONResponse:
    return error_response("NOT_FOUND", f"{resource} not found", 404, request=request)


def forbidden(reason: str = "Access denied", request: Request | None = None) -> JSONResponse:
    return error_response("FORBIDDEN", reason, 403, request=request)


def bad_request(message: str, request: Request | None = None) -> JSONResponse:
    return error_response("BAD_REQUEST", message, 400, request=request)


def internal_error(request: Request | None = None) -> JSONResponse:
    return error_response("INTERNAL_ERROR", "An internal error occurred", 500, request=request)
