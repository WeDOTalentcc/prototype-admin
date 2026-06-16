"""
Email-related Pydantic models and schemas.

Extracted from email_service.py for better modularity.
Used by MailgunEmailService and API endpoints.
"""
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class EmailDeliveryStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class EmailRecipient(BaseModel):
    email: str = Field(..., description="Recipient email address")
    name: str | None = Field(None, description="Recipient name")


class EmailAttachment(BaseModel):
    filename: str = Field(..., description="Attachment filename")
    content: str = Field(..., description="Base64-encoded file content")
    content_type: str = Field("application/octet-stream", description="MIME type")


class SendEmailRequest(WeDoBaseModel):
    to_email: str = Field(..., description="Primary recipient email")
    to_name: str | None = Field(None, description="Recipient name")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Plain text body")
    body_html: str | None = Field(None, description="HTML body")
    cc: list[str] | None = Field(default=None, description="CC recipients")
    bcc: list[str] | None = Field(default=None, description="BCC recipients")
    reply_to: str | None = Field(None, description="Reply-to address")
    categories: list[str] | None = Field(default=None, description="Categories for tracking")
    metadata: dict[str, Any] | None = Field(default=None, description="Custom metadata")


class SendTemplateEmailRequest(WeDoBaseModel):
    to_email: str = Field(..., description="Primary recipient email")
    to_name: str | None = Field(None, description="Recipient name")
    template_name: str = Field(..., description="Template name from EmailTemplates")
    template_data: dict[str, Any] = Field(..., description="Template variables")
    cc: list[str] | None = Field(default=None, description="CC recipients")
    reply_to: str | None = Field(None, description="Reply-to address")
    categories: list[str] | None = Field(default=None, description="Categories")
    metadata: dict[str, Any] | None = Field(default=None, description="Custom metadata")


class BulkEmailRecipient(BaseModel):
    email: str
    name: str | None = None
    personalization: dict[str, Any] | None = Field(default_factory=dict)


class SendBulkEmailRequest(WeDoBaseModel):
    recipients: list[BulkEmailRecipient] = Field(..., description="List of recipients")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Plain text body")
    body_html: str | None = Field(None, description="HTML body")
    categories: list[str] | None = Field(default=None, description="Categories")
    metadata: dict[str, Any] | None = Field(default=None, description="Custom metadata")


class EmailSendResult(BaseModel):
    success: bool
    message_id: str | None = None
    status: str = "pending"
    provider: str = "mailgun"
    error: str | None = None
    error_code: str | None = None
    sent_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BulkEmailResult(BaseModel):
    total: int
    successful: int
    failed: int
    results: list[EmailSendResult]
