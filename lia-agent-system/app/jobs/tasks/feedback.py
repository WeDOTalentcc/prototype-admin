"""Celery tasks: feedback (Fase 7)."""
import asyncio
import re
from datetime import UTC

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
    _emit_celery_retry, _emit_dlq_push,
)

@celery_app.task(base=TenantAwareTask, name="feedback.generate_and_send", bind=True, max_retries=2)
def feedback_generate_and_send_task(
    self, candidate_id: str, job_id: str, reason: str, company_id: str = None
) -> dict:
    """
    Generate rejection feedback and auto-send (email + WhatsApp).

    Called from reject_candidate tool. Generates personalized feedback
    with auto_send=True and channel=BOTH, which triggers immediate
    dispatch via feedback.auto_send after FairnessGuard passes.
    """
    async def _run() -> dict:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from app.domains.cv_screening.services.personalized_feedback_service import (
            CandidateContext,
            FeedbackChannel,
            JobContext,
            PersonalizedFeedbackRequest,
            WSIEvaluationContext,
            personalized_feedback_service,
        )
        from app.models.candidate import Candidate

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Candidate).where(Candidate.id == candidate_id)
            )
            candidate = result.scalar_one_or_none()
            if not candidate:
                return {"success": False, "reason": "candidate_not_found"}

            candidate_ctx = CandidateContext(
                candidate_id=candidate_id,
                name=getattr(candidate, "name", "Candidato"),
                email=getattr(candidate, "email", None) or "",
                phone=getattr(candidate, "phone", None),
            )

            job_ctx = JobContext(
                job_id=job_id,
                title=getattr(candidate, "applied_job_title", "Vaga"),
                seniority_level=None,
            )

            wsi_score = getattr(candidate, "wsi_score", 0.0) or 0.0
            eval_ctx = WSIEvaluationContext(
                overall_wsi=wsi_score,
                classification="abaixo_da_media" if wsi_score < 2.5 else "regular",
                strengths=[],
                development_areas=[reason] if reason else [],
            )

            request = PersonalizedFeedbackRequest(
                candidate=candidate_ctx,
                job=job_ctx,
                evaluation=eval_ctx,
                channel=FeedbackChannel.BOTH,
                auto_send=True,
                company_id=company_id,
                decision_type="REPROVADO",
            )

            fb_result = await personalized_feedback_service.generate_personalized_feedback(
                request=request, db=db
            )
            return {
                "success": True,
                "feedback_id": fb_result.feedback_id,
                "auto_sent": True,
            }

    span = _celery_span("celery.task_start", "feedback.generate_and_send")
    span.set_attribute("candidate_id", candidate_id)
    span.set_attribute("job_id", job_id)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "feedback.generate_and_send")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "feedback.generate_and_send", exc)
        logger.error("feedback.generate_and_send failed: %s", exc)
        _emit_celery_retry("feedback.generate_and_send", exc, self.request.retries, self.max_retries, 60)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("feedback.generate_and_send", exc)
        raise self.retry(exc=exc, countdown=60)

async def feedback_auto_send_canonical(
    feedback_id: str,
    company_id: str,
    db=None,
) -> dict:
    """Sprint 11.3 Batch 2.5+ (2026-05-24) — canonical async function for
    feedback auto-send (extracted from feedback_auto_send_task Celery task).

    Sends approved/edited rejection feedback via email/WhatsApp + marks SENT.
    Callable from MonitoringLoop safety net OR from event-driven service
    layer without requiring asyncio.run() wrapper.

    Args:
        feedback_id: UUID of PersonalizedFeedbackRecord.
        company_id: UUID da empresa (multi-tenant).
        db: Optional AsyncSession. If None, opens new session.

    Returns:
        Dict com { feedback_id, status, channel, success, results }
    """
    if db is None:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as own_db:
            return await _feedback_auto_send_impl(feedback_id, company_id, own_db)
    return await _feedback_auto_send_impl(feedback_id, company_id, db)


