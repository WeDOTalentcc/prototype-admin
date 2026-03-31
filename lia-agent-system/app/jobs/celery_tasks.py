"""
Celery Task Definitions

Tasks registradas:
  - drift.run_batch              — drift check em todas as empresas ativas
  - agents.wsi_interview.start   — inicia entrevista WSI em background
  - agents.triagem.run           — triagem curricular em lote
  - agents.sourcing.search       — busca de candidatos via Pearch (async)
  - communication.email.send_bulk — envio de email em massa
  - briefing.send_daily          — envia briefing diário a todos os recrutadores ativos (P3-1)
  - followup.process_pending     — reenvio automático de convites WSI não abertos (Gap A / I1)
  - wsi.check_abandoned          — detecção de sessões WSI abandonadas + lembretes (Gap B / I3)
  - feedback.auto_send           — envio automático de feedback aprovado (I6)
  - feedback.process_pending_sends — batch safety net para feedback aprovado não enviado (I6)
  - ragas.evaluate_batch         — avaliação RAGAS de qualidade LLM (ACH-027)
"""
import asyncio

from app.core.celery_app import celery_app
from app.shared.pii_masking import get_masked_logger

logger = get_masked_logger(__name__)


@celery_app.task(name="drift.run_batch", bind=True, max_retries=3)
def run_drift_batch_task(self, notify_user_id: str | None = None) -> dict:
    """
    Executa drift check para todas as empresas ativas.

    Celery wrapper assíncrono para run_drift_check_all_companies.
    Pode ser agendado via Celery Beat ou chamado manualmente.

    Args:
        notify_user_id: Opcional. ID do usuário que receberá alertas Bell+Teams.

    Returns:
        Dict com { checked, drifted, errors }

    Raises:
        Retry automático em caso de erro (max_retries=3).
    """
    from app.jobs.drift_job import run_drift_check_all_companies
    from app.core.database import AsyncSessionLocal

    async def _run() -> dict:
        async with AsyncSessionLocal() as db:
            return await run_drift_check_all_companies(db, notify_user_id)

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("drift.run_batch falhou: %s", exc)
        raise self.retry(exc=exc, countdown=60)


# ---------------------------------------------------------------------------
# F5 — Tasks para operações agênticas de longa duração
# ---------------------------------------------------------------------------

@celery_app.task(name="agents.wsi_interview.start", bind=True, max_retries=3)
def start_wsi_interview_task(self, request_data: dict, company_id: str) -> dict:
    """
    Inicia entrevista WSI em background.

    Operações longas (sessões de 30-120 min) não devem bloquear o request HTTP.
    O cliente recebe um job_id e acompanha progresso via WebSocket /ws/jobs/{job_id}.

    Args:
        request_data: Dict com candidate_id, job_id, interview_type, context.
        company_id: ID da empresa (multi-tenant).

    Returns:
        Dict com { status, interview_id, transcript_url }
    """
    from app.core.database import AsyncSessionLocal

    async def _run() -> dict:
        from app.domains.interview_scheduling.services import interview_service
        async with AsyncSessionLocal() as db:
            return await interview_service.start_wsi_session(
                db=db,
                candidate_id=request_data["candidate_id"],
                job_id=request_data["job_id"],
                interview_type=request_data.get("interview_type", "wsi_full"),
                company_id=company_id,
                context=request_data.get("context", {}),
            )

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.wsi_interview.start falhou company=%s: %s", company_id, exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="agents.triagem.run", bind=True, max_retries=3)
def run_triagem_task(self, candidate_ids: list, job_id: str, company_id: str) -> dict:
    """
    Triagem curricular em lote — processa N candidatos em paralelo.

    Para lotes grandes (> 20 candidatos), pode levar 2-10 minutos.
    Emite progresso via WebSocket a cada candidato processado.

    Args:
        candidate_ids: Lista de IDs de candidatos a triar.
        job_id: ID da vaga.
        company_id: ID da empresa.

    Returns:
        Dict com { processed, approved, rejected, review, ranking }
    """
    async def _run() -> dict:
        from app.domains.cv_screening.services.cv_screening_batch_service import run_batch
        return await run_batch(
            candidate_ids=candidate_ids,
            job_id=job_id,
            company_id=company_id,
        )

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.triagem.run falhou job=%s company=%s: %s", job_id, company_id, exc)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="agents.sourcing.search", bind=True, max_retries=3)
def run_sourcing_task(self, criteria: dict, job_id: str, company_id: str) -> dict:
    """
    Busca de candidatos via Pearch AI e banco interno.

    Chamadas ao Pearch podem levar 30-120s dependendo do perfil.
    O cliente recebe resultado completo via WebSocket quando concluído.

    Args:
        criteria: Dict com skills, location, seniority, salary_range, etc.
        job_id: ID da vaga para contexto.
        company_id: ID da empresa.

    Returns:
        Dict com { candidates: [...], total, sources, search_time_ms }
    """
    from app.core.database import AsyncSessionLocal

    async def _run() -> dict:
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        agent = SourcingReActAgent()
        async with AsyncSessionLocal() as db:
            return await agent.search_candidates(
                criteria=criteria,
                job_id=job_id,
                company_id=company_id,
                db=db,
            )

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.sourcing.search falhou job=%s: %s", job_id, exc)
        raise self.retry(exc=exc, countdown=45)


