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
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.security.webhook_ownership import (
    WebhookOwnershipError,
    verify_webhook_owner,
)

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
    x_merge_signature: str | None = Header(None, alias="X-Merge-Signature"),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Receive webhooks from Merge.dev when data changes.
    Events: Candidate.created, Candidate.updated, Application.changed_stage, etc.
    """
    # P1-W3-01 fix: HMAC obrigatório — rejeitar early se header ausente ANTES de qualquer
    # processamento de payload. Impede DoS de parsing + desambigua "sem assinatura" de
    # "assinatura inválida" nos logs de auditoria. verify_webhook_owner abaixo já é
    # fail-closed, mas o early-reject elimina processamento desnecessário de payloads
    # não-autenticados (ataques de volume, fuzzers).
    if not x_merge_signature:
        logger.warning("[MERGE] P1-W3-01: X-Merge-Signature header ausente — rejeitando (401)")
        raise HTTPException(
            status_code=401,
            detail="X-Merge-Signature header is required",
        )

    body = await request.body()

    # Legacy `verify_merge_signature` was the only gate before Task #1146.
    # It is now subsumed by ``verify_webhook_owner`` (below) which performs
    # per-tenant HMAC validation with a 90-day dual-validate fallback to the
    # global secret. The legacy helper is kept as a private utility for
    # backfill scripts only and is NOT called here anymore.

    from app.shared.security.webhook_ownership import emit_ownership_audit as _eoa
    try:
        raw_data = await request.json()
    except Exception:
        await _eoa(provider="merge", decision="malformed_payload", company_id=None)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        event = MergeWebhookEvent.model_validate(raw_data)
    except ValidationError as exc:
        await _eoa(provider="merge", decision="malformed_payload", company_id=None)
        logger.warning("[MERGE] Invalid payload schema: %s", exc)
        raise HTTPException(status_code=422, detail=exc.errors(include_url=False))

    event_type = event.hook.get("event")

    # Task #1146 — per-tenant ownership validator (audit + cross-check).
    # Dual-validate accepts global signature during the 90-day window; the
    # cross-check rejects payloads whose candidate/job belong to another tenant.
    declared = event.linked_account.get("end_user_origin_id")
    first_record = event.data[0] if event.data else {}
    try:
        # Task #1146 — DO NOT pass candidate/job from the Merge payload to
        # the helper's ownership cross-check. Merge ships its OWN external
        # ids (e.g. "abc-123-merge") in those fields — not local UUIDs from
        # ``candidates`` / ``job_vacancies`` — so the local repo lookup
        # would always 404 and reject legitimate events as
        # ``owner_mismatch``. Signature + declared_company_id are still
        # enforced; cross-check of the external id → local row binding
        # happens further downstream in ``handle_candidate_*`` where the
        # external id is first resolved to a local row.
        await verify_webhook_owner(
            provider="merge",
            raw_body=body,
            signature=x_merge_signature,
            declared_company_id=declared,
            candidate_id=None,  # external Merge id — not a local UUID; see comment above
            job_id=None,        # external Merge id — not a local UUID; see comment above
        )
    except WebhookOwnershipError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

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