async def _feedback_auto_send_impl(feedback_id: str, company_id: str, db) -> dict:
    """Internal impl shared by canonical function + Celery task body."""
    from sqlalchemy import select

    from app.domains.communication.services.email_service import MailgunEmailService
    from app.domains.cv_screening.services.personalized_feedback_service import (
        PersonalizedFeedbackRecord,
        PersonalizedFeedbackStatus,
        personalized_feedback_service,
    )

    email_service = MailgunEmailService()

    result = await db.execute(
        select(PersonalizedFeedbackRecord).where(
            PersonalizedFeedbackRecord.id == feedback_id
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        return {"feedback_id": feedback_id, "status": "not_found", "success": False}

    if record.status not in (
        PersonalizedFeedbackStatus.APPROVED.value,
        PersonalizedFeedbackStatus.EDITED.value,
        PersonalizedFeedbackStatus.FAILED.value,
    ):
        return {"feedback_id": feedback_id, "status": record.status, "success": False, "reason": "not_approved"}

    subject = record.edited_subject or record.subject
    body_text = record.edited_body or record.body_text
    body_html = record.body_html

    from app.shared.compliance.fairness_guard import FairnessGuard
    fg = FairnessGuard()
    content_to_check = body_text or ""
    fg_result = fg.check(content_to_check)
    if fg_result.is_blocked:
        logger.warning(
            "feedback.auto_send: FairnessGuard BLOCKED id=%s category=%s terms=%s",
            feedback_id, fg_result.category, fg_result.blocked_terms,
        )
        await personalized_feedback_service.mark_as_failed(
            feedback_id=feedback_id,
            reason=f"FairnessGuard blocked: {fg_result.category} — {fg_result.blocked_terms}",
            db=db,
        )
        return {
            "feedback_id": feedback_id,
            "status": "blocked",
            "reason": "fairness_guard",
            "category": fg_result.category,
            "success": False,
        }

    send_result = {}
    channel_used = record.channel or "email"

    if record.candidate_email and channel_used in ("email", "both"):
        email_result = await email_service.send_email(
            to_email=record.candidate_email,
            to_name=record.candidate_name or None,
            subject=subject,
            body=body_text or "",
            body_html=body_html or f"<p>{body_text}</p>",
            categories=["rejection_feedback", "auto_send"],
            metadata={
                "feedback_id": feedback_id,
                "company_id": company_id,
                "template_id": f"feedback:{record.tone}:{record.wsi_classification}",
            },
        )
        sg_message_id = getattr(email_result, "message_id", None)
        send_result["email"] = {
            "success": email_result.success if hasattr(email_result, "success") else True,
            "message_id": sg_message_id,
        }
        if sg_message_id:
            from datetime import datetime as dt_util

            from app.domains.communication.models.message_queue import MessageQueue as MQModel
            mq_entry = MQModel(
                company_id=company_id,
                candidate_id=record.candidate_id or "",
                candidate_name=record.candidate_name or "",
                candidate_email=record.candidate_email,
                vacancy_id=record.job_id,
                vacancy_title=record.job_title,
                channel="email",
                message_type="rejection_feedback",
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                status="sent",
                provider_message_id=sg_message_id,
                sent_at=dt_util.utcnow(),
                created_by="feedback_auto_send",
                extra_data={
                    "sg_message_id": sg_message_id,
                    "feedback_id": feedback_id,
                    "template_id": f"feedback:{record.tone}:{record.wsi_classification}",
                    "source": "feedback_auto_send",
                },
            )
            db.add(mq_entry)
            await db.commit()
            logger.info(
                "feedback.auto_send: MessageQueue created id=%s sg_id=%s",
                mq_entry.id, sg_message_id,
            )

    if record.candidate_phone and channel_used in ("whatsapp", "both"):
        from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher
        dispatcher = CommunicationDispatcher()
        msg = record.whatsapp_message or body_text[:500]
        send_result["whatsapp"] = dispatcher.send_whatsapp(
            to_phone=record.candidate_phone,
            message=msg,
        )

    any_success = any(r.get("success") for r in send_result.values())

    if any_success:
        await personalized_feedback_service.mark_as_sent(
            feedback_id=feedback_id,
            channel=channel_used,
            send_result=send_result,
            db=db,
        )
    else:
        await personalized_feedback_service.mark_as_failed(
            feedback_id=feedback_id,
            reason="all_channels_failed",
            send_result=send_result,
            db=db,
        )

    try:
        from app.shared.intelligence.template_learning import template_learning_service
        template_learning_service.record_send(
            company_id=company_id,
            template_id=f"feedback:{record.tone}:{record.wsi_classification}",
        )
    except Exception:
        pass

    logger.info(
        "feedback.auto_send: id=%s channel=%s success=%s",
        feedback_id, channel_used, any_success,
    )
    return {
        "feedback_id": feedback_id,
        "status": "sent" if any_success else "failed",
        "channel": channel_used,
        "success": any_success,
        "results": {k: {"success": v.get("success"), "message_id": v.get("message_id")} for k, v in send_result.items()},
    }


@celery_app.task(base=TenantAwareTask, name="feedback.auto_send", bind=True, max_retries=3)
def feedback_auto_send_task(self, feedback_id: str, company_id: str) -> dict:
    """
    Auto-send approved/edited rejection feedback via email/WhatsApp.

    Triggered after recruiter approves feedback in the PersonalizedFeedbackService.
    Sends via CommunicationDispatcher and marks the record as SENT.

    Args:
        feedback_id: UUID of the PersonalizedFeedbackRecord.
        company_id: UUID da empresa (multi-tenant).

    Returns:
        Dict com { feedback_id, status, channel, success }
    """
    async def _run() -> dict:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from app.domains.communication.services.email_service import MailgunEmailService
        from app.domains.cv_screening.services.personalized_feedback_service import (
            PersonalizedFeedbackRecord,
            PersonalizedFeedbackStatus,
            personalized_feedback_service,
        )

        email_service = MailgunEmailService()

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(PersonalizedFeedbackRecord).where(
                    PersonalizedFeedbackRecord.id == feedback_id
                )
            )
            record = result.scalar_one_or_none()

            if not record:
                return {"feedback_id": feedback_id, "status": "not_found", "success": False}

            if record.status not in (
                PersonalizedFeedbackStatus.APPROVED.value,
                PersonalizedFeedbackStatus.EDITED.value,
                PersonalizedFeedbackStatus.FAILED.value,
            ):
                return {"feedback_id": feedback_id, "status": record.status, "success": False, "reason": "not_approved"}

            subject = record.edited_subject or record.subject
            body_text = record.edited_body or record.body_text
            body_html = record.body_html

            from app.shared.compliance.fairness_guard import FairnessGuard
            fg = FairnessGuard()
            content_to_check = body_text or ""
            fg_result = fg.check(content_to_check)
            if fg_result.is_blocked:
                logger.warning(
                    "feedback.auto_send: FairnessGuard BLOCKED id=%s category=%s terms=%s",
                    feedback_id, fg_result.category, fg_result.blocked_terms,
                )
                await personalized_feedback_service.mark_as_failed(
                    feedback_id=feedback_id,
                    reason=f"FairnessGuard blocked: {fg_result.category} — {fg_result.blocked_terms}",
                    db=db,
                )
                return {
                    "feedback_id": feedback_id,
                    "status": "blocked",
                    "reason": "fairness_guard",
                    "category": fg_result.category,
                    "success": False,
                }

            send_result = {}
            channel_used = record.channel or "email"

            if record.candidate_email and channel_used in ("email", "both"):
                email_result = await email_service.send_email(
                    to_email=record.candidate_email,
                    to_name=record.candidate_name or None,
                    subject=subject,
                    body=body_text or "",
                    body_html=body_html or f"<p>{body_text}</p>",
                    categories=["rejection_feedback", "auto_send"],
                    metadata={
                        "feedback_id": feedback_id,
                        "company_id": company_id,
                        "template_id": f"feedback:{record.tone}:{record.wsi_classification}",
                    },
                )
                sg_message_id = getattr(email_result, "message_id", None)
                send_result["email"] = {
                    "success": email_result.success if hasattr(email_result, "success") else True,
                    "message_id": sg_message_id,
                }
                if sg_message_id:
                    from datetime import datetime as dt_util

                    from app.domains.communication.models.message_queue import MessageQueue as MQModel
                    mq_entry = MQModel(
                        company_id=company_id,
                        candidate_id=record.candidate_id or "",
                        candidate_name=record.candidate_name or "",
                        candidate_email=record.candidate_email,
                        vacancy_id=record.job_id,
                        vacancy_title=record.job_title,
                        channel="email",
                        message_type="rejection_feedback",
                        subject=subject,
                        body_text=body_text,
                        body_html=body_html,
                        status="sent",
                        provider_message_id=sg_message_id,
                        sent_at=dt_util.utcnow(),
                        created_by="feedback_auto_send",
                        extra_data={
                            "sg_message_id": sg_message_id,
                            "feedback_id": feedback_id,
                            "template_id": f"feedback:{record.tone}:{record.wsi_classification}",
                            "source": "feedback_auto_send",
                        },
                    )
                    db.add(mq_entry)
                    await db.commit()
                    logger.info(
                        "feedback.auto_send: MessageQueue created id=%s sg_id=%s",
                        mq_entry.id, sg_message_id,
                    )

            if record.candidate_phone and channel_used in ("whatsapp", "both"):
                from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher
                dispatcher = CommunicationDispatcher()
                msg = record.whatsapp_message or body_text[:500]
                send_result["whatsapp"] = dispatcher.send_whatsapp(
                    to_phone=record.candidate_phone,
                    message=msg,
                )

            any_success = any(r.get("success") for r in send_result.values())

            if any_success:
                await personalized_feedback_service.mark_as_sent(
                    feedback_id=feedback_id,
                    channel=channel_used,
                    send_result=send_result,
                    db=db,
                )
            else:
                await personalized_feedback_service.mark_as_failed(
                    feedback_id=feedback_id,
                    reason="all_channels_failed",
                    send_result=send_result,
                    db=db,
                )

            try:
                from app.shared.intelligence.template_learning import template_learning_service
                template_learning_service.record_send(
                    company_id=company_id,
                    template_id=f"feedback:{record.tone}:{record.wsi_classification}",
                )
            except Exception:
                pass

            logger.info(
                "feedback.auto_send: id=%s channel=%s success=%s",
                feedback_id, channel_used, any_success,
            )
            return {
                "feedback_id": feedback_id,
                "status": "sent" if any_success else "failed",
                "channel": channel_used,
                "success": any_success,
                "results": {k: {"success": v.get("success"), "message_id": v.get("message_id")} for k, v in send_result.items()},
            }

    span = _celery_span("celery.task_start", "feedback.auto_send")
    span.set_attribute("feedback_id", feedback_id)
    span.set_attribute("company_id", company_id)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "feedback.auto_send")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "feedback.auto_send", exc)
        logger.error("feedback.auto_send falhou id=%s: %s", feedback_id, exc)
        _emit_celery_retry("feedback.auto_send", exc, self.request.retries, self.max_retries, 60)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("feedback.auto_send", exc)
        raise self.retry(exc=exc, countdown=60)

