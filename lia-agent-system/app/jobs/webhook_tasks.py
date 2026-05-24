"""
Celery tasks for webhook delivery.

deliver_webhook_task: posts payload to webhook URL with HMAC signature.
On 4xx/5xx, retries up to 3 times with exponential backoff.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="webhooks.deliver",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 60s, then 120s, 240s
)
def deliver_webhook_task(
    self,
    webhook_id: str,
    url: str,
    secret: str,
    event: str,
    payload: dict,
):
    """Deliver a webhook payload with HMAC-SHA256 signature.

    Retries on 4xx/5xx (max 3 retries). Updates webhook stats after each attempt.
    """
    import requests
    # Wave 3 P1.WHK1: prefer sign_payload_v1 (timestamp + replay protection canonical).
    # Receivers extract t={ts} from X-WeDO-Signature header, verify ts > now()-300s, recompute HMAC.
    from app.services.webhook_dispatcher import sign_payload, sign_payload_v1

    body_dict = {
        "event": event,
        "data": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "delivery_id": self.request.id,
    }
    body = json.dumps(body_dict, sort_keys=True)
    signature_v1 = sign_payload_v1(secret, body)
    # Backward-compat: keep legacy sig in separate header so old receivers don't break.
    signature_legacy = sign_payload(secret, body)

    headers = {
        "Content-Type": "application/json",
        "X-WeDO-Event": event,
        "X-WeDO-Signature": signature_v1,
        "X-WeDO-Signature-Legacy": signature_legacy,
        "X-WeDO-Delivery-Id": str(self.request.id),
        "User-Agent": "WeDOTalent-Webhook/1.0",
    }

    error_msg = None
    status_code = None
    success = False

    try:
        response = requests.post(url, data=body, headers=headers, timeout=10)
        status_code = response.status_code
        if 200 <= status_code < 300:
            success = True
            logger.info(
                "[Webhook] delivered: webhook=%s event=%s status=%s",
                webhook_id, event, status_code,
            )
        else:
            error_msg = f"HTTP {status_code}: {response.text[:200]}"
            logger.warning(
                "[Webhook] delivery failed: webhook=%s event=%s status=%s",
                webhook_id, event, status_code,
            )
    except requests.RequestException as exc:
        error_msg = str(exc)[:500]
        logger.warning("[Webhook] delivery exception: webhook=%s err=%s", webhook_id, error_msg)

    # Update stats (best-effort, async)
    try:
        async def _update_stats():
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import select
            from lia_models.webhook import Webhook

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
                wh = result.scalar_one_or_none()
                if wh:
                    wh.total_deliveries = (wh.total_deliveries or 0) + 1
                    if not success:
                        wh.total_failures = (wh.total_failures or 0) + 1
                    wh.last_delivery_at = datetime.now(timezone.utc)
                    wh.last_status_code = status_code
                    wh.last_error = error_msg if not success else None
                    await db.commit()

        # P2-W3-WHK-5: asyncio.run() pode conflitar com gevent/eventlet pool do Celery.
        # Usar get_event_loop() com fallback para new_event_loop() — safe em workers sync.
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Celery gevent/eventlet: loop ja esta rodando — criar novo loop isolado
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(asyncio.run, _update_stats())
                    future.result(timeout=5)
            else:
                loop.run_until_complete(_update_stats())
        except RuntimeError:
            # Fallback: novo event loop (Celery prefork — sem loop ativo)
            asyncio.run(_update_stats())
    except Exception as stats_exc:
        logger.warning("[Webhook] stats update failed: %s", stats_exc)

    # Retry on failure
    if not success:
        try:
            countdown = 60 * (2 ** self.request.retries)  # 60, 120, 240
            raise self.retry(countdown=countdown)
        except self.MaxRetriesExceededError:
            logger.error("[Webhook] max retries exceeded: webhook=%s", webhook_id)

    return {"success": success, "status_code": status_code, "error": error_msg}
