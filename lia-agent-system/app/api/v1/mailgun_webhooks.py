"""
Mailgun Webhook Endpoint — receives delivery status events from Mailgun.

Validates HMAC-SHA256 signature using MAILGUN_WEBHOOK_SIGNING_KEY,
then updates CommunicationLog status accordingly.

Events handled:
- delivered  → status="delivered", delivered_at set
- failed / bounced → status="failed", failed_at set
- opened     → status="read", read_at set
- complained → status="complained"
- unsubscribed → status="unsubscribed"
"""
import hashlib
import hmac
import logging
import os
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.domains.communication.dependencies import get_communication_repo
from app.domains.communication.repositories.communication_repository import (
    CommunicationRepository,
)
from app.shared.security.require_company_id import require_company_id

MAX_TIMESTAMP_AGE_SECONDS = 300

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/mailgun", tags=["mailgun-webhooks"])

MAILGUN_EVENT_MAP = {
    "delivered": ("delivered", "delivered_at"),
    "failed": ("failed", "failed_at"),
    "bounced": ("failed", "failed_at"),
    "dropped": ("failed", "failed_at"),
    "opened": ("read", "read_at"),
    "clicked": None,
    "complained": ("complained", None),
    "unsubscribed": ("unsubscribed", None),
}


def _verify_mailgun_signature(
    timestamp: str, token: str, signature: str, signing_key: str
) -> bool:
    """Verify Mailgun webhook signature using HMAC-SHA256."""
    if not all([timestamp, token, signature, signing_key]):
        return False

    expected = hmac.new(
        signing_key.encode("utf-8"),
        f"{timestamp}{token}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@router.post("", status_code=200)
async def mailgun_webhook(
    request: Request,
    repo: CommunicationRepository = Depends(get_communication_repo),
):
    """
    Receive Mailgun delivery events.

    Mailgun POSTs JSON with this structure:
    {
      "signature": {
        "timestamp": "...",
        "token": "...",
        "signature": "..."
      },
      "event-data": {
        "event": "delivered",
        "message": { "headers": { "message-id": "..." } },
        "timestamp": 1234567890.123,
        ...
      }
    }
    """
    # Task #1146 — legacy upfront 503-on-missing-MAILGUN_WEBHOOK_SIGNING_KEY
    # gate removed. The canonical ``verify_webhook_owner`` helper enforces
    # tenant-first per-tenant secret resolution with a global fallback
    # during the 90-day rollout window; once D+90 expires and global is
    # removed, per-tenant secrets in ``company_webhook_secrets`` take over.
    try:
        body = await request.json()
    except Exception:
        # Task #1146 — even malformed payloads emit ONE canonical audit row.
        from app.shared.security.webhook_ownership import emit_ownership_audit as _eoa
        await _eoa(provider="mailgun", decision="malformed_payload", company_id=None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        )

    sig_data = body.get("signature", {})
    ts = str(sig_data.get("timestamp", ""))
    token = sig_data.get("token", "")
    sig = sig_data.get("signature", "")

    from app.shared.security.webhook_ownership import emit_ownership_audit as _eoa
    try:
        ts_int = int(ts)
        if abs(time.time() - ts_int) > MAX_TIMESTAMP_AGE_SECONDS:
            await _eoa(provider="mailgun", decision="timestamp_expired", company_id=None)
            logger.warning("[MailgunWebhook] Timestamp too old/future — rejecting (replay protection)")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Webhook timestamp expired",
            )
    except (ValueError, TypeError):
        await _eoa(provider="mailgun", decision="malformed_payload", company_id=None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timestamp",
        )

    # Task #1146 — tenant-first single helper invocation. We extract
    # message_id from the payload, resolve the tenant via CommunicationLog
    # BEFORE signature verification, then call ``verify_webhook_owner``
    # exactly once. This guarantees: (a) one canonical audit row per
    # request, (b) the per-tenant secret path is exercised on every
    # request whose tenant we can resolve, (c) the D+90 deprecation works
    # because we never short-circuit to global-only.
    from app.shared.security.webhook_ownership import (
        WebhookOwnershipError,
        emit_ownership_audit,
        verify_webhook_owner,
    )

    sig_payload = f"{ts}{token}".encode("utf-8")
    event_data = body.get("event-data", {})
    event_type = event_data.get("event", "").lower()

    mapping = MAILGUN_EVENT_MAP.get(event_type)
    if mapping is None:
        # Task #1146 — emit canonical ownership audit (decision='skipped')
        # so EVERY received webhook produces exactly one audit row.
        await emit_ownership_audit(
            provider="mailgun",
            decision="skipped",
            company_id=None,
        )
        logger.debug("[MailgunWebhook] Ignoring event type: %s", event_type)
        return {"status": "ignored", "event": event_type}

    new_status, timestamp_field = mapping

    message_id = (
        event_data.get("message", {}).get("headers", {}).get("message-id", "")
    )
    if not message_id:
        await emit_ownership_audit(
            provider="mailgun",
            decision="skipped",
            company_id=None,
        )
        logger.warning("[MailgunWebhook] No message-id in event — skipping")
        return {"status": "skipped", "reason": "no_message_id"}

    message_id = message_id.strip("<>")

    # Tenant resolution via CommunicationLog (Task #1146).
    try:
        from sqlalchemy import select  # local import — keep top-level clean
        from app.models.communication_log import CommunicationLog  # type: ignore

        res = await repo.db.execute(
            select(CommunicationLog.company_id)
            .where(CommunicationLog.provider_message_id == message_id)
            .limit(1)
        )
        row = res.first()
        resolved_company_id: str | None = str(row[0]) if row else None
    except Exception:
        resolved_company_id = None

    if not resolved_company_id:
        # Task #1146 — reject with 403 + canonical audit row when we
        # cannot bind the webhook to a tenant. Acceptance criterion
        # explicitly requires rejection (NOT ACK) before any state work.
        await emit_ownership_audit(
            provider="mailgun",
            decision="unresolved_tenant",
            company_id=None,
        )
        logger.warning(
            "[MailgunWebhook] message_id=%s could not be bound to a tenant — "
            "rejecting 403 (Task #1146)",
            message_id,
        )
        raise HTTPException(
            status_code=403,
            detail="webhook payload could not be bound to a tenant",
        )

    # Single canonical helper invocation — per-tenant secret with global
    # fallback during the 90-day window. Emits exactly one audit row.
    try:
        await verify_webhook_owner(
            provider="mailgun",
            raw_body=b"",
            signature=sig,
            signature_payload=sig_payload,
            declared_company_id=resolved_company_id,
            enforce_ownership=False,  # ownership = resolution itself
        )
    except WebhookOwnershipError as exc:
        logger.warning("[MailgunWebhook] Ownership/signature rejected: %s", exc)
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    event_ts_raw = event_data.get("timestamp")
    event_ts = (
        datetime.utcfromtimestamp(float(event_ts_raw))
        if event_ts_raw
        else datetime.utcnow()
    )

    severity = event_data.get("severity", "")
    reason = event_data.get("reason", "")
    delivery_message = event_data.get("delivery-status", {}).get("message", "")

    try:
        values: dict = {
            "status": new_status,
            "updated_at": datetime.utcnow(),
        }
        if timestamp_field:
            values[timestamp_field] = event_ts

        if new_status == "failed":
            error_parts = [p for p in [severity, reason, delivery_message] if p]
            values["error_message"] = " | ".join(error_parts) or "delivery failed"

        rows = await repo.update_log_by_provider_message_id(message_id, values)

        if rows == 0:
            logger.info(
                "[MailgunWebhook] No CommunicationLog found for message_id=%s (event=%s)",
                message_id,
                event_type,
            )
        else:
            logger.info(
                "[MailgunWebhook] Updated %d log(s): message_id=%s → status=%s",
                rows,
                message_id,
                new_status,
            )

    except Exception:
        logger.exception("[MailgunWebhook] DB error processing event %s", event_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error processing webhook",
        )

    return {"status": "processed", "event": event_type, "message_id": message_id}
