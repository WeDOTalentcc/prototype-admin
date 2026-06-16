"""Schemas Pydantic canonical pra AgentTemplateCatalog.

WeDoBaseModel garante extra='forbid' (REGRA 1 Pydantic conventions).
NÃO inclui company_id no request (REGRA 2 — multi-tenancy via JWT).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.shared.types import WeDoBaseModel


CONTEXT_LEVELS = {"minimal", "standard", "full"}


class AgentTemplateCatalogRequest(WeDoBaseModel):
    slug: str = Field(..., min_length=3, max_length=128)
    name: str = Field(..., min_length=2, max_length=256)
    description: str = Field(..., min_length=2)
    category_id: str = Field(..., min_length=2, max_length=64)
    sector_id: str | None = Field(default=None, max_length=64)
    system_prompt: str = Field(..., min_length=10)
    allowed_tools: list[str] = Field(default_factory=list)
    context_level: str = "standard"
    max_steps: int = Field(default=10, ge=1, le=50)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    enable_memory: bool = True
    excluded_tools: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    vertical_prompts: dict[str, str] | None = None
    icon: str | None = Field(default=None, max_length=64)
    accent_color: str | None = Field(default=None, max_length=32)
    badge_variant: str | None = Field(default=None, max_length=32)
    sort_order: int = 0
    is_active: bool = True
    # Sem company_id (REGRA 2 — derivado de JWT no handler)


class AgentTemplateCatalogResponse(BaseModel):
    """Response inclui campos do banco. Não herda WeDoBaseModel pra permitir
    `from_attributes=True` (serialização direta de ORM).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    description: str
    category_id: str
    sector_id: str | None
    system_prompt: str
    allowed_tools: list[str]
    context_level: str
    max_steps: int
    temperature: float
    enable_memory: bool
    excluded_tools: list[str]
    tags: list[str]
    vertical_prompts: dict[str, str] | None
    icon: str | None
    accent_color: str | None
    badge_variant: str | None
    sort_order: int
    is_active: bool
    company_id: str | None
    created_at: datetime
    updated_at: datetime


class AgentCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label_pt: str
    label_en: str
    icon: str | None
    sort_order: int
    is_active: bool


class AgentSectorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label_pt: str
    label_en: str
    sort_order: int
    is_active: bool
