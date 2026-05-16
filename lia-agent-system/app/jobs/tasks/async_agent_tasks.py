"""Celery tasks: agents_legacy (Fase 7)."""
import asyncio
import re
from datetime import UTC

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
    _emit_celery_retry, _emit_dlq_push,
)

@celery_app.task(base=TenantAwareTask, name="drift.run_batch", bind=True, max_retries=3)
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

@celery_app.task(base=TenantAwareTask, name="agents.wsi_interview.start", bind=True, max_retries=3)
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

@celery_app.task(base=TenantAwareTask, name="agents.triagem.run", bind=True, max_retries=3)
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

@celery_app.task(base=TenantAwareTask, name="agents.sourcing.search", bind=True, max_retries=3)
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

