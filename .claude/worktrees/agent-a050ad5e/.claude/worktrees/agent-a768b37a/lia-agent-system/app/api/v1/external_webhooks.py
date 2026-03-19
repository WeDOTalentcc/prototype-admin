"""
External Webhook Endpoints - Inbound webhooks from external services.

Receives events from:
- ATS platforms (Gupy, Pandapé, StackOne)
- Deepgram (transcription completion)
- Other external integrations

Note: OpenMic.ai webhooks are handled in openmic.py
"""
from fastapi import APIRouter, Request, HTTPException, Header, BackgroundTasks, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import hmac
import hashlib
import logging
import os
import uuid
from app.domains.automation.services.webhook_adapters import (
    InterviewWebhookAdapter,
    TestWebhookAdapter,
    DocumentWebhookAdapter,
    WebhookAdapter,
    WebhookEventType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/external-webhooks", tags=["external-webhooks"])


def is_webhook_adapter_enabled(provider: str) -> bool:
    flag = os.getenv(f"ENABLE_WEBHOOK_{provider.upper()}", "true")
    return flag.lower() == "true"


class ATSWebhookEvent(BaseModel):
    """ATS webhook event payload."""
    event_type: str
    ats_candidate_id: str
    ats_vacancy_id: Optional[str] = None
    new_stage: Optional[str] = None
    previous_stage: Optional[str] = None
    candidate_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class DeepgramWebhookEvent(BaseModel):
    """Deepgram transcription webhook payload."""
    request_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


def verify_webhook_signature(payload: bytes, signature: str, secret: str, platform: str = "unknown") -> bool:
    """
    Verify webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw request body bytes
        signature: Signature from header
        secret: Webhook secret
        platform: Platform name for logging
        
    Returns:
        True if signature is valid
    """
    if not secret:
        logger.warning(f"[WEBHOOK] No secret configured for {platform}, rejecting request for security")
        return False
    
    try:
        expected = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature.replace("sha256=", ""))
    except Exception as e:
        logger.error(f"❌ Signature verification error: {e}")
        return False


@router.post("/ats/{platform}")
async def handle_ats_webhook(
    platform: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    x_gupy_signature: Optional[str] = Header(None, alias="X-Gupy-Signature"),
    x_pandape_signature: Optional[str] = Header(None, alias="X-Pandape-Signature"),
    x_stackone_signature: Optional[str] = Header(None, alias="X-StackOne-Signature")
):
    """
    Receive webhook from ATS platforms (Gupy, Pandapé, StackOne).
    Used for inbound sync when changes happen in external ATS.
    
    Supported platforms:
    - gupy: Gupy ATS
    - pandape: Pandapé ATS
    - stackone: StackOne unified ATS API
    
    Events:
    - candidate_created: New candidate in ATS
    - candidate_updated: Candidate data changed
    - stage_changed: Candidate moved to new stage
    - candidate_hired: Candidate was hired
    - candidate_rejected: Candidate was rejected
    """
    platform_lower = platform.lower()
    
    if platform_lower not in ["gupy", "pandape", "stackone"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported ATS platform: {platform}"
        )
    
    raw_body = await request.body()
    
    signature = (
        x_gupy_signature if platform_lower == "gupy"
        else x_pandape_signature if platform_lower == "pandape"
        else x_stackone_signature if platform_lower == "stackone"
        else x_webhook_signature
    )
    
    secret_env_key = f"{platform.upper()}_WEBHOOK_SECRET"
    secret = os.getenv(secret_env_key)
    
    if not verify_webhook_signature(raw_body, signature or "", secret or "", platform_lower):
        logger.error(f"❌ Invalid or missing webhook signature for {platform}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature or secret not configured"
        )
    
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"❌ Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    event_type = payload.get("event_type") or payload.get("event") or payload.get("type", "unknown")
    candidate_id = (
        payload.get("ats_candidate_id") or 
        payload.get("candidate_id") or 
        payload.get("candidateId") or
        payload.get("data", {}).get("candidate_id")
    )
    
    logger.info(f"[WEBHOOK] ATS {platform} event: {event_type} for candidate {candidate_id}")
    
    if event_type in ["candidate_updated", "candidate.updated"]:
        background_tasks.add_task(
            process_ats_candidate_updated,
            platform_lower,
            payload
        )
    elif event_type in ["stage_changed", "stage.changed", "candidate_moved"]:
        background_tasks.add_task(
            process_ats_stage_changed,
            platform_lower,
            payload
        )
    elif event_type in ["candidate_created", "candidate.created"]:
        background_tasks.add_task(
            process_ats_candidate_created,
            platform_lower,
            payload
        )
    elif event_type in ["candidate_hired", "candidate.hired"]:
        background_tasks.add_task(
            process_ats_candidate_hired,
            platform_lower,
            payload
        )
    elif event_type in ["candidate_rejected", "candidate.rejected"]:
        background_tasks.add_task(
            process_ats_candidate_rejected,
            platform_lower,
            payload
        )
    else:
        logger.warning(f"[WEBHOOK] Unknown ATS event type: {event_type}")
    
    return {
        "status": "received",
        "platform": platform_lower,
        "event_type": event_type,
        "candidate_id": candidate_id
    }


