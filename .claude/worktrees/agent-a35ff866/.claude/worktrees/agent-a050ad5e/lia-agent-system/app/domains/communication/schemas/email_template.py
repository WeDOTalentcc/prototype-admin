"""
Pydantic schemas for Email Templates API.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


class EmailTemplateBase(BaseModel):
    """Base email/WhatsApp template schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    subject: Optional[str] = Field(None, max_length=500, description="Email subject line (required for email, optional for whatsapp)")
    body_html: str = Field(..., min_length=1, description="HTML body content")
    body_text: Optional[str] = Field(None, description="Plain text body (optional)")
    category: Optional[str] = Field(None, max_length=50, description="Template category: interview, rejection, offer, followup")
    channel: str = Field(default="email", description="Communication channel: email or whatsapp")
    situation: Optional[str] = Field(None, max_length=50, description="Situation/context: triagem, entrevista, follow_up, rejeicao, proposta, feedback, agendamento")
    trigger_type: Optional[str] = Field(default="manual", max_length=20, description="Trigger type: automatic, manual, or both")
    used_in: List[str] = Field(default_factory=list, description="Component names where template is used: close_vacancy_modal, communication_modal, automation")
    priority: Optional[str] = Field(default="medium", max_length=10, description="Priority level: high, medium, or low")
    variables: List[str] = Field(default_factory=list, description="List of variable names used in template")


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating a new email template."""
    created_by: Optional[str] = Field(None, description="User who created the template")


class EmailTemplateUpdate(BaseModel):
    """Schema for updating an email template (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, max_length=500)
    body_html: Optional[str] = Field(None, min_length=1)
    body_text: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    channel: Optional[str] = Field(None, max_length=20)
    situation: Optional[str] = Field(None, max_length=50)
    trigger_type: Optional[str] = Field(None, max_length=20)
    used_in: Optional[List[str]] = None
    priority: Optional[str] = Field(None, max_length=10)
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(BaseModel):
    """Complete email template response."""
    id: UUID
    name: str
    subject: Optional[str] = None
    body_html: str
    body_text: Optional[str] = None
    category: Optional[str] = None
    channel: str = "email"
    situation: Optional[str] = None
    trigger_type: Optional[str] = "manual"
    used_in: List[str] = Field(default_factory=list)
    priority: Optional[str] = "medium"
    variables: List[str] = Field(default_factory=list)
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmailTemplateListResponse(BaseModel):
    """Response for listing email templates."""
    total: int
    items: List[EmailTemplateResponse]


class EmailPreviewRequest(BaseModel):
    """Request for previewing an email with variables substituted."""
    template_id: Optional[UUID] = Field(None, description="ID of template to preview (optional if subject/body provided)")
    subject: Optional[str] = Field(None, description="Custom subject (overrides template)")
    body_html: Optional[str] = Field(None, description="Custom HTML body (overrides template)")
    body_text: Optional[str] = Field(None, description="Custom text body (overrides template)")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variables to substitute in template")


class EmailPreviewResponse(BaseModel):
    """Response with rendered email preview."""
    subject: str
    body_html: str
    body_text: Optional[str] = None
    variables_used: Dict[str, Any]
    missing_variables: List[str] = Field(default_factory=list)


class EmailSendRequest(BaseModel):
    """Request for sending an email using a template."""
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    recipient_name: Optional[str] = Field(None, description="Recipient name (used in variables)")
    candidate_id: Optional[str] = Field(None, description="Associated candidate ID")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variables to substitute in template")
    send_immediately: bool = Field(True, description="If False, email is queued but not sent")
    subject_override: Optional[str] = Field(None, description="Custom subject (overrides template)")
    body_override: Optional[str] = Field(None, description="Custom body HTML (overrides template)")


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
    template_id: Optional[UUID] = None
    candidate_id: Optional[str] = None
    recipient_email: str
    subject: str
    status: str
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    variables_used: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmailLogListResponse(BaseModel):
    """Response for listing email logs."""
    total: int
    items: List[EmailLogResponse]


class DefaultTemplatesResponse(BaseModel):
    """Response after seeding default templates."""
    created: int
    templates: List[EmailTemplateResponse]
    message: str


class TemplatePreviewByIdRequest(BaseModel):
    """Request for previewing a template by ID with variables substituted."""
    variables: Dict[str, str] = Field(default_factory=dict, description="Variables to substitute in template, e.g. {'candidate_name': 'João Silva', 'job_title': 'Desenvolvedor'}")


class TemplatePreviewByIdData(BaseModel):
    """Rendered template preview content."""
    subject: str = Field(..., description="Rendered email subject")
    body_html: str = Field(..., description="Rendered HTML body content")
    body_text: Optional[str] = Field(None, description="Rendered plain text body content")


class TemplatePreviewByIdResponse(BaseModel):
    """Response for template preview by ID."""
    success: bool
    data: TemplatePreviewByIdData


class TemplateGenerateRequest(BaseModel):
    """Request for AI-powered email template generation."""
    template_type: str = Field(..., description="Type of template: initial_contact, screening_reminder, offer_letter, rejection, interview_invitation, follow_up")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context variables like job_title, company_name, tone (formal/casual)")
    language: str = Field(default="pt-BR", description="Language for the generated content")


class TemplateGenerateData(BaseModel):
    """Generated template content."""
    subject: str = Field(..., description="Email subject generated by AI")
    body_html: str = Field(..., description="HTML body content generated by AI")
    variables_used: List[str] = Field(default_factory=list, description="List of placeholder variables used in the template")


class TemplateGenerateResponse(BaseModel):
    """Response for AI-generated template."""
    success: bool
    data: TemplateGenerateData


class TemplateAdjustRequest(BaseModel):
    """Request for AI-powered template adjustment using free-form prompt."""
    template_id: Optional[str] = Field(None, description="ID of the template being adjusted (optional)")
    prompt: str = Field(..., min_length=3, description="Free-form prompt describing the desired adjustments")
    current_subject: Optional[str] = Field(None, description="Current subject line to adjust")
    current_body: str = Field(..., min_length=1, description="Current body content to adjust")
    channel: str = Field(default="email", description="Channel type: email or whatsapp")


class TemplateAdjustData(BaseModel):
    """Adjusted template content."""
    subject: Optional[str] = Field(None, description="Adjusted email subject (if provided)")
    body: str = Field(..., description="Adjusted body content")
    changes_made: List[str] = Field(default_factory=list, description="Summary of changes made by AI")


class TemplateAdjustResponse(BaseModel):
    """Response for AI-adjusted template."""
    success: bool
    data: TemplateAdjustData
