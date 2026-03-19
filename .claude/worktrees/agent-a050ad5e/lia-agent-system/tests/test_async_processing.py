import pytest
import asyncio
import time
from app.shared.async_processing.task_queue import (
    AsyncTask, TaskPriority, TaskState, DomainTaskQueue
)
from app.shared.async_processing.task_manager import DomainTaskManager, ASYNC_ELIGIBLE_ACTIONS


class TestAsyncTask:
    def test_create_task(self):
        task = AsyncTask(
            task_id="test-001",
            domain_id="sourcing",
            action_id="bulk_search",
            params={"skills": ["python"]},
        )
        assert task.task_id == "test-001"
        assert task.domain_id == "sourcing"
        assert task.action_id == "bulk_search"
        assert task.priority == TaskPriority.NORMAL
        assert task.state == TaskState.QUEUED
        assert task.retry_count == 0
        assert task.max_retries == 2

    def test_is_terminal_completed(self):
        task = AsyncTask(task_id="t1", domain_id="d", action_id="a", state=TaskState.COMPLETED)
        assert task.is_terminal is True

    def test_is_terminal_failed(self):
        task = AsyncTask(task_id="t1", domain_id="d", action_id="a", state=TaskState.FAILED)
        assert task.is_terminal is True

    def test_is_terminal_cancelled(self):
        task = AsyncTask(task_id="t1", domain_id="d", action_id="a", state=TaskState.CANCELLED)
        assert task.is_terminal is True

    def test_is_terminal_queued(self):
        task = AsyncTask(task_id="t1", domain_id="d", action_id="a", state=TaskState.QUEUED)
        assert task.is_terminal is False

    def test_is_terminal_running(self):
        task = AsyncTask(task_id="t1", domain_id="d", action_id="a", state=TaskState.RUNNING)
        assert task.is_terminal is False

    def test_duration_seconds(self):
        task = AsyncTask(task_id="t1", domain_id="d", action_id="a")
        task.started_at = 1000.0
        task.completed_at = 1005.0
        assert task.duration_seconds == 5.0

    def test_duration_seconds_running(self):
        task = AsyncTask(task_id="t1", domain_id="d", action_id="a")
        task.started_at = time.time() - 2.0
        dur = task.duration_seconds
        assert dur is not None
        assert dur >= 1.5

    def test_duration_seconds_none(self):
        task = AsyncTask(task_id="t1", domain_id="d", action_id="a")
        assert task.duration_seconds is None

    def test_to_dict(self):
        task = AsyncTask(
            task_id="t1",
            domain_id="sourcing",
            action_id="bulk_search",
            user_id="user_1",
            tenant_id="tenant_1",
        )
        d = task.to_dict()
        assert d["task_id"] == "t1"
        assert d["domain_id"] == "sourcing"
        assert d["action_id"] == "bulk_search"
        assert d["priority"] == "normal"
        assert d["state"] == "queued"
        assert d["user_id"] == "user_1"
        assert d["tenant_id"] == "tenant_1"
        assert "created_at" in d
        assert "metadata" in d

    def test_priority_ordering(self):
        assert TaskPriority.URGENT > TaskPriority.HIGH
        assert TaskPriority.HIGH > TaskPriority.NORMAL
        assert TaskPriority.NORMAL > TaskPriority.LOW
        assert TaskPriority.URGENT.value == 3
        assert TaskPriority.LOW.value == 0


