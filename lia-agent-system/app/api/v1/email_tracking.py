"""
Email Tracking endpoints — COMP-7.

GET  /api/v1/email-tracking/pixel/{token}.gif  — pixel 1x1 (open tracking)
GET  /api/v1/email-tracking/click/{token}      — redirect com click tracking
GET  /api/v1/email-tracking/stats/{notification_id} — stats agregadas
POST /api/v1/email-tracking/webhook             — Mailgun Event Webhook

LGPD disclosure obrigatória nos emails:
"Este email contém pixels de rastreamento para medir abertura. Veja nossa Política de Privacidade."
"""
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as get_async_db
from app.shared.learning.ab_testing_service import ABTestingService, get_ab_testing_service
from app.shared.security.require_company_id import require_company_id
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/email-tracking", tags=["Email Tracking"])
communication_webhook_router = APIRouter(prefix="/communication/webhook", tags=["Email Tracking"])

_MAILGUN_WEBHOOK_SIGNING_KEY = os.getenv("MAILGUN_WEBHOOK_SIGNING_KEY", "")

logger = logging.getLogger(__name__)

# 1x1 GIF transparente (binary, base64-decoded)
_TRANSPARENT_GIF = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0x21,
    0xf9, 0x04, 0x01, 0x00, 0x00, 0x00, 0x00, 0x2c, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3b
])


@router.get("/pixel/{token}.gif", include_in_schema=False, response_model=None)
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
    from app.domains.communication.services.email_tracking_service import email_tracking_service

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


@router.get("/click/{token}", response_model=None)
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
    from app.domains.communication.services.email_tracking_service import email_tracking_service

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


