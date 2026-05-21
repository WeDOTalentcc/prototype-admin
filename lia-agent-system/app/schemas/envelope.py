from __future__ import annotations

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


# DUPLICATE_OF_INTENT: app/shared/api/response.py — legacy envelope meta with pagination, kept for compat (Sprint Q.1 triagem I bucket)
class ResponseMeta(BaseModel):
    page: int | None = None
    per_page: int | None = None
    total: int | None = None
    request_id: str | None = None


class ResponseEnvelope(BaseModel, Generic[T]):
    data: T | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    request_id: str | None = None
    model_config = {"arbitrary_types_allowed": True}


def ok_envelope(data: Any, *, meta: dict | None = None, request_id: str | None = None) -> ResponseEnvelope:
    return ResponseEnvelope(data=data, meta=meta or {}, request_id=request_id)


def error_envelope(message: str, *, status_code: int = 400, request_id: str | None = None) -> ResponseEnvelope:
    return ResponseEnvelope(data=None, errors=[message], meta={"status_code": status_code}, request_id=request_id)