class TestDomainTaskQueue:
    @pytest.fixture
    def queue(self):
        return DomainTaskQueue(domain_id="sourcing", max_concurrent=2, max_queue_size=10)

    @pytest.mark.asyncio
    async def test_enqueue_and_process(self, queue):
        results = []

        async def handler(task):
            results.append(task.task_id)
            return {"processed": True}

        queue.register_handler("bulk_search", handler)
        task = AsyncTask(task_id="t1", domain_id="sourcing", action_id="bulk_search")
        await queue.enqueue(task)
        await queue.start()
        await asyncio.sleep(0.5)
        await queue.stop()

        assert "t1" in results
        completed = queue.get_task_status("t1")
        assert completed is not None
        assert completed.state == TaskState.COMPLETED

    @pytest.mark.asyncio
    async def test_priority_ordering(self, queue):
        order = []

        async def handler(task):
            order.append(task.task_id)
            return {"ok": True}

        queue.register_handler("action", handler)

        low_task = AsyncTask(
            task_id="low", domain_id="sourcing", action_id="action",
            priority=TaskPriority.LOW, created_at=time.time(),
        )
        urgent_task = AsyncTask(
            task_id="urgent", domain_id="sourcing", action_id="action",
            priority=TaskPriority.URGENT, created_at=time.time() + 0.001,
        )
        await queue.enqueue(low_task)
        await queue.enqueue(urgent_task)
        await queue.start()
        await asyncio.sleep(0.5)
        await queue.stop()

        assert order.index("urgent") < order.index("low")

    @pytest.mark.asyncio
    async def test_task_failure_and_retry(self, queue):
        call_count = 0

        async def failing_handler(task):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                raise ValueError("Simulated failure")
            return {"recovered": True}

        queue.register_handler("flaky", failing_handler)
        task = AsyncTask(
            task_id="retry-t", domain_id="sourcing", action_id="flaky",
            max_retries=2,
        )
        await queue.enqueue(task)
        await queue.start()
        await asyncio.sleep(1.5)
        await queue.stop()

        assert call_count >= 2
        status = queue.get_task_status("retry-t")
        assert status is not None
        assert status.state == TaskState.COMPLETED

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, queue):
        async def always_fails(task):
            raise RuntimeError("Always fails")

        queue.register_handler("bad", always_fails)
        task = AsyncTask(
            task_id="fail-t", domain_id="sourcing", action_id="bad",
            max_retries=1,
        )
        await queue.enqueue(task)
        await queue.start()
        await asyncio.sleep(2.0)
        await queue.stop()

        status = queue.get_task_status("fail-t")
        assert status is not None
        assert status.state == TaskState.FAILED
        assert status.error is not None

    @pytest.mark.asyncio
    async def test_get_task_status(self, queue):
        async def handler(task):
            await asyncio.sleep(0.1)
            return {"done": True}

        queue.register_handler("check", handler)
        task = AsyncTask(task_id="status-t", domain_id="sourcing", action_id="check")
        await queue.enqueue(task)
        await queue.start()
        await asyncio.sleep(0.5)
        await queue.stop()

        status = queue.get_task_status("status-t")
        assert status is not None
        assert status.state == TaskState.COMPLETED

        missing = queue.get_task_status("nonexistent")
        assert missing is None

    def test_get_queue_info(self, queue):
        info = queue.get_queue_info()
        assert info["domain_id"] == "sourcing"
        assert info["queue_size"] == 0
        assert info["active_tasks"] == 0
        assert info["total_processed"] == 0
        assert info["total_failed"] == 0
        assert info["max_concurrent"] == 2
        assert info["running"] is False

    @pytest.mark.asyncio
    async def test_cancel_task(self, queue):
        task = AsyncTask(task_id="cancel-t", domain_id="sourcing", action_id="x")
        queue._active_tasks["cancel-t"] = task

        result = queue.cancel_task("cancel-t")
        assert result is True
        assert task.state == TaskState.CANCELLED

        result2 = queue.cancel_task("cancel-t")
        assert result2 is False

    @pytest.mark.asyncio
    async def test_stop(self, queue):
        await queue.start()
        assert queue._running is True
        assert len(queue._workers) == 2

        await queue.stop()
        assert queue._running is False
        assert len(queue._workers) == 0


