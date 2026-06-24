"""Celery tasks: communication (Fase 7)."""
import asyncio
import re
from datetime import UTC

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
    _emit_celery_retry, _emit_dlq_push,
)

@celery_app.task(base=TenantAwareTask, name="communication.email.send_bulk", bind=True, max_retries=5)
def send_bulk_email_task(self, email_data: dict, company_id: str) -> dict:
    """
    Envio de email em massa com controle de rate limiting e retry.

    Para listas grandes (> 100 destinatários), usa envio em chunks via Mailgun.
    Retries com exponential backoff em caso de falha de API.

    Args:
        email_data: Dict com recipients, template_id, variables, subject.
        company_id: ID da empresa (para auditoria LGPD).

    Returns:
        Dict com { sent, failed, queued, message_ids }
    """
    from app.core.database import AsyncSessionLocal

    async def _run() -> dict:
        from app.domains.communication.services.consent_gate import CommunicationConsentGate
        from app.enums.communication import MessageChannel
        from app.shared.channels.adapters.email_adapter import email_adapter

        async with AsyncSessionLocal() as db:
            # LGPD: check consent per candidate, skip those without
            gate = CommunicationConsentGate(db)
            recipients = email_data.get("recipients", [])
            allowed, blocked, skipped = await gate.check_batch(
                [{"candidate_id": r.get("candidate_id", r.get("id", "")), **r} for r in recipients],
                company_id,
                MessageChannel.EMAIL,
                is_marketing=True,
            )
            if skipped:
                logger.warning(
                    "[BulkEmail] %d/%d recipients blocked by consent gate (company=%s)",
                    skipped, len(recipients), company_id,
                )
            if not allowed:
                return {"sent": 0, "failed": 0, "skipped_consent": skipped, "message_ids": []}

            return await email_adapter.send_bulk(
                recipients=allowed,
                template_id=email_data.get("template_id"),
                subject=email_data.get("subject", ""),
                body=email_data.get("body", ""),
                variables=email_data.get("variables", {}),
                company_id=company_id,
                db=db,
            )

    span = _celery_span("celery.task_start", "communication.email.send_bulk")
    span.set_attribute("company_id", company_id)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "communication.email.send_bulk")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "communication.email.send_bulk", exc)
        countdown = 30 * (2 ** self.request.retries)
        logger.error("communication.email.send_bulk falhou company=%s (retry %d): %s",
                     company_id, self.request.retries, exc)
        _emit_celery_retry("communication.email.send_bulk", exc, self.request.retries, self.max_retries, countdown)
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("communication.email.send_bulk", exc)
        raise self.retry(exc=exc, countdown=countdown)

