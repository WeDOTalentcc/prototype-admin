"""Celery tasks canonical pra pool_agent_assignments (Sprint 7C Part 1.5b/c).

Cron infra canonical entrega:
1. dispatch_pool_agent_assignment_task — REAL canonical Part 1.5b. Load assignment +
   CustomAgent, cria PoolAgentRun, executa via CustomAgentRuntime.execute,
   persiste resultados (queued→running→success|error) + audit dim 5.
2. scan_pool_agent_cron_schedules — REAL. Tick 60s lookup canonical
   pool_agent_assignments WHERE schedule_type=cron AND status=active.
   Croniter expression vs last_run_at → dispatch via .delay().

Beat schedule entry registrado neste módulo (idempotente).

REGRA ZERO multi-tenancy: dispatch usa company_id do próprio assignment
(persistido na tabela), nunca de payload.

Decisões Paulo locked 2026-05-26:
- Candidate selection: agent-driven via tools (LangGraph ReAct via _get_tools()).
- dispatch_prompt: CustomAgent.config[default_prompt] (sem migration).
- State: stateless por default. Cada run isolado (conversation_id=run_id).

Refs:
- AGENT_STUDIO_SPRINT7_PLAN.md §4 Sprint 7C
- AGENT_STUDIO_SPRINT7C_PART1_5B_INVESTIGATION.md (decisões + reuse ~85%)
- libs/models/lia_models/pool_agent_assignment.py (model canonical)
- app/jobs/tasks/voice_retention.py (pattern Celery+asyncio.run canonical)
"""
from __future__ import annotations

import asyncio
import logging
import time
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


_FALLBACK_PROMPT_TEMPLATE = (
    "Avalie candidatos do pool {pool_id} conforme critérios do agente."
)


