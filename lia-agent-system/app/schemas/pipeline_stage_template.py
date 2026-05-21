"""
Pydantic schemas canonical para PipelineStageTemplate.

Audit 2026-05-20 Sprint 2 (catalogos dinamicos).
Aplica REGRA 1 (extra='forbid' via WeDoBaseModel), REGRA 2 (company_id
NUNCA no payload — vem do JWT), REGRA 3 (Path UUID via type alias).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.shared.types import WeDoBaseModel


# Canonical action_behavior das DEFAULT_STAGES (RecruitmentJourneyConfig.tsx)
ActionBehavior = Literal[
    "intake",
    "screening",
    "passive",
    "scheduling",
    "evaluation",
    "verification",
    "offer",
    "conclusion_hired",
    "conclusion_declined",
    "conclusion_rejected",
]

DefaultChannel = Literal["email", "email_whatsapp", "whatsapp", "none"]

StageCategory = Literal["system", "custom", "catalog"]

StageType = Literal["system", "custom", "default"]


class PipelineStageSubstatus(BaseModel):
    """Sub-status opcional dentro de uma stage canonical."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=1, max_length=128)
    order: int = Field(0, ge=0)


class PipelineStageData(BaseModel):
    """Schema canonical do payload de stage (armazenado em data JSONB)."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., min_length=1, max_length=128, description="Display name canonical (fallback EN)")
    key: str = Field(..., min_length=1, max_length=64, description="Slug canonical snake_case")
    color: str | None = Field(None, max_length=64, description="CSS var ou hex token")
    icon: str | None = Field(None, max_length=64, description="Lucide icon name")
    order: int = Field(0, ge=0, description="Ordem canonical no pipeline (1..N)")
    is_default_in_pipeline: bool = Field(
        False,
        description="True = aparece por padrao no novo pipeline da company",
    )
    action_behavior: ActionBehavior | None = None
    default_channel: DefaultChannel | None = None
    stage_category: StageCategory | None = None
    type: StageType | None = None
    sla_hours: int = Field(0, ge=0, description="SLA em horas (0=indefinido)")
    substatuses: list[PipelineStageSubstatus] | None = None
    metadata: dict[str, Any] | None = None


class PipelineStageTemplateCreate(WeDoBaseModel):
    """Request body for creating a custom template (canonical novo do zero).

    REGRA 2 canonical: company_id NUNCA no payload — vem do JWT via
    Depends(require_company_id).
    """

    data: PipelineStageData = Field(..., description="Conteudo canonical")


class PipelineStageTemplateUpdate(WeDoBaseModel):
    """Request body for updating an existing custom template.

    Master templates nao podem ser atualizados; apenas customizados (copia).
    """

    data: PipelineStageData


class CustomizeMasterRequest(WeDoBaseModel):
    """Request body para customizar um master template (copia canonical A1).

    Cria uma copia total do master para a company, com parent_template_id
    apontando para o master de origem. Snapshot canonical (B1) — nao
    sincroniza com master apos criacao.
    """

    overrides: PipelineStageData | None = Field(
        None,
        description=(
            "Opcional: fields para override no momento da customizacao. "
            "Se None, cria copia identica ao master."
        ),
    )


class PipelineStageTemplateResponse(BaseModel):
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


class PipelineStageTemplateListResponse(BaseModel):
    """Response canonical para listagem."""

    model_config = ConfigDict(from_attributes=True)

    items: list[PipelineStageTemplateResponse]
    total: int
    master_count: int
    custom_count: int
