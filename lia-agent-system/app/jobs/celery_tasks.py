"""
Celery Task Definitions

Tasks registradas:
  - drift.run_batch              — drift check em todas as empresas ativas
  - agents.wsi_interview.start   — inicia entrevista WSI em background
  - agents.triagem.run           — triagem curricular em lote
  - agents.sourcing.search       — busca de candidatos via Pearch (async)
  - communication.email.send_bulk — envio de email em massa
  - briefing.send_daily          — envia briefing diário a todos os recrutadores ativos (P3-1)
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

                    sent += 1
                except Exception as exc:
                    logger.error(
                        "briefing.send_daily: erro para user=%s: %s", user.id, exc
                    )
                    errors += 1

        return {"sent": sent, "skipped": skipped, "errors": errors}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("briefing.send_daily falhou: %s", exc)
        raise self.retry(exc=exc, countdown=300)
