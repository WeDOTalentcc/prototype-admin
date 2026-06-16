"""Pydantic schemas for webhook management."""
from typing import Optional

from pydantic import BaseModel, Field, validator
from app.shared.types import WeDoBaseModel


ALLOWED_EVENTS = [
    "agent.execution.completed",
    "agent.execution.failed",
    "agent.deployment.created",
    "agent.deployment.paused",
    "agent.approval.requested",
    "agent.approval.reviewed",
]


class CreateWebhookRequest(WeDoBaseModel):
    name: str = Field(..., min_length=2, max_length=256)
    url: str = Field(..., min_length=10, max_length=2048)
    events: list[str] = Field(..., min_length=1)

    @validator("url")
    def validate_url(cls, v):
        # WT-2022 P0.SEG1: SSRF prevention canonical
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        try:
            return safe_outbound_url(v, require_https=True)
        except UnsafeOutboundURLError as exc:
            raise ValueError(f"Webhook URL bloqueada por seguranca: {exc}")

    @validator("events")
    def validate_events(cls, v):
        invalid = [e for e in v if e not in ALLOWED_EVENTS]
        if invalid:
            raise ValueError(f"Invalid events: {invalid}. Allowed: {ALLOWED_EVENTS}")
        return list(set(v))  # dedupe


class UpdateWebhookRequest(WeDoBaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=256)
    url: Optional[str] = Field(None, min_length=10, max_length=2048)
    events: Optional[list[str]] = None
    is_active: Optional[bool] = None

    @validator("url")
    def validate_url(cls, v):
        # WT-2022 P0.SEG1: SSRF prevention canonical
        if v is None:
            return v
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        try:
            return safe_outbound_url(v, require_https=True)
        except UnsafeOutboundURLError as exc:
            raise ValueError(f"Webhook URL bloqueada por seguranca: {exc}")

    @validator("events")
    def validate_events(cls, v):
        if v is None:
            return None
        invalid = [e for e in v if e not in ALLOWED_EVENTS]
        if invalid:
            raise ValueError(f"Invalid events: {invalid}")
        return list(set(v))


class WebhookResponse(BaseModel):
    id: str
    company_id: str
    name: str
    url: str
    events: list[str] = []
    is_active: bool
    total_deliveries: int = 0
    total_failures: int = 0
    last_delivery_at: Optional[str] = None
    last_status_code: Optional[int] = None
    last_error: Optional[str] = None
    created_by: str = ""
    created_at: Optional[str] = None
    secret: Optional[str] = None  # only on create response


class WebhookListResponse(BaseModel):
    webhooks: list[WebhookResponse]
    total: int