@celery_app.task(name="agents.wizard.process_async", bind=True, max_retries=2, queue="vagas_normal")
def wizard_process_async_task(self, message: str, context: dict, session_id: str, company_id: str, user_id: str) -> dict:
    """
    Processa mensagem do Wizard em background para operações longas.

    Usado quando a criação/atualização de vaga envolve chamadas externas
    (benchmark salarial, busca de templates, geração de JD com LLM).

    Args:
        message: Mensagem do usuário.
        context: Contexto da sessão (stage, collected_data).
        session_id: ID da sessão WS para devolver resultado.
        company_id: ID da empresa.
        user_id: ID do usuário.

    Returns:
        AgentOutput serializado como dict.
    """
    from app.shared.agents.agent_interface import AgentInput

    async def _run() -> dict:
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
        agent = WizardReActAgent()
        agent_input = AgentInput(
            message=message,
            context=context,
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
        )
        output = await agent.process(agent_input)
        return output.dict()

    try:
        result = asyncio.run(_run())
        # Notificar via WS se sessão ainda conectada
        try:
            from app.api.v1.ws_manager import ws_manager
            import asyncio as _asyncio
            loop = _asyncio.new_event_loop()
            loop.run_until_complete(ws_manager.send_to_session(session_id, {
                "type": "message",
                "content": result.get("message", ""),
                "confidence": result.get("confidence", 0.7),
                "source": "celery_task",
            }))
            loop.close()
        except Exception:
            pass
        return result
    except Exception as exc:
        logger.error("agents.wizard.process_async falhou session=%s: %s", session_id, exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="agents.pipeline.transition_async", bind=True, max_retries=2, queue="vagas_normal")
def pipeline_transition_async_task(self, transition_data: dict, session_id: str, company_id: str, user_id: str) -> dict:
    """
    Processa transição de pipeline em background.

    Usado para transições que envolvem ações automáticas complexas
    (geração de feedback, envio de comunicações, atualização de CRM).

    Args:
        transition_data: Dict com candidate_id, job_id, from_stage, to_stage, action_behavior.
        session_id: ID da sessão WS.
        company_id: ID da empresa.
        user_id: ID do usuário.
    """
    from app.shared.agents.agent_interface import AgentInput

    async def _run() -> dict:
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        agent = PipelineTransitionAgent()
        agent_input = AgentInput(
            message=f"Executar transição de {transition_data.get('from_stage')} para {transition_data.get('to_stage')}",
            context=transition_data,
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
        )
        output = await agent.process(agent_input)
        return output.dict()

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.pipeline.transition_async falhou session=%s: %s", session_id, exc)
        raise self.retry(exc=exc, countdown=20)


# ---------------------------------------------------------------------------
# F5 — Tasks de execução de agentes via fila (Phase 4.4)
# Padrão: recebem agent_input_dict + session_id + company_id + domain
# Resultado publicado via RabbitMQ reply_to para o WS Gateway
# ---------------------------------------------------------------------------

def _build_agent_input(agent_input_dict: dict):
    """Constrói AgentInput a partir de dict serializado."""
    from app.shared.agents.agent_interface import AgentInput
    return AgentInput(**agent_input_dict)


