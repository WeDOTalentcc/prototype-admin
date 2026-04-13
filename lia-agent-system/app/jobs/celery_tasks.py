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
  - digest.send_weekly           — envia weekly digest a todos os recrutadores ativos
"""

# ─────────────────────────────────────────────────────────────────────────
# LIA-D07: TODO — split this 2108-line file into tasks/ subdirectory.
#
# Planned structure:
#   - tasks/agents.py (7 tasks: execute_wizard, execute_pipeline, etc.)
#   - tasks/agents_legacy.py (4 tasks: run_drift_batch, start_wsi_interview, etc.)
#   - tasks/communication.py (3 tasks: send_bulk_email, send_daily_briefing, etc.)
#   - tasks/compliance.py (5 tasks: apply_audit_lifecycle_policy, run_lgpd_cleanup, etc.)
#   - tasks/followup.py (2 tasks: followup_process_pending, wsi_check_abandoned)
#   - tasks/feedback.py (3 tasks: feedback_generate_and_send, etc.)
#   - tasks/ml.py (7 tasks: run_ragas_evaluate_batch, rebuild_domain_index, etc.)
#   - tasks/registry.py (1 task: check_agent_registry_reload)
#   - tasks/voice.py (1 task: run_openmic_wsi_pipeline)
#   - tasks/_utils.py (shared helpers: _celery_span, _finish_celery_*, etc.)
#
# Main celery_tasks.py becomes a facade that re-exports from tasks/ modules.
# Defer actual split until after celery worker deployment stability verified.
# ─────────────────────────────────────────────────────────────────────────

import asyncio
import re
from datetime import UTC

from app.core.celery_app import celery_app
from app.shared.pii_masking import get_masked_logger
from app.shared.tracing import finish_span, get_tracer

logger = get_masked_logger(__name__)


def _celery_span(name: str, task_name: str):
    """Helper: cria span sync para Celery task com OTel timing."""
    tracer = get_tracer()
    return tracer.create_span(name, attributes={
        "service": "celery_tasks", "tier_name": f"celery_{task_name}",
        "celery.task_name": task_name,
    }, _start_otel=True)


def _finish_celery_success(start_span, task_name: str):
    """Finaliza start span e emite celery.task_success."""
    finish_span(start_span, status="success")
    tracer = get_tracer()
    success_span = tracer.create_span("celery.task_success", attributes={
        "service": "celery_tasks", "tier_name": f"celery_{task_name}",
        "celery.task_name": task_name,
    }, _start_otel=True)
    finish_span(success_span, status="ok")


def _finish_celery_failure(start_span, task_name: str, exc: Exception):
    """Finaliza start span e emite celery.task_failure."""
    finish_span(start_span, status="failure", error=exc)
    tracer = get_tracer()
    fail_span = tracer.create_span("celery.task_failure", attributes={
        "service": "celery_tasks", "tier_name": f"celery_{task_name}",
        "celery.task_name": task_name, "error.type": type(exc).__name__,
    }, _start_otel=True)
    finish_span(fail_span, status="error", error=exc)


def _emit_celery_retry(task_name: str, exc: Exception, attempt: int, max_retries: int, countdown: int):
    """Emite span celery.task_retry com metadados de tentativa."""
    tracer = get_tracer()
    retry_span = tracer.create_span("celery.task_retry", attributes={
        "service": "celery_tasks", "tier_name": f"celery_{task_name}",
        "celery.task_name": task_name, "error.type": type(exc).__name__,
        "retry.attempt": str(attempt), "retry.max_retries": str(max_retries),
        "retry.countdown_seconds": str(countdown),
    }, _start_otel=True)
    finish_span(retry_span, status="retry", error=exc)


def _emit_dlq_push(task_name: str, exc: Exception):
    """Emite span celery.dlq_push quando retries são esgotados."""
    tracer = get_tracer()
    dlq_span = tracer.create_span("celery.dlq_push", attributes={
        "service": "celery_tasks", "tier_name": f"celery_{task_name}_dlq",
        "celery.task_name": task_name, "error.type": type(exc).__name__,
        "dlq.reason": "max_retries_exceeded",
    }, _start_otel=True)
    finish_span(dlq_span, status="error", error=exc)


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
    from app.core.database import AsyncSessionLocal
    from app.jobs.drift_job import run_drift_check_all_companies

    span = _celery_span("celery.task_start", "drift.run_batch")

    async def _run() -> dict:
        async with AsyncSessionLocal() as db:
            return await run_drift_check_all_companies(db, notify_user_id)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "drift.run_batch")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "drift.run_batch", exc)
        logger.error("drift.run_batch falhou: %s", exc)
        _emit_celery_retry("drift.run_batch", exc, self.request.retries, self.max_retries, 60)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("drift.run_batch", exc)
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

    span = _celery_span("celery.task_start", "agents.wsi_interview.start")
    span.set_attribute("company_id", company_id)

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
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.wsi_interview.start")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.wsi_interview.start", exc)
        logger.error("agents.wsi_interview.start falhou company=%s: %s", company_id, exc)
        _emit_celery_retry("agents.wsi_interview.start", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.wsi_interview.start", exc)
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
    span = _celery_span("celery.task_start", "agents.triagem.run")
    span.set_attribute("company_id", company_id)
    span.set_attribute("candidate_count", str(len(candidate_ids)))

    async def _run() -> dict:
        from app.domains.cv_screening.services.cv_screening_batch_service import run_batch
        return await run_batch(
            candidate_ids=candidate_ids,
            job_id=job_id,
            company_id=company_id,
        )

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.triagem.run")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.triagem.run", exc)
        logger.error("agents.triagem.run falhou job=%s company=%s: %s", job_id, company_id, exc)
        _emit_celery_retry("agents.triagem.run", exc, self.request.retries, self.max_retries, 60)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.triagem.run", exc)
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

    span = _celery_span("celery.task_start", "agents.sourcing.search")
    span.set_attribute("company_id", company_id)

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
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.sourcing.search")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.sourcing.search", exc)
        logger.error("agents.sourcing.search falhou job=%s: %s", job_id, exc)
        _emit_celery_retry("agents.sourcing.search", exc, self.request.retries, self.max_retries, 45)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.sourcing.search", exc)
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
    from lia_agents_core.agent_interface import AgentInput

    span = _celery_span("celery.task_start", "agents.wizard.process_async")
    span.set_attribute("company_id", company_id)
    span.set_attribute("session_id", session_id)

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
        try:
            import asyncio as _asyncio

            from app.api.v1.ws_manager import ws_manager
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
        _finish_celery_success(span, "agents.wizard.process_async")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.wizard.process_async", exc)
        logger.error("agents.wizard.process_async falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.wizard.process_async", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.wizard.process_async", exc)
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
    from lia_agents_core.agent_interface import AgentInput

    span = _celery_span("celery.task_start", "agents.pipeline.transition_async")
    span.set_attribute("company_id", company_id)
    span.set_attribute("session_id", session_id)

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
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.pipeline.transition_async")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.pipeline.transition_async", exc)
        logger.error("agents.pipeline.transition_async falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.pipeline.transition_async", exc, self.request.retries, self.max_retries, 20)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.pipeline.transition_async", exc)
        raise self.retry(exc=exc, countdown=20)


# ---------------------------------------------------------------------------
# F5 — Tasks de execução de agentes via fila (Phase 4.4)
# Padrão: recebem agent_input_dict + session_id + company_id + domain
# Resultado publicado via RabbitMQ reply_to para o WS Gateway
# ---------------------------------------------------------------------------

def _build_agent_input(agent_input_dict: dict):
    """Constrói AgentInput a partir de dict serializado."""
    from lia_agents_core.agent_interface import AgentInput
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
    span = _celery_span("celery.task_start", "agents.wizard.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
        agent = WizardReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.wizard.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.wizard.execute", exc)
        logger.error("agents.wizard.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.wizard.execute", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.wizard.execute", exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="agents.pipeline.execute", bind=True, max_retries=2, queue="evaluation_normal")
def execute_pipeline_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "pipeline", reply_to: str = "") -> dict:
    """Executa PipelineReActAgent em background (pipeline, kanban, triagem)."""
    span = _celery_span("celery.task_start", "agents.pipeline.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
        agent = PipelineReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.pipeline.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.pipeline.execute", exc)
        logger.error("agents.pipeline.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.pipeline.execute", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.pipeline.execute", exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="agents.sourcing.execute", bind=True, max_retries=2, queue="sourcing_high")
def execute_sourcing_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "sourcing", reply_to: str = "") -> dict:
    """Executa SourcingReActAgent em background (busca Pearch, 30-120s)."""
    span = _celery_span("celery.task_start", "agents.sourcing.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        agent = SourcingReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.sourcing.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.sourcing.execute", exc)
        logger.error("agents.sourcing.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.sourcing.execute", exc, self.request.retries, self.max_retries, 45)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.sourcing.execute", exc)
        raise self.retry(exc=exc, countdown=45)


@celery_app.task(name="agents.screening.execute", bind=True, max_retries=2, queue="evaluation_normal")
def execute_screening_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "cv_screening", reply_to: str = "") -> dict:
    """Executa triagem curricular / WSI em background."""
    span = _celery_span("celery.task_start", "agents.screening.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
        agent = PipelineReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.screening.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.screening.execute", exc)
        logger.error("agents.screening.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.screening.execute", exc, self.request.retries, self.max_retries, 60)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.screening.execute", exc)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="agents.kanban.execute", bind=True, max_retries=2, queue="vagas_normal")
def execute_kanban_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "kanban", reply_to: str = "") -> dict:
    """Executa KanbanReActAgent / TalentReActAgent em background."""
    span = _celery_span("celery.task_start", "agents.kanban.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        agent = KanbanReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.kanban.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.kanban.execute", exc)
        logger.error("agents.kanban.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.kanban.execute", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.kanban.execute", exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="agents.policy.execute", bind=True, max_retries=2, queue="onboarding_low")
def execute_policy_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "policy", reply_to: str = "") -> dict:
    """Executa PolicyReActAgent em background (compliance, políticas)."""
    span = _celery_span("celery.task_start", "agents.policy.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        agent = PolicyReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.policy.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.policy.execute", exc)
        logger.error("agents.policy.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.policy.execute", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.policy.execute", exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="agents.automation.execute", bind=True, max_retries=2, queue="vagas_normal")
def execute_automation_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "automation", reply_to: str = "") -> dict:
    """Executa AutomationReActAgent em background (decomposição de tarefas)."""
    span = _celery_span("celery.task_start", "agents.automation.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        agent = AutomationReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.automation.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.automation.execute", exc)
        logger.error("agents.automation.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.automation.execute", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.automation.execute", exc)
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

    span = _celery_span("celery.task_start", "audit.apply_lifecycle_policy")

    try:
        storage = get_audit_storage()
        result = asyncio.run(storage.apply_lifecycle_policy())
        _finish_celery_success(span, "audit.apply_lifecycle_policy")
        logger.info(f"[audit.lifecycle] Applied: {result}")
        return {"applied": result}
    except Exception as exc:
        _finish_celery_failure(span, "audit.apply_lifecycle_policy", exc)
        logger.error(f"[audit.lifecycle] Error: {exc}")
        _emit_celery_retry("audit.apply_lifecycle_policy", exc, self.request.retries, self.max_retries, 3600)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("audit.apply_lifecycle_policy", exc)
        raise self.retry(exc=exc, countdown=3600)


@celery_app.task(name="lgpd.run_cleanup_daily", bind=True, max_retries=3)
def run_lgpd_cleanup_task(self, dry_run: bool = False) -> dict:
    """
    Executa limpeza de dados LGPD para todas as empresas.

    Aplica políticas de retenção (LGPD Art. 16):
      - 90 dias: candidatos rejeitados / retirados (dados operacionais)
      - 90 dias: mensagens de chat/conversa (minimização LGPD Art. 18)
      - 180 dias: dados de avaliação e triagem
      - 365 dias: logs de auditoria e compliance

    Agendado diariamente às 02h Brasília via Celery Beat (beat_schedule: lgpd-cleanup-daily).

    Args:
        dry_run: Se True, simula sem deletar (padrão: False em produção).

    Returns:
        Dict com { dry_run, ran_at, candidates_deleted,
                   vacancy_candidates_deleted, ai_consumption_deleted,
                   chat_messages_deleted, interview_notes_deleted,
                   screening_logs_deleted, ai_decision_logs_deleted, errors }
    """
    span = _celery_span("celery.task_start", "lgpd.run_cleanup_daily")
    span.set_attribute("dry_run", str(dry_run))

    async def _run() -> dict:
        from app.shared.services.lgpd_cleanup_service import run_cleanup
        return await run_cleanup(dry_run=dry_run)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "lgpd.run_cleanup_daily")
        logger.info("lgpd.run_cleanup_daily concluído: %s", result)
        return result
    except Exception as exc:
        _finish_celery_failure(span, "lgpd.run_cleanup_daily", exc)
        logger.error("lgpd.run_cleanup_daily falhou: %s", exc)
        _emit_celery_retry("lgpd.run_cleanup_daily", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("lgpd.run_cleanup_daily", exc)
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(name="conversation.ttl_cleanup", bind=True, max_retries=3)
def conversation_ttl_cleanup_task(self, dry_run: bool = False) -> dict:
    """
    Job Celery Beat dedicado para TTL de dados de conversa.

    Aplica TTL por tipo de dado (LGPD Art. 18 — minimização e retenção):
      - chat_messages / conversation_messages: 90 dias
      - interview_notes: 180 dias
      - screening_tasks: 365 dias
      - fairness_audit_log: 365 dias (EU AI Act)

    Agendado diariamente às 03h Brasília via Celery Beat
    (beat_schedule: conversation-ttl-cleanup-daily).

    Args:
        dry_run: Se True, simula sem deletar (padrão: False em produção).

    Returns:
        Dict com { dry_run, ran_at, tables, total_deleted, errors }
    """
    span = _celery_span("celery.task_start", "conversation.ttl_cleanup")
    span.set_attribute("dry_run", str(dry_run))

    async def _run() -> dict:
        from app.shared.services.lgpd_cleanup_service import run_conversation_ttl_cleanup
        return await run_conversation_ttl_cleanup(dry_run=dry_run)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "conversation.ttl_cleanup")
        logger.info("conversation.ttl_cleanup concluído: %s", result)
        return result
    except Exception as exc:
        _finish_celery_failure(span, "conversation.ttl_cleanup", exc)
        logger.error("conversation.ttl_cleanup falhou: %s", exc)
        _emit_celery_retry("conversation.ttl_cleanup", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("conversation.ttl_cleanup", exc)
        raise self.retry(exc=exc, countdown=300)  # retry em 5 min


@celery_app.task(name="pii.backfill_encrypt_existing", bind=True, max_retries=2)
def pii_backfill_encrypt_existing_task(
    self,
    batch_size: int = 500,
    dry_run: bool = False,
) -> dict:
    """
    Phase-2 backfill: encrypt existing plaintext PII bytes for rows added before migration 060.

    For each row where email_encrypted IS NULL but email IS NOT NULL:
      1. Fernet-encrypt the plaintext email → write to email_encrypted
      2. SHA-256 hash the email → write to email_hash (pgcrypto already covers this
         for most rows; this catches any missed rows)
      3. Repeat for cpf → cpf_encrypted on the candidates table

    Runs in batches (batch_size) to avoid long-running transactions.
    Requires FIELD_ENCRYPTION_KEY to be set.

    Safe to re-run: idempotent (WHERE email_encrypted IS NULL ensures skipping done rows).

    Args:
        batch_size: rows per batch (default 500)
        dry_run: log counts without committing (default False)

    Returns:
        Dict with per-table encrypted counts and any errors.
    """
    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.shared.encryption.encrypted_field_mixin import _encrypt, _sha256_hash
        from sqlalchemy import text

        summary: dict = {
            "dry_run": dry_run,
            "batch_size": batch_size,
            "tables": {},
            "errors": [],
        }

        _PII_TABLES_ALLOWED = frozenset(["candidates", "client_users", "users"])
        _SAFE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")

        tables_config = [
            ("candidates", "email", "email_encrypted", "email_hash"),
            ("client_users", "email", "email_encrypted", "email_hash"),
            ("users", "email", "email_encrypted", "email_hash"),
        ]

        async with AsyncSessionLocal() as db:
            for table, email_col, enc_col, hash_col in tables_config:
                if table not in _PII_TABLES_ALLOWED:
                    raise ValueError(f"Table '{table}' not in PII backfill allow-list")
                if not _SAFE_ID_RE.match(table):
                    raise ValueError(f"Table '{table}' contains invalid characters")
                for col in (email_col, enc_col, hash_col):
                    if not _SAFE_ID_RE.match(col):
                        raise ValueError(f"Column '{col}' contains invalid characters")

                encrypted_count = 0
                try:
                    while True:
                        rows = (await db.execute(
                            text(
                                f"SELECT id, {email_col} FROM {table} "
                                f"WHERE {enc_col} IS NULL AND {email_col} IS NOT NULL "
                                f"LIMIT :limit"
                            ),
                            {"limit": batch_size},
                        )).all()

                        if not rows:
                            break

                        for row in rows:
                            enc_val = _encrypt(row[1])
                            hash_val = _sha256_hash(row[1])
                            if not dry_run:
                                await db.execute(
                                    text(
                                        f"UPDATE {table} SET {enc_col} = :enc, {hash_col} = :hsh "
                                        f"WHERE id = :id"
                                    ),
                                    {"enc": enc_val, "hsh": hash_val, "id": row[0]},
                                )
                        if not dry_run:
                            await db.commit()

                        encrypted_count += len(rows)
                        logger.info(
                            "pii.backfill_encrypt_existing%s: %s — encrypted %d rows (batch)",
                            " (dry-run)" if dry_run else "",
                            table,
                            len(rows),
                        )

                        if len(rows) < batch_size:
                            break

                    summary["tables"][table] = {"encrypted": encrypted_count}

                except Exception as exc:
                    logger.error("pii.backfill_encrypt_existing: error on %s: %s", table, exc)
                    summary["errors"].append(f"{table}: {exc}")
                    try:
                        await db.rollback()
                    except Exception:
                        pass

            # Also backfill cpf_encrypted on candidates
            cpf_encrypted_count = 0
            try:
                while True:
                    rows = (await db.execute(
                        text(
                            "SELECT id, cpf FROM candidates "
                            "WHERE cpf_encrypted IS NULL AND cpf IS NOT NULL "
                            "LIMIT :limit"
                        ),
                        {"limit": batch_size},
                    )).all()

                    if not rows:
                        break

                    for row in rows:
                        enc_val = _encrypt(row[1])
                        if not dry_run:
                            await db.execute(
                                text(
                                    "UPDATE candidates SET cpf_encrypted = :enc WHERE id = :id"
                                ),
                                {"enc": enc_val, "id": row[0]},
                            )
                    if not dry_run:
                        await db.commit()

                    cpf_encrypted_count += len(rows)

                    if len(rows) < batch_size:
                        break

                summary["tables"]["candidates_cpf"] = {"encrypted": cpf_encrypted_count}

            except Exception as exc:
                logger.error("pii.backfill_encrypt_existing: error on candidates.cpf: %s", exc)
                summary["errors"].append(f"candidates_cpf: {exc}")

        return summary

    span = _celery_span("celery.task_start", "pii.backfill_encrypt_existing")
    span.set_attribute("batch_size", str(batch_size))
    span.set_attribute("dry_run", str(dry_run))

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "pii.backfill_encrypt_existing")
        logger.info("pii.backfill_encrypt_existing concluído: %s", result)
        return result
    except Exception as exc:
        _finish_celery_failure(span, "pii.backfill_encrypt_existing", exc)
        logger.error("pii.backfill_encrypt_existing falhou: %s", exc)
        _emit_celery_retry("pii.backfill_encrypt_existing", exc, self.request.retries, self.max_retries, 600)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("pii.backfill_encrypt_existing", exc)
        raise self.retry(exc=exc, countdown=600)  # retry em 10 min


@celery_app.task(name="communication.email.send_bulk", bind=True, max_retries=5)
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

    span = _celery_span("celery.task_start", "followup.process_pending")

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "followup.process_pending")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "followup.process_pending", exc)
        logger.error("followup.process_pending falhou: %s", exc)
        _emit_celery_retry("followup.process_pending", exc, self.request.retries, self.max_retries, 120)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("followup.process_pending", exc)
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

    span = _celery_span("celery.task_start", "wsi.check_abandoned")

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "wsi.check_abandoned")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "wsi.check_abandoned", exc)
        logger.error("wsi.check_abandoned falhou: %s", exc)
        _emit_celery_retry("wsi.check_abandoned", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("wsi.check_abandoned", exc)
        raise self.retry(exc=exc, countdown=300)



@celery_app.task(name="feedback.generate_and_send", bind=True, max_retries=2)
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
        from datetime import datetime, timedelta

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        from app.shared.services.ragas_evaluation_service import RAGASEvaluationInput, ragas_evaluation_service

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

    span = _celery_span("celery.task_start", "ragas.evaluate_batch")
    span.set_attribute("domain", domain)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "ragas.evaluate_batch")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "ragas.evaluate_batch", exc)
        logger.error("ragas.evaluate_batch falhou: %s", exc)
        _emit_celery_retry("ragas.evaluate_batch", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("ragas.evaluate_batch", exc)
        raise self.retry(exc=exc, countdown=300)


# ---------------------------------------------------------------------------
# E6 — RAG por Domínio: rebuild de índice de embeddings por domínio
# ---------------------------------------------------------------------------

@celery_app.task(name="rag.rebuild_domain_index")
def rebuild_domain_index_task(domain: str, company_id: str):
    """Celery task to rebuild RAG domain embeddings."""
    import asyncio

    from app.shared.services.domain_embedding_service import domain_embedding_service

    span = _celery_span("celery.task_start", "rag.rebuild_domain_index")
    span.set_attribute("domain", domain)
    span.set_attribute("company_id", company_id)

    async def _run():
        from lia_config.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            return await domain_embedding_service.rebuild_domain_index(domain, company_id, db)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "rag.rebuild_domain_index")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "rag.rebuild_domain_index", exc)
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

        from app.shared.services.routing_learning_service import routing_learning_service

        async with AsyncSessionLocal() as db:
            adj = await routing_learning_service.compute_domain_confidence_adjustments(
                company_id, db
            )
            await routing_learning_service.cache_adjustments(company_id, adj)
            return adj

    span = _celery_span("celery.task_start", "routing.recompute_adjustments")
    span.set_attribute("company_id", company_id)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "routing.recompute_adjustments")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "routing.recompute_adjustments", exc)
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

        from app.shared.services.ml_feedback_service import MLFeedbackService

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

    span = _celery_span("celery.task_start", "ml.feedback.process_weights")
    span.set_attribute("company_id", company_id)
    span.set_attribute("job_id", job_id)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "ml.feedback.process_weights")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "ml.feedback.process_weights", exc)
        logger.error("ml.feedback.process_weights falhou: %s", exc)
        _emit_celery_retry("ml.feedback.process_weights", exc, self.request.retries, self.max_retries, 120)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("ml.feedback.process_weights", exc)
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

    span = _celery_span("celery.task_start", "agents.registry.check_reload")

    try:
        reloaded = asyncio.run(agent_registry_watcher.check_and_reload())
        if reloaded:
            logger.info("[Celery] agents_registry.yaml reloaded: %s", reloaded)
        _finish_celery_success(span, "agents.registry.check_reload")
        return {"reloaded": reloaded}
    except Exception as exc:
        _finish_celery_failure(span, "agents.registry.check_reload", exc)
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
    span = _celery_span("celery.task_start", "rag.rebuild_all_domains")

    _DOMAINS = ["general", "jobs", "talent", "policy", "company"]
    dispatched = 0
    for domain in _DOMAINS:
        try:
            rebuild_domain_index_task.delay(domain, "global")
            dispatched += 1
        except Exception as exc:
            logger.warning("[Celery] rag.rebuild_all_domains dispatch failed for %s: %s", domain, exc)
    _finish_celery_success(span, "rag.rebuild_all_domains")
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

    span = _celery_span("celery.task_start", "memory.compress_old_episodes")
    span.set_attribute("company_id", company_id)
    span.set_attribute("age_days", str(age_days))

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "memory.compress_old_episodes")
        logger.info(
            "[memory.compress] company=%s compressed=%d purged=%d",
            company_id,
            result.get("compressed", 0),
            result.get("purged", 0),
        )
        return result
    except Exception as exc:
        _finish_celery_failure(span, "memory.compress_old_episodes", exc)
        logger.error("memory.compress_old_episodes falhou company=%s: %s", company_id, exc)
        _emit_celery_retry("memory.compress_old_episodes", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("memory.compress_old_episodes", exc)
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(name="ml.feedback.recompute_active_jobs")
def recompute_active_ml_jobs_task():
    """Recomputa pesos ML adaptativos para vagas com feedback nas últimas 48h.

    Wrapper semanal que consulta vagas com feedback recente e despacha
    process_ml_feedback_weights_task para cada. Fail-open.
    """
    import asyncio

    async def _get_active_jobs():
        from datetime import datetime, timedelta

        from lia_config.database import AsyncSessionLocal
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

    span = _celery_span("celery.task_start", "ml.feedback.recompute_active_jobs")

    try:
        rows = asyncio.run(_get_active_jobs())
        dispatched = 0
        for row in rows:
            try:
                process_ml_feedback_weights_task.delay(str(row.company_id), str(row.job_id))
                dispatched += 1
            except Exception as exc:
                logger.warning("[Celery] ml.feedback dispatch failed job=%s: %s", row.job_id, exc)
        _finish_celery_success(span, "ml.feedback.recompute_active_jobs")
        logger.info("[Celery] ml.feedback.recompute_active_jobs dispatched %d jobs", dispatched)
        return {"dispatched": dispatched}
    except Exception as exc:
        _finish_celery_failure(span, "ml.feedback.recompute_active_jobs", exc)
        logger.warning("[Celery] ml.feedback.recompute_active_jobs failed (fail-open): %s", exc)
        return {"dispatched": 0}


@celery_app.task(name="digest.send_weekly", bind=True, max_retries=2)
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


# ── Etapa 4 — Data Retention (LGPD Art. 18) ──────────────────────────────────

@celery_app.task(
    name="data.retention.run",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def run_retention_cleanup(self) -> dict:
    """
    Job mensal de anonimização de candidatos não contratados (LGPD Art. 18).
    Roda apenas para empresas com auto_anonymize=True (opt-in).
    Candidatos contratados (is_hired=True) NUNCA são anonimizados.

    Celery Beat schedule (adicionar em celery_config.py):
        "data-retention-monthly": {
            "task": "data.retention.run",
            "schedule": crontab(day_of_month=1, hour=2, minute=0),
        }
    """
    import asyncio
    span = _celery_span("celery.task_start", "data.retention.run")
    try:
        result = asyncio.run(_run_retention_cleanup_async())
        _finish_celery_success(span, "data.retention.run")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "data.retention.run", exc)
        _emit_celery_retry("data.retention.run", exc, self.request.retries, self.max_retries, 60)
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("data.retention.run", exc)
        raise self.retry(exc=exc)


async def _run_retention_cleanup_async() -> dict:
    from datetime import datetime, timedelta
    from uuid import uuid4

    from sqlalchemy import select, update

    try:
        from lia_config.database import AsyncSessionLocal
    except ImportError:
        from app.core.database import AsyncSessionLocal

    from libs.models.lia_models.retention_policy import CompanyRetentionPolicy

    # Candidate model — try multiple import paths
    try:
        from libs.models.lia_models.candidate import Candidate
    except ImportError:
        from app.models.candidate import Candidate

    total_anonymized = 0
    companies_processed = 0
    errors = []

    async with AsyncSessionLocal() as session:
        from sqlalchemy import text as _text  # noqa: F401
        policies_result = await session.execute(
            select(CompanyRetentionPolicy).where(
                CompanyRetentionPolicy.auto_anonymize == True  # noqa: E712
            )
        )
        policies = policies_result.scalars().all()

        for policy in policies:
            try:
                cutoff_date = datetime.now(UTC) - timedelta(
                    days=policy.retention_months * 30
                )
                result = await session.execute(
                    update(Candidate)
                    .where(
                        Candidate.company_id == policy.company_id,
                        Candidate.is_hired == False,  # noqa: E712
                        Candidate.created_at < cutoff_date,
                        Candidate.anonymized_at == None,  # noqa: E711
                    )
                    .values(
                        name=f"ANONIMIZADO-{uuid4().hex[:8]}",
                        email=None,
                        phone=None,
                        cpf=None,
                        linkedin_url=None,
                        github_url=None,
                        portfolio_url=None,
                        photo_url=None,
                        address=None,
                        anonymized_at=datetime.now(UTC),
                        anonymized_by="data.retention.run",
                    )
                )
                count = result.rowcount
                total_anonymized += count
                companies_processed += 1
                await session.execute(
                    update(CompanyRetentionPolicy)
                    .where(CompanyRetentionPolicy.company_id == policy.company_id)
                    .values(
                        last_cleanup_at=datetime.now(UTC),
                        last_cleanup_count=count,
                    )
                )
                logger.info(
                    "Retention cleanup: company=%s anonymized=%d cutoff=%s",
                    policy.company_id, count, cutoff_date.date()
                )
            except Exception as e:
                errors.append({"company_id": policy.company_id, "error": str(e)})
                logger.error("Retention cleanup failed for company=%s: %s", policy.company_id, e)

        await session.commit()

    result_dict = {
        "companies_processed": companies_processed,
        "total_anonymized": total_anonymized,
        "errors": errors,
        "ran_at": datetime.now(UTC).isoformat(),
    }
    logger.info("Retention cleanup complete: %s", result_dict)
    return result_dict


# ---------------------------------------------------------------------------
# OpenMic Voice Screening — WSI Pipeline Task
# ---------------------------------------------------------------------------

@celery_app.task(name="voice.openmic.wsi_pipeline", bind=True, max_retries=3, queue="evaluation_normal")
def run_openmic_wsi_pipeline_task(self, task_data: dict) -> dict:
    """
    Process OpenMic voice screening result through the WSI scoring pipeline.

    Triggered by the OpenMic webhook after a call completes. Delegates to
    `app.services.voice.wsi_pipeline.run_voice_wsi_pipeline` which handles:
    1. (Optional) Deepgram re-transcription if transcript is missing/short.
    2. WSI deterministic scoring from transcript.
    3. Persist result to `voice_wsi_results` table.
    4. Notify recruiter via Bell notification.

    Args:
        task_data: Dict with call_id, candidate_id, job_id, company_id,
                   transcript, audio_url, duration_seconds, source.

    Returns:
        Dict with wsi_score, classification, candidate_id, job_id, status.
    """
    from app.services.voice.wsi_pipeline import run_voice_wsi_pipeline

    span = _celery_span("celery.task_start", "voice.openmic.wsi_pipeline")
    span.set_attribute("call_id", task_data.get("call_id", "unknown"))
    span.set_attribute("candidate_id", task_data.get("candidate_id", "unknown"))

    try:
        result = asyncio.run(run_voice_wsi_pipeline(task_data))
        _finish_celery_success(span, "voice.openmic.wsi_pipeline")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "voice.openmic.wsi_pipeline", exc)
        logger.error(
            "voice.openmic.wsi_pipeline falhou call_id=%s candidate_id=%s: %s",
            task_data.get("call_id", "unknown"),
            task_data.get("candidate_id", "unknown"),
            exc,
        )
        _emit_celery_retry("voice.openmic.wsi_pipeline", exc, self.request.retries, self.max_retries, 60)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("voice.openmic.wsi_pipeline", exc)
        raise self.retry(exc=exc, countdown=60)
