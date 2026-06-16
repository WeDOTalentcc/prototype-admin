"""
WhatsApp Business API Service (Meta Cloud API)

Direct integration with Meta's WhatsApp Business Cloud API.
This is an alternative to Twilio for WhatsApp messaging.

Environment Variables Required:
- WHATSAPP_PHONE_NUMBER_ID: The phone number ID from Meta Business
- WHATSAPP_ACCESS_TOKEN: Access token from Meta Developer Portal
- WHATSAPP_VERIFY_TOKEN: Token for webhook verification
- WHATSAPP_APP_SECRET: App secret for webhook signature verification
"""

import hashlib
import hmac
import logging
import os
from datetime import datetime
from typing import Any

import httpx

from app.domains.communication.services.whatsapp_provider import (
    IncomingMessage,
    ProviderType,
    SendResult,
    WhatsAppProvider,
)

logger = logging.getLogger(__name__)


class MetaWhatsAppService(WhatsAppProvider):
    """
    WhatsApp Business Cloud API Service (Meta direct integration).
    
    Features:
    - Direct Meta API integration (no Twilio dependency)
    - Text messages
    - Interactive messages with buttons
    - Document/media handling
    - Webhook verification and parsing
    
    Setup Requirements:
    1. Meta Business Account
    2. WhatsApp Business API access
    3. Phone number registered with WhatsApp Business
    4. Access token from Meta Developer Portal
    """
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self):
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
        if not self.verify_token:
            logger.warning("WHATSAPP_VERIFY_TOKEN not configured. Webhook verification will fail.")
        self.app_secret = os.getenv("WHATSAPP_APP_SECRET")
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        if not self.is_configured:
            missing = []
            if not self.phone_number_id:
                missing.append("WHATSAPP_PHONE_NUMBER_ID")
            if not self.access_token:
                missing.append("WHATSAPP_ACCESS_TOKEN")
            logger.warning(
                "[MetaWhatsAppService] Credentials not configured — missing: %s. "
                "All sends will use development log fallback (no real messages sent). "
                "Set these env vars to enable the Meta Cloud API.",
                ", ".join(missing),
            )
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.META
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev", "local", "test")
    
    @property
    def is_configured(self) -> bool:
        """Check if WhatsApp service is properly configured."""
        return bool(self.phone_number_id and self.access_token)
    
    async def send_text_message(
        self, 
        to: str, 
        text: str,
        preview_url: bool = False
    ) -> SendResult:
        """
        Send a text message to a WhatsApp number.
        
        Args:
            to: Phone number in any format (will be cleaned)
            text: Message text (max 4096 characters)
            preview_url: Whether to show URL previews
            
        Returns:
            SendResult with message ID
        """
        # ORCHESTRATOR-GHOST-EXEMPT: format_phone_number defined in WhatsAppProvider base
        formatted_to = self.format_phone_number(to)
        
        if self.is_development or not self.is_configured:
            return await self._send_development(formatted_to, text, "text")
        
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": formatted_to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                message_id = data.get("messages", [{}])[0].get("id")
                logger.info(f"[META WHATSAPP] Sent to {formatted_to}: {message_id}")
                
                return SendResult(
                    success=True,
                    message_id=message_id,
                    sent_at=datetime.utcnow(),
                    provider="meta",
                    metadata={"response": data, "to": formatted_to}
                )
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else {}
            logger.error(f"[META WHATSAPP] API error: {e.response.status_code} - {error_detail}")
            return SendResult(
                success=False,
                error=str(e),
                error_code=str(e.response.status_code),
                provider="meta",
                metadata={"details": error_detail}
            )
        except Exception as e:
            logger.error(f"[META WHATSAPP] Send error: {e}")
            return SendResult(success=False, error=str(e), provider="meta")
    
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
            SendResult
        """
        formatted_to = self.format_phone_number(to)
        
        if self.is_development or not self.is_configured:
            button_preview = " | ".join([b["title"] for b in buttons])
            full_text = f"{body_text}\n[Buttons: {button_preview}]"
            return await self._send_development(formatted_to, full_text, "interactive")
        
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        button_list = [
            {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"][:20]}}
            for btn in buttons[:3]
        ]
        
        interactive = {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": button_list}
        }
        
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive["footer"] = {"text": footer_text}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": formatted_to,
            "type": "interactive",
            "interactive": interactive
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                message_id = data.get("messages", [{}])[0].get("id")
                logger.info(f"[META WHATSAPP] Interactive sent to {formatted_to}: {message_id}")
                
                return SendResult(
                    success=True,
                    message_id=message_id,
                    sent_at=datetime.utcnow(),
                    provider="meta",
                    metadata={"response": data}
                )
        except Exception as e:
            logger.error(f"[META WHATSAPP] Interactive send error: {e}")
            return SendResult(success=False, error=str(e), provider="meta")
    
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
        formatted_to = self.format_phone_number(to)
        
        if self.is_development or not self.is_configured:
            msg = f"[Document: {filename or document_url}]"
            if caption:
                msg += f"\n{caption}"
            return await self._send_development(formatted_to, msg, "document")
        
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        document_obj = {"link": document_url}
        if caption:
            document_obj["caption"] = caption
        if filename:
            document_obj["filename"] = filename
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": formatted_to,
            "type": "document",
            "document": document_obj
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                message_id = data.get("messages", [{}])[0].get("id")
                logger.info(f"[META WHATSAPP] Document sent to {formatted_to}: {message_id}")
                
                return SendResult(
                    success=True,
                    message_id=message_id,
                    sent_at=datetime.utcnow(),
                    provider="meta",
                    metadata={"response": data}
                )
        except Exception as e:
            logger.error(f"[META WHATSAPP] Document send error: {e}")
            return SendResult(success=False, error=str(e), provider="meta")
    
    async def download_media(self, media_id: str) -> dict[str, Any]:
        """
        Download media (CV, images) from WhatsApp.
        
        Args:
            media_id: The media ID from the webhook
            
        Returns:
            Dict with media content and metadata
        """
        if not self.is_configured:
            return {"success": False, "error": "Service not configured"}
        
        url = f"{self.BASE_URL}/{media_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                media_info = response.json()
                
                media_url = media_info.get("url")
                if not media_url:
                    return {"success": False, "error": "No media URL in response"}
                
                media_response = await client.get(media_url, headers=headers)
                media_response.raise_for_status()
                
                logger.info(f"[META WHATSAPP] Downloaded media: {media_id}")
                
                return {
                    "success": True,
                    "content": media_response.content,
                    "mime_type": media_info.get("mime_type"),
                    "file_size": media_info.get("file_size"),
                    "sha256": media_info.get("sha256")
                }
                
        except Exception as e:
            logger.error(f"[META WHATSAPP] Media download error: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> str | None:
        """
        Verify webhook subscription from Meta.
        
        Args:
            mode: hub.mode from query params
            token: hub.verify_token from query params
            challenge: hub.challenge from query params
            
        Returns:
            Challenge string if verified, None otherwise
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("[META WHATSAPP] Webhook verified successfully")
            return challenge
        
        logger.warning(f"[META WHATSAPP] Webhook verification failed: mode={mode}")
        return None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Meta's X-Hub-Signature-256 header.
        
        Args:
            payload: Raw request body bytes
            signature: Value of X-Hub-Signature-256 header
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.app_secret:
            logger.warning("[META WEBHOOK] WHATSAPP_APP_SECRET not configured, skipping verification")
            return True
        
        if not signature or not signature.startswith("sha256="):
            return False
        
        expected_signature = signature[7:]
        
        computed_signature = hmac.new(
            self.app_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, expected_signature)
    
    def parse_webhook_message(self, payload: dict[str, Any]) -> IncomingMessage | None:
        """
        Parse incoming webhook payload from WhatsApp.
        
        Args:
            payload: The webhook JSON payload
            
        Returns:
            Parsed IncomingMessage or None if not a message
        """
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            if "statuses" in value:
                status = value["statuses"][0]
                return IncomingMessage(
                    type="status_update",
                    message_id=status.get("id"),
                    status=status.get("status"),
                    timestamp=status.get("timestamp"),
                    recipient_id=status.get("recipient_id"),
                    metadata={"provider": "meta"}
                )
            
            if "messages" not in value:
                return None
            
            message = value["messages"][0]
            contact = value.get("contacts", [{}])[0]
            
            parsed = IncomingMessage(
                type="message",
                message_id=message.get("id"),
                from_number=message.get("from"),
                timestamp=message.get("timestamp"),
                message_type=message.get("type"),
                contact_name=contact.get("profile", {}).get("name"),
                metadata={
                    "contact_wa_id": contact.get("wa_id"),
                    "provider": "meta"
                }
            )
            
            msg_type = message["type"]
            
            if msg_type == "text":
                parsed.text = message.get("text", {}).get("body")
            
            elif msg_type == "document":
                doc = message.get("document", {})
                parsed.document = {
                    "id": doc.get("id"),
                    "mime_type": doc.get("mime_type"),
                    "filename": doc.get("filename"),
                    "sha256": doc.get("sha256"),
                    "caption": doc.get("caption")
                }
            
            elif msg_type == "image":
                img = message.get("image", {})
                parsed.image = {
                    "id": img.get("id"),
                    "mime_type": img.get("mime_type"),
                    "sha256": img.get("sha256"),
                    "caption": img.get("caption")
                }
            
            elif msg_type == "interactive":
                interactive = message.get("interactive", {})
                if interactive.get("type") == "button_reply":
                    parsed.button_reply = {
                        "id": interactive.get("button_reply", {}).get("id"),
                        "title": interactive.get("button_reply", {}).get("title")
                    }
                elif interactive.get("type") == "list_reply":
                    parsed.list_reply = {
                        "id": interactive.get("list_reply", {}).get("id"),
                        "title": interactive.get("list_reply", {}).get("title")
                    }
            
            return parsed
            
        except (KeyError, IndexError) as e:
            logger.error(f"[META WHATSAPP] Error parsing webhook: {e}")
            return None
    
    async def _send_development(
        self,
        to: str,
        text: str,
        msg_type: str = "text"
    ) -> SendResult:
        """Log message in development mode."""
        import uuid
        message_id = f"dev_meta_{uuid.uuid4().hex[:12]}"
        
        logger.info("=" * 70)
        logger.info(f"[DEV META WHATSAPP] Mensagem ({msg_type}) - modo desenvolvimento")
        logger.info(f"[DEV META WHATSAPP] Message ID: {message_id}")
        logger.info(f"[DEV META WHATSAPP] Para: {to}")
        logger.info(f"[DEV META WHATSAPP] Conteúdo ({len(text)} chars):")
        for line in text.split('\n')[:20]:
            logger.info(f"[DEV META WHATSAPP]   {line}")
        if len(text.split('\n')) > 20:
            logger.info(f"[DEV META WHATSAPP]   ... ({len(text.split(chr(10))) - 20} mais linhas)")
        logger.info("=" * 70)
        
        return SendResult(
            success=True,
            message_id=message_id,
            sent_at=datetime.utcnow(),
            provider="meta",
            metadata={"mode": "development", "to": to}
        )


meta_whatsapp_service = MetaWhatsAppService()
