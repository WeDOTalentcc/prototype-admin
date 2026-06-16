"""Celery tasks canonical pra agent_deployments (Fase 2.5 Onda C1-core).

O MOTOR DE EXECUÇÃO UNIFICADO. `agent_deployments` é a junction table canonical
agente↔surface (job / talent_pool / pipeline_stage / candidate_list). Esta task é
o ANÁLOGO canonical de `dispatch_pool_agent_assignment_task` (app/jobs/tasks/pool_agents.py)
— mesma fonte única de runs (`pool_agent_runs`), mesma disciplina de status/audit,
mas sourced via `deployment_id` em vez de `assignment_id`.

Entrega:
1. dispatch_agent_deployment_task — load deployment + CustomAgent, cria PoolAgentRun
   (deployment_id), executa via CustomAgentRuntime.execute, persiste resultados
   (queued→running→success|error) + audit dim 5.
2. scan_agent_deployment_cron_schedules — tick 60s lookup agent_deployments WHERE
   is_active AND trigger_mode='on_schedule' (canonical) | 'scheduled' (legacy).
   Croniter expression vs last_execution_at → dispatch via .delay().

Beat schedule entry registrado neste módulo (idempotente).

═══════════════════════════════════════════════════════════════════════════════
BYOK (invariante CRÍTICA da Fase 2.5) — como o tenant LLM config é propagado:
═══════════════════════════════════════════════════════════════════════════════
  1. dispatch resolve `tenant_id = deployment.company_id` (NUNCA de payload).
  2. get_or_create_runtime(company_id=deployment.company_id) — vincula o runtime
     ao tenant (cache key per tenant) e seta self._company_id.
  3. runtime.execute(company_id=deployment.company_id) seta o ContextVar
     `_current_company_id` (auth_enforcement) ANTES de invocar o LLM.
  4. LangGraphReActBase._get_model() lê esse ContextVar via
     tenant_llm_context.get_current_llm_tenant() → carrega tenant_llm_configs do
     tenant (provider + chave própria BYOK). Sem company_id → cai no provider
     global (errado para tenants BYOK). Por isso o company_id do deployment é
     obrigatório em AMBAS as chamadas.
  → Esta task NUNCA chama create_tracked_llm direto: delega ao runtime, que é o
    chokepoint canonical de BYOK. Sensor check_byok_tenant_id_in_llm_calls.py
    permanece baseline 0.

REGRA ZERO multi-tenancy: company_id sempre do próprio deployment (persistido),
nunca de payload/trigger_context.

REGRA 4 (falhar alto): erro no runtime → run.status='error' + error_message +
audit error + re-raise (Celery retry). Nunca silencia.

Refs:
- AGENT_STUDIO_FASE2.5_PLANO_CONSOLIDACAO.md §Onda C1.1 + invariante BYOK §2
- app/jobs/tasks/pool_agents.py (pattern canonical espelhado — canonical-fix)
- app/domains/agent_studio/repositories/pool_agent_run_repository.py (fonte única runs)
- app/shared/trigger_mode_validation.py (VALID_TRIGGER_MODES_BY_TARGET)
- libs/agents-core/lia_agents_core/langgraph_react_base.py:_get_model (BYOK chokepoint)
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

# Canonical scheduled trigger_mode (Onda 3) + legacy alias still accepted.
_SCHEDULED_TRIGGER_MODES = ("on_schedule", "scheduled")

_FALLBACK_PROMPT_TEMPLATE = (
    "Execute a rotina canonical do agente sobre o alvo {target_type} "
    "'{target_name}' conforme seus critérios configurados."
)


async def _dispatch_impl(
    deployment_id: str,
    trigger_source: str = "cron",
    trigger_context: dict | None = None,
) -> None:
    """REAL canonical dispatch do motor unificado (Onda C1-core.1).

    Pipeline:
      1. Load AgentDeployment (com company_id canonical).
      2. Create PoolAgentRun (status=queued) via repository, sourced por deployment_id.
      3. Load CustomAgent (deployment.agent_id).
      4. queued→running.
      5. Resolve dispatch_prompt (config_overrides > CustomAgent.config.default_prompt > fallback).
      6. BYOK: get_or_create_runtime(company_id=deployment.company_id) + execute(company_id=...).
      7. Persist results + runtime_metrics (BYOK model do tenant) + reasoning_payload + success.
      8. deployment.execution_count++ + last_execution_at.
      9. Audit dim 5 (success).

    On exception (REGRA 4): persist run.status=error + error_message + audit error +
    re-raise pra Celery retry policy. Nunca silencia.

    Args:
        deployment_id: UUID do agent_deployment.
        trigger_source: cron | on_demand | event_driven.
        trigger_context: payload opcional do evento (event_driven). NUNCA fonte de
            company_id — multi-tenancy fail-closed usa deployment.company_id.
    """
    from lia_models.agent_deployment import AgentDeployment
    from lia_models.custom_agent import CustomAgent

    from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime
    from app.domains.agent_studio.repositories.pool_agent_run_repository import (
        PoolAgentRunRepository,
    )

    # Map external trigger_source → canonical pool_agent_runs.trigger_source enum.
    run_trigger_source = trigger_source if trigger_source in (
        "cron",
        "on_demand",
        "event_driven",
    ) else "event_driven"

    async with AsyncSessionLocal() as db:
        # Step 1: load deployment.
        stmt_d = select(AgentDeployment).where(AgentDeployment.id == deployment_id)
        result_d = await db.execute(stmt_d)
        deployment = result_d.scalar_one_or_none()
        if deployment is None:
            _log.warning(
                "dispatch_agent_deployment_task: deployment_id=%s não encontrado "
                "(pode ter sido deletado entre scan e dispatch — skip canonical).",
                deployment_id,
            )
            return

        # Multi-tenancy fail-closed: company_id SEMPRE do deployment, nunca de payload.
        company_id = deployment.company_id

        # Step 2: create run (queued) sourced por deployment_id (chk_par_source_present).
        run_repo = PoolAgentRunRepository(db)
        run = await run_repo.create(
            deployment_id=deployment.id,
            company_id=company_id,
            trigger_source=run_trigger_source,
            dispatch_metadata={
                "trigger_source": trigger_source,
                "target_type": deployment.target_type,
                "target_id": str(deployment.target_id),
            },
        )

        # Step 3: load CustomAgent (after run row exists pra trail).
        stmt_a = select(CustomAgent).where(CustomAgent.id == deployment.agent_id)
        result_a = await db.execute(stmt_a)
        agent = result_a.scalar_one_or_none()
        if agent is None:
            err_msg = f"CustomAgent {deployment.agent_id} not found"
            await run_repo.update_status(run.id, "error", error_message=err_msg)
            audit_err = AuditService()
            await audit_err.log_decision(
                company_id=company_id,
                agent_name=str(deployment.agent_id),
                decision_type="dispatch",
                action="agent_deployment_run",
                decision="error",
                reasoning=[f"Run {run.id} failed: {err_msg}"],
                criteria_used=[],
            )
            raise RuntimeError(err_msg)

        try:
            # Step 4: queued → running.
            await run_repo.update_status(run.id, "running")

            # Step 5: resolve dispatch_prompt canonical.
            overrides = deployment.config_overrides or {}
            cfg = agent.config or {}
            dispatch_prompt = None
            if isinstance(overrides, dict):
                dispatch_prompt = overrides.get("dispatch_prompt") or overrides.get(
                    "default_prompt"
                )
            if not dispatch_prompt and isinstance(cfg, dict):
                dispatch_prompt = cfg.get("default_prompt")
            if not dispatch_prompt:
                dispatch_prompt = _FALLBACK_PROMPT_TEMPLATE.format(
                    target_type=deployment.target_type,
                    target_name=deployment.target_name or str(deployment.target_id),
                )

            # Step 6: BYOK — runtime bound to tenant company_id (cache key + ContextVar).
            runtime = get_or_create_runtime(
                agent_id=str(agent.id),
                agent_name=agent.name,
                system_prompt=agent.system_prompt,
                allowed_tools=agent.allowed_tools or [],
                domain=agent.domain,
                max_steps=agent.max_steps,
                temperature=agent.temperature,
                model_override=agent.model_override,
                company_id=company_id,  # BYOK: tenant binding for runtime cache + LLM resolution
                enable_memory=getattr(agent, "enable_memory", True),
                excluded_tools=getattr(agent, "excluded_tools", None),
                context_level=getattr(agent, "context_level", "full"),
            )

            t_start = time.time()
            # Stateless: 1 conversation per run (session_id=run.id).
            # BYOK: execute(company_id=...) sets _current_company_id ContextVar that
            # _get_model() reads to load the tenant's BYOK provider/key.
            output = await runtime.execute(
                message=dispatch_prompt,
                user_id="system",
                company_id=company_id,
                session_id=str(run.id),
                context={
                    "trigger_source": trigger_source,
                    "deployment_id": str(deployment.id),
                    "target_type": deployment.target_type,
                    "target_id": str(deployment.target_id),
                    "target_name": deployment.target_name,
                    "run_id": str(run.id),
                    **({"trigger_event": trigger_context} if trigger_context else {}),
                },
                db=db,
            )
            elapsed_ms = int((time.time() - t_start) * 1000)

            out_meta = output.metadata or {}
            tool_calls = [
                a.params.get("tool", "") if hasattr(a, "params") else ""
                for a in (output.actions or [])
            ]

            # Step 7: persist results + runtime_metrics (BYOK tenant model) + reasoning + success.
            await run_repo.update_status(
                run.id,
                "success",
                results={
                    "response": output.message or "",
                    "tools_used": tool_calls,
                    "confidence": float(output.confidence or 0.0),
                    "candidate_ids": list(
                        out_meta.get("touched_candidate_ids") or []
                    ),
                    "candidate_ids_truncated": bool(
                        out_meta.get("candidate_ids_truncated", False)
                    ),
                },
                runtime_metrics={
                    "latency_ms": elapsed_ms,
                    "tokens_input": out_meta.get("tokens_input", 0),
                    "tokens_output": out_meta.get("tokens_output", 0),
                    "input_tokens": out_meta.get(
                        "input_tokens", out_meta.get("tokens_input", 0)
                    ),
                    "output_tokens": out_meta.get(
                        "output_tokens", out_meta.get("tokens_output", 0)
                    ),
                    "model_used": out_meta.get("model_used", ""),
                    "cost_usd": float(out_meta.get("cost_usd", 0.0) or 0.0),
                },
                reasoning_payload=out_meta.get("reasoning_steps") or out_meta.get("reasoning_payload"),
            )

            # Step 8: deployment metrics (execution_count + last_execution_at).
            candidate_count = len(out_meta.get("touched_candidate_ids") or [])
            deployment.execution_count = (deployment.execution_count or 0) + 1
            deployment.candidates_processed = (
                deployment.candidates_processed or 0
            ) + candidate_count
            deployment.last_execution_at = datetime.now(timezone.utc)
            await db.commit()

            # Step 9: audit dim 5 (success).
            audit = AuditService()
            await audit.log_decision(
                company_id=company_id,
                agent_name=agent.name,
                decision_type="dispatch",
                action="agent_deployment_run",
                decision="success",
                reasoning=[
                    f"Run {run.id} completed via {trigger_source} "
                    f"(target={deployment.target_type}:{deployment.target_id}).",
                    f"Latency {elapsed_ms}ms, tool_calls={len(tool_calls)}.",
                ],
                criteria_used=[],
            )

        except Exception as exc:
            # REGRA 4 error path: persist run.status=error + audit + re-raise pra retry.
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
            audit_err = AuditService()
            try:
                await audit_err.log_decision(
                    company_id=company_id,
                    agent_name=agent.name if agent else str(deployment.agent_id),
                    decision_type="dispatch",
                    action="agent_deployment_run",
                    decision="error",
                    reasoning=[f"Run {run.id} failed: {err_text}"],
                    criteria_used=[],
                )
            except Exception as inner:
                _log.error("audit error path log failed: %s", inner)

            raise


async def _scan_impl() -> None:
    """REAL scan canonical: agent_deployments cron-due → dispatch via .delay().

    Tick 60s: lookup WHERE is_active AND trigger_mode IN (on_schedule, scheduled).
    Pra cada deployment, croniter(schedule_cron) vs last_execution_at (ou created_at
    se nulo) → dispatch quando next_run <= now (idempotência: ancorar no
    last_execution_at impede disparo 2× no mesmo slot).

    Cron expression inválida/ausente: log warning + continue scan (REGRA 4 — não
    silent fallback, sinaliza explicitamente e segue).
    """
    from croniter import croniter

    from lia_models.agent_deployment import AgentDeployment

    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        stmt = select(AgentDeployment).where(
            AgentDeployment.is_active == True,  # noqa: E712
            AgentDeployment.trigger_mode.in_(_SCHEDULED_TRIGGER_MODES),
        )
        result = await db.execute(stmt)
        deployments = result.scalars().all()

        for d in deployments:
            cron_expr = d.schedule_cron
            if not cron_expr:
                _log.warning(
                    "scan_agent_deployment_cron_schedules: deployment_id=%s "
                    "trigger_mode=on_schedule mas schedule_cron vazio — skip.",
                    d.id,
                )
                continue

            try:
                last_run = d.last_execution_at or getattr(d, "created_at", None) or now
                if last_run.tzinfo is None:
                    last_run = last_run.replace(tzinfo=timezone.utc)
                iter_ = croniter(cron_expr, last_run)
                next_run = iter_.get_next(datetime)
                if next_run.tzinfo is None:
                    next_run = next_run.replace(tzinfo=timezone.utc)
                if next_run <= now:
                    dispatch_agent_deployment_task.delay(
                        deployment_id=str(d.id),
                        trigger_source="cron",
                    )
            except (ValueError, KeyError, TypeError) as exc:
                _log.warning(
                    "scan_agent_deployment_cron_schedules: cron expression inválida "
                    "deployment_id=%s expr=%r erro=%s — skip canonical, continue scan.",
                    d.id,
                    cron_expr,
                    exc,
                )
                continue


# ─────────────────────────────────────────────────────────────────────────────
# Celery tasks (wrap async impls with span/retry canonical).
# ─────────────────────────────────────────────────────────────────────────────


@celery_app.task(
    base=TenantAwareTask,
    name="agent_deployments.dispatch",
    bind=True,
    max_retries=3,
    queue="agents_high",
)
def dispatch_agent_deployment_task(
    self,
    deployment_id: str,
    trigger_source: str = "cron",
    trigger_context: dict | None = None,
) -> dict:
    """Celery task wrapper canonical do motor unificado (Onda C1-core.1).

    Delega pra _dispatch_impl — audit canonical é responsabilidade do impl.
    Consumido por: scan_agent_deployment_cron_schedules (on_schedule) e, futuramente,
    pelo event consumer C1.2 (on_apply / on_enter_stage / etc).
    """
    span = _celery_span("celery.task_start", "agent_deployments.dispatch")
    span.set_attribute("deployment_id", str(deployment_id))
    span.set_attribute("trigger_source", trigger_source)

    try:
        asyncio.run(
            _dispatch_impl(
                deployment_id=deployment_id,
                trigger_source=trigger_source,
                trigger_context=trigger_context,
            )
        )
        _finish_celery_success(span, "agent_deployments.dispatch")
        logger.info(
            "agent_deployments.dispatch OK deployment_id=%s trigger=%s",
            deployment_id,
            trigger_source,
        )
        return {"deployment_id": deployment_id, "status": "dispatched"}
    except Exception as exc:
        _finish_celery_failure(span, "agent_deployments.dispatch", exc)
        logger.error(
            "agent_deployments.dispatch FAIL deployment_id=%s: %s",
            deployment_id,
            exc,
        )
        _emit_celery_retry(
            "agent_deployments.dispatch",
            exc,
            self.request.retries,
            self.max_retries,
            60,
        )
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("agent_deployments.dispatch", exc)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(
    base=TenantAwareTask,
    name="agent_deployments.scan_cron_schedules",
    bind=True,
    queue="default",
)
def scan_agent_deployment_cron_schedules(self) -> dict:
    """Celery task wrapper canonical (tick 60s REAL scan do motor unificado)."""
    span = _celery_span("celery.task_start", "agent_deployments.scan_cron_schedules")
    try:
        asyncio.run(_scan_impl())
        _finish_celery_success(span, "agent_deployments.scan_cron_schedules")
        return {"status": "ok"}
    except Exception as exc:
        _finish_celery_failure(span, "agent_deployments.scan_cron_schedules", exc)
        logger.error("agent_deployments.scan_cron_schedules FAIL: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Beat schedule entry — idempotent: side-effect na import canonical.
# ─────────────────────────────────────────────────────────────────────────────


def _register_beat_schedule() -> None:
    """Registra scan do motor unificado no beat_schedule canonical.

    Idempotente: pode ser chamado múltiplas vezes (override seguro).
    """
    schedule = getattr(celery_app.conf, "beat_schedule", None) or {}
    schedule["scan-agent-deployment-cron-schedules"] = {
        "task": "agent_deployments.scan_cron_schedules",
        "schedule": 60.0,
        "options": {"expires": 120, "queue": "default"},
    }
    celery_app.conf.beat_schedule = schedule


_register_beat_schedule()
