import logging
import time
from datetime import datetime
from typing import Any, Optional


from app.shared.async_processing.task_manager import DomainTaskManager
from app.shared.async_processing.task_persistence import TaskPersistenceService
from app.shared.async_processing.task_queue import AsyncTask, DomainTaskQueue, TaskPriority, TaskState

logger = logging.getLogger(__name__)


class _PersistentTaskQueue(DomainTaskQueue):

    def __init__(self, domain_id: str, manager: "EnhancedTaskManager", max_concurrent: int = 3, max_queue_size: int = 100):
        super().__init__(domain_id, max_concurrent, max_queue_size)
        self._manager = manager

    async def _process_task(self, task: AsyncTask, worker_name: str) -> None:
        task.state = TaskState.RUNNING
        task.started_at = time.time()
        self._active_tasks[task.task_id] = task

        await self._manager.on_task_started(task.task_id)

        handler = self._task_handlers.get(task.action_id)
        if not handler:
            handler = self._task_handlers.get("default")

        try:
            if handler:
                task.result = await handler(task)
            else:
                task.result = {"message": f"No handler for {task.action_id}", "status": "no_handler"}

            task.state = TaskState.COMPLETED
            task.completed_at = time.time()
            self._total_processed += 1
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.debug(f"Task {task.task_id} completed by {worker_name}")

            await self._manager.on_task_completed(task.task_id, task.result)

        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)

            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.state = TaskState.RETRYING
                task.started_at = None
                await self.enqueue(task)
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Task {task.task_id} retrying ({task.retry_count}/{task.max_retries})")
                await self._manager.on_task_failed(
                    task_id=task.task_id,
                    error=str(e),
                    retry_count=task.retry_count,
                    max_retries=task.max_retries,
                    domain_id=task.domain_id,
                    action_id=task.action_id,
                    params=task.params,
                    tenant_id=task.tenant_id,
                    metadata=task.metadata,
                    created_at=task.created_at,
                )
            else:
                task.state = TaskState.FAILED
                task.error = str(e)
                task.completed_at = time.time()
                self._total_failed += 1
                await self._manager.on_task_failed(
                    task_id=task.task_id,
                    error=str(e),
                    retry_count=task.retry_count,
                    max_retries=task.max_retries,
                    domain_id=task.domain_id,
                    action_id=task.action_id,
                    params=task.params,
                    tenant_id=task.tenant_id,
                    metadata=task.metadata,
                    created_at=task.created_at,
                )

        finally:
            self._active_tasks.pop(task.task_id, None)
            if task.is_terminal:
                self._completed_tasks[task.task_id] = task
                if len(self._completed_tasks) > self._max_completed_history:
                    oldest_key = min(self._completed_tasks,
                                     key=lambda k: self._completed_tasks[k].completed_at or 0)
                    del self._completed_tasks[oldest_key]


