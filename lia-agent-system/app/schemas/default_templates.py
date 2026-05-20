"""
Pydantic schemas for Default Templates API.
"""
from datetime import datetime
from enum import Enum, StrEnum
from uuid import UUID

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class TemplateCategoryEnum(StrEnum):
    """Category of communication template."""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"


class TemplateStatusEnum(StrEnum):
    """Status of the template."""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class TemplateVariableResponse(BaseModel):
    """Available template variable."""
    name: str = Field(..., description="Variable name to use in template")
    description: str = Field(..., description="Description of the variable")
    example_value: str = Field(..., description="Example value for this variable")
    required: bool = Field(False, description="Whether this variable is required")


class DefaultTemplateBase(BaseModel):
    """Base default template schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    category: TemplateCategoryEnum = Field(default=TemplateCategoryEnum.EMAIL, description="Template category: email, sms, whatsapp, push")
    subject: str | None = Field(None, max_length=500, description="Subject line (required for email)")
    body: str = Field(..., min_length=1, description="Template body content")
    variables: list[str] = Field(default_factory=list, description="List of variable names used in template")
    status: TemplateStatusEnum = Field(default=TemplateStatusEnum.DRAFT, description="Template status: active, draft, archived")


class DefaultTemplateCreate(DefaultTemplateBase):
    """Schema for creating a new default template."""
    created_by: str | None = Field(None, description="User who created the template")


class DefaultTemplateUpdate(WeDoBaseModel):
    """Schema for updating a default template (all fields optional)."""
    name: str | None = Field(None, min_length=1, max_length=255)
    category: TemplateCategoryEnum | None = None
    subject: str | None = Field(None, max_length=500)
    body: str | None = Field(None, min_length=1)
    variables: list[str] | None = None
    status: TemplateStatusEnum | None = None


class DefaultTemplateResponse(BaseModel):
    """Complete default template response."""
    id: UUID
    name: str
    category: str
    subject: str | None = None
    body: str
    variables: list[str] = Field(default_factory=list)
    status: str
    client_usage_count: int = 0
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DefaultTemplateListResponse(BaseModel):
    """Response for listing default templates."""
    total: int
    items: list[DefaultTemplateResponse]


class TemplateVariablesListResponse(BaseModel):
    """Response for listing available template variables."""
    variables: list[TemplateVariableResponse]


class DefaultTemplateDuplicateRequest(WeDoBaseModel):
    """Request for duplicating a template."""
    new_name: str | None = Field(None, description="Name for the duplicated template. If not provided, appends ' (Copy)'")


class SeedTemplatesResponse(BaseModel):
    """Response after seeding default templates."""
    created: int
    templates: list[DefaultTemplateResponse]
    message: str