async def feedback_process_pending_sends_canonical() -> dict:
    """Sprint 11.3 Batch 2.5+ (2026-05-24) — canonical async function for
    pending feedback safety net.

    Finds APPROVED/EDITED feedback records not yet sent AND dispatches
    via feedback_auto_send_canonical(...) direct (no Celery .delay).

    Replaces the broken .delay() chain since Celery não está deployado
    em produção Replit (Sprint 4.4 audit).

    Returns:
        Dict com { scanned, dispatched, errors }
    """
    from sqlalchemy import and_, or_, select
    from sqlalchemy import text as sa_text

    from app.core.database import AsyncSessionLocal
    from app.domains.cv_screening.services.personalized_feedback_service import (
        PersonalizedFeedbackRecord,
        PersonalizedFeedbackStatus,
    )

    dispatched = 0
    errors = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PersonalizedFeedbackRecord.id, PersonalizedFeedbackRecord.company_id).where(
                or_(
                    PersonalizedFeedbackRecord.status == PersonalizedFeedbackStatus.APPROVED.value,
                    PersonalizedFeedbackRecord.status == PersonalizedFeedbackStatus.EDITED.value,
                    and_(
                        PersonalizedFeedbackRecord.status == PersonalizedFeedbackStatus.FAILED.value,
                        sa_text(
                            "COALESCE(extra_data->>'failure_type', 'transient') != 'policy_blocked'"
                        ),
                    ),
                ),
                PersonalizedFeedbackRecord.sent_at.is_(None),
            ).limit(50)
        )
        rows = result.fetchall()

        for row in rows:
            try:
                # Sprint 11.3 Batch 2.5+: call canonical direct, NÃO .delay()
                # (Celery não deployado em Replit prod)
                await feedback_auto_send_canonical(
                    feedback_id=str(row.id),
                    company_id=str(row.company_id),
                )
                dispatched += 1
            except Exception as exc:
                errors += 1
                logger.warning(
                    "feedback.process_pending_sends canonical: dispatch failed id=%s: %s",
                    row.id, exc,
                )

    logger.info(
        "feedback.process_pending_sends canonical: scanned=%d dispatched=%d errors=%d",
        len(rows), dispatched, errors,
    )
    return {"scanned": len(rows), "dispatched": dispatched, "errors": errors}


