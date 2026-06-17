"""Celery tasks: memory (Fase 7)."""
import asyncio
import re
from datetime import UTC

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
    _emit_celery_retry, _emit_dlq_push,
)

@celery_app.task(base=TenantAwareTask, name="memory.compress_old_episodes", bind=True, max_retries=2)
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

        _DOMAINS = ["sourcing", "pipeline", "kanban", "wizard", "hiring_policy", "talent", "screening"]
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

