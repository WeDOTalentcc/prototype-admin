"""
Email Tracking endpoints — COMP-7.

GET  /api/v1/email-tracking/pixel/{token}.gif  — pixel 1x1 (open tracking)
GET  /api/v1/email-tracking/click/{token}      — redirect com click tracking
GET  /api/v1/email-tracking/stats/{notification_id} — stats agregadas
POST /api/v1/email-tracking/webhook             — SendGrid Event Webhook

LGPD disclosure obrigatória nos emails:
"Este email contém pixels de rastreamento para medir abertura. Veja nossa Política de Privacidade."
"""
import hashlib
import hmac
import logging
import os
from fastapi import APIRouter, Request, Depends, Path, Query, HTTPException
from fastapi.responses import Response, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db as get_async_db

router = APIRouter(prefix="/email-tracking", tags=["Email Tracking"])

_SENDGRID_WEBHOOK_VERIFICATION_KEY = os.getenv("SENDGRID_WEBHOOK_VERIFICATION_KEY", "")

logger = logging.getLogger(__name__)

# 1x1 GIF transparente (binary, base64-decoded)
_TRANSPARENT_GIF = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0x21,
    0xf9, 0x04, 0x01, 0x00, 0x00, 0x00, 0x00, 0x2c, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3b
])


@router.get("/pixel/{token}.gif", include_in_schema=False)
async def tracking_pixel(
    request: Request,
    token: str = Path(...),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Pixel de rastreamento 1x1 GIF.

    Registra abertura do email. Retorna GIF transparente.
    IP é armazenado apenas como SHA256 hash (LGPD-safe).
    """
    from app.services.email_tracking_service import email_tracking_service

    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")

    try:
        await email_tracking_service.record_open(
            db=db,
            token=token,
            ip=ip,
            user_agent=user_agent,
        )
    except Exception as e:
        logger.debug("[EmailTracking] pixel error (non-blocking): %s", e)

    return Response(
        content=_TRANSPARENT_GIF,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/click/{token}")
async def tracking_click(
    request: Request,
    token: str = Path(...),
    url: str = Query(..., description="URL de destino (encoded)"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Link redirect com tracking de clique.

    Registra clique e redireciona para URL de destino.
    """
    from app.services.email_tracking_service import email_tracking_service

    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")

    # Validação básica de URL (evitar open redirect para domínios externos maliciosos)
    # Aceita apenas http/https
    if not url.startswith(("http://", "https://")):
        url = "https://app.wedotalent.com"  # fallback seguro

    try:
        redirect_url = await email_tracking_service.record_click(
            db=db,
            token=token,
            link_url=url,
            ip=ip,
            user_agent=user_agent,
        )
        return RedirectResponse(url=redirect_url or url, status_code=302)
    except Exception as e:
        logger.debug("[EmailTracking] click error (non-blocking): %s", e)
        return RedirectResponse(url=url, status_code=302)


def _verify_sendgrid_signature(request: Request, body: bytes) -> bool:
    """Verify SendGrid Event Webhook signature (v3 ECDSA or v1 HMAC fallback).

    If SENDGRID_WEBHOOK_VERIFICATION_KEY is not set, verification is skipped
    (dev/staging only — production MUST set the key).
    """
    if not _SENDGRID_WEBHOOK_VERIFICATION_KEY:
        logger.warning("[EmailTracking] webhook signature verification SKIPPED — SENDGRID_WEBHOOK_VERIFICATION_KEY not set")
        return True

    signature = request.headers.get("x-twilio-email-event-webhook-signature", "")
    timestamp = request.headers.get("x-twilio-email-event-webhook-timestamp", "")

    if not signature or not timestamp:
        logger.warning("[EmailTracking] webhook missing signature headers")
        return False

    try:
        payload = timestamp + body.decode("utf-8")
        expected = hmac.new(
            _SENDGRID_WEBHOOK_VERIFICATION_KEY.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception as exc:
        logger.warning("[EmailTracking] webhook signature verification error: %s", exc)
        return False


@router.post("/webhook")
async def tracking_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    SendGrid Event Webhook — receives delivery/open/click/bounce events.

    SendGrid posts batched JSON arrays of event objects.
    Each event contains: email, event, sg_message_id, timestamp, etc.
    Mapped to internal EmailTrackingEvent records.

    Security: Validates SendGrid webhook signature when SENDGRID_WEBHOOK_VERIFICATION_KEY is set.
    LGPD: email addresses are stored as SHA256 hashes only.
    """
    from app.services.email_tracking_service import email_tracking_service

    body = await request.body()

    if not _verify_sendgrid_signature(request, body):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        import json
        events = json.loads(body)
    except Exception:
        logger.warning("[EmailTracking] webhook: invalid JSON body")
        return {"accepted": 0, "errors": 1}

    if not isinstance(events, list):
        events = [events]

    accepted = 0
    errors = 0

    _EVENT_MAP = {
        "delivered": "delivered",
        "open": "open",
        "click": "click",
        "bounce": "bounce",
        "dropped": "dropped",
        "deferred": "deferred",
        "spamreport": "spam",
        "unsubscribe": "unsubscribe",
    }

    for event in events:
        try:
            sg_event = event.get("event", "")
            mapped_type = _EVENT_MAP.get(sg_event)
            if not mapped_type:
                continue

            sg_message_id = event.get("sg_message_id", "")
            email_addr = event.get("email", "")

            await email_tracking_service.record_webhook_event(
                db=db,
                sg_message_id=sg_message_id,
                event_type=mapped_type,
                email=email_addr,
                ip=event.get("ip"),
                user_agent=event.get("useragent", ""),
                url=event.get("url"),
                timestamp=event.get("timestamp"),
                raw_event=event,
            )

            if mapped_type in ("open", "click"):
                try:
                    from app.shared.intelligence.template_learning import template_learning_service
                    company_id = event.get("company_id", "")
                    template_id = event.get("template_id", "")
                    if not company_id or not template_id:
                        company_id, template_id = await email_tracking_service.resolve_company_template(
                            db=db, sg_message_id=sg_message_id
                        )
                    if company_id and template_id:
                        if mapped_type == "open":
                            template_learning_service.record_open(company_id, template_id)
                        else:
                            template_learning_service.record_click(company_id, template_id)
                except Exception as tl_exc:
                    logger.debug("[EmailTracking] template learning update skipped: %s", tl_exc)

            accepted += 1
        except Exception as e:
            errors += 1
            logger.debug("[EmailTracking] webhook event error: %s", e)

    if accepted > 0:
        try:
            await db.commit()
        except Exception as commit_exc:
            logger.warning("[EmailTracking] webhook commit error: %s", commit_exc)

    logger.info("[EmailTracking] webhook processed accepted=%d errors=%d", accepted, errors)
    return {"accepted": accepted, "errors": errors}


@router.get("/stats/{notification_id}")
async def get_tracking_stats(
    notification_id: str = Path(...),
    company_id: str = Query(..., description="ID da empresa (multi-tenant)"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Estatísticas de tracking para uma notificação.

    Retorna opens, clicks, unique_opens.
    Dados agregados — sem PII individual (LGPD-safe).
    """
    from app.services.email_tracking_service import email_tracking_service

    stats = await email_tracking_service.get_stats(
        db=db,
        notification_id=notification_id,
        company_id=company_id,
    )
    return stats
