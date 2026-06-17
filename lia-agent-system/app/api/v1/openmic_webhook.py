"""
OpenMic.ai Webhook Endpoint — /api/v1/openmic/webhook

Receives call completion events from OpenMic.ai after an automated voice
screening interview finishes. Immediately returns 200 to acknowledge, then
enqueues a Celery task to run the full WSI scoring pipeline.

Event payload (OpenMic call_completed):
  {
    "event": "call_completed",
    "call_id": "oc_abc123",
    "status": "completed" | "failed" | "no_answer" | "voicemail",
    "duration_seconds": 480,
    "transcript": "...",
    "audio_url": "https://...",
    "metadata": {
      "candidate_id": "...",
      "job_id": "...",
      "company_id": "..."
    },
    "created_at": "2024-01-01T12:00:00Z"
  }

Security:
  - HMAC-SHA256 signature validated via X-OpenMic-Signature header.
  - OPENMIC_WEBHOOK_SECRET MUST be set in production; missing secret rejects all
    requests unless OPENMIC_ALLOW_UNSIGNED_WEBHOOK=true (local dev only).
  - audio_url validated against allowlist (scheme + trusted host domain) before
    any outbound HTTP fetch to prevent SSRF.
  - LGPD: transcript processed in-memory, never logged in plaintext.
"""
import ipaddress
import json
import logging
import os
import re
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.shared.pii_masking import mask_pii
from app.services.voice.openmic_service import OpenMicSignatureError, openmic_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.security.webhook_ownership import (
    WebhookOwnershipError,
    verify_webhook_owner,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/openmic", tags=["openmic-voice"])

# ── SSRF protection: allowed schemes and trusted audio host domains ────────────
# Allowlist is intentionally narrow: only known provider domains/storage patterns.
# - openmic.ai, *.openmic.ai — OpenMic recordings and callbacks
# - deepgram.com, *.deepgram.com — Deepgram hosted audio
# - *.s3.amazonaws.com, *.s3-*.amazonaws.com — AWS S3 buckets (not the broad amazonaws.com)
# - storage.googleapis.com — Google Cloud Storage public objects
_ALLOWED_AUDIO_SCHEMES = {"https"}
_ALLOWED_AUDIO_HOST_PATTERN = re.compile(
    r"^(?:"
    r"([a-z0-9-]+\.)*openmic\.ai"
    r"|([a-z0-9-]+\.)*deepgram\.com"
    r"|[a-z0-9-]+\.s3(?:[.-][a-z0-9-]+)?\.amazonaws\.com"
    r"|storage\.googleapis\.com"
    r")$",
    re.IGNORECASE,
)

# Private CIDR ranges — block any fetch to internal network
_PRIVATE_CIDRS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _validate_audio_url(url: str) -> str:
    """
    Validate audio_url is safe to fetch (anti-SSRF).

    Rules:
    - Must use https scheme.
    - Hostname must match trusted audio provider allowlist.
    - Hostname must not resolve to a private/loopback address (checked syntactically).

    Returns:
        Normalized URL string.

    Raises:
        ValueError: If URL fails validation.
    """
    if not url:
        return ""

    parsed = urlparse(url)

    if parsed.scheme.lower() not in _ALLOWED_AUDIO_SCHEMES:
        raise ValueError(f"audio_url must use HTTPS, got scheme={parsed.scheme!r}")

    hostname = parsed.hostname or ""
    if not _ALLOWED_AUDIO_HOST_PATTERN.match(hostname):
        raise ValueError(
            f"audio_url hostname {hostname!r} is not in the trusted audio provider allowlist."
        )

    # Reject if hostname is a raw IP (could target internal services)
    try:
        ip = ipaddress.ip_address(hostname)
        for cidr in _PRIVATE_CIDRS:
            if ip in cidr:
                raise ValueError(f"audio_url resolves to private IP {hostname!r} — SSRF blocked.")
    except ValueError as exc:
        # ip_address() raises ValueError for non-IP hostnames — that's fine, skip
        if "SSRF blocked" in str(exc):
            raise

    return url


@router.post("/webhook", status_code=status.HTTP_200_OK, response_model=None)
async def openmic_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_openmic_signature: str | None = Header(None, alias="X-OpenMic-Signature"),
):
    """
    Receive and process OpenMic.ai call completion webhook.

    Security: validates HMAC-SHA256 signature. OPENMIC_WEBHOOK_SECRET must be
    set in production; missing secret causes 503 (fail-closed) unless
    OPENMIC_ALLOW_UNSIGNED_WEBHOOK=true is explicitly set (dev only).

    Returns 200 immediately to prevent OpenMic from retrying.
    """
    raw_body = await request.body()

    # Signature validation is delegated to ``verify_webhook_owner`` (Task
    # #1146) below — it covers both the per-tenant secret AND the legacy
    # global ``OPENMIC_WEBHOOK_SECRET`` during the 90-day dual-validate
    # window. We MUST still parse the body before we can resolve the
    # ``metadata.company_id``, so the helper is invoked AFTER JSON parse
    # and AFTER metadata extraction (see block further down).

    # --- Parse JSON payload ---
    try:
        payload: dict = json.loads(raw_body)
    except Exception as exc:
        # Task #1146 — even malformed payloads emit ONE canonical audit row.
        from app.shared.security.webhook_ownership import emit_ownership_audit as _eoa
        await _eoa(provider="openmic", decision="malformed_payload", company_id=None)
        logger.error("[OpenMic Webhook] Failed to parse JSON body: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload.",
        )

    event = payload.get("event", "unknown")
    call_id = payload.get("call_id", "unknown")
    call_status = payload.get("status", "unknown")

    logger.info(
        "[OpenMic Webhook] Received event=%s call_id=%s status=%s",
        event,
        call_id,
        call_status,
    )

    # Only process completed calls — acknowledge others without processing.
    # Task #1146 — emit canonical ownership audit row (decision='skipped')
    # so EVERY received webhook produces exactly one ownership audit row.
    if event != "call_completed" or call_status not in ("completed",):
        from app.shared.security.webhook_ownership import emit_ownership_audit
        await emit_ownership_audit(
            provider="openmic",
            decision="skipped",
            company_id=(payload.get("metadata") or {}).get("company_id"),
            session_id=call_id,
        )
        logger.info(
            "[OpenMic Webhook] Skipping non-completed event: event=%s status=%s call_id=%s",
            event,
            call_status,
            call_id,
        )
        return {"received": True, "processed": False, "reason": f"event={event} status={call_status}"}

    # --- Extract data ---
    metadata = payload.get("metadata") or {}
    candidate_id = metadata.get("candidate_id")
    job_id = metadata.get("job_id")
    company_id = metadata.get("company_id")
    transcript = payload.get("transcript", "")
    duration_seconds = payload.get("duration_seconds", 0)

    # --- Validate audio_url before storing (SSRF protection) ---
    raw_audio_url = payload.get("audio_url", "")
    try:
        audio_url = _validate_audio_url(raw_audio_url)
    except ValueError as exc:
        logger.warning(
            "[OpenMic Webhook] audio_url validation failed (dropping URL) — call_id=%s error=%s",
            call_id,
            exc,
        )
        audio_url = ""  # Drop invalid URL; pipeline proceeds with transcript only

    if not candidate_id or not job_id or not company_id:
        from app.shared.security.webhook_ownership import emit_ownership_audit as _eoa
        await _eoa(
            provider="openmic",
            decision="malformed_payload",
            company_id=company_id,
            candidate_id=candidate_id,
            job_id=job_id,
            session_id=call_id,
        )
        logger.error(
            "[OpenMic Webhook] Missing required metadata fields — "
            "call_id=%s candidate_id=%s job_id=%s company_id=%s",
            call_id,
            candidate_id,
            job_id,
            company_id,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Webhook payload missing required metadata: candidate_id, job_id, company_id.",
        )

    # Task #1146 — per-tenant ownership validator (audit + cross-check). Rejects
    # payloads whose candidate/job belong to a different tenant than the
    # ``metadata.company_id`` claimed in the OpenMic body.
    try:
        await verify_webhook_owner(
            provider="openmic",
            raw_body=raw_body,
            signature=x_openmic_signature,
            declared_company_id=company_id,
            candidate_id=candidate_id,
            job_id=job_id,
            session_id=call_id,
        )
    except WebhookOwnershipError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    logger.info(
        "[OpenMic Webhook] Processing completed call — call_id=%s candidate_id=%s job_id=%s duration=%ds",
        call_id,
        mask_pii(candidate_id),
        job_id,
        duration_seconds,
    )

    # --- Enqueue WSI pipeline as Celery background task ---
    task_data = {
        "call_id": call_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "company_id": company_id,
        "transcript": transcript,
        "audio_url": audio_url,
        "duration_seconds": duration_seconds,
        "source": "openmic",
    }

    background_tasks.add_task(_enqueue_wsi_pipeline, task_data)

    return {
        "received": True,
        "processed": True,
        "call_id": call_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
    }


