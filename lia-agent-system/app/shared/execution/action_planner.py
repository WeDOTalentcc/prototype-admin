import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


from app.domains.base import DomainContext
from app.shared.execution.execution_plan import ExecutionPlan, PlanStatus, TaskStatus
from app.shared.execution.plan_executor import PlanExecutor

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    max_retries: int = 2
    backoff_type: str = "exponential"
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0

    def get_delay(self, attempt: int) -> float:
        if self.backoff_type == "fixed":
            delay = self.base_delay_seconds
        elif self.backoff_type == "linear":
            delay = self.base_delay_seconds * attempt
        else:
            delay = self.base_delay_seconds * (2 ** (attempt - 1))
        return min(delay, self.max_delay_seconds)


@dataclass
class RollbackHook:
    task_id: str
    action_id: str
    domain_id: str
    params: dict[str, Any] = field(default_factory=dict)
    description: str = ""


class ActionPlanner(PlanExecutor):
    """
    Extended PlanExecutor with retry policies, exponential backoff,
    rollback hooks, and plan templates for multi-step workflows.
    """

    def __init__(self, domain_registry=None, domain_workflow=None):
        super().__init__(domain_registry, domain_workflow)
        self.retry_policy = RetryPolicy()
        self.rollback_hooks: dict[str, RollbackHook] = {}
        self._executed_rollbacks: list[str] = []

    def set_retry_policy(self, policy: RetryPolicy):
        self.retry_policy = policy

    def add_rollback_hook(self, hook: RollbackHook):
        self.rollback_hooks[hook.task_id] = hook

    async def execute(
        self,
        plan: ExecutionPlan,
        user_id: str = "system",
        session_id: str = "",
        tenant_id: str | None = None,
        base_context: dict[str, Any] | None = None,
    ) -> ExecutionPlan:
        plan.status = PlanStatus.IN_PROGRESS
        logger.info(f"ActionPlanner executing plan {plan.plan_id} with {len(plan.tasks)} tasks "
                     f"(retry: max={self.retry_policy.max_retries}, backoff={self.retry_policy.backoff_type})")

        iteration_limit = len(plan.tasks) * (self.retry_policy.max_retries + 2)
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
                task.max_retries = self.retry_policy.max_retries
                await self._execute_task_with_backoff(task, plan, user_id, session_id, tenant_id, base_context)

                if task.status == TaskStatus.FAILED and task.is_critical:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.warning(f"Critical task {task.task_id} failed. Initiating rollback for plan {plan.plan_id}.")
                    await self._rollback_completed_tasks(plan, user_id, session_id, tenant_id, base_context)
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

        summary = plan.get_summary()
        logger.info(f"ActionPlanner plan {plan.plan_id} {plan.status.value}: "
                     f"{summary['completed']}/{summary['total_tasks']} completed, "
                     f"{summary['failed']} failed, {summary['skipped']} skipped")

        return plan

    async def _execute_task_with_backoff(
        self, task, plan, user_id, session_id, tenant_id, base_context
    ):
        attempt = 0
        max_attempts = self.retry_policy.max_retries + 1

        while attempt < max_attempts:
            attempt += 1
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()

            try:
                await self._execute_task(task, plan, user_id, session_id, tenant_id, base_context)
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.error(f"Task {task.task_id} attempt {attempt} error: {e}")
                task.status = TaskStatus.FAILED
                task.error = str(e)

            if task.status == TaskStatus.COMPLETED:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Task {task.task_id} completed on attempt {attempt}")
                return

            if task.status == TaskStatus.FAILED and attempt < max_attempts:
                delay = self.retry_policy.get_delay(attempt)
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Task {task.task_id} failed (attempt {attempt}/{max_attempts}). "
                           f"Retrying in {delay:.1f}s...")
                task.retry_count = attempt
                task.status = TaskStatus.PENDING
                await asyncio.sleep(delay)

    async def _rollback_completed_tasks(
        self, plan, user_id, session_id, tenant_id, base_context
    ):
        completed_tasks = [t for t in plan.tasks if t.status == TaskStatus.COMPLETED]
        completed_tasks.reverse()

        for task in completed_tasks:
            hook = self.rollback_hooks.get(task.task_id)
            if hook:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Rolling back task {task.task_id}: {hook.description}")
                try:
                    if self._domain_registry and self._domain_workflow:
                        domain = self._domain_registry.get_instance(hook.domain_id)
                        if domain:
                            dc = DomainContext(
                                domain_id=hook.domain_id,
                                user_id=user_id,
                                session_id=session_id,
                                tenant_id=tenant_id,
                                current_data=base_context or {},
                            )
                            query = f"rollback {hook.action_id}"
                            await self._domain_workflow.process(domain, dc, query)

                    self._executed_rollbacks.append(task.task_id)
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.info(f"Rollback completed for task {task.task_id}")
                except Exception as e:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.error(f"Rollback failed for task {task.task_id}: {e}")

    def get_execution_report(self, plan: ExecutionPlan) -> dict[str, Any]:
        report = plan.get_summary()
        report["retry_policy"] = {
            "max_retries": self.retry_policy.max_retries,
            "backoff_type": self.retry_policy.backoff_type,
        }
        report["rollback_hooks_defined"] = len(self.rollback_hooks)
        report["rollbacks_executed"] = self._executed_rollbacks
        report["task_details"] = []
        for task in plan.tasks:
            detail = task.to_dict()
            detail["had_retries"] = task.retry_count > 0
            detail["rollback_available"] = task.task_id in self.rollback_hooks
            report["task_details"].append(detail)
        return report
