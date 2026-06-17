"""
Pydantic schemas for Search Archetypes API.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class ArchetypeBase(BaseModel):
    """Base archetype schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    emoji: str = Field(default="🎯", max_length=10)
    query: str = Field(..., min_length=1)
    filters: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    industry: str | None = Field(None, max_length=100)
    seniority: str | None = Field(None, max_length=50)


class ArchetypeCreate(ArchetypeBase):
    """Schema for creating a new archetype."""
    id: str | None = Field(None, max_length=50, description="Custom ID, auto-generated if not provided")
    is_default: bool = Field(default=False)


class ArchetypeUpdate(WeDoBaseModel):
    """Schema for updating an archetype."""
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    emoji: str | None = Field(None, max_length=10)
    query: str | None = None
    filters: dict[str, Any] | None = None
    tags: list[str] | None = None
    industry: str | None = Field(None, max_length=100)
    seniority: str | None = Field(None, max_length=50)
    is_active: bool | None = None


class ArchetypeResponse(BaseModel):
    """Complete archetype response with all fields."""
    id: str
    name: str
    description: str | None = None
    emoji: str
    query: str
    filters: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    industry: str | None = None
    seniority: str | None = None
    is_default: bool = False
    is_active: bool = True
    usage_count: int = 0
    company_id: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ArchetypeFromSearchCreate(WeDoBaseModel):
    """Schema for creating an archetype from a search specification."""
    search_spec: dict[str, Any] = Field(..., description="The search specification to convert to archetype")
    name: str = Field(..., min_length=1, max_length=100, description="Name for the archetype")
    description: str | None = Field(None, max_length=500, description="Description of the archetype")
    emoji: str | None = Field(default="🎯", max_length=10, description="Emoji icon for the archetype")


class ArchetypeFromSearchResponse(BaseModel):
    """Response when creating an archetype from search."""
    archetype: ArchetypeResponse
    extracted_tags: list[str] = Field(default_factory=list, description="Tags automatically extracted from search_spec")
    message: str = Field(default="Archetype created successfully")


class ArchetypeListResponse(BaseModel):
    """Paginated list of archetypes."""
    total: int
    skip: int
    limit: int
    items: list[ArchetypeResponse]
