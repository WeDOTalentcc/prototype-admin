"""
SSE broadcast for Kanban real-time updates (GAP-09-001).

When any recruiter moves a candidate between stages, all connected clients
for the same company receive an instant push via Redis pub/sub → SSE.

Channel: kanban:broadcast:{company_id}

FE connects: GET /api/v1/kanban/events?job_id=X
BE publishes: after PATCH /candidates/{id}/stage succeeds
"""
import asyncio
import json
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request
from starlette.responses import StreamingResponse

from app.shared.chat_event_serializer import format_sse_event
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/kanban", tags=["kanban-broadcast"])

CHANNEL_PREFIX = "kanban:broadcast"
KEEPALIVE_INTERVAL_S = 25


def _channel_for_company(company_id: str) -> str:
    return f"{CHANNEL_PREFIX}:{company_id}"


async def publish_candidate_stage_change(
    company_id: str,
    candidate_id: str,
    candidate_name: str,
    vacancy_id: str,
    from_stage: str,
    to_stage: str,
    sub_status: str | None = None,
    moved_by_user_id: str = "",
) -> bool:
    """Publish a candidate stage change event to all connected kanban clients.

    Called from candidates_crud.update_candidate_stage after DB commit.
    Fail-open: returns False on error (stage transition is NOT blocked).
    """
    try:
        from app.core.redis_client import get_redis
        redis = await get_redis()
        channel = _channel_for_company(company_id)
        payload = {
            "type": "candidate_stage_changed",
            "candidate_id": str(candidate_id),
            "candidate_name": candidate_name or "",
            "vacancy_id": str(vacancy_id),
            "from_stage": from_stage,
            "to_stage": to_stage,
            "sub_status": sub_status or "",
            "moved_by": moved_by_user_id,
            "ts": time.time(),
        }
        await redis.publish(channel, json.dumps(payload))
        logger.info(
            "[kanban-broadcast] published stage_change candidate=%s %s->%s company=%s",
            candidate_id, from_stage, to_stage, company_id,
        )
        return True
    except Exception as exc:
        logger.warning("[kanban-broadcast] publish failed (fail-open): %s", exc)
        return False


@router.get("/events")
async def kanban_events(
    request: Request,
    job_id: str = Query(default="", description="Filter events to specific vacancy"),
    company_id: str = Depends(require_company_id),
):
    """SSE endpoint for real-time kanban updates.

    Clients connect and receive candidate_stage_changed events for their company.
    Optional job_id filter narrows to a specific vacancy board.
    Auto-reconnects via standard SSE protocol.
    """
    async def event_generator():
        from app.core.redis_client import get_redis
        redis = await get_redis()
        pubsub = redis.pubsub()
        channel = _channel_for_company(company_id)

        try:
            await pubsub.subscribe(channel)
            logger.info("[kanban-broadcast] client subscribed company=%s job=%s", company_id, job_id or "all")
            seq = 0

            while True:
                if await request.is_disconnected():
                    break

                msg = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=KEEPALIVE_INTERVAL_S),
                    timeout=KEEPALIVE_INTERVAL_S + 5,
                )

                if msg and msg["type"] == "message":
                    try:
                        data = json.loads(msg["data"])
                        if job_id and data.get("vacancy_id") != job_id:
                            continue
                        seq += 1
                        yield format_sse_event(data, f"kb-{seq}")
                    except (json.JSONDecodeError, KeyError):
                        pass
                else:
                    yield ": keepalive\n\n"

        except asyncio.TimeoutError:
            yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.warning("[kanban-broadcast] stream error: %s", exc)
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except Exception:
                pass
            logger.info("[kanban-broadcast] client disconnected company=%s", company_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
