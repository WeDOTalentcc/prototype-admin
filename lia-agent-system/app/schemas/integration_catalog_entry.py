"""
Pydantic schemas canonical para IntegrationCatalogEntry.

Audit 2026-05-20 Sprint 4 (catalogos dinamicos).
Aplica REGRA 1 (extra='forbid' via WeDoBaseModel), REGRA 2 (company_id
NUNCA no payload — vem do JWT), REGRA 3 (Path UUID via type alias).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.shared.types import WeDoBaseModel


IntegrationCategory = Literal[
    "ai_models",
    "ats",
    "calendar",
    "communication",
    "crm_hris",
    "mcps_apis",
]

IntegrationStatus = Literal[
    "production",       # canonical hoje em uso (= connected / not_configured)
    "coming_soon",      # roadmap canonical
    "deprecated",       # legado, nao listar para novos tenants
]

ConnectAction = Literal["oauth", "config", "webhook", "none"]


class IntegrationCapability(BaseModel):
    """Capability canonical de uma integracao (display-only)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=500)


class IntegrationMetadata(BaseModel):
    """Catch-all metadata canonical — hints visuais + config fields.

    Mantem retro-compat com shape do antigo integration-data.ts hardcoded.
    """

    model_config = ConfigDict(extra="forbid")

    icon_bg: str | None = Field(None, max_length=200)
    icon_color: str | None = Field(None, max_length=200)
    icon_letter: str | None = Field(None, max_length=10)
    is_active_provider: bool | None = None
    connect_action: ConnectAction | None = None
    capabilities: list[IntegrationCapability] | None = None
    config_fields: list[str] | None = None


class IntegrationCatalogData(BaseModel):
    """Schema canonical do payload de catalogo (armazenado em data JSONB)."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Slug canonical (ex: gupy, pandape, merge)",
    )
    label: str = Field(..., min_length=1, max_length=200)
    category: IntegrationCategory
    logo_url: str | None = Field(None, max_length=500)
    description: str = Field(..., min_length=1, max_length=500)
    full_description: str | None = Field(None, max_length=4000)
    status: IntegrationStatus = "production"
    industries_recommended: list[str] = Field(default_factory=list)
    metadata: IntegrationMetadata | None = None


class IntegrationCatalogEntryCreate(WeDoBaseModel):
    """Request body para criar custom entry (canonical novo do zero).

    REGRA 2 canonical: company_id NUNCA no payload — vem do JWT via
    Depends(require_company_id).
    """

    data: IntegrationCatalogData = Field(..., description="Conteudo canonical")


class IntegrationCatalogEntryUpdate(WeDoBaseModel):
    """Request body para update de custom entry.

    Master entries nao podem ser atualizadas; apenas customs (cópia).
    """

    data: IntegrationCatalogData


class CustomizeIntegrationMasterRequest(WeDoBaseModel):
    """Request body para customizar um master entry (cópia canonical A1).

    Snapshot canonical (B1) — nao sincroniza com master apos criacao.
    """

    overrides: IntegrationCatalogData | None = Field(
        None,
        description=(
            "Opcional: fields para override no momento da customizacao. "
            "Se None, cria copia identica ao master."
        ),
    )


class IntegrationCatalogEntryResponse(BaseModel):
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


class IntegrationCatalogEntryListResponse(BaseModel):
    """Response canonical para listagem."""

    model_config = ConfigDict(from_attributes=True)

    items: list[IntegrationCatalogEntryResponse]
    total: int
    master_count: int
    custom_count: int
