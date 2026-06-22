import ast
import asyncio
import logging
import operator
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any


from app.domains.base import DomainContext, DomainResponse
from app.shared.execution.agent_handoff import HANDOFF_METADATA_KEY, build_handoff_response
from app.shared.execution.discrete_actions import ActionContext, get_discrete_handler
from app.shared.execution.execution_plan import AgentTask, ExecutionPlan, PlanStatus, TaskStatus

logger = logging.getLogger(__name__)

TASK_TIMEOUT_SECONDS = 15

ProgressCallback = Callable[[str, dict[str, Any]], Awaitable[None]]

_SAFE_OPS = {
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}


def _resolve_name(node: ast.AST, ctx: dict[str, Any]) -> Any:
    if isinstance(node, ast.Name):
        if node.id not in ctx:
            raise ValueError(f"Unknown variable: {node.id}")
        return ctx[node.id]
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        obj = ctx.get(node.value.id)
        if obj is None:
            raise ValueError(f"Unknown variable: {node.value.id}")
        if isinstance(obj, dict):
            return obj.get(node.attr)
        raise ValueError(f"Cannot access attribute on non-dict: {node.value.id}")
    if isinstance(node, ast.Constant):
        return node.value
    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def _safe_eval_condition(expr: str, ctx: dict[str, Any]) -> bool:
    tree = ast.parse(expr.strip(), mode="eval")
    body = tree.body

    if isinstance(body, ast.BoolOp):
        if isinstance(body.op, ast.And):
            return all(_eval_compare(v, ctx) for v in body.values)
        if isinstance(body.op, ast.Or):
            return any(_eval_compare(v, ctx) for v in body.values)

    return _eval_compare(body, ctx)


def _eval_compare(node: ast.AST, ctx: dict[str, Any]) -> bool:
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        left = _resolve_name(node.left, ctx)
        right = _resolve_name(node.comparators[0], ctx)
        op_func = _SAFE_OPS.get(type(node.ops[0]))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.ops[0]).__name__}")
        return op_func(left, right)

    if isinstance(node, ast.Name):
        return bool(_resolve_name(node, ctx))

    if isinstance(node, ast.Constant):
        return bool(node.value)

    raise ValueError(f"Unsupported condition expression: {ast.dump(node)}")