async def process_ats_candidate_updated(platform: str, payload: Dict[str, Any]):
    """Sync candidate data from ATS to LIA."""
    try:
        from app.services.ats_sync_service import ATSSyncService, ATSSyncTrigger
        
        sync_service = ATSSyncService()
        
        candidate_id = (
            payload.get("ats_candidate_id") or 
            payload.get("candidate_id") or 
            payload.get("candidateId")
        )
        
        logger.info(f"[ATS SYNC] Processing candidate update from {platform}: {candidate_id}")
        
        result = await sync_service.pull_candidate(
            ats_type=platform,
            ats_candidate_id=candidate_id,
            source_agent="external_webhook"
        )
        
        logger.info(f"[ATS SYNC] Candidate update processed: {result}")
    except Exception as e:
        logger.error(f"❌ Error processing ATS candidate update: {e}", exc_info=True)


async def process_ats_stage_changed(platform: str, payload: Dict[str, Any]):
    """Sync stage change from ATS to LIA (inbound sync)."""
    try:
        from app.services.ats_sync_service import ATSSyncService
        
        candidate_id = (
            payload.get("ats_candidate_id") or 
            payload.get("candidate_id") or
            payload.get("candidateId")
        )
        new_stage = payload.get("new_stage") or payload.get("stage") or payload.get("data", {}).get("stage")
        previous_stage = payload.get("previous_stage") or payload.get("old_stage")
        
        logger.info(f"[ATS SYNC] Stage change from {platform}: {candidate_id} -> {new_stage}")
        
        sync_service = ATSSyncService()
        result = await sync_service.sync_stage_from_ats(
            ats_type=platform,
            ats_candidate_id=candidate_id,
            new_stage=new_stage,
            previous_stage=previous_stage
        )
        
        logger.info(f"[ATS SYNC] Stage change processed: {result}")
    except Exception as e:
        logger.error(f"❌ Error processing ATS stage change: {e}", exc_info=True)


async def process_ats_candidate_created(platform: str, payload: Dict[str, Any]):
    """Handle new candidate created in ATS."""
    try:
        logger.info(f"[ATS SYNC] New candidate from {platform}")
        
        candidate_data = payload.get("candidate_data") or payload.get("data", {})
        
        logger.info(f"[ATS SYNC] Candidate created event received - may need to import to LIA")
    except Exception as e:
        logger.error(f"❌ Error processing ATS candidate created: {e}", exc_info=True)


async def process_ats_candidate_hired(platform: str, payload: Dict[str, Any]):
    """Handle candidate hired in ATS."""
    try:
        from app.services.activity_service import activity_service
        
        candidate_id = (
            payload.get("ats_candidate_id") or 
            payload.get("candidate_id")
        )
        
        logger.info(f"[ATS SYNC] Candidate hired in {platform}: {candidate_id}")
        
        await activity_service.log_activity(
            action="candidate_hired_ats",
            entity_type="candidate",
            entity_id=candidate_id,
            details={
                "source": f"{platform}_webhook",
                "ats_platform": platform
            }
        )
    except Exception as e:
        logger.error(f"❌ Error processing ATS candidate hired: {e}", exc_info=True)


async def process_ats_candidate_rejected(platform: str, payload: Dict[str, Any]):
    """Handle candidate rejected in ATS."""
    try:
        candidate_id = (
            payload.get("ats_candidate_id") or 
            payload.get("candidate_id")
        )
        rejection_reason = payload.get("rejection_reason") or payload.get("reason")
        
        logger.info(f"[ATS SYNC] Candidate rejected in {platform}: {candidate_id}")
    except Exception as e:
        logger.error(f"❌ Error processing ATS candidate rejected: {e}", exc_info=True)


