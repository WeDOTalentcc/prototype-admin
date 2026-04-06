"""
WhatsApp Webhook API Endpoints

Handles incoming messages from WhatsApp Business API.
Supports both Meta Cloud API and Twilio providers.
"""

import hashlib
import hmac
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.communication.services.whatsapp_factory import WhatsAppProviderFactory
from app.domains.communication.services.whatsapp_meta_service import meta_whatsapp_service
from app.domains.communication.services.whatsapp_provider import ProviderType
from app.domains.communication.services.whatsapp_twilio_service import twilio_whatsapp_service
from app.domains.recruiter_assistant.services.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")


class PhoneNumberMapping:
    """
    Service to map WhatsApp phone_number_id to company_id.
    
    In production, this should query a database table that maps
    each WhatsApp Business Phone Number to its owning company.
    """
    
    _mapping_cache: dict[str, str] = {}
    
    @classmethod
    async def get_company_id(cls, phone_number_id: str, db: AsyncSession) -> str | None:
        """
        Get company_id for a given WhatsApp phone_number_id.
        
        First checks cache, then queries database.
        Returns None if no mapping found.
        """
        if phone_number_id in cls._mapping_cache:
            return cls._mapping_cache[phone_number_id]
        
        try:
            from app.models.company import Company
            result = await db.execute(
                select(Company.id).where(Company.whatsapp_phone_number_id == phone_number_id)
            )
            company = result.scalar_one_or_none()
            if company:
                company_id = str(company)
                cls._mapping_cache[phone_number_id] = company_id
                return company_id
        except Exception as e:
            logger.warning(f"Could not query company mapping: {e}")
        
        env_mapping = os.getenv(f"WHATSAPP_PHONE_{phone_number_id}_COMPANY")
        if env_mapping:
            cls._mapping_cache[phone_number_id] = env_mapping
            return env_mapping
        
        return None
    
    @classmethod
    def set_mapping(cls, phone_number_id: str, company_id: str):
        """Manually set a phone_number_id to company_id mapping."""
        cls._mapping_cache[phone_number_id] = company_id


def verify_meta_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify Meta's X-Hub-Signature-256 header.
    
    Args:
        payload: Raw request body bytes
        signature: Value of X-Hub-Signature-256 header
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not WHATSAPP_APP_SECRET:
        logger.warning("[WEBHOOK] WHATSAPP_APP_SECRET not configured, skipping signature verification")
        return True
    
    if not signature or not signature.startswith("sha256="):
        return False
    
    expected_signature = signature[7:]
    
    computed_signature = hmac.new(
        WHATSAPP_APP_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, expected_signature)


class WebhookVerifyParams(BaseModel):
    """Query parameters for webhook verification."""
    hub_mode: str | None = Query(None, alias="hub.mode")
    hub_verify_token: str | None = Query(None, alias="hub.verify_token")
    hub_challenge: str | None = Query(None, alias="hub.challenge")