@celery_app.task(base=TenantAwareTask, name="briefing.send_daily", bind=True, max_retries=2)
def send_daily_briefing_task(self) -> dict:
    """
    Gera e envia briefing diário para todos os recrutadores ativos.

    Agendado diariamente às 06h Brasília via Celery Beat (beat_schedule: briefing-daily).
    Para cada recrutador ativo:
      1. Gera briefing via BriefingService (com cache Redis TTL=6h)
      2. Dispara notificação Bell (in-app) via NotificationService
      3. Dispara email de resumo se recrutador tiver email ativo

    Returns:
        Dict com { sent, skipped, errors }
    """
    async def _run() -> dict:
        from app.auth.models import User
        from app.core.database import AsyncSessionLocal
        from app.shared.services.briefing_service import BriefingService

        briefing_service = BriefingService()
        sent = 0
        skipped = 0
        errors = 0

        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            # Batch global por design: cada BriefingService.generate_daily_briefing()
            # é company-scoped internamente via user.company_id.
            # Não há vazamento cross-tenant pois o briefing é gerado por user_id
            # e a notificação Bell é roteada para o próprio usuário.
            result = await db.execute(
                select(User).where(User.is_active == True)  # noqa: E712
            )
            users = result.scalars().all()

            for user in users:
                try:
                    # WT-2022 P0.TASK: resolve company_id per user (multi-tenancy)
                    user_company_id = str(user.company_id) if hasattr(user, "company_id") and user.company_id else None
                    briefing = await briefing_service.generate_daily_briefing(
                        user_id=str(user.id), db=db, company_id=user_company_id
                    )

                    # Bell notification — best-effort
                    try:
                        from app.services.notification_service import notification_service
                        urgent_count = len(briefing.get("urgent_actions", []))
                        title = "☀️ Briefing do dia"
                        body = (
                            f"{urgent_count} ações urgentes pendentes"
                            if urgent_count > 0
                            else "Seu pipeline está atualizado"
                        )
                        await notification_service.send_notification(
                            user_id=str(user.id),
                            company_id=str(user.company_id) if hasattr(user, "company_id") else None,
                            channel="bell",
                            title=title,
                            body=body,
                            data={"type": "daily_briefing", "briefing_date": briefing.get("date")},
                            db=db,
                        )
                    except Exception as notif_exc:
                        logger.warning(
                            "briefing.send_daily: notificação falhou user=%s: %s",
                            user.id, notif_exc,
                        )

                    # Audit: briefing enviado com sucesso
                    logger.info(
                        "[briefing.send_daily] sent user=%s company=%s urgent=%d",
                        user.id,
                        getattr(user, "company_id", None),
                        len(briefing.get("urgent_actions", [])),
                    )
                    sent += 1
                except Exception as exc:
                    logger.error(
                        "briefing.send_daily: erro para user=%s: %s", user.id, exc
                    )
                    errors += 1

        logger.info(
            "[briefing.send_daily] batch complete sent=%d skipped=%d errors=%d",
            sent, skipped, errors,
        )
        return {"sent": sent, "skipped": skipped, "errors": errors}

    span = _celery_span("celery.task_start", "briefing.send_daily")

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "briefing.send_daily")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "briefing.send_daily", exc)
        logger.error("briefing.send_daily falhou: %s", exc)
        _emit_celery_retry("briefing.send_daily", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("briefing.send_daily", exc)
        raise self.retry(exc=exc, countdown=300)

@celery_app.task(base=TenantAwareTask, name="digest.send_weekly", bind=True, max_retries=2)
def send_weekly_digest_task(self) -> dict:
    """
    Envia weekly digest consolidado a todos os recrutadores ativos.

    Agrega dados de PredictiveAnalytics, FairnessGuard, ABTesting e LearningLoop.
    Entrega via Teams (Adaptive Card), Chat (proativo) e Bell (notificação).

    Agendado: segundas-feiras 08h Brasília (11h UTC) via Celery Beat.
    Pode ser disparado manualmente via POST /api/v1/digest/weekly/send-all.
    """
    import asyncio

    async def _run() -> dict:
        from lia_config.database import AsyncSessionLocal

        from app.domains.analytics.services.weekly_digest_service import WeeklyDigestService

        svc = WeeklyDigestService()
        async with AsyncSessionLocal() as db:
            return await svc.send_to_all_recruiters(db)

    span = _celery_span("celery.task_start", "digest.send_weekly")

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "digest.send_weekly")
        logger.info(
            "[Celery] digest.send_weekly completed: sent=%s skipped=%s errors=%s",
            result.get("sent", 0),
            result.get("skipped", 0),
            result.get("errors", 0),
        )
        return result
    except Exception as exc:
        _finish_celery_failure(span, "digest.send_weekly", exc)
        logger.error("[Celery] digest.send_weekly failed: %s", exc)
        _emit_celery_retry("digest.send_weekly", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("digest.send_weekly", exc)
        raise self.retry(exc=exc, countdown=300)



@celery_app.task(base=TenantAwareTask, name="communication.process_queued_messages", bind=True, max_retries=2)
def process_queued_messages_task(self) -> dict:
    """
    Processa mensagens na fila QUEUED que estavam fora da janela de envio.

    GAP-07-001: esta task NÃO tinha caller no Celery Beat — emails QUEUED
    ficavam presos indefinidamente. Agora roda a cada 5 min via beat_schedule.

    Respeita sending hours per-tenant (LGPD Art. 7). Fora da janela global,
    retorna early sem processar. Dentro da janela, re-checa per-tenant.
    """
    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.domains.communication.services.communication_service import (
            get_communication_service,
        )

        svc = get_communication_service()
        async with AsyncSessionLocal() as db:
            return await svc.process_queued_messages(db=db)

    span = _celery_span("celery.task_start", "communication.process_queued_messages")

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "communication.process_queued_messages")
        processed = result.get("processed", 0)
        if processed > 0:
            logger.info(
                "[Celery] communication.process_queued_messages: processed=%d total_queued=%d skipped_tenant=%d",
                processed,
                result.get("total_queued", 0),
                result.get("skipped_tenant_hours", 0),
            )
        return result
    except Exception as exc:
        _finish_celery_failure(span, "communication.process_queued_messages", exc)
        logger.error("communication.process_queued_messages falhou (retry %d): %s", self.request.retries, exc)
        _emit_celery_retry("communication.process_queued_messages", exc, self.request.retries, self.max_retries, 60)
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("communication.process_queued_messages", exc)
        raise self.retry(exc=exc, countdown=60)
