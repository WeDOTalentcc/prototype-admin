"""
Pydantic schemas canonical para AlertRuleTemplate.

Audit 2026-05-20 Sprint 3 (catalogos dinamicos).
Aplica REGRA 1 (extra='forbid' via WeDoBaseModel), REGRA 2 (company_id
NUNCA no payload - vem do JWT), REGRA 3 (Path UUID via type alias).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.shared.types import WeDoBaseModel


AlertAudience = Literal["recruiter", "admin", "candidate"]
AlertChannel = Literal["email", "in_app", "teams", "whatsapp"]


class AlertRuleData(BaseModel):
    """Schema canonical do payload de alert rule (armazenado em data JSONB).

    Schema canonical (decidido Paulo 2026-05-20):
    - event_type: chave estavel referenciada pelo pipeline events
    - label: nome humano
    - audience: recruiter|admin|candidate
    - channels: lista canonical (email|in_app|teams|whatsapp)
    - delay_minutes: int >= 0
    - schedule_lgpd_compliant: bool (respeita horarios comerciais)
    - rationale: texto explicando o porque do delay/canal canonical
    """

    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(..., min_length=2, max_length=128, description="Chave canonical do evento")
    label: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(None, max_length=1000)
    audience: AlertAudience
    channels: list[AlertChannel] = Field(..., min_length=1)
    delay_minutes: int = Field(..., ge=0, le=43200, description="0-30 dias em minutos")
    schedule_lgpd_compliant: bool = Field(
        True, description="Se True, respeita horario comercial (LGPD Art.7)"
    )
    rationale: str | None = Field(None, max_length=1000)
    enabled_default: bool = Field(True, description="Default on/off do alert")
    legacy_id: str | None = None  # Reference to DEFAULT_ALERTS hardcoded id


class AlertRuleTemplateCreate(WeDoBaseModel):
    """Request body for creating a custom template (canonical novo do zero).

    REGRA 2 canonical: company_id NUNCA no payload - vem do JWT via
    Depends(require_company_id).
    """

    data: AlertRuleData = Field(..., description="Conteudo canonical")


class AlertRuleTemplateUpdate(WeDoBaseModel):
    """Request body for updating an existing custom template.

    Master templates nao podem ser atualizados; apenas customizados (copia).
    """

    data: AlertRuleData


class CustomizeMasterRequest(WeDoBaseModel):
    """Request body para customizar um master template (copia canonical A1).

    Cria uma copia total do master para a company, com parent_template_id
    apontando para o master de origem. Snapshot canonical (B1) - nao
    sincroniza com master apos criacao.
    """

    overrides: AlertRuleData | None = Field(
        None,
        description=(
            "Opcional: fields para override no momento da customizacao. "
            "Se None, cria copia identica ao master."
        ),
    )


class AlertRuleTemplateResponse(BaseModel):
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


class AlertRuleTemplateListResponse(BaseModel):
    """Response canonical para listagem."""

    model_config = ConfigDict(from_attributes=True)

    items: list[AlertRuleTemplateResponse]
    total: int
    master_count: int
    custom_count: int