async def _dispatch_impl(assignment_id: str, trigger_source: str = "cron") -> None:
    """REAL canonical dispatch Part 1.5b/c.

    Pipeline:
      1. Load assignment + CustomAgent (cross-tenant validated by FK + company_id).
      2. Create PoolAgentRun (status=queued) via canonical repository.
      3. Transition queued→running.
      4. Resolve dispatch_prompt (CustomAgent.config.default_prompt OR canonical fallback).
      5. get_or_create_runtime + execute (stateless: conversation_id=run.id).
      6. Persist run.results + runtime_metrics + status=success.
      7. Update assignment.last_run_at + last_run_status.
      8. Audit dim 5 (success or error).

    On exception: persist run.status=error + run.error_message + audit error +
    re-raise pra Celery retry policy.

    Args:
        assignment_id: UUID do pool_agent_assignment.
        trigger_source: cron | on_demand | (futuro Part 2 event_driven).
    """
    from lia_models.custom_agent import CustomAgent
    from lia_models.pool_agent_assignment import PoolAgentAssignment

    from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime
    from app.domains.agent_studio.repositories.pool_agent_run_repository import (
        PoolAgentRunRepository,
    )

    async with AsyncSessionLocal() as db:
        # Step 1: load assignment.
        stmt_a = select(PoolAgentAssignment).where(
            PoolAgentAssignment.id == assignment_id
        )
        result_a = await db.execute(stmt_a)
        assignment = result_a.scalar_one_or_none()
        if assignment is None:
            _log.warning(
                "dispatch_pool_agent_assignment_task: assignment_id=%s não encontrado "
                "(pode ter sido deletado entre scan e dispatch — skip canonical).",
                assignment_id,
            )
            return

        # Step 2: create run (queued).
        run_repo = PoolAgentRunRepository(db)
        run = await run_repo.create(
            assignment_id=assignment.id,
            company_id=assignment.company_id,
            trigger_source=trigger_source,
            dispatch_metadata={"trigger_source": trigger_source},
        )

        # Step 1b: load CustomAgent (after run row exists pra trail).
        stmt_c = select(CustomAgent).where(
            CustomAgent.id == assignment.custom_agent_id
        )
        result_c = await db.execute(stmt_c)
        agent = result_c.scalar_one_or_none()
        if agent is None:
            err_msg = f"CustomAgent {assignment.custom_agent_id} not found"
            await run_repo.update_status(run.id, "error", error_message=err_msg)
            assignment.last_run_status = "error"
            assignment.last_run_at = datetime.now(timezone.utc)
            await db.commit()
            audit_err = AuditService()
            await audit_err.log_decision(
                company_id=assignment.company_id,
                agent_name=str(assignment.custom_agent_id),
                decision_type="dispatch",
                action=f"pool_agent_dispatch_{trigger_source}",
                decision="error",
                reasoning=[f"Run {run.id} failed: {err_msg}"],
                criteria_used=[],
            )
            raise RuntimeError(err_msg)

        try:
            # Step 3: queued → running.
            await run_repo.update_status(run.id, "running")

            # Step 4: resolve dispatch_prompt canonical.
            cfg = agent.config or {}
            dispatch_prompt = cfg.get("default_prompt") if isinstance(cfg, dict) else None
            if not dispatch_prompt:
                dispatch_prompt = _FALLBACK_PROMPT_TEMPLATE.format(
                    pool_id=assignment.talent_pool_id
                )

            # Step 5: runtime + execute (canonical pattern from custom_agents.py:316).
            runtime = get_or_create_runtime(
                agent_id=str(agent.id),
                agent_name=agent.name,
                system_prompt=agent.system_prompt,
                allowed_tools=agent.allowed_tools or [],
                domain=agent.domain,
                max_steps=agent.max_steps,
                temperature=agent.temperature,
                model_override=agent.model_override,
                company_id=assignment.company_id,
                enable_memory=getattr(agent, "enable_memory", True),
                excluded_tools=getattr(agent, "excluded_tools", None),
                context_level=getattr(agent, "context_level", "full"),
            )

            t_start = time.time()
            # Stateless: 1 conversation per run (decisão Paulo #3).
            output = await runtime.execute(
                message=dispatch_prompt,
                user_id="system",
                company_id=assignment.company_id,
                session_id=str(run.id),
                context={
                    "trigger_source": trigger_source,
                    "assignment_id": str(assignment.id),
                    "pool_id": str(assignment.talent_pool_id),
                    "run_id": str(run.id),
                },
                db=db,
            )
            elapsed_ms = int((time.time() - t_start) * 1000)

            out_meta = output.metadata or {}
            tool_calls = [
                a.params.get("tool", "") if hasattr(a, "params") else ""
                for a in (output.actions or [])
            ]

            # Step 6: persist results + status=success.
            await run_repo.update_status(
                run.id,
                "success",
                results={
                    "response": output.message or "",
                    "tools_used": tool_calls,
                    "confidence": float(output.confidence or 0.0),
                },
                runtime_metrics={
                    "latency_ms": elapsed_ms,
                    "tokens_input": out_meta.get("tokens_input", 0),
                    "tokens_output": out_meta.get("tokens_output", 0),
                },
            )

            # Step 7: assignment.last_run_at + status.
            assignment.last_run_at = datetime.now(timezone.utc)
            assignment.last_run_status = "success"
            await db.commit()

            # Step 8: audit dim 5 (success).
            audit = AuditService()
            await audit.log_decision(
                company_id=assignment.company_id,
                agent_name=agent.name,
                decision_type="dispatch",
                action=f"pool_agent_dispatch_{trigger_source}",
                decision="success",
                reasoning=[
                    f"Run {run.id} completed via {trigger_source}.",
                    f"Latency {elapsed_ms}ms, tool_calls={len(tool_calls)}.",
                ],
                criteria_used=[],
            )

        except Exception as exc:
            # Error path: persist run.status=error + audit + re-raise pra retry.
            err_text = str(exc)
            try:
                await run_repo.update_status(
                    run.id, "error", error_message=err_text
                )
            except Exception as inner:
                _log.error(
                    "Falha ao persistir run.status=error run=%s: %s",
                    run.id, inner,
                )
            try:
                assignment.last_run_status = "error"
                assignment.last_run_at = datetime.now(timezone.utc)
                await db.commit()
            except Exception as inner:
                _log.error(
                    "Falha ao atualizar assignment.last_run_status=error %s: %s",
                    assignment.id, inner,
                )

            audit_err = AuditService()
            try:
                await audit_err.log_decision(
                    company_id=assignment.company_id,
                    agent_name=agent.name if agent else str(assignment.custom_agent_id),
                    decision_type="dispatch",
                    action=f"pool_agent_dispatch_{trigger_source}",
                    decision="error",
                    reasoning=[f"Run {run.id} failed: {err_text}"],
                    criteria_used=[],
                )
            except Exception as inner:
                _log.error("audit error path log failed: %s", inner)

            raise


async def _scan_impl() -> None:
    """REAL scan canonical: pool_agent_assignments cron-due → dispatch via .delay().

    Tick 60s: lookup WHERE schedule_type=cron AND status=active. Pra cada
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
    """Celery task wrapper canonical (REAL Part 1.5b/c).

    Delega pra _dispatch_impl — audit canonical é responsabilidade do impl
    (sensor #10 honra delegação para ).
    """
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
        return {"assignment_id": assignment_id, "status": "dispatched"}
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
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Beat schedule entry — idempotent: side-effect na import canonical.
# ─────────────────────────────────────────────────────────────────────────────


def _register_beat_schedule() -> None:
    """Registra  no beat_schedule canonical.

    Idempotente: pode ser chamado múltiplas vezes (override seguro).
    """
    schedule = getattr(celery_app.conf, "beat_schedule", None) or {}
    schedule["scan-pool-agent-cron-schedules"] = {
        "task": "pool_agents.scan_cron_schedules",
        "schedule": 60.0,
        "options": {"expires": 120, "queue": "default"},
    }
    celery_app.conf.beat_schedule = schedule


_register_beat_schedule()