def _verify_mailgun_signature(request: Request, body: bytes) -> bool:
    """Verify Mailgun webhook signature using HMAC-SHA256.

    Mailgun signs payloads with HMAC-SHA256 using the webhook signing key and provides:
      - timestamp: Unix timestamp string
      - token: A randomly generated string with 50 characters
      - signature: SHA256 HMAC of concatenated timestamp and token values

    Verification key is MAILGUN_WEBHOOK_SIGNING_KEY from your Mailgun dashboard.

    If MAILGUN_WEBHOOK_SIGNING_KEY is not set, verification is skipped
    (dev/staging only — production MUST set the key).
    """
    if not _MAILGUN_WEBHOOK_SIGNING_KEY:
        _env = os.getenv("ENVIRONMENT", "development")
        if _env in ("production", "staging"):
            logger.warning("[EmailTracking] MAILGUN_WEBHOOK_SIGNING_KEY not set — rejecting in %s", _env)
            return False
        logger.debug("[EmailTracking] signature verification skipped (dev mode, key not set)")
        return True

    try:
        import hashlib
        import hmac
        import json

        try:
            data = json.loads(body)
        except Exception:
            logger.warning("[EmailTracking] webhook: invalid JSON body for signature verification")
            return False

        signature_data = data.get("signature", {})
        timestamp = str(signature_data.get("timestamp", ""))
        token = str(signature_data.get("token", ""))
        signature = str(signature_data.get("signature", ""))

        if not timestamp or not token or not signature:
            logger.warning("[EmailTracking] webhook missing Mailgun signature fields")
            return False

        value = (timestamp + token).encode("utf-8")
        expected = hmac.new(
            _MAILGUN_WEBHOOK_SIGNING_KEY.encode("utf-8"),
            value,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            logger.warning("[EmailTracking] Mailgun webhook HMAC signature mismatch")
            return False

        return True
    except Exception as exc:
        logger.warning("[EmailTracking] webhook signature verification error: %s", exc)
        return False


@router.post("/webhook", response_model=None)
async def tracking_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    ab_service: ABTestingService = Depends(get_ab_testing_service),
):
    """
    Mailgun Event Webhook — receives delivery/open/click/bounce events.

    Mailgun posts individual JSON event objects with a 'signature' block.
    Each event contains: event-data.event, event-data.message.headers.message-id, etc.
    Mapped to internal EmailTrackingEvent records.

    Security: Validates Mailgun webhook HMAC signature when MAILGUN_WEBHOOK_SIGNING_KEY is set.
    LGPD: email addresses are stored as SHA256 hashes only.
    """
    from app.domains.communication.services.email_tracking_service import email_tracking_service

    body = await request.body()

    if not _verify_mailgun_signature(request, body):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        import json
        payload = json.loads(body)
    except Exception:
        logger.warning("[EmailTracking] webhook: invalid JSON body")
        return {"accepted": 0, "errors": 1}

    event_data = payload.get("event-data", payload)
    events = event_data if isinstance(event_data, list) else [event_data]

    accepted = 0
    errors = 0

    _EVENT_MAP = {
        "delivered": "delivered",
        "opened": "open",
        "clicked": "click",
        "failed": "bounce",
        "unsubscribed": "unsubscribe",
        "complained": "spam",
        "rejected": "dropped",
        "queued": "deferred",
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
            mg_event = event.get("event", "")
            mapped_type = _EVENT_MAP.get(mg_event)
            if not mapped_type:
                continue

            message_headers = event.get("message", {}).get("headers", {})
            message_id = (
                event.get("id")
                or message_headers.get("message-id")
                or event.get("sg_message_id", "")
            )
            email_addr = event.get("recipient", event.get("email", ""))

            await email_tracking_service.record_webhook_event(
                db=db,
                sg_message_id=message_id,
                event_type=mapped_type,
                email=email_addr,
                ip=event.get("ip"),
                user_agent=event.get("client-info", {}).get("user-agent", event.get("useragent", "")),
                url=event.get("url"),
                timestamp=event.get("timestamp"),
                raw_event=event,
            )

            if mapped_type in ("open", "click"):
                company_id = ""
                template_id = ""
                ab_test = ""
                ab_variant = ""

                try:
                    ab_data = await email_tracking_service.resolve_ab_data(
                        db=db, sg_message_id=message_id
                    )
                    company_id = ab_data.get("company_id", "")
                    template_id = ab_data.get("template_id", "")
                    ab_test = ab_data.get("ab_test", "")
                    ab_variant = ab_data.get("ab_variant", "")
                except Exception:
                    pass

                if not company_id or not template_id:
                    try:
                        company_id, template_id = await email_tracking_service.resolve_company_template(
                            db=db, sg_message_id=message_id
                        )
                    except Exception:
                        pass

                try:
                    from app.shared.intelligence.template_learning import template_learning_service
                    if company_id and template_id:
                        if mapped_type == "open":
                            template_learning_service.record_open(company_id, template_id)
                        else:
                            template_learning_service.record_click(company_id, template_id)
                except Exception as tl_exc:
                    logger.debug("[EmailTracking] template learning update skipped: %s", tl_exc)

                if ab_test and ab_variant and company_id:
                    try:
                        await ab_service.record_metric(
                            test_name=ab_test,
                            variant_name=ab_variant,
                            session_id=message_id,
                            company_id=company_id,
                            metric_name=f"email_{mapped_type}",
                            metric_value=1.0,
                            db=db,
                        )
                    except Exception as ab_exc:
                        logger.debug("[EmailTracking] A/B testing update skipped: %s", ab_exc)

            accepted += 1
        except Exception as e:
            errors += 1
            logger.debug("[EmailTracking] webhook event error: %s", e)


    logger.info("[EmailTracking] webhook processed accepted=%d errors=%d", accepted, errors)
    return {"accepted": accepted, "errors": errors}


@router.get("/stats/{notification_id}", response_model=None)
async def get_tracking_stats(
    notification_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    company_id: str = Query(..., description="ID da empresa (multi-tenant)"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Estatísticas de tracking para uma notificação.

    Retorna opens, clicks, unique_opens.
    Dados agregados — sem PII individual (LGPD-safe).
    """
    from app.domains.communication.services.email_tracking_service import email_tracking_service

    stats = await email_tracking_service.get_stats(
        db=db,
        notification_id=notification_id,
        company_id=company_id,
    )
    return stats


@communication_webhook_router.post("/tracking")
async def communication_webhook_tracking(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """Alias route: POST /api/v1/communication/webhook/tracking → tracking_webhook."""
    return await tracking_webhook(request, db)

reorder_collection_before_item(router)
