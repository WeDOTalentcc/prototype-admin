"""
CrewPlanExecutor — Orchestrates CrewPlan execution respecting DAG dependencies.

Extends the PlanExecutor concept to support CrewPlan with:
- DAG-based task ordering
- Shared CrewContext accessible to all agents in the crew
- Request-reply delegation via AgentBus (with local handler fallback)
- Per-task timeout enforcement
- CrewAuditService integration for full traceability
- Feature flag gating (CREW_DELEGATION_ENABLED)
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from app.shared.agents.crew_audit import crew_audit_service
from app.shared.agents.crew_context import CrewContext
from app.shared.agents.crew_models import (
    AgentCrew,
    CrewExecutionResult,
    CrewExecutionStatus,
    CrewPlan,
    CrewTask,
    CrewTaskStatus,
)

logger = logging.getLogger(__name__)

CrewProgressCallback = Callable[[str, dict[str, Any]], Awaitable[None]]

CREW_DELEGATION_ENABLED_ENV = "CREW_DELEGATION_ENABLED"


async def is_crew_delegation_enabled_async(db=None, company_id: str | None = None) -> bool:
    """Check the flag via FeatureFlagService when a db session is available.

    When ``db`` is None, short-circuits to the synchronous env-var check so
    that ``CREW_DELEGATION_ENABLED=false`` always works as a rollback switch.
    """
    if db is None:
        return is_crew_delegation_enabled()
    try:
        from app.shared.governance.feature_flag_service import FeatureFlagService
        svc = FeatureFlagService()
        return await svc.is_enabled(db, CREW_DELEGATION_ENABLED_ENV, company_id=company_id)
    except Exception:
        return is_crew_delegation_enabled()


def is_crew_delegation_enabled() -> bool:
    """Synchronous fallback — reads the env var directly.

    Used when no db session is available (tests, CLI, startup checks).
    The canonical source of truth is ``FeatureFlagService`` (which also
    reads the ``DEFAULT_FLAGS`` dict where this flag defaults to True).
    """
    return os.environ.get(CREW_DELEGATION_ENABLED_ENV, "true").lower() in ("1", "true", "yes")


class CrewPlanExecutor:
    def __init__(
        self,
        task_handlers: dict[str, Callable[..., Awaitable[dict[str, Any]]]] | None = None,
        use_bus_delegation: bool = False,
    ):
        self._task_handlers: dict[str, Callable[..., Awaitable[dict[str, Any]]]] = task_handlers or {}
        self._use_bus_delegation = use_bus_delegation

    def register_handler(
        self,
        action: str,
        handler: Callable[..., Awaitable[dict[str, Any]]],
    ) -> None:
        self._task_handlers[action] = handler

    async def execute(
        self,
        crew: AgentCrew,
        progress_callback: CrewProgressCallback | None = None,
        db=None,
    ) -> CrewExecutionResult:
        enabled = await is_crew_delegation_enabled_async(db=db, company_id=crew.company_id)
        if not enabled:
            logger.warning("[CrewExecutor] CREW_DELEGATION_ENABLED=false — skipping crew execution")
            return CrewExecutionResult(
                crew_id=crew.crew_id,
                company_id=crew.company_id,
                status=CrewExecutionStatus.FAILED,
                error="Crew delegation is disabled (feature flag)",
            )

        plan = crew.plan
        if not plan or not plan.tasks:
            return CrewExecutionResult(
                crew_id=crew.crew_id,
                company_id=crew.company_id,
                status=CrewExecutionStatus.FAILED,
                error="No plan or tasks defined",
            )

        dag_errors = plan.validate_dag()
        if dag_errors:
            return CrewExecutionResult(
                crew_id=crew.crew_id,
                company_id=crew.company_id,
                status=CrewExecutionStatus.FAILED,
                error=f"Invalid plan DAG: {'; '.join(dag_errors)}",
            )

        result = CrewExecutionResult(
            crew_id=crew.crew_id,
            company_id=crew.company_id,
            status=CrewExecutionStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )

        crew_ctx = CrewContext(
            crew_execution_id=result.execution_id,
            company_id=crew.company_id,
        )
        await crew_ctx.set("crew_id", crew.crew_id)
        await crew_ctx.set("company_id", crew.company_id)

        await crew_audit_service.log_crew_started(
            crew_id=crew.crew_id,
            execution_id=result.execution_id,
            company_id=crew.company_id,
            crew_name=crew.name,
            plan_name=plan.name,
            total_tasks=len(plan.tasks),
            roles=[r.model_dump() for r in crew.roles],
        )

        await self._emit(progress_callback, "crew_started", {
            "crew_id": crew.crew_id,
            "execution_id": result.execution_id,
            "plan_name": plan.name,
            "total_tasks": len(plan.tasks),
        })

        iteration_limit = len(plan.tasks) * 3
        iterations = 0

        while not plan.is_complete and iterations < iteration_limit:
            iterations += 1
            next_tasks = plan.get_next_tasks()

            if not next_tasks:
                pending = [t for t in plan.tasks if t.status == CrewTaskStatus.PENDING]
                if pending:
                    for task in pending:
                        failed_deps = [
                            dep for dep in task.depends_on
                            if any(
                                t.task_id == dep and t.status in (CrewTaskStatus.FAILED, CrewTaskStatus.TIMED_OUT)
                                for t in plan.tasks
                            )
                        ]
                        if failed_deps:
                            if task.is_critical:
                                task.status = CrewTaskStatus.FAILED
                                task.error = f"Blocked by failed dependencies: {failed_deps}"
                            else:
                                task.status = CrewTaskStatus.SKIPPED
                    continue
                break

            coros = [
                self._execute_task(task, plan, crew, crew_ctx, result.execution_id, progress_callback)
                for task in next_tasks
            ]
            await asyncio.gather(*coros, return_exceptions=True)

            for task in next_tasks:
                if task.status in (CrewTaskStatus.FAILED, CrewTaskStatus.TIMED_OUT) and task.is_critical:
                    self._mark_remaining_blocked(plan, task.task_id)

        result.completed_at = datetime.utcnow()
        result.plan_summary = plan.get_summary()
        result.context_snapshot = await crew_ctx.get_all()

        has_pending = any(t.status == CrewTaskStatus.PENDING for t in plan.tasks)
        if has_pending:
            result.status = CrewExecutionStatus.FAILED
            result.error = "Plan did not complete: tasks remain pending (possible unresolvable dependencies)"
        elif plan.all_succeeded:
            result.status = CrewExecutionStatus.COMPLETED
        elif plan.has_failures:
            completed_count = sum(1 for t in plan.tasks if t.status == CrewTaskStatus.COMPLETED)
            result.status = CrewExecutionStatus.PARTIAL if completed_count > 0 else CrewExecutionStatus.FAILED
        else:
            result.status = CrewExecutionStatus.COMPLETED

        await crew_audit_service.log_crew_completed(
            crew_id=crew.crew_id,
            execution_id=result.execution_id,
            company_id=crew.company_id,
            crew_name=crew.name,
            status=result.status.value,
            summary=result.plan_summary,
            duration_ms=result.duration_ms,
        )

        await self._emit(progress_callback, "crew_completed", {
            "crew_id": crew.crew_id,
            "execution_id": result.execution_id,
            "status": result.status.value,
            "summary": result.plan_summary,
        })

        await crew_ctx.delete()

        logger.info(
            "[CrewExecutor] Crew '%s' execution %s: %s",
            crew.name, result.execution_id, result.status.value,
        )

        return result

    async def _execute_task(
        self,
        task: CrewTask,
        plan: CrewPlan,
        crew: AgentCrew,
        crew_ctx: CrewContext,
        execution_id: str,
        progress_callback: CrewProgressCallback | None,
    ) -> None:
        task.status = CrewTaskStatus.RUNNING
        task.started_at = datetime.utcnow()

        await crew_audit_service.log_task_started(
            execution_id=execution_id,
            company_id=crew.company_id,
            task_id=task.task_id,
            assigned_agent=task.assigned_agent,
            action=task.action,
        )

        await self._emit(progress_callback, "task_started", {
            "execution_id": execution_id,
            "task_id": task.task_id,
            "assigned_agent": task.assigned_agent,
            "action": task.action,
        })

        resolved_params = dict(task.params)
        for param_key, context_path in task.context_mappings.items():
            value = await crew_ctx.get(context_path)
            if value is not None:
                resolved_params[param_key] = value

        resolved_params["crew_execution_id"] = execution_id
        resolved_params["company_id"] = crew.company_id

        correlation_id = uuid.uuid4().hex[:12]

        if self._use_bus_delegation and task.action not in self._task_handlers:
            task_result = await self._delegate_via_bus(
                task, resolved_params, crew, execution_id, correlation_id,
            )
        else:
            handler = self._task_handlers.get(task.action)
            if not handler:
                task.status = CrewTaskStatus.FAILED
                task.error = f"No handler registered for action '{task.action}'"
                task.completed_at = datetime.utcnow()
                await self._log_task_done(task, execution_id, crew.company_id, progress_callback)
                return

            await crew_audit_service.log_delegation(
                execution_id=execution_id,
                company_id=crew.company_id,
                from_agent="crew_orchestrator",
                to_agent=task.assigned_agent,
                action=task.action,
                correlation_id=correlation_id,
            )

            try:
                task_result = await asyncio.wait_for(
                    handler(resolved_params, crew_ctx),
                    timeout=task.timeout_seconds,
                )
            except asyncio.TimeoutError:
                task.status = CrewTaskStatus.TIMED_OUT
                task.error = f"Task timed out after {task.timeout_seconds}s"
                task.completed_at = datetime.utcnow()
                await self._log_task_done(task, execution_id, crew.company_id, progress_callback)
                return
            except Exception as exc:
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = CrewTaskStatus.PENDING
                    logger.info(
                        "[CrewExecutor] Retrying task %s (attempt %d/%d)",
                        task.task_id, task.retry_count, task.max_retries,
                    )
                    return
                task.status = CrewTaskStatus.FAILED
                task.error = str(exc)
                task.completed_at = datetime.utcnow()
                await self._log_task_done(task, execution_id, crew.company_id, progress_callback)
                return

        if task_result is None:
            if task.status == CrewTaskStatus.RUNNING:
                task.status = CrewTaskStatus.FAILED
                task.error = "No result returned from delegation"
                task.completed_at = datetime.utcnow()
            await self._log_task_done(task, execution_id, crew.company_id, progress_callback)
            return

        task.result = task_result
        task.status = CrewTaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()

        if isinstance(task_result, dict):
            for key, value in task_result.items():
                await crew_ctx.set(f"{task.task_id}.{key}", value)

        await self._log_task_done(task, execution_id, crew.company_id, progress_callback)

    async def _delegate_via_bus(
        self,
        task: CrewTask,
        params: dict[str, Any],
        crew: AgentCrew,
        execution_id: str,
        correlation_id: str,
    ) -> dict[str, Any] | None:
        """Delegate a task to another agent via AgentBus request-reply."""
        try:
            from app.shared.agents.agent_bus import agent_bus

            await crew_audit_service.log_delegation(
                execution_id=execution_id,
                company_id=crew.company_id,
                from_agent="crew_orchestrator",
                to_agent=task.assigned_agent,
                action=task.action,
                correlation_id=correlation_id,
            )

            result = await agent_bus.request(
                from_agent="crew_orchestrator",
                to_agent=task.assigned_agent,
                event_type=f"crew_task:{task.action}",
                payload={
                    "task_id": task.task_id,
                    "action": task.action,
                    "params": params,
                    "crew_execution_id": execution_id,
                },
                company_id=crew.company_id,
                timeout=task.timeout_seconds,
                correlation_id=correlation_id,
            )

            if result is None:
                task.status = CrewTaskStatus.TIMED_OUT
                task.error = f"Bus delegation timed out after {task.timeout_seconds}s"
                task.completed_at = datetime.utcnow()
                return None

            return result

        except Exception as exc:
            logger.warning("[CrewExecutor] Bus delegation failed for %s: %s", task.task_id, exc)
            task.status = CrewTaskStatus.FAILED
            task.error = f"Bus delegation error: {exc}"
            task.completed_at = datetime.utcnow()
            return None

    async def _log_task_done(
        self,
        task: CrewTask,
        execution_id: str,
        company_id: str,
        progress_callback: CrewProgressCallback | None,
    ) -> None:
        success = task.status == CrewTaskStatus.COMPLETED
        await crew_audit_service.log_task_completed(
            execution_id=execution_id,
            company_id=company_id,
            task_id=task.task_id,
            assigned_agent=task.assigned_agent,
            action=task.action,
            success=success,
            duration_ms=task.duration_ms,
            error=task.error,
        )
        await self._emit(progress_callback, "task_completed", {
            "execution_id": execution_id,
            "task_id": task.task_id,
            "assigned_agent": task.assigned_agent,
            "action": task.action,
            "status": task.status.value,
            "duration_ms": task.duration_ms,
            "error": task.error,
        })

    def _mark_remaining_blocked(self, plan: CrewPlan, failed_task_id: str) -> None:
        for task in plan.tasks:
            if task.status == CrewTaskStatus.PENDING and failed_task_id in task.depends_on:
                if task.is_critical:
                    task.status = CrewTaskStatus.FAILED
                    task.error = f"Blocked by failed task {failed_task_id}"
                else:
                    task.status = CrewTaskStatus.SKIPPED

    async def _emit(
        self,
        callback: CrewProgressCallback | None,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        if callback:
            try:
                await callback(event_type, data)
            except Exception as exc:
                logger.warning("[CrewExecutor] progress callback error: %s", exc)