async def _publish_response(session_id: str, reply_to: str, output_dict: dict, domain: str) -> None:
    """Publica resultado do agente na fila de resposta (reply_to)."""
    try:
        from app.shared.messaging.rabbitmq_producer import rabbitmq_producer
        await rabbitmq_producer.publish_agent_response(
            response_data={
                "session_id": session_id,
                "content": output_dict.get("message", ""),
                "confidence": output_dict.get("confidence", 0.7),
                "actions": [a if isinstance(a, dict) else a for a in output_dict.get("actions", [])],
                "navigation": output_dict.get("navigation"),
                "state_updates": output_dict.get("state_updates", {}),
                "domain": domain,
                "error": output_dict.get("error"),
                "done": True,
            },
            reply_to=reply_to,
        )
    except Exception as exc:
        logger.warning("_publish_response failed session=%s: %s", session_id, exc)


@celery_app.task(name="agents.wizard.execute", bind=True, max_retries=2, queue="vagas_normal")
def execute_wizard_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "wizard", reply_to: str = "") -> dict:
    """Executa WizardReActAgent em background (vaga, templates, JD)."""
    async def _run() -> dict:
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
        agent = WizardReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.wizard.execute falhou session=%s: %s", session_id, exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="agents.pipeline.execute", bind=True, max_retries=2, queue="evaluation_normal")
def execute_pipeline_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "pipeline", reply_to: str = "") -> dict:
    """Executa PipelineReActAgent em background (pipeline, kanban, triagem)."""
    async def _run() -> dict:
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
        agent = PipelineReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.pipeline.execute falhou session=%s: %s", session_id, exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="agents.sourcing.execute", bind=True, max_retries=2, queue="sourcing_high")
def execute_sourcing_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "sourcing", reply_to: str = "") -> dict:
    """Executa SourcingReActAgent em background (busca Pearch, 30-120s)."""
    async def _run() -> dict:
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        agent = SourcingReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.sourcing.execute falhou session=%s: %s", session_id, exc)
        raise self.retry(exc=exc, countdown=45)


@celery_app.task(name="agents.screening.execute", bind=True, max_retries=2, queue="evaluation_normal")
def execute_screening_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "cv_screening", reply_to: str = "") -> dict:
    """Executa triagem curricular / WSI em background."""
    async def _run() -> dict:
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
        agent = PipelineReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.screening.execute falhou session=%s: %s", session_id, exc)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="agents.kanban.execute", bind=True, max_retries=2, queue="vagas_normal")
def execute_kanban_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "kanban", reply_to: str = "") -> dict:
    """Executa KanbanReActAgent / TalentReActAgent em background."""
    async def _run() -> dict:
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        agent = KanbanReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.kanban.execute falhou session=%s: %s", session_id, exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="agents.policy.execute", bind=True, max_retries=2, queue="onboarding_low")
def execute_policy_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "policy", reply_to: str = "") -> dict:
    """Executa PolicyReActAgent em background (compliance, políticas)."""
    async def _run() -> dict:
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        agent = PolicyReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.policy.execute falhou session=%s: %s", session_id, exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="agents.automation.execute", bind=True, max_retries=2, queue="vagas_normal")
def execute_automation_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "automation", reply_to: str = "") -> dict:
    """Executa AutomationReActAgent em background (decomposição de tarefas)."""
    async def _run() -> dict:
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        agent = AutomationReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("agents.automation.execute falhou session=%s: %s", session_id, exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="audit.apply_lifecycle_policy", bind=True, max_retries=3)
def apply_audit_lifecycle_policy(self) -> dict:
    """
    Aplica política de retenção S3 no bucket de auditoria.
    Executada 1x por mês via Celery Beat.
    Idempotente.
    """
    import asyncio
    from lia_audit.audit_storage import get_audit_storage

    try:
        storage = get_audit_storage()
        result = asyncio.run(storage.apply_lifecycle_policy())
        logger.info(f"[audit.lifecycle] Applied: {result}")
        return {"applied": result}
    except Exception as exc:
        logger.error(f"[audit.lifecycle] Error: {exc}")
        raise self.retry(exc=exc, countdown=3600)