async def _enqueue_wsi_pipeline(task_data: dict) -> None:
    """
    Enqueue the WSI scoring pipeline via Celery.

    Runs in background so the webhook endpoint returns 200 immediately.
    Falls back to direct async execution if Celery is unavailable.
    """
    call_id = task_data.get("call_id", "unknown")
    candidate_id = task_data.get("candidate_id", "unknown")

    try:
        from app.jobs.celery_tasks import run_openmic_wsi_pipeline_task
        result = run_openmic_wsi_pipeline_task.apply_async(
            kwargs={"task_data": task_data},
            queue="evaluation_normal",
        )
        logger.info(
            "[OpenMic Webhook] WSI pipeline task enqueued — celery_task_id=%s call_id=%s candidate_id=%s",
            result.id,
            call_id,
            mask_pii(candidate_id),
        )
    except Exception as celery_exc:
        logger.warning(
            "[OpenMic Webhook] Celery unavailable (%s) — running WSI pipeline inline. call_id=%s",
            celery_exc,
            call_id,
        )
        try:
            await _run_wsi_pipeline_inline(task_data)
        except Exception as inline_exc:
            logger.error(
                "[OpenMic Webhook] Inline WSI pipeline failed — call_id=%s candidate_id=%s error=%s",
                call_id,
                mask_pii(candidate_id),
                inline_exc,
            )


async def _run_wsi_pipeline_inline(task_data: dict) -> None:
    """
    Run the WSI scoring pipeline inline (Celery fallback).

    Delegates to the shared `run_voice_wsi_pipeline` service so that the
    inline path and the Celery task stay in sync.
    """
    from app.services.voice.wsi_pipeline import run_voice_wsi_pipeline
    await run_voice_wsi_pipeline(task_data)


@router.get("/webhook/health", response_model=None)
async def openmic_webhook_health():
    # multi-tenancy: public endpoint (health) — no tenant data
    """Health check for OpenMic webhook service."""
    health = await openmic_service.health_check()
    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=health)
