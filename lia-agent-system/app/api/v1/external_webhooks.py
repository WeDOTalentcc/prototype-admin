"""
External Webhook Endpoints - Inbound webhooks from external services.

Receives events from:
- ATS platforms (Gupy, Pandapé, Merge)
- Other external integrations
"""
import hashlib
import hmac
import logging
import os
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ValidationError

from app.domains.automation.services.webhook_adapters import (
    DocumentWebhookAdapter,
    InterviewWebhookAdapter,
    TestWebhookAdapter,
    WebhookAdapter,
)

from app.domains.ats_integration.services.ats_sync_service import ATSSyncService, get_ats_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/external-webhooks", tags=["external-webhooks"])


def is_webhook_adapter_enabled(provider: str) -> bool:
    flag = os.getenv(f"ENABLE_WEBHOOK_{provider.upper()}", "true")
    return flag.lower() == "true"


class ATSWebhookEvent(BaseModel):
    """ATS webhook event payload."""
    event_type: str
    ats_candidate_id: str
    ats_vacancy_id: str | None = None
    new_stage: str | None = None
    previous_stage: str | None = None
    candidate_data: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


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


@router.post("/ats/{platform}", response_model=None)
async def handle_ats_webhook(
    platform: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
    x_gupy_signature: str | None = Header(None, alias="X-Gupy-Signature"),
    x_pandape_signature: str | None = Header(None, alias="X-Pandape-Signature"),
    x_merge_signature: str | None = Header(None, alias="X-Merge-Signature"),
):
    """
    Receive webhook from ATS platforms (Gupy, Pandapé, Merge).
    Used for inbound sync when changes happen in external ATS.
    
    Supported platforms:
    - gupy: Gupy ATS
    - pandape: Pandapé ATS
    - merge: Merge.dev unified ATS API
    
    Events:
    - candidate_created: New candidate in ATS
    - candidate_updated: Candidate data changed
    - stage_changed: Candidate moved to new stage
    - candidate_hired: Candidate was hired
    - candidate_rejected: Candidate was rejected
    """
    platform_lower = platform.lower()
    
    if platform_lower not in ["gupy", "pandape", "merge"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported ATS platform: {platform}"
        )
    
    raw_body = await request.body()
    
    signature = (
        x_gupy_signature if platform_lower == "gupy"
        else x_pandape_signature if platform_lower == "pandape"
        else x_merge_signature if platform_lower == "merge"
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
        raw_payload = await request.json()
    except Exception as e:
        logger.error("Failed to parse webhook payload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    # Validate against typed model where fields match; fall back to raw dict for flexible ATS schemas
    try:
        ats_event = ATSWebhookEvent.model_validate(raw_payload)
        event_type = ats_event.event_type
        candidate_id = ats_event.ats_candidate_id
        payload = raw_payload  # keep raw dict for background tasks that access extra fields
    except ValidationError:
        # ATS payloads often have platform-specific field names — fall back gracefully
        payload = raw_payload
        event_type = payload.get("event_type") or payload.get("event") or payload.get("type", "unknown")
        candidate_id = (
            payload.get("ats_candidate_id") or
            payload.get("candidate_id") or
            payload.get("candidateId") or
            payload.get("data", {}).get("candidate_id")
        )
    
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[WEBHOOK] Unknown ATS event type: {event_type}")
    
    return {
        "status": "received",
        "platform": platform_lower,
        "event_type": event_type,
        "candidate_id": candidate_id
    }


async def process_ats_candidate_updated(platform: str, payload: dict[str, Any]):
    """Sync candidate data from ATS to LIA."""
    try:
        sync_service = get_ats_sync_service()
        
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


async def process_ats_stage_changed(platform: str, payload: dict[str, Any]):
    """Sync stage change from ATS to LIA (inbound sync)."""
    try:
        candidate_id = (
            payload.get("ats_candidate_id") or 
            payload.get("candidate_id") or
            payload.get("candidateId")
        )
        new_stage = payload.get("new_stage") or payload.get("stage") or payload.get("data", {}).get("stage")
        previous_stage = payload.get("previous_stage") or payload.get("old_stage")
        
        logger.info(f"[ATS SYNC] Stage change from {platform}: {candidate_id} -> {new_stage}")
        
        sync_service = get_ats_sync_service()
        result = await sync_service.sync_stage_from_ats(
            ats_type=platform,
            ats_candidate_id=candidate_id,
            new_stage=new_stage,
            previous_stage=previous_stage
        )
        
        logger.info(f"[ATS SYNC] Stage change processed: {result}")
    except Exception as e:
        logger.error(f"❌ Error processing ATS stage change: {e}", exc_info=True)


async def process_ats_candidate_created(platform: str, payload: dict[str, Any]):
    """Handle new candidate created in ATS."""
    try:
        logger.info(f"[ATS SYNC] New candidate from {platform}")
        
        payload.get("candidate_data") or payload.get("data", {})
        
        logger.info("[ATS SYNC] Candidate created event received - may need to import to LIA")
    except Exception as e:
        logger.error(f"❌ Error processing ATS candidate created: {e}", exc_info=True)


async def process_ats_candidate_hired(platform: str, payload: dict[str, Any]):
    """Handle candidate hired in ATS."""
    try:
        from app.domains.analytics.services.activity_service import activity_service
        
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


async def process_ats_candidate_rejected(platform: str, payload: dict[str, Any]):
    """Handle candidate rejected in ATS."""
    try:
        candidate_id = (
            payload.get("ats_candidate_id") or 
            payload.get("candidate_id")
        )
        payload.get("rejection_reason") or payload.get("reason")
        
        logger.info(f"[ATS SYNC] Candidate rejected in {platform}: {candidate_id}")
    except Exception as e:
        logger.error(f"❌ Error processing ATS candidate rejected: {e}", exc_info=True)


@router.post("/interview/{provider}", response_model=None)
async def handle_interview_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Receive webhook from interview scheduling tools.
    Supported providers: calendly, custom
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


@router.post("/test/{provider}", response_model=None)
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


@router.post("/document/{provider}", response_model=None)
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


@router.get("/event-log", response_model=None)
async def get_webhook_event_log(limit: int = 50):
    """Get recent webhook event processing log."""
    return {
        "events": WebhookAdapter.get_event_log(limit),
        "total_processed": len(WebhookAdapter._processed_events),
    }


# multi-tenancy: public endpoint (health) — no tenant data
@router.get("/health", response_model=None)
async def external_webhooks_health():
    """Check external webhook endpoints health and configuration."""
    return {
        "status": "healthy",
        "endpoints": {
            "ats": "/external-webhooks/ats/{platform}",
            "interview": "/external-webhooks/interview/{provider}",
            "test": "/external-webhooks/test/{provider}",
            "document": "/external-webhooks/document/{provider}",
            "event_log": "/external-webhooks/event-log",
        },
        "supported_ats_platforms": ["gupy", "pandape", "merge"],
        "secrets_configured": {
            "gupy": bool(os.getenv("GUPY_WEBHOOK_SECRET")),
            "pandape": bool(os.getenv("PANDAPE_WEBHOOK_SECRET")),
            "merge": bool(os.getenv("MERGE_WEBHOOK_SECRET")),
        },
        "feature_flags": {
            "interview_calendly": is_webhook_adapter_enabled("interview_calendly"),
            "test_testgorilla": is_webhook_adapter_enabled("test_testgorilla"),
            "test_codility": is_webhook_adapter_enabled("test_codility"),
            "document_custom": is_webhook_adapter_enabled("document_custom"),
        }
    }