@celery_app.task(name="lgpd.run_cleanup_daily", bind=True, max_retries=3)
def run_lgpd_cleanup_task(self, dry_run: bool = False) -> dict:
    """
    Executa limpeza de dados LGPD para todas as empresas.

    Aplica políticas de retenção (LGPD Art. 16):
      - 90 dias: candidatos rejeitados / retirados (dados operacionais)
      - 180 dias: dados de avaliação e triagem
      - 365 dias: logs de auditoria e compliance

    Agendado diariamente às 02h Brasília via Celery Beat (beat_schedule: lgpd-cleanup-daily).

    Args:
        dry_run: Se True, simula sem deletar (padrão: False em produção).

    Returns:
        Dict com { dry_run, ran_at, candidates_deleted,
                   vacancy_candidates_deleted, ai_consumption_deleted, errors }
    """
    async def _run() -> dict:
        from app.services.lgpd_cleanup_service import run_cleanup
        return await run_cleanup(dry_run=dry_run)

    try:
        result = asyncio.run(_run())
        logger.info("lgpd.run_cleanup_daily concluído: %s", result)
        return result
    except Exception as exc:
        logger.error("lgpd.run_cleanup_daily falhou: %s", exc)
        raise self.retry(exc=exc, countdown=300)  # retry em 5 min


@celery_app.task(name="communication.email.send_bulk", bind=True, max_retries=5)
def send_bulk_email_task(self, email_data: dict, company_id: str) -> dict:
    """
    Envio de email em massa com controle de rate limiting e retry.

    Para listas grandes (> 100 destinatários), usa envio em chunks via SendGrid.
    Retries com exponential backoff em caso de falha de API.

    Args:
        email_data: Dict com recipients, template_id, variables, subject.
        company_id: ID da empresa (para auditoria LGPD).

    Returns:
        Dict com { sent, failed, queued, message_ids }
    """
    from app.core.database import AsyncSessionLocal

    async def _run() -> dict:
        from app.shared.channels.adapters.email_adapter import email_adapter
        async with AsyncSessionLocal() as db:
            return await email_adapter.send_bulk(
                recipients=email_data["recipients"],
                template_id=email_data.get("template_id"),
                subject=email_data.get("subject", ""),
                body=email_data.get("body", ""),
                variables=email_data.get("variables", {}),
                company_id=company_id,
                db=db,
            )

    try:
        return asyncio.run(_run())
    except Exception as exc:
        # Exponential backoff: 30s, 60s, 120s, 240s, 480s
        countdown = 30 * (2 ** self.request.retries)
        logger.error("communication.email.send_bulk falhou company=%s (retry %d): %s",
                     company_id, self.request.retries, exc)
        raise self.retry(exc=exc, countdown=countdown)


# ---------------------------------------------------------------------------
# P3-1 — Briefing diário automático para recrutadores
# ---------------------------------------------------------------------------