@celery_app.task(base=TenantAwareTask, name="feedback.process_pending_sends", bind=True, max_retries=2)
def feedback_process_pending_sends_task(self) -> dict:
    """
    Batch process: finds approved feedback records not yet sent and dispatches auto_send.

    Safety net for any feedback that was approved but auto_send was not triggered.
    Runs every 2 hours via Celery Beat.

    Returns:
        Dict com { dispatched, skipped, errors }
    """
    async def _run() -> dict:
        from sqlalchemy import or_, select

        from app.core.database import AsyncSessionLocal
        from app.domains.cv_screening.services.personalized_feedback_service import (
            PersonalizedFeedbackRecord,
            PersonalizedFeedbackStatus,
        )

        dispatched = 0

        async with AsyncSessionLocal() as db:
            from sqlalchemy import and_
            from sqlalchemy import text as sa_text
            result = await db.execute(
                select(PersonalizedFeedbackRecord.id, PersonalizedFeedbackRecord.company_id).where(
                    or_(
                        PersonalizedFeedbackRecord.status == PersonalizedFeedbackStatus.APPROVED.value,
                        PersonalizedFeedbackRecord.status == PersonalizedFeedbackStatus.EDITED.value,
                        and_(
                            PersonalizedFeedbackRecord.status == PersonalizedFeedbackStatus.FAILED.value,
                            sa_text(
                                "COALESCE(extra_data->>'failure_type', 'transient') != 'policy_blocked'"
                            ),
                        ),
                    ),
                    PersonalizedFeedbackRecord.sent_at.is_(None),
                ).limit(50)
            )
            rows = result.fetchall()

            for row in rows:
                try:
                    feedback_auto_send_task.delay(str(row.id), str(row.company_id))
                    dispatched += 1
                except Exception as exc:
                    logger.warning("feedback.process_pending_sends: dispatch failed id=%s: %s", row.id, exc)

        logger.info("feedback.process_pending_sends: dispatched=%d", dispatched)
        return {"dispatched": dispatched}

    span = _celery_span("celery.task_start", "feedback.process_pending_sends")

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "feedback.process_pending_sends")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "feedback.process_pending_sends", exc)
        logger.error("feedback.process_pending_sends falhou: %s", exc)
        _emit_celery_retry("feedback.process_pending_sends", exc, self.request.retries, self.max_retries, 120)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("feedback.process_pending_sends", exc)
        raise self.retry(exc=exc, countdown=120)

