"""
WhatsApp Provider Interface

Abstract base class defining the contract for WhatsApp messaging providers.
Both Meta Cloud API and Twilio implementations must follow this interface.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProviderType(StrEnum):
    """Supported WhatsApp provider types."""
    META = "meta"
    TWILIO = "twilio"


class SendResult(BaseModel):
    """Unified result of a WhatsApp send operation."""
    success: bool
    message_id: str | None = None
    error: str | None = None
    error_code: str | None = None
    sent_at: datetime | None = None
    provider: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncomingMessage(BaseModel):
    """Unified representation of an incoming WhatsApp message."""
    model_config = ConfigDict(extra='forbid')

    type: str
    message_id: str | None = None
    from_number: str | None = None
    timestamp: str | None = None
    message_type: str | None = None
    text: str | None = None
    document: dict[str, Any] | None = None
    image: dict[str, Any] | None = None
    button_reply: dict[str, str] | None = None
    list_reply: dict[str, str] | None = None
    contact_name: str | None = None
    status: str | None = None
    recipient_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WhatsAppProvider(ABC):
    """
    Abstract base class for WhatsApp messaging providers.
    
    All WhatsApp providers (Meta, Twilio, etc.) must implement this interface
    to ensure consistent behavior across the application.
    """
    
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type identifier."""
        pass
    
    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is properly configured with credentials."""
        pass
    
    @abstractmethod
    async def send_text_message(self, to: str, text: str) -> SendResult:
        """
        Send a text message to a WhatsApp number.
        
        Args:
            to: Phone number in any format (will be cleaned by implementation)
            text: Message text
            
        Returns:
            SendResult with message ID if successful
        """
        pass
    
    @abstractmethod
    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: list[dict[str, str]],
        header_text: str | None = None,
        footer_text: str | None = None
    ) -> SendResult:
        """
        Send an interactive message with buttons.
        
        Args:
            to: Phone number
            body_text: Main message text
            buttons: List of buttons [{"id": "btn_1", "title": "Option 1"}, ...]
            header_text: Optional header
            footer_text: Optional footer
            
        Returns:
            SendResult with message ID if successful
        """
        pass
    
    @abstractmethod
    async def send_document(
        self,
        to: str,
        document_url: str,
        caption: str | None = None,
        filename: str | None = None
    ) -> SendResult:
        """
        Send a document to a WhatsApp number.
        
        Args:
            to: Phone number
            document_url: URL of the document to send
            caption: Optional caption for the document
            filename: Optional filename to display
            
        Returns:
            SendResult with message ID if successful
        """
        pass
    
    @abstractmethod
    def parse_webhook_message(self, payload: dict[str, Any]) -> IncomingMessage | None:
        """
        Parse incoming webhook payload from the provider.
        
        Args:
            payload: The raw webhook JSON payload
            
        Returns:
            Parsed IncomingMessage or None if not a valid message
        """
        pass
    
    @abstractmethod
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the webhook signature from the provider.
        
        Args:
            payload: Raw request body bytes
            signature: Signature header value
            
        Returns:
            True if signature is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def download_media(self, media_id_or_url: str) -> dict[str, Any]:
        """
        Download media (CV, images) from WhatsApp.
        
        Args:
            media_id_or_url: The media ID (Meta) or URL (Twilio) from the webhook
            
        Returns:
            Dict with:
                - success: bool
                - content: bytes (the file content)
                - mime_type: str
                - file_size: int (optional)
                - error: str (if success=False)
        """
        pass
    
    def format_phone_number(self, phone: str, country_code: str = "55") -> str:
        """
        Format phone number for WhatsApp API (digits only).
        
        Args:
            phone: Phone number in any format
            country_code: Default country code (Brazil = 55)
            
        Returns:
            Cleaned phone number with country code
        """
        phone = phone.strip()
        cleaned = "".join(c for c in phone if c.isdigit())
        
        if not cleaned.startswith(country_code):
            cleaned = country_code + cleaned
        
        return cleaned
