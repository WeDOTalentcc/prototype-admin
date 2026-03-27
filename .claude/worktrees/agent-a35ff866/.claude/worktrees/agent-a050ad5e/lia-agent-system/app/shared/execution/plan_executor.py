import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.shared.execution.execution_plan import (
    ExecutionPlan, AgentTask, TaskStatus, PlanStatus
)
from app.domains.base import DomainContext, DomainResponse

logger = logging.getLogger(__name__)

TASK_TIMEOUT_SECONDS = 15


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
    ) -> ExecutionPlan:
        plan.status = PlanStatus.IN_PROGRESS
        logger.info(f"Executing plan {plan.plan_id} with {len(plan.tasks)} tasks")

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
                                task.error = f"Skipped due to failed dependencies: {failed_deps}"
                    continue
                break

            for task in next_tasks:
                await self._execute_task(task, plan, user_id, session_id, tenant_id, base_context)

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

        return plan

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
                        task.error = f"Skipped due to failed task {failed_task_id}"

    def build_consolidated_response(self, plan: ExecutionPlan) -> DomainResponse:
        messages = []
        for task in plan.tasks:
            status_icon = {"completed": "[OK]", "failed": "[FAIL]", "skipped": "[SKIP]"}.get(task.status.value, "[...]")
            msg = f"{status_icon} {task.domain_id}.{task.action_id}"
            if task.result and isinstance(task.result, DomainResponse):
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