class PlanExecutor:
    def __init__(self, domain_registry=None, domain_workflow=None):
        self._domain_registry = domain_registry
        self._domain_workflow = domain_workflow

    async def execute(
        self,
        plan: ExecutionPlan,
        user_id: str = "system",
        session_id: str = "",
        tenant_id: str | None = None,
        base_context: dict[str, Any] | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> ExecutionPlan:
        plan.status = PlanStatus.IN_PROGRESS
        logger.info(f"Executing plan {plan.plan_id} with {len(plan.tasks)} tasks")

        await self._emit(progress_callback, "plan_started", {
            "plan_id": plan.plan_id,
            "pattern": plan.detected_pattern,
            "total_tasks": len(plan.tasks),
            "tasks": [{"task_id": t.task_id, "domain_id": t.domain_id, "action_id": t.action_id} for t in plan.tasks],
        })

        iteration_limit = len(plan.tasks) * 3
        iterations = 0

        while not plan.is_complete and iterations < iteration_limit:
            iterations += 1
            next_tasks = plan.get_next_tasks()

            if not next_tasks:
                pending = [t for t in plan.tasks if t.status == TaskStatus.PENDING]
                if pending:
                    for task in pending:
                        failed_deps = [
                            dep for dep in task.depends_on
                            if any(t.task_id == dep and t.status == TaskStatus.FAILED for t in plan.tasks)
                        ]
                        if failed_deps:
                            if task.is_critical:
                                task.status = TaskStatus.FAILED
                                task.error = f"Blocked by failed dependencies: {failed_deps}"
                            else:
                                task.status = TaskStatus.SKIPPED
                                task.skip_reason = f"Skipped due to failed dependencies: {failed_deps}"
                    continue
                break

            for task in next_tasks:
                # Evaluate condition before executing
                should_skip, skip_reason = self._evaluate_condition(task, plan)
                if should_skip:
                    task.status = TaskStatus.SKIPPED
                    task.skip_reason = skip_reason
                    task.completed_at = datetime.utcnow()
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.info(f"Task {task.task_id} skipped: {skip_reason}")
                    await self._emit(progress_callback, "step_skipped", {
                        "plan_id": plan.plan_id,
                        "task_id": task.task_id,
                        "domain_id": task.domain_id,
                        "action_id": task.action_id,
                        "skip_reason": skip_reason,
                    })
                    continue

                await self._emit(progress_callback, "step_running", {
                    "plan_id": plan.plan_id,
                    "task_id": task.task_id,
                    "domain_id": task.domain_id,
                    "action_id": task.action_id,
                    "step_index": plan.tasks.index(task),
                    "total_steps": len(plan.tasks),
                })

                await self._execute_task(task, plan, user_id, session_id, tenant_id, base_context)

                await self._emit(progress_callback, "step_completed", {
                    "plan_id": plan.plan_id,
                    "task_id": task.task_id,
                    "domain_id": task.domain_id,
                    "action_id": task.action_id,
                    "status": task.status.value,
                    "duration_ms": task.duration_ms,
                    "error": task.error,
                })

                if task.status == TaskStatus.FAILED and task.is_critical:
                    logger.warning(
                        f"Critical task {task.task_id} failed in plan {plan.plan_id}. "
                        f"Marking remaining tasks."
                    )
                    self._mark_remaining_as_blocked(plan, task.task_id)
                    break

        plan.completed_at = datetime.utcnow()
        if plan.all_succeeded:
            plan.status = PlanStatus.COMPLETED
        elif plan.has_failures:
            completed_count = sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED)
            plan.status = PlanStatus.PARTIAL if completed_count > 0 else PlanStatus.FAILED
        else:
            plan.status = PlanStatus.COMPLETED

        logger.info(
            f"Plan {plan.plan_id} {plan.status.value}: "
            f"{sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED)}/{len(plan.tasks)} completed"
        )

        await self._emit(progress_callback, "plan_completed", {
            "plan_id": plan.plan_id,
            "status": plan.status.value,
            "summary": plan.get_summary(),
        })

        return plan

    def _evaluate_condition(self, task: AgentTask, plan: ExecutionPlan):
        """Evaluate a task condition against plan context. Returns (should_skip, reason)."""
        if not task.condition:
            return False, None

        try:
            local_vars = dict(plan.context_data)
            expr = task.condition
            result = _safe_eval_condition(expr, local_vars)

            if not result:
                threshold_info = f" (threshold: {task.condition_threshold})" if task.condition_threshold else ""
                return True, f"Condition not met: {expr}{threshold_info}"
            return False, None

        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.warning(f"Condition evaluation error for task {task.task_id}: {e}")
            # If condition can't be evaluated, don't skip (fail safe)
            return False, None

    async def _execute_task(
        self,
        task: AgentTask,
        plan: ExecutionPlan,
        user_id: str,
        session_id: str,
        tenant_id: str,
        base_context: dict[str, Any] | None,
    ) -> None:
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.debug(f"Executing task {task.task_id}: {task.domain_id}.{task.action_id}")

        # ── Honest handoff guard (Task #1222) ────────────────────────────────
        # Some steps map to CONTINUOUS, monetizable agents (triagem/WSI, sourcing
        # contínuo, onboarding) that are not available yet. The P&E executor must
        # NEVER run — or fake — these. Hand off honestly and stop here, so even
        # the no-registry fallback below can't produce a false success.
        handoff = build_handoff_response(task.domain_id, task.action_id)
        if handoff is not None:
            logger.info(
                f"Task {task.task_id} ({task.domain_id}.{task.action_id}) handed off "
                f"to a continuous agent (not yet available) — not executed."
            )
            plan.update_task_result(
                task.task_id,
                result=handoff,
                success=False,
                error="agent_handoff: etapa contínua pertence a um agente ainda não disponível",
            )
            return

        resolved_params = dict(task.params)
        for param_key, context_path in task.context_mappings.items():
            value = self._resolve_context_path(context_path, plan)
            if value is not None:
                resolved_params[param_key] = value

        ctx_data = dict(base_context or {})
        ctx_data.update(plan.context_data)
        ctx_data["execution_plan_id"] = plan.plan_id
        ctx_data["task_id"] = task.task_id

        try:
            # ── Discrete handler path (Task #1226) ───────────────────────────
            # Some steps map to discrete, one-shot actions (move candidate,
            # notify team) that MUST run through the compliant services instead
            # of the lossy keyword-matching DomainWorkflow re-derivation. When a
            # handler is registered for (domain_id, action_id), execute it
            # directly and inject its result into the plan context for chaining.
            discrete_handler = get_discrete_handler(task.domain_id, task.action_id)
            if discrete_handler is not None:
                actx = ActionContext(
                    company_id=ctx_data.get("company_id") or tenant_id,
                    user_id=user_id,
                    session_id=session_id,
                    tenant_id=tenant_id,
                    raw_query=(
                        getattr(plan, "original_query", None)
                        or ctx_data.get("original_query")
                        or ctx_data.get("query")
                        or ""
                    ),
                    base_context=ctx_data,
                )
                try:
                    response = await asyncio.wait_for(
                        discrete_handler(resolved_params, actx),
                        timeout=TASK_TIMEOUT_SECONDS,
                    )
                except TimeoutError:
                    logger.warning(
                        f"Discrete task {task.task_id} timed out after {TASK_TIMEOUT_SECONDS}s"
                    )
                    plan.update_task_result(
                        task.task_id,
                        result=None,
                        success=False,
                        error=f"Task timed out after {TASK_TIMEOUT_SECONDS}s",
                    )
                    return

                plan.update_task_result(
                    task.task_id,
                    result=response,
                    success=response.success,
                    error=response.error,
                )
                if response.success and response.data:
                    result_data = (
                        response.data if isinstance(response.data, dict) else {"result": response.data}
                    )
                    for key, value in result_data.items():
                        plan.inject_context(f"{task.task_id}.{key}", value)
                return

            if self._domain_registry and self._domain_workflow:
                domain = self._domain_registry.get_instance(task.domain_id)
                if domain:
                    # Guard: validate action_id exists in domain before executing
                    if hasattr(domain, '_ACTION_MAP') and task.action_id not in getattr(domain, '_ACTION_MAP', {}):
                        logger.warning(
                            "[PlanExecutor] action_id '%s' not found in domain '%s' action map. "
                            "Available: %s. Skipping task %s.",
                            task.action_id, task.domain_id,
                            list(getattr(domain, '_ACTION_MAP', {}).keys())[:10],
                            task.task_id,
                        )
                        plan.update_task_result(
                            task.task_id,
                            result=None,
                            success=False,
                            error=f"Action '{task.action_id}' not available in domain '{task.domain_id}'. This plan step cannot execute yet.",
                        )
                        return
                    dc = DomainContext(
                        domain_id=task.domain_id,
                        user_id=user_id,
                        session_id=session_id,
                        tenant_id=tenant_id,
                        current_data=ctx_data,
                        conversation_state=ctx_data.get("conversation_state"),
                    )

                    query = self._build_task_query(task, resolved_params)
                    try:
                        response = await asyncio.wait_for(
                            self._domain_workflow.process(domain, dc, query),
                            timeout=TASK_TIMEOUT_SECONDS,
                        )
                    except TimeoutError:
                        logger.warning(
                            f"Task {task.task_id} timed out after {TASK_TIMEOUT_SECONDS}s"
                        )
                        plan.update_task_result(
                            task.task_id,
                            result=None,
                            success=False,
                            error=f"Task timed out after {TASK_TIMEOUT_SECONDS}s",
                        )
                        return

                    plan.update_task_result(
                        task.task_id,
                        result=response,
                        success=response.success,
                        error=response.error,
                    )

                    if response.success and response.data:
                        result_data = response.data if isinstance(response.data, dict) else {"result": response.data}
                        for key, value in result_data.items():
                            plan.inject_context(f"{task.task_id}.{key}", value)
                else:
                    plan.update_task_result(
                        task.task_id,
                        result=None,
                        success=False,
                        error=f"Domain '{task.domain_id}' not found in registry",
                    )
            else:
                logger.error(
                    "[PlanExecutor] No domain_registry/domain_workflow — cannot execute task %s. "
                    "This is a wiring bug: PlanExecutor must be instantiated with both args.",
                    task.task_id,
                )
                plan.update_task_result(
                    task.task_id,
                    result=None,
                    success=False,
                    error=f"Plan executor not properly configured (missing domain registry). Task {task.task_id} cannot execute.",
                )

        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Task {task.task_id} execution error: {e}", exc_info=True)

            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries})")
            else:
                plan.update_task_result(
                    task.task_id,
                    result=None,
                    success=False,
                    error=str(e),
                )

    async def _emit(self, callback: ProgressCallback | None, event_type: str, data: dict[str, Any]) -> None:
        """Emit a progress event via callback if provided."""
        if callback:
            try:
                await callback(event_type, data)
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Progress callback error for event {event_type}: {e}")

    def _resolve_context_path(self, context_path: str, plan: ExecutionPlan) -> Any:
        value = plan.get_context(context_path)
        if value is not None:
            return value

        parts = context_path.split(".", 1)
        if len(parts) == 2:
            source_task_id, result_key = parts
            task = plan.get_task(source_task_id)
            if task and task.result:
                if isinstance(task.result, DomainResponse) and isinstance(task.result.data, dict):
                    return task.result.data.get(result_key)
                elif isinstance(task.result, dict):
                    return task.result.get(result_key)

        return None

    def _build_task_query(self, task: AgentTask, params: dict[str, Any]) -> str:
        base = task.action_id.replace("_", " ")
        parts = [base]
        for key, value in params.items():
            if isinstance(value, (list, tuple)) and len(value) > 3:
                parts.append(f"{key}: {len(value)} itens")
            elif value is not None:
                parts.append(f"{key}: {value}")
        return " ".join(parts)

    def _mark_remaining_as_blocked(self, plan: ExecutionPlan, failed_task_id: str) -> None:
        for task in plan.tasks:
            if task.status == TaskStatus.PENDING:
                if failed_task_id in task.depends_on:
                    if task.is_critical:
                        task.status = TaskStatus.FAILED
                        task.error = f"Blocked by failed task {failed_task_id}"
                    else:
                        task.status = TaskStatus.SKIPPED
                        task.skip_reason = f"Skipped due to failed task {failed_task_id}"

    async def execute_crew(
        self,
        crew,
        progress_callback: ProgressCallback | None = None,
        task_handlers: dict[str, Any] | None = None,
        use_bus_delegation: bool = True,
        db=None,
    ):
        """Execute a CrewPlan via CrewPlanExecutor.

        Integrates crew-mode execution into the main PlanExecutor so
        callers can use the same entrypoint for both ExecutionPlan and
        CrewPlan/AgentCrew workflows.

        When ``task_handlers`` are provided the executor uses them for
        known actions and falls back to AgentBus for actions without a
        registered handler (when ``use_bus_delegation=True``).  This
        makes crew execution reliable regardless of whether remote
        agent subscribers are active.

        Args:
            crew: An ``AgentCrew`` instance with a ``CrewPlan`` attached.
            progress_callback: Optional progress callback (same signature).
            task_handlers: Optional mapping of action names to async handler
                functions ``(params, crew_ctx) -> dict``.
            use_bus_delegation: If True (default), actions without a local
                handler are delegated over AgentBus.  Set to False to run
                entirely with local handlers.
            db: Optional async DB session for per-company feature flag checks.
                When None, the env-var fallback is used.

        Returns:
            ``CrewExecutionResult`` from the crew executor.
        """
        from app.shared.agents.crew_executor import CrewPlanExecutor
        from app.shared.agents.crew_examples import get_production_handlers

        merged_handlers = get_production_handlers()
        if task_handlers:
            merged_handlers.update(task_handlers)

        executor = CrewPlanExecutor(
            task_handlers=merged_handlers,
            use_bus_delegation=use_bus_delegation,
        )
        return await executor.execute(crew, progress_callback=progress_callback, db=db)

    def build_consolidated_response(self, plan: ExecutionPlan) -> DomainResponse:
        messages = []
        for task in plan.tasks:
            status_icon = {"completed": "[OK]", "failed": "[FAIL]", "skipped": "[SKIP]"}.get(task.status.value, "[...]")
            msg = f"{status_icon} {task.domain_id}.{task.action_id}"
            if task.status.value == "skipped" and task.skip_reason:
                msg += f": {task.skip_reason[:100]}"
            elif task.result and isinstance(task.result, DomainResponse):
                msg += f": {task.result.message[:100]}"
            elif task.error:
                msg += f": {task.error[:100]}"
            messages.append(msg)

        # ── Honest handoff propagation (Task #1222) ──────────────────────────
        # If any step handed off to a continuous agent, the plan did NOT fully
        # execute its intended action. Never let the consolidated envelope claim
        # success=True (even on PARTIAL) — that would be a fake success to the
        # consumer. Surface the handoff explicitly so the LIA can be honest, and
        # never headline the message with "executado" when nothing fully ran.
        handoffs = [
            task.result.metadata[HANDOFF_METADATA_KEY]
            for task in plan.tasks
            if isinstance(task.result, DomainResponse)
            and task.result.metadata
            and HANDOFF_METADATA_KEY in task.result.metadata
        ]

        if handoffs:
            _header = f"Plano '{plan.detected_pattern}' — etapa(s) encaminhada(s) a um agente"
        elif plan.status == PlanStatus.PARTIAL:
            _header = f"Plano '{plan.detected_pattern}' parcialmente executado"
        elif plan.status == PlanStatus.FAILED:
            _header = f"Plano '{plan.detected_pattern}' não executado"
        else:
            _header = f"Plano '{plan.detected_pattern}' executado"
        combined_message = f"{_header}:\n" + "\n".join(messages)

        combined_data: dict[str, Any] = {}
        for task in plan.tasks:
            if task.result and isinstance(task.result, DomainResponse) and task.result.data:
                combined_data[task.task_id] = task.result.data

        if handoffs:
            return DomainResponse.error_response(
                error="agent_handoff",
                message=combined_message,
                metadata={
                    "execution_plan": plan.get_summary(),
                    "agent_handoffs": handoffs,
                },
            )

        if plan.status in (PlanStatus.COMPLETED, PlanStatus.PARTIAL):
            return DomainResponse.success_response(
                message=combined_message,
                data=combined_data,
                metadata={"execution_plan": plan.get_summary()},
            )
        else:
            return DomainResponse.error_response(
                error=f"Plan execution {plan.status.value}",
                message=combined_message,
                metadata={"execution_plan": plan.get_summary()},
            )