class EnhancedTaskManager(DomainTaskManager):
    _instance: Optional["EnhancedTaskManager"] = None

    @classmethod
    def get_instance(cls, **kwargs) -> "EnhancedTaskManager":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance:
            cls._instance = None

    def __init__(self, max_concurrent_per_domain: int = 3, max_queue_size: int = 100):
        super().__init__(max_concurrent_per_domain, max_queue_size)
        self._persistence = TaskPersistenceService.get_instance()

    def _get_or_create_queue(self, domain_id: str) -> DomainTaskQueue:
        if domain_id not in self._queues:
            self._queues[domain_id] = _PersistentTaskQueue(
                domain_id=domain_id,
                manager=self,
                max_concurrent=self._max_concurrent,
                max_queue_size=self._max_queue_size,
            )
        return self._queues[domain_id]

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
        scheduled_at: datetime | None = None,
    ) -> str:
        task_id = await super().submit_task(
            domain_id=domain_id,
            action_id=action_id,
            params=params,
            user_id=user_id,
            tenant_id=tenant_id,
            priority=priority,
            max_retries=max_retries,
            callback=callback,
            metadata=metadata,
        )

        try:
            await self._persistence.save_task(
                task_id=task_id,
                domain_id=domain_id,
                action_id=action_id,
                params=params,
                priority=priority.value,
                state="queued",
                user_id=user_id,
                tenant_id=tenant_id,
                max_retries=max_retries,
                callback=callback,
                metadata=metadata,
                scheduled_at=scheduled_at,
            )
        except Exception as e:
            logger.error(f"Failed to persist task {task_id}: {e}")

        return task_id

    async def on_task_started(self, task_id: str) -> None:
        try:
            await self._persistence.update_task_state(task_id, "running")
        except Exception as e:
            logger.error(f"Failed to update task {task_id} start state: {e}")

    async def on_task_completed(self, task_id: str, result: Any = None) -> None:
        try:
            serializable_result = None
            if result is not None:
                if isinstance(result, dict):
                    serializable_result = result
                else:
                    serializable_result = {"value": str(result)}
            await self._persistence.update_task_state(task_id, "completed", result=serializable_result)
        except Exception as e:
            logger.error(f"Failed to update task {task_id} completion state: {e}")

    async def on_task_failed(
        self,
        task_id: str,
        error: str,
        retry_count: int,
        max_retries: int,
        domain_id: str = "",
        action_id: str = "",
        params: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: float | None = None,
    ) -> None:
        if retry_count >= max_retries:
            try:
                await self._persistence.update_task_state(
                    task_id, "failed", error=error, retry_count=retry_count
                )
                original_created = None
                if created_at:
                    original_created = datetime.utcfromtimestamp(created_at)
                await self._persistence.move_to_dlq(
                    task_id=task_id,
                    domain_id=domain_id,
                    action_id=action_id,
                    params=params,
                    error=error,
                    retry_count=retry_count,
                    original_created_at=original_created,
                    tenant_id=tenant_id,
                    metadata=metadata,
                )
            except Exception as e:
                logger.error(f"Failed to handle task {task_id} final failure: {e}")
        else:
            try:
                await self._persistence.update_task_state(
                    task_id, "retrying", error=error, retry_count=retry_count
                )
            except Exception as e:
                logger.error(f"Failed to update task {task_id} retry state: {e}")

    async def recover_tasks(self) -> int:
        try:
            pending = await self._persistence.load_pending_tasks()
            recovered = 0
            for record in pending:
                try:
                    priority_map = {
                        0: TaskPriority.LOW,
                        1: TaskPriority.NORMAL,
                        2: TaskPriority.HIGH,
                        3: TaskPriority.URGENT,
                    }
                    priority = priority_map.get(record.priority, TaskPriority.NORMAL)

                    # RLS-EXEMPT: AsyncTask is an in-memory @dataclass (app/shared/async_processing/task_queue.py), NOT an ORM Base — no DB row written here, no RLS surface. Sensor false positive (user_id kwarg on a DTO).  WT-LEGACY-RLS-EXEMPT exp:2026-11-30
                    task = AsyncTask(
                        task_id=record.id,
                        domain_id=record.domain_id,
                        action_id=record.action_id,
                        params=record.params or {},
                        priority=priority,
                        user_id=record.user_id or "",
                        tenant_id=record.tenant_id,
                        max_retries=record.max_retries or 2,
                        callback=record.callback,
                        metadata=record.metadata_ or {},
                    )

                    queue = self._get_or_create_queue(record.domain_id)
                    if not queue._running:
                        await queue.start()
                    await queue.enqueue(task)
                    self._task_index[record.id] = record.domain_id
                    recovered += 1
                except Exception as e:
                    logger.error(f"Failed to recover task {record.id}: {e}")

            logger.info(f"Recovered {recovered} tasks from database")
            return recovered
        except Exception as e:
            logger.error(f"Task recovery failed: {e}")
            return 0

    async def get_task_history(
        self,
        domain_id: str | None = None,
        state: str | None = None,
        user_id: str | None = None,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return await self._persistence.get_task_history(
            domain_id=domain_id,
            state=state,
            user_id=user_id,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

    def get_stats(self) -> dict[str, Any]:
        base_stats = super().get_stats()
        base_stats["persistence_enabled"] = True
        return base_stats

    async def get_enhanced_stats(self) -> dict[str, Any]:
        base_stats = self.get_stats()
        try:
            db_stats = await self._persistence.get_db_stats()
            base_stats["database"] = db_stats
        except Exception as e:
            logger.error(f"Failed to get DB stats: {e}")
            base_stats["database"] = {"error": str(e)}
        return base_stats

    async def get_task_status_enhanced(self, task_id: str) -> dict[str, Any] | None:
        status = self.get_task_status(task_id)
        if status:
            return status
        return await self._persistence.get_task_record(task_id)

    async def shutdown(self) -> None:
        await self.stop_all()
        self.__class__._instance = None
        logger.info("EnhancedTaskManager shutdown complete")
