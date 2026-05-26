"""Celery tasks canonical pra pool_agent_assignments (Sprint 7C Part 1 v2).

Cron infra canonical entrega:
1. dispatch_pool_agent_assignment_task — STUB canonical Part 1. Atualiza
   last_run_at + audit dim 5. Orchestrator real (execute CustomAgent +
   persist pool_agent_runs) fica Part 1.5 com decisão arquitetural separada.
2. scan_pool_agent_cron_schedules — REAL. Tick 60s lookup canonical
   pool_agent_assignments WHERE schedule_type='cron' AND status='active'.
   Croniter expression vs last_run_at → dispatch via .delay().

Beat schedule entry registrado neste módulo (idempotente): toda vez que
app/jobs/tasks/pool_agents é importado pelo Celery beat ou worker, garante
que `scan-pool-agent-cron-schedules` está em celery_app.conf.beat_schedule
com schedule=60.0s.

REGRA ZERO multi-tenancy: dispatch usa company_id do próprio assignment
(persistido na tabela), nunca de payload. AuditService.log_decision
emite trail dim 5 canonical (LGPD/SOX trail).

Sprint 7C Part 1.5 vai trocar status 'stub_dispatched' por 'success' | 'error'
do CustomAgent run real + persistir pool_agent_runs row.

Refs:
- AGENT_STUDIO_SPRINT7_PLAN.md §4 Sprint 7C
- libs/models/lia_models/pool_agent_assignment.py (model canonical)
- app/jobs/tasks/voice_retention.py (pattern Celery+asyncio.run canonical)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.jobs.tasks._utils import (
    _celery_span,
    _emit_celery_retry,
    _emit_dlq_push,
    _finish_celery_failure,
    _finish_celery_success,
    logger,
)
from app.jobs.tenant_aware_task import TenantAwareTask
from app.shared.compliance.audit_service import AuditService

# Re-exported for tests/patch — modules above are the canonical source.
from app.core.database import AsyncSessionLocal  # noqa: F401

_log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Async impls (testable directly, separate from Celery task wrapper).
# ─────────────────────────────────────────────────────────────────────────────


async def _dispatch_impl(assignment_id: str, trigger_source: str = "cron") -> None:
    """STUB canonical dispatch Part 1 v2.

    Atualiza last_run_at + audit dim 5. Não executa CustomAgent (Part 1.5).

    Args:
        assignment_id: UUID do pool_agent_assignment.
        trigger_source: 'cron' | 'on_demand' | (futuro Part 2 'event_driven').
    """
    from lia_models.pool_agent_assignment import PoolAgentAssignment

    async with AsyncSessionLocal() as db:
        stmt = select(PoolAgentAssignment).where(PoolAgentAssignment.id == assignment_id)
        result = await db.execute(stmt)
        assignment = result.scalar_one_or_none()
        if assignment is None:
            _log.warning(
                "dispatch_pool_agent_assignment_task: assignment_id=%s não encontrado "
                "(pode ter sido deletado entre scan e dispatch — skip canonical).",
                assignment_id,
            )
            return

        # Update last_run_at + status canonical (Part 1 v2 stub).
        assignment.last_run_at = datetime.now(timezone.utc)
        assignment.last_run_status = "stub_dispatched"  # Part 1.5 muda pra success/error real
        await db.commit()

        # Audit dim 5 obrigatório (feature-audit canonical).
        audit = AuditService()
        await audit.log_decision(
            company_id=assignment.company_id,
            agent_name=f"pool_agent_assignment:{assignment_id}",
            decision_type="dispatch",
            action=f"pool_agent_dispatch_{trigger_source}",
            decision="stub_executed",
            reasoning=[
                f"Sprint 7C Part 1 v2 stub: dispatch via {trigger_source}.",
                "Orchestrator real (CustomAgent execute + pool_agent_runs persist) "
                "fica Part 1.5 com decisão arquitetural separada.",
            ],
            criteria_used=[],
        )


async def _scan_impl() -> None:
    """REAL scan canonical: pool_agent_assignments cron-due → dispatch via .delay().

    Tick 60s: lookup WHERE schedule_type='cron' AND status='active'. Pra cada
    assignment match croniter expression vs last_run_at (ou created_at se
    last_run_at nulo) → dispatch.

    Cron expression inválida: log warning + continue scan (não silent fallback).
    """
    from croniter import croniter

    from lia_models.pool_agent_assignment import PoolAgentAssignment

    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        stmt = select(PoolAgentAssignment).where(
            PoolAgentAssignment.schedule_type == "cron",
            PoolAgentAssignment.status == "active",
        )
        result = await db.execute(stmt)
        assignments = result.scalars().all()

        for a in assignments:
            cron_expr = (a.schedule_config or {}).get("cron_expression")
            if not cron_expr:
                _log.warning(
                    "scan_pool_agent_cron_schedules: assignment_id=%s schedule_type=cron "
                    "mas schedule_config.cron_expression vazio — skip.",
                    a.id,
                )
                continue

            try:
                last_run = a.last_run_at or a.created_at
                iter_ = croniter(cron_expr, last_run)
                next_run = iter_.get_next(datetime)
                if next_run.tzinfo is None:
                    next_run = next_run.replace(tzinfo=timezone.utc)
                if next_run <= now:
                    dispatch_pool_agent_assignment_task.delay(
                        assignment_id=str(a.id),
                        trigger_source="cron",
                    )
            except (ValueError, KeyError, TypeError) as exc:
                # Não silent fallback: log explícito + continue scan.
                _log.warning(
                    "scan_pool_agent_cron_schedules: cron expression inválida "
                    "assignment_id=%s expr=%r erro=%s — skip canonical, continue scan.",
                    a.id,
                    cron_expr,
                    exc,
                )
                continue


# ─────────────────────────────────────────────────────────────────────────────
# Celery tasks (wrap async impls with span/retry canonical).
# ─────────────────────────────────────────────────────────────────────────────


@celery_app.task(
    base=TenantAwareTask,
    name="pool_agents.dispatch_assignment",
    bind=True,
    max_retries=3,
    queue="agents_high",
)
def dispatch_pool_agent_assignment_task(
    self, assignment_id: str, trigger_source: str = "cron"
) -> dict:
    """Celery task wrapper canonical (STUB Part 1 v2)."""
    span = _celery_span("celery.task_start", "pool_agents.dispatch_assignment")
    span.set_attribute("assignment_id", str(assignment_id))
    span.set_attribute("trigger_source", trigger_source)

    try:
        asyncio.run(_dispatch_impl(assignment_id=assignment_id, trigger_source=trigger_source))
        _finish_celery_success(span, "pool_agents.dispatch_assignment")
        logger.info(
            "pool_agents.dispatch_assignment OK assignment_id=%s trigger=%s",
            assignment_id,
            trigger_source,
        )
        return {"assignment_id": assignment_id, "status": "stub_dispatched"}
    except Exception as exc:
        _finish_celery_failure(span, "pool_agents.dispatch_assignment", exc)
        logger.error(
            "pool_agents.dispatch_assignment FAIL assignment_id=%s: %s",
            assignment_id,
            exc,
        )
        _emit_celery_retry(
            "pool_agents.dispatch_assignment",
            exc,
            self.request.retries,
            self.max_retries,
            60,
        )
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("pool_agents.dispatch_assignment", exc)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(
    base=TenantAwareTask,
    name="pool_agents.scan_cron_schedules",
    bind=True,
    queue="default",
)
def scan_pool_agent_cron_schedules(self) -> dict:
    """Celery task wrapper canonical (tick 60s REAL scan)."""
    span = _celery_span("celery.task_start", "pool_agents.scan_cron_schedules")
    try:
        asyncio.run(_scan_impl())
        _finish_celery_success(span, "pool_agents.scan_cron_schedules")
        return {"status": "ok"}
    except Exception as exc:
        _finish_celery_failure(span, "pool_agents.scan_cron_schedules", exc)
        logger.error("pool_agents.scan_cron_schedules FAIL: %s", exc)
        # No retry pra scan (próximo tick 60s pega de novo).
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Beat schedule entry — idempotent: side-effect na import canonical.
# ─────────────────────────────────────────────────────────────────────────────


def _register_beat_schedule() -> None:
    """Registra `scan-pool-agent-cron-schedules` no beat_schedule canonical.

    Idempotente: pode ser chamado múltiplas vezes (override seguro).
    """
    schedule = getattr(celery_app.conf, "beat_schedule", None) or {}
    schedule["scan-pool-agent-cron-schedules"] = {
        "task": "pool_agents.scan_cron_schedules",
        "schedule": 60.0,  # tick canonical Sprint 7C Part 1 v2
        "options": {"expires": 120, "queue": "default"},
    }
    celery_app.conf.beat_schedule = schedule


_register_beat_schedule()
