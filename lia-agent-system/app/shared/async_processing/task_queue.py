import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)

# Lazy import to avoid circular deps — loaded on first use
_priority_calculator = None


def _get_priority_calculator():
    global _priority_calculator
    if _priority_calculator is None:
        try:
            from app.shared.async_processing.priority_calculator import priority_calculator
            _priority_calculator = priority_calculator
        except Exception as exc:
            logger.warning("[TaskQueue] PriorityCalculator unavailable (fail-open): %s", exc)
    return _priority_calculator


class TaskPriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class TaskState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class AsyncTask:
    task_id: str
    domain_id: str
    action_id: str
    params: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    state: TaskState = TaskState.QUEUED
    result: Any | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 2
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    user_id: str = ""
    tenant_id: str | None = None
    callback: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED)

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return time.time() - self.started_at
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "domain_id": self.domain_id,
            "action_id": self.action_id,
            "priority": self.priority.name.lower(),
            "state": self.state.value,
            "error": self.error,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
        }


class DomainTaskQueue:
    """
    Per-domain async task queue with priority support.
    Uses asyncio.PriorityQueue for ordering.
    """

    def __init__(self, domain_id: str, max_concurrent: int = 3, max_queue_size: int = 100):
        self.domain_id = domain_id
        self._max_concurrent = max_concurrent
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._active_tasks: dict[str, AsyncTask] = {}
        self._completed_tasks: dict[str, AsyncTask] = {}
        self._max_completed_history = 50
        self._running = False
        self._workers: list[asyncio.Task] = []
        self._task_handlers: dict[str, Callable] = {}
        self._total_processed = 0
        self._total_failed = 0

    def register_handler(self, action_id: str, handler: Callable[[AsyncTask], Awaitable[Any]]) -> None:
        self._task_handlers[action_id] = handler

    async def enqueue(
        self,
        task: AsyncTask,
        priority: int | None = None,
    ) -> str:
        """Enqueue a task for processing.

        Args:
            task: The AsyncTask to enqueue.
            priority: Optional numeric priority override (1=URGENT … 5=LOW).
                      If None and task.priority is still NORMAL, attempts to
                      compute urgency via PriorityCalculator using task.action_id
                      and task.metadata (E11 — Priority Queue).
                      Lower number = higher priority.

        Returns:
            task_id of the enqueued task.
        """
        # E11: auto-compute priority if not explicitly set
        if priority is not None:
            # Map numeric priority (1–5) to TaskPriority enum value
            # Invert: priority 1 (urgent) → TaskPriority.URGENT (3); 5 (low) → TaskPriority.LOW (0)
            _numeric_to_enum = {1: TaskPriority.URGENT, 2: TaskPriority.HIGH,
                                3: TaskPriority.NORMAL, 5: TaskPriority.LOW}
            task.priority = _numeric_to_enum.get(priority, TaskPriority.NORMAL)
        elif task.priority == TaskPriority.NORMAL:
            calc = _get_priority_calculator()
            if calc is not None:
                try:
                    computed = calc.compute(task.action_id, task.metadata)
                    _numeric_to_enum = {1: TaskPriority.URGENT, 2: TaskPriority.HIGH,
                                        3: TaskPriority.NORMAL, 5: TaskPriority.LOW}
                    task.priority = _numeric_to_enum.get(computed, TaskPriority.NORMAL)
                    logger.debug(
                        "[TaskQueue] E11 auto-priority: task=%s action=%s → %s",
                        task.task_id, task.action_id, task.priority.name,
                    )
                except Exception as exc:
                    logger.warning("[TaskQueue] PriorityCalculator.compute failed (fail-open): %s", exc)

        priority_key = -task.priority.value
        await self._queue.put((priority_key, task.created_at, task))
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.debug(f"Task {task.task_id} enqueued in {self.domain_id} queue (priority={task.priority.name})")
        return task.task_id

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        for i in range(self._max_concurrent):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._workers.append(worker)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"DomainTaskQueue '{self.domain_id}' started with {self._max_concurrent} workers")

    async def stop(self) -> None:
        self._running = False
        for worker in self._workers:
            worker.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"DomainTaskQueue '{self.domain_id}' stopped")

    async def drain(self) -> None:
        await self._queue.join()
        await self.stop()

    async def _worker_loop(self, worker_name: str) -> None:
        while self._running:
            try:
                priority_key, created_at, task = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
                await self._process_task(task, worker_name)
                self._queue.task_done()
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.error(f"Worker {worker_name} error: {e}", exc_info=True)

    async def _process_task(self, task: AsyncTask, worker_name: str) -> None:
        task.state = TaskState.RUNNING
        task.started_at = time.time()
        self._active_tasks[task.task_id] = task

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
            else:
                task.state = TaskState.FAILED
                task.error = str(e)
                task.completed_at = time.time()
                self._total_failed += 1

        finally:
            self._active_tasks.pop(task.task_id, None)
            if task.is_terminal:
                self._completed_tasks[task.task_id] = task
                if len(self._completed_tasks) > self._max_completed_history:
                    oldest_key = min(self._completed_tasks,
                                     key=lambda k: self._completed_tasks[k].completed_at or 0)
                    del self._completed_tasks[oldest_key]

    def get_task_status(self, task_id: str) -> AsyncTask | None:
        if task_id in self._active_tasks:
            return self._active_tasks[task_id]
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        return None

    def cancel_task(self, task_id: str) -> bool:
        task = self._active_tasks.get(task_id) or self._completed_tasks.get(task_id)
        if task and not task.is_terminal:
            task.state = TaskState.CANCELLED
            task.completed_at = time.time()
            return True
        return False

    def get_queue_info(self) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "queue_size": self._queue.qsize(),
            "active_tasks": len(self._active_tasks),
            "completed_history": len(self._completed_tasks),
            "total_processed": self._total_processed,
            "total_failed": self._total_failed,
            "max_concurrent": self._max_concurrent,
            "running": self._running,
        }
