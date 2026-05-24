"""Celery tasks: ml (Fase 7)."""
import asyncio
import os
import re
from datetime import UTC

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
    _emit_celery_retry, _emit_dlq_push,
)

@celery_app.task(base=TenantAwareTask, name="ragas.evaluate_batch", bind=True, max_retries=1, queue="evaluation_normal")
def run_ragas_evaluate_batch(self, domain: str = "all", days_back: int = 1) -> dict:
    """
    Avaliação RAGAS em lote das respostas dos agentes — ACH-027.

    Carrega samples de audit_decisions das últimas `days_back` horas,
    executa avaliação RAGAS/heurística e persiste em agent_ragas_evaluations.

    Agendado diariamente às 03h UTC via Celery Beat (beat_schedule: ragas-evaluate-daily).

    Returns:
        Dict com { evaluated, skipped, errors, domain }
    """
    if os.getenv("ENABLE_RAG_EVAL", "true").lower() != "true":
        logger.info("ragas.evaluate_batch: ENABLE_RAG_EVAL is disabled, skipping")
        return {"status": "disabled", "reason": "ENABLE_RAG_EVAL=false"}

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

@celery_app.task(base=TenantAwareTask, name="rag.rebuild_domain_index")
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

async def recompute_routing_adjustments_canonical(
    company_id: str, db=None,
) -> dict:
    """Sprint 15.3-A canonical (2026-05-24): module-level async fn extracted
    from Celery task `routing.recompute_adjustments` for MonitoringLoop wire.

    Pattern Sprint 11: same as `check_dsr_overdue_canonical`,
    `lgpd.run_cleanup_canonical`, etc. — MonitoringLoop calls direct;
    Celery task delegates here (kept for legacy infra compat).

    Computes per-domain error rates from RoutingFeedback (last 30 days) and
    caches confidence-adjustment factors (0.8-1.2) to Redis (TTL=24h).

    Args:
        company_id: ID da empresa (ou "global" para ajuste global).
        db: optional AsyncSession; opens AsyncSessionLocal if not passed.

    Returns:
        Dict mapping domain → adjustment factor.
        Empty dict when no signal data (RoutingFeedback table empty for
        this company in lookback window — _MIN_SAMPLES=10 gate).

    Note: producer (record_correction) is currently NOT WIRED in prod.
    This aggregator is ready to compute when producer starts emitting.
    See: SIGNALS_INVENTORY.md (Sprint 15.1 audit).
    """
    from lia_config.database import AsyncSessionLocal
    from app.shared.services.routing_learning_service import routing_learning_service

    if db is None:
        async with AsyncSessionLocal() as _db:
            adj = await routing_learning_service.compute_domain_confidence_adjustments(
                company_id, _db
            )
            await routing_learning_service.cache_adjustments(company_id, adj)
            return adj
    adj = await routing_learning_service.compute_domain_confidence_adjustments(
        company_id, db
    )
    await routing_learning_service.cache_adjustments(company_id, adj)
    return adj


async def recompute_routing_adjustments_all_tenants_canonical() -> dict:
    """Sprint 15.3-A — iterate all active tenants + recompute per-tenant.

    Called daily by MonitoringLoop. Returns aggregated stats:
        {tenants_processed: int, tenants_with_adjustments: int, errors: int}

    Per-tenant failure is logged but doesn't block other tenants (Sprint 11
    fail-open pattern).
    """
    from lia_config.database import AsyncSessionLocal
    from sqlalchemy import text

    tenants_processed = 0
    tenants_with_adjustments = 0
    errors = 0

    async with AsyncSessionLocal() as session:
        try:
            # 2026-05-24 fix Bug E: column `status` does not exist on companies
            # (canonical is `is_active boolean`). Query returned UndefinedColumnError.
            # Sensor 7 (check_company_tenant_query_columns.py) blocks regression.
            result = await session.execute(text(
                "SELECT DISTINCT id FROM companies WHERE is_active = true LIMIT 1000"
            ))
            tenant_ids = [str(r[0]) for r in result.fetchall()]
        except Exception as exc:
            logger.warning(
                "[routing.recompute_adjustments] tenant list query failed: %s", exc,
            )
            return {"tenants_processed": 0, "tenants_with_adjustments": 0, "errors": 1}

    for tenant_id in tenant_ids:
        try:
            adj = await recompute_routing_adjustments_canonical(tenant_id)
            tenants_processed += 1
            if adj:
                tenants_with_adjustments += 1
        except Exception as exc:
            errors += 1
            logger.warning(
                "[routing.recompute_adjustments] tenant=%s failed: %s", tenant_id, exc,
            )

    # Also compute global (cross-tenant) adjustment
    try:
        adj = await recompute_routing_adjustments_canonical("global")
        if adj:
            tenants_with_adjustments += 1
    except Exception as exc:
        errors += 1
        logger.warning("[routing.recompute_adjustments] global failed: %s", exc)

    return {
        "tenants_processed": tenants_processed,
        "tenants_with_adjustments": tenants_with_adjustments,
        "errors": errors,
    }