@celery_app.task(name="briefing.send_daily", bind=True, max_retries=2)
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
        from app.core.database import AsyncSessionLocal
        from app.services.briefing_service import BriefingService
        from app.auth.models import User

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
                    briefing = await briefing_service.generate_daily_briefing(
                        user_id=str(user.id), db=db
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
                        getattr(user, "company_id", "unknown"),
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

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("briefing.send_daily falhou: %s", exc)
        raise self.retry(exc=exc, countdown=300)


# ---------------------------------------------------------------------------
# Gap A — Follow-up automático de convites WSI não abertos (Passo 6B Alpha 1)
# ---------------------------------------------------------------------------

@celery_app.task(name="followup.process_pending", bind=True, max_retries=2)
def followup_process_pending_task(self) -> dict:
    """
    Reenvia convites WSI não abertos.

    Agendado a cada hora via Celery Beat (beat_schedule: followup-check-hourly).
    Após 7 reenvios sem resposta: marca candidato como 'sem_resposta' e notifica recruiter.

    Returns:
        Dict com { sent, skipped, errors, marked_no_response }
    """
    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.jobs.followup_service import process_email_followups

        async with AsyncSessionLocal() as db:
            return await process_email_followups(db)

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("followup.process_pending falhou: %s", exc)
        raise self.retry(exc=exc, countdown=120)


# ---------------------------------------------------------------------------
# Gap B — Triagem WSI abandonada / timeout (Passo 7A Alpha 1)
# ---------------------------------------------------------------------------

@celery_app.task(name="wsi.check_abandoned", bind=True, max_retries=2)
def wsi_check_abandoned_task(self) -> dict:
    """
    Detecta sessões WSI abandonadas e envia lembretes.

    Agendado a cada 4h via Celery Beat (beat_schedule: wsi-abandoned-check).
    1º lembrete (48h): email ao candidato.
    2º lembrete (96h): email ao candidato + Bell+Teams ao recruiter.

    Returns:
        Dict com { first_reminders, second_reminders, errors }
    """
    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.jobs.wsi_abandoned_service import check_abandoned_sessions

        async with AsyncSessionLocal() as db:
            return await check_abandoned_sessions(db)

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("wsi.check_abandoned falhou: %s", exc)
        raise self.retry(exc=exc, countdown=300)



@celery_app.task(name="feedback.auto_send", bind=True, max_retries=3)
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
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import select
        from app.domains.cv_screening.services.personalized_feedback_service import (
            PersonalizedFeedbackRecord,
            PersonalizedFeedbackStatus,
            personalized_feedback_service,
        )
        from app.domains.communication.services.email_service import SendGridEmailService

        email_service = SendGridEmailService()

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
                    },
                )
                send_result["email"] = {
                    "success": email_result.success if hasattr(email_result, "success") else True,
                    "message_id": getattr(email_result, "message_id", None),
                }

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

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("feedback.auto_send falhou id=%s: %s", feedback_id, exc)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="feedback.process_pending_sends", bind=True, max_retries=2)
def feedback_process_pending_sends_task(self) -> dict:
    """
    Batch process: finds approved feedback records not yet sent and dispatches auto_send.

    Safety net for any feedback that was approved but auto_send was not triggered.
    Runs every 2 hours via Celery Beat.

    Returns:
        Dict com { dispatched, skipped, errors }
    """
    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import select, or_
        from app.domains.cv_screening.services.personalized_feedback_service import (
            PersonalizedFeedbackRecord,
            PersonalizedFeedbackStatus,
        )

        dispatched = 0

        async with AsyncSessionLocal() as db:
            from sqlalchemy import and_, text as sa_text
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

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("feedback.process_pending_sends falhou: %s", exc)
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(name="ragas.evaluate_batch", bind=True, max_retries=1, queue="evaluation_normal")
def run_ragas_evaluate_batch(self, domain: str = "all", days_back: int = 1) -> dict:
    """
    Avaliação RAGAS em lote das respostas dos agentes — ACH-027.

    Carrega samples de audit_decisions das últimas `days_back` horas,
    executa avaliação RAGAS/heurística e persiste em agent_ragas_evaluations.

    Agendado diariamente às 03h UTC via Celery Beat (beat_schedule: ragas-evaluate-daily).

    Returns:
        Dict com { evaluated, skipped, errors, domain }
    """
    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.services.ragas_evaluation_service import ragas_evaluation_service, RAGASEvaluationInput
        from sqlalchemy import text
        from datetime import timedelta, datetime

        since = datetime.utcnow() - timedelta(days=days_back)
        evaluated = 0
        skipped = 0
        errors = 0

        async with AsyncSessionLocal() as db:
            # Busca decisions recentes para avaliação
            domain_filter = "" if domain == "all" else "AND domain = :domain"
            result = await db.execute(
                text(
                    f"""
                    SELECT id, session_id, domain, agent_name,
                           reasoning, decision, metadata
                    FROM audit_decisions
                    WHERE created_at >= :since
                      {domain_filter}
                    ORDER BY created_at DESC
                    LIMIT 100
                    """
                ),
                {"since": since, "domain": domain} if domain != "all" else {"since": since},
            )
            rows = result.fetchall()

            for row in rows:
                try:
                    reasoning_list = row.reasoning or []
                    answer = " ".join(reasoning_list) if isinstance(reasoning_list, list) else str(reasoning_list)
                    if not answer or len(answer) < 20:
                        skipped += 1
                        continue

                    inp = RAGASEvaluationInput(
                        question=f"decision:{row.decision} domain:{row.domain}",
                        answer=answer,
                        contexts=[],
                        session_id=str(row.session_id or ""),
                        company_id="",
                        domain=str(row.domain or ""),
                        agent_name=str(row.agent_name or ""),
                        metadata={"source": "audit_decisions", "decision_id": str(row.id)},
                    )
                    await ragas_evaluation_service.evaluate(inp, db)
                    evaluated += 1
                except Exception as exc:
                    logger.warning("ragas.evaluate_batch: erro em row %s: %s", row.id, exc)
                    errors += 1

        logger.info(
            "ragas.evaluate_batch: evaluated=%d skipped=%d errors=%d domain=%s",
            evaluated, skipped, errors, domain,
        )
        return {"evaluated": evaluated, "skipped": skipped, "errors": errors, "domain": domain}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("ragas.evaluate_batch falhou: %s", exc)
        raise self.retry(exc=exc, countdown=300)