@router.post("/deepgram")
async def handle_deepgram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_deepgram_signature: Optional[str] = Header(None, alias="X-Deepgram-Signature")
):
    """
    Receive webhook from Deepgram when transcription is complete.
    
    Events:
    - transcription_completed: Audio transcription finished
    - transcription_failed: Transcription failed
    """
    raw_body = await request.body()
    
    secret = os.getenv("DEEPGRAM_WEBHOOK_SECRET")
    if x_deepgram_signature and not verify_webhook_signature(raw_body, x_deepgram_signature, secret or ""):
        logger.error("❌ Invalid Deepgram webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"❌ Failed to parse Deepgram webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    request_id = payload.get("request_id") or payload.get("requestId")
    status_val = payload.get("status", "unknown")
    
    logger.info(f"[WEBHOOK] Deepgram transcription: {request_id} - {status_val}")
    
    background_tasks.add_task(
        process_deepgram_transcription,
        payload
    )
    
    return {
        "status": "received",
        "request_id": request_id
    }


async def process_deepgram_transcription(data: Dict[str, Any]):
    """Process Deepgram transcription result."""
    try:
        request_id = data.get("request_id") or data.get("requestId")
        status_val = data.get("status")
        
        if status_val == "completed":
            results = data.get("results", {})
            transcript = ""
            
            if "channels" in results:
                for channel in results.get("channels", []):
                    for alternative in channel.get("alternatives", []):
                        transcript += alternative.get("transcript", "") + " "
            
            logger.info(f"[DEEPGRAM] Transcription completed for {request_id}: {len(transcript)} chars")
            
            metadata = data.get("metadata", {})
            if metadata.get("candidate_id"):
                pass
            
        elif status_val == "failed":
            error = data.get("error", "Unknown error")
            logger.error(f"[DEEPGRAM] Transcription failed for {request_id}: {error}")
        
    except Exception as e:
        logger.error(f"❌ Error processing Deepgram transcription: {e}", exc_info=True)


@router.post("/interview/{provider}")
async def handle_interview_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Receive webhook from interview scheduling tools.
    Supported providers: calendly, openmic, custom
    """
    if not is_webhook_adapter_enabled(f"interview_{provider}"):
        return {"status": "disabled", "provider": provider}

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = payload.get("event_id") or payload.get("id") or str(uuid.uuid4())
    event_type = payload.get("event_type") or payload.get("type") or "interview_confirmed"

    result = await InterviewWebhookAdapter.process(event_id, event_type, payload)
    return result


@router.post("/test/{provider}")
async def handle_test_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Receive webhook from assessment/test platforms.
    Supported providers: testgorilla, codility, custom
    """
    if not is_webhook_adapter_enabled(f"test_{provider}"):
        return {"status": "disabled", "provider": provider}

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = payload.get("event_id") or payload.get("id") or str(uuid.uuid4())
    event_type = payload.get("event_type") or payload.get("type") or "test_completed"

    result = await TestWebhookAdapter.process(event_id, event_type, payload)
    return result


@router.post("/document/{provider}")
async def handle_document_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Receive webhook from document collection services.
    """
    if not is_webhook_adapter_enabled(f"document_{provider}"):
        return {"status": "disabled", "provider": provider}

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = payload.get("event_id") or payload.get("id") or str(uuid.uuid4())
    event_type = payload.get("event_type") or payload.get("type") or "document_submitted"

    result = await DocumentWebhookAdapter.process(event_id, event_type, payload)
    return result


@router.get("/event-log")
async def get_webhook_event_log(limit: int = 50):
    """Get recent webhook event processing log."""
    return {
        "events": WebhookAdapter.get_event_log(limit),
        "total_processed": len(WebhookAdapter._processed_events),
    }


@router.get("/health")
async def external_webhooks_health():
    """Check external webhook endpoints health and configuration."""
    return {
        "status": "healthy",
        "endpoints": {
            "ats": "/external-webhooks/ats/{platform}",
            "deepgram": "/external-webhooks/deepgram",
            "interview": "/external-webhooks/interview/{provider}",
            "test": "/external-webhooks/test/{provider}",
            "document": "/external-webhooks/document/{provider}",
            "event_log": "/external-webhooks/event-log",
        },
        "supported_ats_platforms": ["gupy", "pandape", "stackone"],
        "secrets_configured": {
            "gupy": bool(os.getenv("GUPY_WEBHOOK_SECRET")),
            "pandape": bool(os.getenv("PANDAPE_WEBHOOK_SECRET")),
            "stackone": bool(os.getenv("STACKONE_WEBHOOK_SECRET")),
            "deepgram": bool(os.getenv("DEEPGRAM_WEBHOOK_SECRET"))
        },
        "feature_flags": {
            "interview_calendly": is_webhook_adapter_enabled("interview_calendly"),
            "interview_openmic": is_webhook_adapter_enabled("interview_openmic"),
            "test_testgorilla": is_webhook_adapter_enabled("test_testgorilla"),
            "test_codility": is_webhook_adapter_enabled("test_codility"),
            "document_custom": is_webhook_adapter_enabled("document_custom"),
        }
    }
