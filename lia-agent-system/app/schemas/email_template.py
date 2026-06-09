"""
Pydantic schemas for Email Templates API.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.shared.types import WeDoBaseModel


class EmailTemplateBase(BaseModel):
    """Base email/WhatsApp template schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    subject: str | None = Field(None, max_length=500, description="Email subject line (required for email, optional for whatsapp)")
    body_html: str = Field(..., min_length=1, description="HTML body content")
    body_text: str | None = Field(None, description="Plain text body (optional)")
    category: str | None = Field(None, max_length=50, description="Template category: interview, rejection, offer, followup")
    channel: str = Field(default="email", description="Communication channel: email or whatsapp")
    situation: str | None = Field(None, max_length=50, description="Situation/context: triagem, entrevista, follow_up, rejeicao, proposta, feedback, agendamento")
    trigger_type: str | None = Field(default="manual", max_length=20, description="Trigger type: automatic, manual, or both")
    used_in: list[str] = Field(default_factory=list, description="Component names where template is used: close_vacancy_modal, communication_modal, automation")
    priority: str | None = Field(default="medium", max_length=10, description="Priority level: high, medium, or low")
    variables: list[str] = Field(default_factory=list, description="List of variable names used in template")
    cc_emails: list[str] | None = Field(default=None, description="Additional CC recipients")


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating a new email template."""
    created_by: str | None = Field(None, description="User who created the template")


class EmailTemplateUpdate(WeDoBaseModel):
    """Schema for updating an email template (all fields optional)."""
    name: str | None = Field(None, min_length=1, max_length=255)
    subject: str | None = Field(None, max_length=500)
    body_html: str | None = Field(None, min_length=1)
    body_text: str | None = None
    category: str | None = Field(None, max_length=50)
    channel: str | None = Field(None, max_length=20)
    situation: str | None = Field(None, max_length=50)
    trigger_type: str | None = Field(None, max_length=20)
    used_in: list[str] | None = None
    priority: str | None = Field(None, max_length=10)
    variables: list[str] | None = None
    cc_emails: list[str] | None = None
    is_active: bool | None = None


class EmailTemplateResponse(BaseModel):
    """Complete email template response."""
    id: UUID
    name: str
    subject: str | None = None
    body_html: str
    body_text: str | None = None
    category: str | None = None
    channel: str = "email"
    situation: str | None = None
    trigger_type: str | None = "manual"
    used_in: list[str] = Field(default_factory=list)
    priority: str | None = "medium"
    variables: list[str] = Field(default_factory=list)
    cc_emails: list[str] | None = None
    is_active: bool
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmailTemplateListResponse(BaseModel):
    """Response for listing email templates."""
    total: int
    items: list[EmailTemplateResponse]


class EmailPreviewRequest(WeDoBaseModel):
    """Request for previewing an email with variables substituted."""
    template_id: UUID | None = Field(None, description="ID of template to preview (optional if subject/body provided)")
    subject: str | None = Field(None, description="Custom subject (overrides template)")
    body_html: str | None = Field(None, description="Custom HTML body (overrides template)")
    body_text: str | None = Field(None, description="Custom text body (overrides template)")
    variables: dict[str, Any] = Field(default_factory=dict, description="Variables to substitute in template")


class EmailPreviewResponse(BaseModel):
    """Response with rendered email preview."""
    subject: str
    body_html: str
    body_text: str | None = None
    variables_used: dict[str, Any]
    missing_variables: list[str] = Field(default_factory=list)


class EmailSendRequest(WeDoBaseModel):
    """Request for sending an email using a template."""
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    recipient_name: str | None = Field(None, description="Recipient name (used in variables)")
    candidate_id: str | None = Field(None, description="Associated candidate ID")
    variables: dict[str, Any] = Field(default_factory=dict, description="Variables to substitute in template")
    send_immediately: bool = Field(True, description="If False, email is queued but not sent")
    subject_override: str | None = Field(None, description="Custom subject (overrides template)")
    body_override: str | None = Field(None, description="Custom body HTML (overrides template)")


class EmailSendResponse(BaseModel):
    """Response after sending an email."""
    success: bool
    email_log_id: UUID
    status: str
    message: str
    recipient_email: str
    subject: str


class EmailLogResponse(BaseModel):
    """Email log entry response."""
    id: UUID
    template_id: UUID | None = None
    candidate_id: str | None = None
    recipient_email: str
    subject: str
    status: str
    sent_at: datetime | None = None
    error_message: str | None = None
    variables_used: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmailLogListResponse(BaseModel):
    """Response for listing email logs."""
    total: int
    items: list[EmailLogResponse]


class DefaultTemplatesResponse(BaseModel):
    """Response after seeding default templates."""
    created: int
    templates: list[EmailTemplateResponse]
    message: str


class TemplatePreviewByIdRequest(WeDoBaseModel):
    """Request for previewing a template by ID with variables substituted."""
    variables: dict[str, str] = Field(default_factory=dict, description="Variables to substitute in template, e.g. {'candidate_name': 'João Silva', 'job_title': 'Desenvolvedor'}")


class TemplatePreviewByIdData(BaseModel):
    """Rendered template preview content."""
    model_config = ConfigDict(extra='forbid')

    subject: str = Field(..., description="Rendered email subject")
    body_html: str = Field(..., description="Rendered HTML body content")
    body_text: str | None = Field(None, description="Rendered plain text body content")


class TemplatePreviewByIdResponse(BaseModel):
    """Response for template preview by ID."""
    success: bool
    data: TemplatePreviewByIdData


class TemplateGenerateRequest(WeDoBaseModel):
    """Request for AI-powered email template generation."""
    template_type: str = Field(..., description="Type of template: initial_contact, screening_reminder, offer_letter, rejection, interview_invitation, follow_up")
    context: dict[str, Any] = Field(default_factory=dict, description="Context variables like job_title, company_name, tone (formal/casual)")
    language: str = Field(default="pt-BR", description="Language for the generated content")


class TemplateGenerateData(BaseModel):
    """Generated template content."""
    model_config = ConfigDict(extra='forbid')

    subject: str = Field(..., description="Email subject generated by AI")
    body_html: str = Field(..., description="HTML body content generated by AI")
    variables_used: list[str] = Field(default_factory=list, description="List of placeholder variables used in the template")


class TemplateGenerateResponse(BaseModel):
    """Response for AI-generated template."""
    success: bool
    data: TemplateGenerateData


class TemplateAdjustRequest(WeDoBaseModel):
    """Request for AI-powered template adjustment using free-form prompt."""
    template_id: str | None = Field(None, description="ID of the template being adjusted (optional)")
    prompt: str = Field(..., min_length=3, description="Free-form prompt describing the desired adjustments")
    current_subject: str | None = Field(None, description="Current subject line to adjust")
    current_body: str = Field(..., min_length=1, description="Current body content to adjust")
    channel: str = Field(default="email", description="Channel type: email or whatsapp")


class TemplateAdjustData(BaseModel):
    """Adjusted template content."""
    model_config = ConfigDict(extra='forbid')

    subject: str | None = Field(None, description="Adjusted email subject (if provided)")
    body: str = Field(..., description="Adjusted body content")
    changes_made: list[str] = Field(default_factory=list, description="Summary of changes made by AI")


class TemplateAdjustResponse(BaseModel):
    """Response for AI-adjusted template."""
    success: bool
    data: TemplateAdjustData