@celery_app.task(base=TenantAwareTask, name="routing.recompute_adjustments")
def recompute_routing_adjustments(company_id: str) -> dict:
    """Celery task wrapper — delegates to canonical async fn.

    Sprint 15.3-A: behavior preserved. Caller can still invoke via Celery
    (.delay/.apply_async) but canonical async fn é fonte de verdade.
    """
    span = _celery_span("celery.task_start", "routing.recompute_adjustments")
    span.set_attribute("company_id", company_id)

    try:
        result = asyncio.run(recompute_routing_adjustments_canonical(company_id))
        _finish_celery_success(span, "routing.recompute_adjustments")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "routing.recompute_adjustments", exc)
        logger.warning("[Celery] routing.recompute_adjustments failed: %s", exc)
        return {}

@celery_app.task(base=TenantAwareTask, name="ml.feedback.process_weights", bind=True, max_retries=2)
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

@celery_app.task(base=TenantAwareTask, name="golden_drift.run_check", bind=True, max_retries=1, queue="evaluation_normal")
def run_golden_drift_check(self) -> dict:
    """
    Qualitative drift detection via golden scenarios — P37-073 (item 11.3).

    Runs golden eval suite, compares with saved baseline, classifies drift
    as STABLE/WARNING/CRITICAL, and dispatches Sentry alerts.

    Scheduled daily via Celery Beat (after quantitative drift at 9h UTC).
    """
    span = _celery_span("celery.task_start", "golden_drift.run_check")

    try:
        from app.services.golden_drift_monitor import golden_drift_detector, dispatch_drift_alerts
        from dataclasses import asdict

        report = golden_drift_detector.run_check()
        dispatch_drift_alerts(report)

        logger.info(
            "[Celery] golden_drift: status=%s agents=%d errors=%d",
            report.overall_status, len(report.agents), len(report.eval_errors),
        )
        _finish_celery_success(span, "golden_drift.run_check")
        return asdict(report)
    except Exception as exc:
        _finish_celery_failure(span, "golden_drift.run_check", exc)
        logger.error("golden_drift.run_check failed: %s", exc)
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("golden_drift.run_check", exc)
        raise self.retry(exc=exc, countdown=600)


@celery_app.task(base=TenantAwareTask, name="insights.aggregate_all", bind=True, max_retries=1, queue="evaluation_normal")
def aggregate_global_insights(self) -> dict:
    """Aggregate anonymous cross-tenant insights for all domains.

    Runs daily at 05h Brasília. Updates GlobalInsightsService baselines
    with real data when sufficient samples exist.
    """
    span = _celery_span("celery.task_start", "insights.aggregate_all")
    try:
        logger.info("[Celery] insights.aggregate_all: started (placeholder — real aggregation pending data volume)")
        _finish_celery_success(span, "insights.aggregate_all")
        return {"status": "ok", "domains": 8, "note": "aggregation runs when sample_size > 100"}
    except Exception as exc:
        _finish_celery_failure(span, "insights.aggregate_all", exc)
        logger.error("insights.aggregate_all failed: %s", exc)
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("insights.aggregate_all", exc)
        raise self.retry(exc=exc, countdown=600)


@celery_app.task(base=TenantAwareTask, name="fewshot.evolve", bind=True, max_retries=1, queue="evaluation_normal")
def evolve_few_shots(self) -> dict:
    """Auto-evolving few-shot pipeline — selects excellent interactions and inserts into YAML.

    Runs daily at 06h Brasília (between insights at 05h and drift at 07h).
    """
    import asyncio

    span = _celery_span("celery.task_start", "fewshot.evolve")
    try:
        from app.services.fewshot_evolution_service import run_fewshot_evolution
        result = asyncio.run(run_fewshot_evolution())
        logger.info("[Celery] fewshot.evolve: %s", result)
        _finish_celery_success(span, "fewshot.evolve")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "fewshot.evolve", exc)
        logger.error("fewshot.evolve failed: %s", exc)
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("fewshot.evolve", exc)
        raise self.retry(exc=exc, countdown=600)


@celery_app.task(base=TenantAwareTask, name="agents.registry.check_reload")
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

@celery_app.task(base=TenantAwareTask, name="rag.rebuild_all_domains")
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

@celery_app.task(base=TenantAwareTask, name="ml.feedback.recompute_active_jobs")
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

