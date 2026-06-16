"""
Pydantic schemas canonical para WebhookEventType.

Audit 2026-05-20 Sprint 5 (catalogos dinamicos).
Aplica REGRA 1 (extra='forbid' via WeDoBaseModel), REGRA 2 (company_id
NUNCA no payload — vem do JWT), REGRA 3 (Path UUID via type alias).
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.types import WeDoBaseModel


# Categorias canonical — mantenha em sync com migration 157 seed.
# Brief mencionou: candidates | jobs | interviews | offers | ats.
# Adicionei agents/system pra acomodar eventos reais existentes no codebase.
EventCategory = Literal[
    "candidates",
    "jobs",
    "interviews",
    "offers",
    "ats",
    "agents",
    "system",
]


# Slug canonical: namespace.action (e.g., "candidate.created"), lowercase,
# permite letras/dígitos/underscore em cada parte, separador `.`.
_EVENT_TYPE_SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")


class WebhookEventTypeData(BaseModel):
    """Schema canonical do payload do evento (armazenado em data JSONB)."""

    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(
        ...,
        min_length=3,
        max_length=128,
        description="Slug canonical (namespace.action). e.g., 'candidate.created'",
    )
    label: str = Field(..., min_length=2, max_length=256)
    category: EventCategory
    description: str | None = Field(None, max_length=2000)
    payload_schema: dict[str, Any] | None = Field(
        None,
        description="JSONSchema do payload (opcional, valida shape do evento)",
    )
    deprecated: bool = False
    metadata: dict[str, Any] | None = None

    @field_validator("event_type")
    @classmethod
    def _validate_event_type_slug(cls, v: str) -> str:
        if not _EVENT_TYPE_SLUG_RE.match(v):
            raise ValueError(
                "event_type deve ser slug canonical 'namespace.action' (lowercase, "
                "letras/dígitos/underscore separados por ponto). Ex: 'candidate.created'"
            )
        return v


class WebhookEventTypeCreate(WeDoBaseModel):
    """Request body for creating a custom event type (canonical novo do zero).

    REGRA 2 canonical: company_id NUNCA no payload — vem do JWT via
    Depends(require_company_id).
    """

    data: WebhookEventTypeData = Field(..., description="Conteúdo canonical")


class WebhookEventTypeUpdate(WeDoBaseModel):
    """Request body for updating an existing custom event type.

    Master events não podem ser atualizados; apenas customizados (cópia).
    """

    data: WebhookEventTypeData


class CustomizeMasterRequest(WeDoBaseModel):
    """Request body para customizar um master event type (cópia canonical A1).

    Cria uma cópia total do master para a company, com parent_template_id
    apontando para o master de origem. Snapshot canonical (B1) — não
    sincroniza com master após criação.
    """

    overrides: WebhookEventTypeData | None = Field(
        None,
        description=(
            "Opcional: fields para override no momento da customizacao. "
            "Se None, cria cópia identica ao master."
        ),
    )


class WebhookEventTypeResponse(BaseModel):
    """Response canonical."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: str | None
    is_master_template: bool
    parent_template_id: uuid.UUID | None
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    deleted_at: datetime | None


class WebhookEventTypeListResponse(BaseModel):
    """Response canonical para listagem."""

    model_config = ConfigDict(from_attributes=True)

    items: list[WebhookEventTypeResponse]
    total: int
    master_count: int
    custom_count: int
