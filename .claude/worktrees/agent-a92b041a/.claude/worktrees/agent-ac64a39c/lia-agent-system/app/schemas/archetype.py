"""
Pydantic schemas for Search Archetypes API.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ArchetypeBase(BaseModel):
    """Base archetype schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    emoji: str = Field(default="🎯", max_length=10)
    query: str = Field(..., min_length=1)
    filters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    industry: Optional[str] = Field(None, max_length=100)
    seniority: Optional[str] = Field(None, max_length=50)


class ArchetypeCreate(ArchetypeBase):
    """Schema for creating a new archetype."""
    id: Optional[str] = Field(None, max_length=50, description="Custom ID, auto-generated if not provided")
    is_default: bool = Field(default=False)


class ArchetypeUpdate(BaseModel):
    """Schema for updating an archetype."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    emoji: Optional[str] = Field(None, max_length=10)
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    industry: Optional[str] = Field(None, max_length=100)
    seniority: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class ArchetypeResponse(BaseModel):
    """Complete archetype response with all fields."""
    id: str
    name: str
    description: Optional[str] = None
    emoji: str
    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    seniority: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    usage_count: int = 0
    company_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArchetypeFromSearchCreate(BaseModel):
    """Schema for creating an archetype from a search specification."""
    search_spec: Dict[str, Any] = Field(..., description="The search specification to convert to archetype")
    name: str = Field(..., min_length=1, max_length=100, description="Name for the archetype")
    description: Optional[str] = Field(None, max_length=500, description="Description of the archetype")
    emoji: Optional[str] = Field(default="🎯", max_length=10, description="Emoji icon for the archetype")


class ArchetypeFromSearchResponse(BaseModel):
    """Response when creating an archetype from search."""
    archetype: ArchetypeResponse
    extracted_tags: List[str] = Field(default_factory=list, description="Tags automatically extracted from search_spec")
    message: str = Field(default="Archetype created successfully")


class ArchetypeListResponse(BaseModel):
    """Paginated list of archetypes."""
    total: int
    skip: int
    limit: int
    items: List[ArchetypeResponse]
