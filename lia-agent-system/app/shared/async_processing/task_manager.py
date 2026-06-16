import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any, Optional

from app.shared.async_processing.task_queue import AsyncTask, DomainTaskQueue, TaskPriority, TaskState

logger = logging.getLogger(__name__)

ASYNC_ELIGIBLE_ACTIONS = {
    "sourcing": ["bulk_search", "mass_outreach", "import_candidates"],
    "cv_screening": ["bulk_screen", "batch_evaluate", "full_pipeline_screen"],
    "communication": ["mass_email", "mass_whatsapp", "bulk_notification"],
    "analytics": ["generate_full_report", "export_large_dataset", "predictive_analysis"],
    "ats_integration": ["bulk_sync", "full_import", "full_export"],
    "automation": ["batch_stage_transition", "run_automation_rules"],
    "job_management": ["bulk_publish", "batch_update_jobs"],
    "interview_scheduling": ["batch_schedule"],
    "recruiter_assistant": ["generate_daily_briefing"],
}


class DomainTaskManager:
    """
    Central manager for async task processing across all domains.

    Creates and manages per-domain queues, provides a unified API for:
    - Submitting async tasks
    - Checking task status
    - Listing queued/active tasks
    - Cancelling tasks

    Usage:
        manager = DomainTaskManager.get_instance()
        task_id = await manager.submit_task(
            domain_id="sourcing",
            action_id="bulk_search",
            params={"skills": ["python"], "limit": 500},
            user_id="user_123",
            priority=TaskPriority.HIGH,
        )
        status = manager.get_task_status(task_id)
    """

    _instance: Optional["DomainTaskManager"] = None

    @classmethod
    def get_instance(cls, **kwargs) -> "DomainTaskManager":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance:
            cls._instance = None

    async def shutdown(self) -> None:
        await self.stop_all()
        self.__class__._instance = None
        logger.info("DomainTaskManager shutdown complete")

    def __init__(self, max_concurrent_per_domain: int = 3, max_queue_size: int = 100):
        self._queues: dict[str, DomainTaskQueue] = {}
        self._task_index: dict[str, str] = {}
        self._max_concurrent = max_concurrent_per_domain
        self._max_queue_size = max_queue_size
        self._started = False

    def _get_or_create_queue(self, domain_id: str) -> DomainTaskQueue:
        if domain_id not in self._queues:
            self._queues[domain_id] = DomainTaskQueue(
                domain_id=domain_id,
                max_concurrent=self._max_concurrent,
                max_queue_size=self._max_queue_size,
            )
        return self._queues[domain_id]

    def register_handler(
        self, domain_id: str, action_id: str, handler: Callable[[AsyncTask], Awaitable[Any]]
    ) -> None:
        queue = self._get_or_create_queue(domain_id)
        queue.register_handler(action_id, handler)

    async def start_all(self) -> None:
        if self._started:
            return
        for queue in self._queues.values():
            await queue.start()
        self._started = True
        logger.info(f"DomainTaskManager started with {len(self._queues)} queues")

    async def stop_all(self) -> None:
        for queue in self._queues.values():
            await queue.stop()
        self._started = False
        logger.info("DomainTaskManager stopped")

    async def submit_task(
        self,
        domain_id: str,
        action_id: str,
        params: dict[str, Any] | None = None,
        user_id: str = "",
        tenant_id: str | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 2,
        callback: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        # RLS-EXEMPT: AsyncTask is an in-memory @dataclass, not an ORM Base — no DB row written here. Sensor false positive (user_id kwarg on a DTO).  WT-LEGACY-RLS-EXEMPT exp:2026-11-30
        task = AsyncTask(
            task_id=str(uuid.uuid4())[:12],
            domain_id=domain_id,
            action_id=action_id,
            params=params or {},
            priority=priority,
            user_id=user_id,
            tenant_id=tenant_id,
            max_retries=max_retries,
            callback=callback,
            metadata=metadata or {},
        )

        queue = self._get_or_create_queue(domain_id)
        if not queue._running:
            await queue.start()

        await queue.enqueue(task)
        self._task_index[task.task_id] = domain_id

        logger.info(
            f"Task {task.task_id} submitted: {domain_id}.{action_id} "
            f"priority={priority.name}"
        )
        return task.task_id

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        domain_id = self._task_index.get(task_id)
        if not domain_id:
            return None
        queue = self._queues.get(domain_id)
        if not queue:
            return None
        task = queue.get_task_status(task_id)
        if task:
            return task.to_dict()
        return None

    def cancel_task(self, task_id: str) -> bool:
        domain_id = self._task_index.get(task_id)
        if not domain_id:
            return False
        queue = self._queues.get(domain_id)
        if not queue:
            return False
        return queue.cancel_task(task_id)

    def is_async_eligible(self, domain_id: str, action_id: str) -> bool:
        eligible = ASYNC_ELIGIBLE_ACTIONS.get(domain_id, [])
        return action_id in eligible

    def list_tasks(
        self,
        domain_id: str | None = None,
        state: TaskState | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        tasks = []
        queues = [self._queues[domain_id]] if domain_id and domain_id in self._queues else self._queues.values()

        for queue in queues:
            for task in list(queue._active_tasks.values()) + list(queue._completed_tasks.values()):
                if state and task.state != state:
                    continue
                if user_id and task.user_id != user_id:
                    continue
                tasks.append(task.to_dict())

        return sorted(tasks, key=lambda t: t.get("created_at", 0), reverse=True)

    def get_all_queue_info(self) -> dict[str, Any]:
        return {
            domain_id: queue.get_queue_info()
            for domain_id, queue in self._queues.items()
        }

    def get_stats(self) -> dict[str, Any]:
        total_processed = sum(q._total_processed for q in self._queues.values())
        total_failed = sum(q._total_failed for q in self._queues.values())
        total_queued = sum(q._queue.qsize() for q in self._queues.values())
        total_active = sum(len(q._active_tasks) for q in self._queues.values())

        return {
            "total_queues": len(self._queues),
            "total_processed": total_processed,
            "total_failed": total_failed,
            "total_queued": total_queued,
            "total_active": total_active,
            "started": self._started,
            "queues": {did: q.get_queue_info() for did, q in self._queues.items()},
        }
