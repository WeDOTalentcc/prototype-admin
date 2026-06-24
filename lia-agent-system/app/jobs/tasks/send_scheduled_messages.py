"""Celery task: deliver scheduled messages — GAP-07-007.

Polls scheduled_messages WHERE status='pending' AND send_at <= now()
and dispatches via CommunicationDispatcher (email/whatsapp).

Schedule via celery beat: add
    "communication.send_scheduled_messages": {
        "task": "communication.send_scheduled_messages",
        "schedule": 60.0,  # every 60 seconds
    }
to the beat schedule in lia_config/celery_schedule.py.
"""
import asyncio
import logging
from datetime import datetime, UTC

from app.jobs.tasks._utils import (
    celery_app,
    logger,
    _celery_span,
    _finish_celery_success,
    _finish_celery_failure,
)
from app.jobs.tenant_aware_task import TenantAwareTask


@celery_app.task(
    base=TenantAwareTask,
    name="communication.send_scheduled_messages",
    bind=True,
    max_retries=3,
)
def send_scheduled_messages_task(self) -> dict:
    """Deliver all due scheduled messages (status=pending, send_at <= now)."""
    span = _celery_span("celery.task_start", "communication.send_scheduled_messages")

    async def _run() -> dict:
        from sqlalchemy import select, update
        from app.core.database import AsyncSessionLocal
        from app.models import ScheduledMessage, ScheduledMessageStatus

        now = datetime.now(UTC).replace(tzinfo=None)
        sent, failed = 0, 0

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ScheduledMessage)
                .where(
                    ScheduledMessage.status == ScheduledMessageStatus.PENDING,
                    ScheduledMessage.send_at <= now,
                )
                .limit(100)
                .with_for_update(skip_locked=True)
            )
            due = list(result.scalars().all())

        for msg in due:
            try:
                await _dispatch_message(msg)
                async with AsyncSessionLocal() as db:
                    await db.execute(
                        update(ScheduledMessage)
                        .where(ScheduledMessage.id == msg.id)
                        .values(
                            status=ScheduledMessageStatus.SENT,
                            sent_at=datetime.now(UTC).replace(tzinfo=None),
                        )
                    )
                    await db.commit()
                sent += 1
                logger.info(
                    "send_scheduled_messages: sent %s via %s", msg.id, msg.channel
                )
            except Exception as exc:
                logger.error(
                    "send_scheduled_messages: dispatch failed for %s: %s", msg.id, exc
                )
                async with AsyncSessionLocal() as db:
                    await db.execute(
                        update(ScheduledMessage)
                        .where(ScheduledMessage.id == msg.id)
                        .values(
                            status=ScheduledMessageStatus.FAILED,
                            error_detail=str(exc)[:500],
                        )
                    )
                    await db.commit()
                failed += 1

        return {"sent": sent, "failed": failed, "total_due": len(due)}

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "communication.send_scheduled_messages")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "communication.send_scheduled_messages", exc)
        logger.error("send_scheduled_messages task error: %s", exc)
        raise self.retry(exc=exc, countdown=60)


async def _dispatch_message(msg) -> None:
    """Dispatch a single scheduled message via the appropriate channel.

    Resolves candidate contact info from DB, then delegates to
    CommunicationDispatcher. Raises ValueError if contact info is missing.
    """
    import uuid as _uuid
    from app.core.database import AsyncSessionLocal
    from app.domains.candidates.repositories.candidate_repository import CandidateRepository
    from app.domains.communication.services.communication_dispatcher import communication_dispatcher

    channel = (msg.channel or "email").lower()

    async with AsyncSessionLocal() as db:
        repo = CandidateRepository(db)
        try:
            cand_uuid = _uuid.UUID(str(msg.candidate_id))
        except ValueError:
            cand_uuid = None  # type: ignore[assignment]

        candidate = None
        if cand_uuid:
            candidate = await repo.get_by_id(cand_uuid, company_id=msg.company_id)

    if channel == "email":
        to_email = getattr(candidate, "email", None) if candidate else None
        if not to_email:
            raise ValueError(
                f"No email found for candidate {msg.candidate_id} — cannot deliver scheduled email"
            )
        communication_dispatcher.send_email(
            to_email=to_email,
            to_name=msg.candidate_name or "",
            subject=msg.subject or "Mensagem da WeDOTalent",
            body_html=msg.message_content,
            body_text=msg.message_content,
        )

    elif channel == "whatsapp":
        to_phone = getattr(candidate, "phone", None) if candidate else None
        if not to_phone:
            raise ValueError(
                f"No phone found for candidate {msg.candidate_id} — cannot deliver scheduled WhatsApp"
            )
        communication_dispatcher.send_whatsapp(
            to_phone=to_phone,
            message=msg.message_content,
        )

    else:
        raise ValueError(f"Unsupported channel: {channel}")