class TestDomainTaskManager:
    def setup_method(self):
        DomainTaskManager.reset_instance()

    def teardown_method(self):
        DomainTaskManager.reset_instance()

    @pytest.mark.asyncio
    async def test_submit_task(self):
        manager = DomainTaskManager(max_concurrent_per_domain=1)
        task_id = await manager.submit_task(
            domain_id="sourcing",
            action_id="bulk_search",
            params={"skills": ["python"]},
            user_id="u1",
        )
        assert task_id is not None
        assert len(task_id) == 12
        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_get_task_status(self):
        manager = DomainTaskManager(max_concurrent_per_domain=1)

        async def handler(task):
            return {"result": "ok"}

        manager.register_handler("sourcing", "test_action", handler)
        task_id = await manager.submit_task(
            domain_id="sourcing", action_id="test_action",
        )
        await asyncio.sleep(0.5)

        status = manager.get_task_status(task_id)
        assert status is not None
        assert status["task_id"] == task_id
        assert status["state"] == "completed"
        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        manager = DomainTaskManager(max_concurrent_per_domain=1)
        queue = manager._get_or_create_queue("sourcing")
        task = AsyncTask(task_id="cancel-m", domain_id="sourcing", action_id="x")
        queue._active_tasks["cancel-m"] = task
        manager._task_index["cancel-m"] = "sourcing"

        result = manager.cancel_task("cancel-m")
        assert result is True

        result2 = manager.cancel_task("nonexistent")
        assert result2 is False

    def test_is_async_eligible(self):
        manager = DomainTaskManager()
        assert manager.is_async_eligible("sourcing", "bulk_search") is True
        assert manager.is_async_eligible("sourcing", "search") is False
        assert manager.is_async_eligible("cv_screening", "bulk_screen") is True
        assert manager.is_async_eligible("communication", "mass_email") is True

    def test_is_async_eligible_unknown_domain(self):
        manager = DomainTaskManager()
        assert manager.is_async_eligible("unknown_domain", "some_action") is False

    @pytest.mark.asyncio
    async def test_list_tasks(self):
        manager = DomainTaskManager(max_concurrent_per_domain=1)

        async def handler(task):
            return {"done": True}

        manager.register_handler("sourcing", "a1", handler)
        manager.register_handler("analytics", "a2", handler)

        await manager.submit_task(domain_id="sourcing", action_id="a1", user_id="u1")
        await manager.submit_task(domain_id="analytics", action_id="a2", user_id="u2")
        await asyncio.sleep(0.5)

        all_tasks = manager.list_tasks()
        assert len(all_tasks) >= 2

        sourcing_tasks = manager.list_tasks(domain_id="sourcing")
        assert all(t["domain_id"] == "sourcing" for t in sourcing_tasks)

        user_tasks = manager.list_tasks(user_id="u1")
        assert all(t["user_id"] == "u1" for t in user_tasks)
        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_get_stats(self):
        manager = DomainTaskManager(max_concurrent_per_domain=1)

        async def handler(task):
            return {"done": True}

        manager.register_handler("sourcing", "s1", handler)
        await manager.submit_task(domain_id="sourcing", action_id="s1")
        await asyncio.sleep(0.5)

        stats = manager.get_stats()
        assert stats["total_queues"] >= 1
        assert stats["total_processed"] >= 1
        assert "queues" in stats
        await manager.stop_all()

    def test_singleton(self):
        m1 = DomainTaskManager.get_instance()
        m2 = DomainTaskManager.get_instance()
        assert m1 is m2

    def test_reset_singleton(self):
        m1 = DomainTaskManager.get_instance()
        DomainTaskManager.reset_instance()
        m2 = DomainTaskManager.get_instance()
        assert m1 is not m2

    @pytest.mark.asyncio
    async def test_submit_with_handler(self):
        manager = DomainTaskManager(max_concurrent_per_domain=1)

        async def search_handler(task):
            return {"found": len(task.params.get("skills", [])) * 10}

        manager.register_handler("sourcing", "bulk_search", search_handler)
        task_id = await manager.submit_task(
            domain_id="sourcing",
            action_id="bulk_search",
            params={"skills": ["python", "java"]},
            priority=TaskPriority.HIGH,
        )
        await asyncio.sleep(0.5)

        status = manager.get_task_status(task_id)
        assert status is not None
        assert status["state"] == "completed"
        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_get_all_queue_info(self):
        manager = DomainTaskManager(max_concurrent_per_domain=1)
        manager._get_or_create_queue("sourcing")
        manager._get_or_create_queue("analytics")

        info = manager.get_all_queue_info()
        assert "sourcing" in info
        assert "analytics" in info
        assert info["sourcing"]["domain_id"] == "sourcing"
        assert info["analytics"]["domain_id"] == "analytics"
