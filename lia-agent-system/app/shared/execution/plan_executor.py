import asyncio
import logging
import re
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime

from app.shared.execution.execution_plan import (
    ExecutionPlan, AgentTask, TaskStatus, PlanStatus
)
from app.domains.base import DomainContext, DomainResponse

logger = logging.getLogger(__name__)

TASK_TIMEOUT_SECONDS = 15

# Type alias for progress callback
ProgressCallback = Callable[[str, Dict[str, Any]], Awaitable[None]]


class PlanExecutor:
    def __init__(self, domain_registry=None, domain_workflow=None):
        self._domain_registry = domain_registry
        self._domain_workflow = domain_workflow

    async def execute(
        self,
        plan: ExecutionPlan,
        user_id: str = "system",
        session_id: str = "",
        tenant_id: str = "default",
        base_context: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[ProgressCallback] = None,
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
            # Build local eval context from plan context data
            local_vars = dict(plan.context_data)

            # Support simple expressions like "task_0.match_score >= 40"
            # Replace dotted paths with underscored keys if needed
            expr = task.condition
            # Allow direct evaluation with plan context keys
            result = eval(expr, {"__builtins__": {}}, local_vars)

            if not result:
                threshold_info = f" (threshold: {task.condition_threshold})" if task.condition_threshold else ""
                return True, f"Condition not met: {expr}{threshold_info}"
            return False, None

        except Exception as e:
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
        base_context: Optional[Dict[str, Any]],
    ) -> None:
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()

        logger.debug(f"Executing task {task.task_id}: {task.domain_id}.{task.action_id}")

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
            if self._domain_registry and self._domain_workflow:
                domain = self._domain_registry.get_instance(task.domain_id)
                if domain:
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
                    except asyncio.TimeoutError:
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
                plan.update_task_result(
                    task.task_id,
                    result=DomainResponse.success_response(
                        message=f"Task {task.task_id} executed (no domain registry)",
                        data=resolved_params,
                    ),
                    success=True,
                )

        except Exception as e:
            logger.error(f"Task {task.task_id} execution error: {e}", exc_info=True)

            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries})")
            else:
                plan.update_task_result(
                    task.task_id,
                    result=None,
                    success=False,
                    error=str(e),
                )

    async def _emit(self, callback: Optional[ProgressCallback], event_type: str, data: Dict[str, Any]) -> None:
        """Emit a progress event via callback if provided."""
        if callback:
            try:
                await callback(event_type, data)
            except Exception as e:
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

    def _build_task_query(self, task: AgentTask, params: Dict[str, Any]) -> str:
        parts = [task.action_id.replace("_", " ")]
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

        combined_message = f"Plano '{plan.detected_pattern}' executado:\n" + "\n".join(messages)

        combined_data: Dict[str, Any] = {}
        for task in plan.tasks:
            if task.result and isinstance(task.result, DomainResponse) and task.result.data:
                combined_data[task.task_id] = task.result.data

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
