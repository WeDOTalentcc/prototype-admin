"""
Email-related Pydantic models and schemas.

Extracted from email_service.py for better modularity.
Used by MailgunEmailService and API endpoints.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field


class EmailDeliveryStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class EmailRecipient(BaseModel):
    email: str = Field(..., description="Recipient email address")
    name: Optional[str] = Field(None, description="Recipient name")


class EmailAttachment(BaseModel):
    filename: str = Field(..., description="Attachment filename")
    content: str = Field(..., description="Base64-encoded file content")
    content_type: str = Field("application/octet-stream", description="MIME type")


class SendEmailRequest(BaseModel):
    to_email: str = Field(..., description="Primary recipient email")
    to_name: Optional[str] = Field(None, description="Recipient name")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Plain text body")
    body_html: Optional[str] = Field(None, description="HTML body")
    cc: Optional[List[str]] = Field(default=None, description="CC recipients")
    bcc: Optional[List[str]] = Field(default=None, description="BCC recipients")
    reply_to: Optional[str] = Field(None, description="Reply-to address")
    categories: Optional[List[str]] = Field(default=None, description="Categories for tracking")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Custom metadata")
    company_id: Optional[str] = Field(None, description="Company ID for multi-tenancy")


class SendTemplateEmailRequest(BaseModel):
    to_email: str = Field(..., description="Primary recipient email")
    to_name: Optional[str] = Field(None, description="Recipient name")
    template_name: str = Field(..., description="Template name from EmailTemplates")
    template_data: Dict[str, Any] = Field(..., description="Template variables")
    cc: Optional[List[str]] = Field(default=None, description="CC recipients")
    reply_to: Optional[str] = Field(None, description="Reply-to address")
    categories: Optional[List[str]] = Field(default=None, description="Categories")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Custom metadata")
    company_id: Optional[str] = Field(None, description="Company ID")


class BulkEmailRecipient(BaseModel):
    email: str
    name: Optional[str] = None
    personalization: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SendBulkEmailRequest(BaseModel):
    recipients: List[BulkEmailRecipient] = Field(..., description="List of recipients")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Plain text body")
    body_html: Optional[str] = Field(None, description="HTML body")
    categories: Optional[List[str]] = Field(default=None, description="Categories")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Custom metadata")
    company_id: Optional[str] = Field(None, description="Company ID")


class EmailSendResult(BaseModel):
    success: bool
    message_id: Optional[str] = None
    status: str = "pending"
    provider: str = "mailgun"
    error: Optional[str] = None
    error_code: Optional[str] = None
    sent_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BulkEmailResult(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[EmailSendResult]