# ---------------------------------------------------------------------------
# E6 — RAG por Domínio: rebuild de índice de embeddings por domínio
# ---------------------------------------------------------------------------

@celery_app.task(name="rag.rebuild_domain_index")
def rebuild_domain_index_task(domain: str, company_id: str):
    """Celery task to rebuild RAG domain embeddings."""
    import asyncio
    from app.services.domain_embedding_service import domain_embedding_service

    async def _run():
        from lia_config.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            return await domain_embedding_service.rebuild_domain_index(domain, company_id, db)

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.warning("[Celery] rag.rebuild_domain_index failed: %s", exc)
        return 0


# ---------------------------------------------------------------------------
# E9 — Adaptive Routing: recompute domain confidence adjustments per company
# ---------------------------------------------------------------------------

@celery_app.task(name="routing.recompute_adjustments")
def recompute_routing_adjustments(company_id: str) -> dict:
    """Recompute adaptive routing adjustments for a company.

    Computes per-domain error rates from RoutingFeedback (last 30 days) and
    caches the resulting confidence-adjustment factors to Redis (TTL=24h).

    Args:
        company_id: ID da empresa (ou "global" para ajuste global).

    Returns:
        Dict mapping domain → adjustment factor (0.8–1.2).
    """
    async def _run():
        from lia_config.database import AsyncSessionLocal
        from app.services.routing_learning_service import routing_learning_service

        async with AsyncSessionLocal() as db:
            adj = await routing_learning_service.compute_domain_confidence_adjustments(
                company_id, db
            )
            await routing_learning_service.cache_adjustments(company_id, adj)
            return adj

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.warning("[Celery] routing.recompute_adjustments failed: %s", exc)
        return {}


@celery_app.task(name="ml.feedback.process_weights", bind=True, max_retries=2)
def process_ml_feedback_weights_task(self, company_id: str, job_id: str) -> dict:
    """
    Computa pesos adaptativos ML para uma vaga específica (D6 — Feedback Loop).

    Disparado após acúmulo de feedback de recrutadores (hire/reject/override).
    Roda on-demand ou via beat semanal.

    Args:
        company_id: UUID da empresa (multi-tenant)
        job_id: UUID da vaga
    """
    import asyncio

    async def _run() -> dict:
        from lia_config.database import AsyncSessionLocal
        from app.services.ml_feedback_service import MLFeedbackService

        service = MLFeedbackService()
        async with AsyncSessionLocal() as db:
            weights = await service.compute_job_weights(
                db=db, job_id=job_id, company_id=company_id
            )
            logger.info(
                "ml.feedback.process_weights: job=%s company=%s samples=%d",
                job_id, company_id, weights.sample_count,
            )
            return weights.to_dict()

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("ml.feedback.process_weights falhou: %s", exc)
        raise self.retry(exc=exc, countdown=120)


# ---------------------------------------------------------------------------
# E4 — Hot-Reload de Agentes: verifica alterações no agents_registry.yaml
# ---------------------------------------------------------------------------

@celery_app.task(name="agents.registry.check_reload")
def check_agent_registry_reload():
    """Verifica se agents_registry.yaml foi modificado e recarrega o registry.

    Executa a cada 1 minuto via beat schedule. Usa mtime-gating para evitar
    reloads desnecessários (fail-open — nunca bloqueia o worker).
    """
    import asyncio
    from app.core.agent_registry_watcher import agent_registry_watcher

    try:
        reloaded = asyncio.run(agent_registry_watcher.check_and_reload())
        if reloaded:
            logger.info("[Celery] agents_registry.yaml reloaded: %s", reloaded)
        return {"reloaded": reloaded}
    except Exception as exc:
        logger.warning("[Celery] agents.registry.check_reload failed (fail-open): %s", exc)
        return {"reloaded": []}


# ---------------------------------------------------------------------------
# E6 — RAG rebuild: reconstrução diária de todos os índices de domínio
# ---------------------------------------------------------------------------

