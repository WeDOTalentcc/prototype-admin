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

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.communication.services.communication_service import CommunicationLog

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
async def mailgun_webhook(request: Request):
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
    signing_key = os.getenv("MAILGUN_WEBHOOK_SIGNING_KEY", "")
    if not signing_key:
        logger.error("[MailgunWebhook] MAILGUN_WEBHOOK_SIGNING_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook signing key not configured",
        )

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        )

    sig_data = body.get("signature", {})
    ts = str(sig_data.get("timestamp", ""))
    token = sig_data.get("token", "")
    sig = sig_data.get("signature", "")

    try:
        ts_int = int(ts)
        if abs(time.time() - ts_int) > MAX_TIMESTAMP_AGE_SECONDS:
            logger.warning("[MailgunWebhook] Timestamp too old/future — rejecting (replay protection)")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Webhook timestamp expired",
            )
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timestamp",
        )

    if not _verify_mailgun_signature(ts, token, sig, signing_key):
        logger.warning("[MailgunWebhook] Invalid signature — rejecting payload")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature",
        )

    event_data = body.get("event-data", {})
    event_type = event_data.get("event", "").lower()

    mapping = MAILGUN_EVENT_MAP.get(event_type)
    if mapping is None:
        logger.debug("[MailgunWebhook] Ignoring event type: %s", event_type)
        return {"status": "ignored", "event": event_type}

    new_status, timestamp_field = mapping

    message_id = (
        event_data.get("message", {}).get("headers", {}).get("message-id", "")
    )
    if not message_id:
        logger.warning("[MailgunWebhook] No message-id in event — skipping")
        return {"status": "skipped", "reason": "no_message_id"}

    message_id = message_id.strip("<>")

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
        async with AsyncSessionLocal() as db:
            values: dict = {
                "status": new_status,
                "updated_at": datetime.utcnow(),
            }
            if timestamp_field:
                values[timestamp_field] = event_ts

            if new_status == "failed":
                error_parts = [p for p in [severity, reason, delivery_message] if p]
                values["error_message"] = " | ".join(error_parts) or "delivery failed"

            result = await db.execute(
                update(CommunicationLog)
                .where(CommunicationLog.provider_message_id == message_id)
                .values(**values)
            )
            await db.commit()

            rows = result.rowcount  # type: ignore[union-attr]
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
