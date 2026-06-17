"""
Pydantic schemas canonical para EligibilityQuestionTemplate.

Audit 2026-05-20 Sprint 1 (catalogos dinamicos).
Aplica REGRA 1 (extra='forbid' via WeDoBaseModel), REGRA 2 (company_id
NUNCA no payload — vem do JWT), REGRA 3 (Path UUID via type alias).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.shared.types import WeDoBaseModel


QuestionType = Literal["text", "yes_no", "scale", "multiple"]
QuestionCategory = Literal[
    "general",
    "eligibility",
    "availability",
    "education",
    "experience",
    "languages",
    "compensation",
    "work_model",
    "compliance",
    "system_default",
]


class TriggerCondition(BaseModel):
    """Condition canonical for conditional questions."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(..., description="Campo da vaga que dispara")
    operator: Literal["equals", "contains", "greater_than"] = Field(...)
    value: str | int | bool = Field(...)


class EligibilityQuestionData(BaseModel):
    """Schema canonical do payload de pergunta (armazenado em data JSONB)."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=3, max_length=1000)
    type: QuestionType
    category: QuestionCategory
    contextHint: str | None = Field(None, max_length=500)
    options: list[str] | None = None
    triggerCondition: TriggerCondition | None = None
    linkedField: str | None = None
    isSystemDefault: bool = False
    eliminatory: bool = False
    eliminatoryAnswer: str | bool | None = None
    legacy_id: str | None = None  # Reference to ts bank id (sys-workmodel, etc)


class EligibilityQuestionTemplateCreate(WeDoBaseModel):
    """Request body for creating a custom template (canonical novo do zero).

    REGRA 2 canonical: company_id NUNCA no payload — vem do JWT via
    Depends(require_company_id).
    """

    data: EligibilityQuestionData = Field(..., description="Conteúdo canonical")


class EligibilityQuestionTemplateUpdate(WeDoBaseModel):
    """Request body for updating an existing custom template.

    Master templates não podem ser atualizados; apenas customizados (cópia).
    """

    data: EligibilityQuestionData


class CustomizeMasterRequest(WeDoBaseModel):
    """Request body para customizar um master template (cópia canonical A1).

    Cria uma cópia total do master para a company, com parent_template_id
    apontando para o master de origem. Snapshot canonical (B1) — não
    sincroniza com master após criação.
    """

    overrides: EligibilityQuestionData | None = Field(
        None,
        description=(
            "Opcional: fields para override no momento da customizacao. "
            "Se None, cria copia identica ao master."
        ),
    )


class EligibilityQuestionTemplateResponse(BaseModel):
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


class EligibilityQuestionTemplateListResponse(BaseModel):
    """Response canonical para listagem."""

    model_config = ConfigDict(from_attributes=True)

    items: list[EligibilityQuestionTemplateResponse]
    total: int
    master_count: int
    custom_count: int