@celery_app.task(name="rag.rebuild_all_domains")
def rebuild_all_domains_task():
    """Dispara rebuild de embeddings para todos os domínios RAG conhecidos.

    Wrapper que itera os 5 domínios fixos e despacha rebuild_domain_index_task
    para cada. Executado diariamente via beat schedule (04h UTC / 01h Brasília).
    """
    _DOMAINS = ["general", "jobs", "talent", "policy", "company"]
    dispatched = 0
    for domain in _DOMAINS:
        try:
            rebuild_domain_index_task.delay(domain, "global")
            dispatched += 1
        except Exception as exc:
            logger.warning("[Celery] rag.rebuild_all_domains dispatch failed for %s: %s", domain, exc)
    logger.info("[Celery] rag.rebuild_all_domains dispatched %d/%d domains", dispatched, len(_DOMAINS))
    return {"dispatched": dispatched, "domains": _DOMAINS}


# ---------------------------------------------------------------------------
# D6 — ML Feedback: recomputa pesos adaptativos para vagas com feedback recente
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Z4-02 — LTM Compression: comprime episódios antigos para economizar storage
# ---------------------------------------------------------------------------

@celery_app.task(name="memory.compress_old_episodes", bind=True, max_retries=2)
def compress_old_episodes_task(self, company_id: str, domain: str = None, age_days: int = 30) -> dict:
    """
    Z4-02: Comprime episódios LTM > age_days para economizar armazenamento.

    Gera resumo LLM dos episódios antigos, armazena como episódio comprimido
    e marca os originais para purge. Agendado diariamente às 03h UTC.

    Args:
        company_id: UUID da empresa (multi-tenant).
        domain: Domínio específico ou None para todos os domínios.
        age_days: Episódios mais antigos que este número de dias serão comprimidos.

    Returns:
        Dict com { company_id, domain, compressed, purged }
    """
    import asyncio
    from lia_agents_core.long_term_memory import LongTermMemoryService

    async def _run() -> dict:
        service = LongTermMemoryService()
        compressed = 0
        purged = 0

        _DOMAINS = ["sourcing", "pipeline", "kanban", "wizard", "policy", "talent", "screening"]
        domains_to_process = [domain] if domain else _DOMAINS

        for d in domains_to_process:
            try:
                c = await service.compress_old_episodes(company_id, d, age_days)
                compressed += c
            except Exception as exc:
                logger.warning(
                    "[memory.compress] domain=%s company=%s falhou: %s", d, company_id, exc
                )

        # Purge after compression
        try:
            purged = await service.purge_expired(company_id)
        except Exception as exc:
            logger.warning("[memory.compress] purge falhou company=%s: %s", company_id, exc)

        return {"company_id": company_id, "domain": domain, "compressed": compressed, "purged": purged}

    try:
        result = asyncio.run(_run())
        logger.info(
            "[memory.compress] company=%s compressed=%d purged=%d",
            company_id,
            result.get("compressed", 0),
            result.get("purged", 0),
        )
        return result
    except Exception as exc:
        logger.error("memory.compress_old_episodes falhou company=%s: %s", company_id, exc)
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(name="ml.feedback.recompute_active_jobs")
def recompute_active_ml_jobs_task():
    """Recomputa pesos ML adaptativos para vagas com feedback nas últimas 48h.

    Wrapper semanal que consulta vagas com feedback recente e despacha
    process_ml_feedback_weights_task para cada. Fail-open.
    """
    import asyncio

    async def _get_active_jobs():
        from lia_config.database import AsyncSessionLocal
        from datetime import datetime, timedelta
        from sqlalchemy import text

        cutoff = datetime.utcnow() - timedelta(hours=48)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text(
                    "SELECT DISTINCT job_id, company_id FROM recruiter_decision_feedback "
                    "WHERE created_at >= :cutoff LIMIT 200"
                ),
                {"cutoff": cutoff},
            )
            return result.fetchall()

    try:
        rows = asyncio.run(_get_active_jobs())
        dispatched = 0
        for row in rows:
            try:
                process_ml_feedback_weights_task.delay(str(row.company_id), str(row.job_id))
                dispatched += 1
            except Exception as exc:
                logger.warning("[Celery] ml.feedback dispatch failed job=%s: %s", row.job_id, exc)
        logger.info("[Celery] ml.feedback.recompute_active_jobs dispatched %d jobs", dispatched)
        return {"dispatched": dispatched}
    except Exception as exc:
        logger.warning("[Celery] ml.feedback.recompute_active_jobs failed (fail-open): %s", exc)
        return {"dispatched": 0}
