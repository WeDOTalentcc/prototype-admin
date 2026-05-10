"""
Merge.dev Webhook Endpoints
Receives events from Merge when data changes in linked ATS platforms.
"""
import hashlib
import hmac
import logging
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from pydantic import BaseModel, ValidationError

router = APIRouter(prefix="/webhooks/merge", tags=["merge-webhooks"])
logger = logging.getLogger(__name__)


class MergeWebhookEvent(BaseModel):
    hook: dict[str, Any]
    linked_account: dict[str, Any]
    data: list[dict[str, Any]]


def verify_merge_signature(payload: bytes, signature: str) -> bool:
    """Verify Merge webhook signature."""
    secret = os.getenv("MERGE_WEBHOOK_SECRET")
    if not secret:
        logger.warning("[MERGE] No webhook secret configured")
        return False
    
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


@router.post("/", include_in_schema=True, response_model=None)
@router.post("", include_in_schema=False, response_model=None)
async def handle_merge_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_merge_signature: str | None = Header(None, alias="X-Merge-Signature")
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """
    Receive webhooks from Merge.dev when data changes.
    Events: Candidate.created, Candidate.updated, Application.changed_stage, etc.
    """
    body = await request.body()
    
    if x_merge_signature:
        if not verify_merge_signature(body, x_merge_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        raw_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        event = MergeWebhookEvent.model_validate(raw_data)
    except ValidationError as exc:
        logger.warning("[MERGE] Invalid payload schema: %s", exc)
        raise HTTPException(status_code=422, detail=exc.errors())

    event_type = event.hook.get("event")

    logger.info("[MERGE] Received webhook: %s", event_type)

    background_tasks.add_task(process_merge_event, raw_data)

    return {"status": "received", "event": event_type}


async def process_merge_event(data: dict[str, Any]):
    """Process Merge webhook event."""
    hook = data.get("hook", {})
    event_type = hook.get("event", "")
    linked_account = data.get("linked_account", {})
    records = data.get("data", [])
    
    company_id = linked_account.get("end_user_origin_id", "")
    account_token = linked_account.get("id", "")
    integration_name = linked_account.get("integration", "")
    
    logger.info(
        "[MERGE] Processing webhook event",
        extra={"event_type": event_type, "integration_name": integration_name, "company_id": company_id},
    )
    
    for record in records:
        try:
            if event_type == "Candidate.created":
                await handle_candidate_created(record, company_id, account_token)
            elif event_type == "Candidate.updated":
                await handle_candidate_updated(record, company_id, account_token)
            elif event_type == "Application.created":
                await handle_application_created(record, company_id, account_token)
            elif event_type == "Application.changed_stage":
                await handle_stage_changed(record, company_id, account_token)
            elif event_type == "ScheduledInterview.created":
                await handle_interview_created(record, company_id, account_token)
            elif event_type == "ScheduledInterview.updated":
                await handle_interview_updated(record, company_id, account_token)
            elif event_type == "Job.created":
                await handle_job_created(record, company_id, account_token)
            elif event_type == "Job.updated":
                await handle_job_updated(record, company_id, account_token)
            else:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"[MERGE] Unhandled event type: {event_type}")
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"[MERGE] Error processing {event_type}: {e}", exc_info=True)


async def handle_candidate_created(record: dict, company_id: str, account_token: str):
    """Handle new candidate from external ATS."""
    candidate_id = record.get("id")
    first_name = record.get("first_name", "")
    last_name = record.get("last_name", "")
    
    # P0-1 fix: removed first_name + last_name (PII direta — LGPD Art.12). Mantém candidate_id apenas.
    logger.info(
        "[MERGE] New candidate created",
        extra={"candidate_id": candidate_id},
    )
    
    try:
        from app.domains.analytics.services.activity_service import activity_service
        await activity_service.log_activity(
            action="candidate_created_external",
            entity_type="candidate",
            entity_id=candidate_id,
            details={
                "source": "merge_webhook",
                "company_id": company_id,
                "first_name": first_name,
                "last_name": last_name
            }
        )
    except Exception as e:
        logger.error(f"[MERGE] Failed to log candidate created activity: {e}")


async def handle_candidate_updated(record: dict, company_id: str, account_token: str):
    """Handle candidate update from external ATS."""
    candidate_id = record.get("id")
    modified_at = record.get("modified_at")
    
    logger.info(f"[MERGE] Updated candidate: {candidate_id} at {modified_at}")


async def handle_application_created(record: dict, company_id: str, account_token: str):
    """Handle new application from external ATS."""
    application_id = record.get("id")
    candidate_id = record.get("candidate")
    job_id = record.get("job")
    
    logger.info(f"[MERGE] New application: {application_id} (candidate: {candidate_id}, job: {job_id})")


async def handle_stage_changed(record: dict, company_id: str, account_token: str):
    """Handle stage change from external ATS (inbound sync)."""
    application_id = record.get("id")
    current_stage = record.get("current_stage", {})
    new_stage_name = current_stage.get("name", "") if isinstance(current_stage, dict) else ""
    candidate_id = record.get("candidate")
    job_id = record.get("job")
    
    logger.info(
        "[MERGE] Stage changed",
        extra={"application_id": application_id, "new_stage_name": new_stage_name},
    )
    
    try:
        from app.domains.ats_integration.services.merge_ats_service import merge_ats_service
        lia_stage = merge_ats_service.map_merge_stage_to_lia(new_stage_name)
        
        from app.domains.analytics.services.activity_service import activity_service
        await activity_service.log_activity(
            action="stage_changed_external",
            entity_type="application",
            entity_id=application_id,
            details={
                "source": "merge_webhook",
                "company_id": company_id,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "new_stage": new_stage_name,
                "lia_stage": lia_stage
            }
        )
    except Exception as e:
        logger.error(f"[MERGE] Failed to log stage change activity: {e}")


async def handle_interview_created(record: dict, company_id: str, account_token: str):
    """Handle new interview scheduled in external ATS."""
    interview_id = record.get("id")
    application_id = record.get("application")
    scheduled_at = record.get("scheduled_at")
    
    logger.info(f"[MERGE] New interview: {interview_id} for application {application_id} at {scheduled_at}")


async def handle_interview_updated(record: dict, company_id: str, account_token: str):
    """Handle interview update from external ATS."""
    interview_id = record.get("id")
    status = record.get("status")
    
    logger.info(f"[MERGE] Updated interview: {interview_id} - status: {status}")


async def handle_job_created(record: dict, company_id: str, account_token: str):
    """Handle new job from external ATS."""
    job_id = record.get("id")
    job_name = record.get("name", "")
    
    logger.info(
        "[MERGE] New job created",
        extra={"job_id": job_id, "job_name": job_name},
    )


async def handle_job_updated(record: dict, company_id: str, account_token: str):
    """Handle job update from external ATS."""
    job_id = record.get("id")
    status = record.get("status")
    
    logger.info(f"[MERGE] Updated job: {job_id} - status: {status}")