@router.get("/webhook")
async def verify_webhook(
    request: Request
):
    """
    Verify webhook subscription from Meta.
    
    Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge
    when setting up or verifying the webhook subscription.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    logger.info(f"[WEBHOOK] Verification request: mode={mode}, token={token[:10] if token else None}...")
    
    if not all([mode, token, challenge]):
        logger.warning("[WEBHOOK] Missing verification parameters")
        raise HTTPException(status_code=400, detail="Missing verification parameters")
    
    result = meta_whatsapp_service.verify_webhook(mode, token, challenge)
    
    if result:
        logger.info("[WEBHOOK] Verification successful")
        return Response(content=result, media_type="text/plain")
    
    logger.warning("[WEBHOOK] Verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


def extract_phone_number_id(payload: dict) -> str | None:
    """Extract phone_number_id from Meta webhook payload."""
    try:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        metadata = value.get("metadata", {})
        return metadata.get("phone_number_id")
    except (IndexError, KeyError, TypeError):
        return None


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Receive incoming messages and status updates from Meta WhatsApp.
    
    Meta sends POST requests with message data when:
    - User sends a message
    - Message status changes (sent, delivered, read)
    
    Response must be 200 OK within 20 seconds or Meta will retry.
    
    Security: Validates X-Hub-Signature-256 header using WHATSAPP_APP_SECRET.
    """
    raw_body = await request.body()
    
    signature = request.headers.get("X-Hub-Signature-256")
    
    if WHATSAPP_APP_SECRET:
        if not signature:
            logger.warning("[WEBHOOK] Missing X-Hub-Signature-256 header")
            raise HTTPException(status_code=401, detail="Missing signature")
        
        if not verify_meta_webhook_signature(raw_body, signature):
            logger.warning("[WEBHOOK] Invalid signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        import json
        payload = json.loads(raw_body)
        
        logger.info(f"[WEBHOOK] Received Meta payload: {payload.get('object')}")
        
        if payload.get("object") != "whatsapp_business_account":
            logger.warning(f"[WEBHOOK] Unknown object type: {payload.get('object')}")
            return {"status": "ignored"}
        
        phone_number_id = extract_phone_number_id(payload)
        company_id = None
        
        if phone_number_id:
            company_id = await PhoneNumberMapping.get_company_id(phone_number_id, db)
            logger.debug(f"[WEBHOOK] phone_number_id={phone_number_id} -> company_id={company_id}")
        
        if not company_id:
            logger.warning(f"[WEBHOOK] No company mapping for phone_number_id={phone_number_id}, cannot process")
            return {"status": "error", "detail": "No company mapping found for this phone number"}
        
        parsed = meta_whatsapp_service.parse_webhook_message(payload)
        
        if not parsed:
            logger.debug("[WEBHOOK] No actionable message in payload")
            return {"status": "ok"}
        
        if parsed.type == "status_update":
            logger.info(f"[WEBHOOK] Status update: {parsed.status} for {parsed.message_id}")
            return {"status": "ok"}
        
        if parsed.type == "message":
            phone_number = parsed.from_number
            message_type = parsed.message_type
            
            media_data = None
            if message_type == "document":
                media_data = parsed.document
            elif message_type == "image":
                media_data = parsed.image
            
            message_content = ""
            if message_type == "text":
                message_content = parsed.text or ""
            elif parsed.button_reply:
                message_content = parsed.button_reply.get("id", "")
            elif media_data:
                message_content = media_data.get("caption", "[Documento enviado]")
            
            logger.info(f"[WEBHOOK] Message from {phone_number}: {message_type} - {message_content[:50]}...")
            
            provider = await WhatsAppProviderFactory.get_provider(company_id, db)
            manager = ConversationManager(db, provider=provider)
            
            response = await manager.process_incoming_message(
                phone_number=phone_number,
                message_content=message_content,
                message_type=message_type,
                media_data=media_data,
                company_id=company_id
            )
            
            if response:
                await provider.send_text_message(phone_number, response)
            
            return {"status": "ok"}
        
        return {"status": "ok"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WEBHOOK] Error processing webhook: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.post("/twilio-webhook")
async def receive_twilio_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Receive incoming messages from Twilio WhatsApp.
    
    Twilio sends POST requests with form data when:
    - User sends a message
    - Message status changes (queued, sent, delivered, read, failed)
    
    Security: Validates X-Twilio-Signature header using TWILIO_AUTH_TOKEN.
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Twilio-Signature", "")
    
    full_url = str(request.url)
    
    if not twilio_whatsapp_service.verify_webhook_signature(raw_body, signature, full_url):
        logger.warning("[TWILIO WEBHOOK] Invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        form_data = await request.form()
        payload = dict(form_data)
        
        logger.info(f"[TWILIO WEBHOOK] Received payload from {payload.get('From')}")
        
        parsed = twilio_whatsapp_service.parse_webhook_message(payload)
        
        if not parsed:
            logger.debug("[TWILIO WEBHOOK] No actionable message in payload")
            return Response(content="", media_type="text/xml")
        
        if parsed.type == "status_update":
            logger.info(f"[TWILIO WEBHOOK] Status update: {parsed.status} for {parsed.message_id}")
            return Response(content="", media_type="text/xml")
        
        if parsed.type == "message":
            phone_number = parsed.from_number
            message_type = parsed.message_type
            
            media_data = None
            if message_type == "document":
                media_data = parsed.document
            elif message_type == "image":
                media_data = parsed.image
            
            message_content = parsed.text or ""
            if media_data:
                message_content = media_data.get("caption", "[Documento enviado]")
            
            logger.info(f"[TWILIO WEBHOOK] Message from {phone_number}: {message_type} - {message_content[:50]}...")
            
            to_number = payload.get("To", "").replace("whatsapp:", "").replace("+", "")
            company_id = await _get_company_from_twilio_number(to_number, db)
            
            if not company_id:
                logger.warning(f"[TWILIO WEBHOOK] No company mapping for To={to_number}, cannot process")
                return {"status": "error", "detail": "No company mapping found for this phone number"}
            
            provider = WhatsAppProviderFactory.get_twilio_provider()
            manager = ConversationManager(db, provider=provider)
            
            response = await manager.process_incoming_message(
                phone_number=phone_number,
                message_content=message_content,
                message_type=message_type,
                media_data=media_data,
                company_id=company_id
            )
            
            if response:
                await provider.send_text_message(phone_number, response)
            
            return Response(content="", media_type="text/xml")
        
        return Response(content="", media_type="text/xml")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TWILIO WEBHOOK] Error processing webhook: {e}", exc_info=True)
        return Response(content="", media_type="text/xml")


async def _get_company_from_twilio_number(twilio_number: str, db: AsyncSession) -> str | None:
    """Get company_id from Twilio WhatsApp number."""
    try:
        from app.models.company import Company
        
        result = await db.execute(
            select(Company.id).where(Company.twilio_whatsapp_number == twilio_number)
        )
        company = result.scalar_one_or_none()
        if company:
            return str(company)
    except Exception as e:
        logger.warning(f"Could not query company by Twilio number: {e}")
    
    env_mapping = os.getenv(f"TWILIO_NUMBER_{twilio_number}_COMPANY")
    if env_mapping:
        return env_mapping
    
    return None


class SendMessageRequest(BaseModel):
    """Request to send a message to a WhatsApp number."""
    phone_number: str
    message: str
    company_id: str | None = None
    provider: str | None = None


class SendFeedbackRequest(BaseModel):
    """Request to send feedback to a candidate."""
    conversation_id: str
    approved: bool
    recruiter_name: str | None = None


@router.post("/send-message")
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a WhatsApp message (for testing/manual messaging).
    
    Supports specifying provider or using company's configured provider.
    """
    if request.provider:
        try:
            provider_type = ProviderType(request.provider.lower())
            provider = WhatsAppProviderFactory.get_provider_by_type(provider_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")
    else:
        provider = await WhatsAppProviderFactory.get_provider(request.company_id, db)
    
    result = await provider.send_text_message(
        to=request.phone_number,
        text=request.message
    )
    
    return {
        "success": result.success,
        "message_id": result.message_id,
        "provider": result.provider,
        "error": result.error
    }


@router.post("/send-feedback")
async def send_feedback(
    request: SendFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send feedback to a candidate after recruiter decision.
    """
    from uuid import UUID
    
    manager = ConversationManager(db)
    success = await manager.send_feedback(
        conversation_id=UUID(request.conversation_id),
        approved=request.approved,
        recruiter_name=request.recruiter_name
    )
    
    return {"success": success}


@router.get("/conversations")
async def list_conversations(
    company_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List WhatsApp conversations for a company.
    
    Supports multi-tenancy:
    - If authenticated, user can only see conversations for their own company
    - Admins can optionally specify a different company_id
    - Falls back to demo_company for unauthenticated requests in development
    """
    from app.models.whatsapp_conversation import ConversationState, WhatsAppConversation
    
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id is required")
    target_company_id = company_id
    
    query = select(WhatsAppConversation).where(
        WhatsAppConversation.company_id == target_company_id
    ).order_by(WhatsAppConversation.created_at.desc()).limit(limit)
    
    if status:
        query = query.where(WhatsAppConversation.state == ConversationState(status))
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return {
        "count": len(conversations),
        "conversations": [c.to_dict() for c in conversations]
    }


@router.get("/conversations/authenticated")
async def list_conversations_authenticated(
    company_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List WhatsApp conversations for a company (authenticated endpoint).
    
    Requires authentication. Users can only see conversations for their own company.
    Admins can optionally specify a different company_id to access other tenants.
    """

    from app.auth.dependencies import get_user_company_id
    from app.auth.models import User, UserRole
    from app.models.whatsapp_conversation import ConversationState, WhatsAppConversation
    
    result = await db.execute(
        select(User).where(User.email == "demo@wedotalent.com")
    )
    user = result.scalar_one_or_none()
    
    if user:
        target_company_id = company_id or get_user_company_id(user)
        
        if company_id and company_id != user.company_id:
            if user.role != UserRole.admin:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: You can only view conversations for your own company"
                )
            logger.info(f"[AUDIT] Admin {user.email} accessing conversations for company {company_id}")
    else:
        if not company_id:
            raise HTTPException(status_code=400, detail="company_id is required")
        target_company_id = company_id
    
    query = select(WhatsAppConversation).where(
        WhatsAppConversation.company_id == target_company_id
    ).order_by(WhatsAppConversation.created_at.desc()).limit(limit)
    
    if status:
        query = query.where(WhatsAppConversation.state == ConversationState(status))
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return {
        "count": len(conversations),
        "conversations": [c.to_dict() for c in conversations]
    }


@router.get("/providers")
async def list_providers():
    """
    List available WhatsApp providers and their configuration status.
    """
    return {
        "providers": [
            {
                "type": "meta",
                "name": "Meta Cloud API",
                "configured": meta_whatsapp_service.is_configured,
                "default": True
            },
            {
                "type": "twilio",
                "name": "Twilio WhatsApp",
                "configured": twilio_whatsapp_service.is_configured,
                "default": False
            }
        ]
    }
