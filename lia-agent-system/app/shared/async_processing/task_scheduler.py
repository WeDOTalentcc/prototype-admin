import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.task_record import TaskSchedule

logger = logging.getLogger(__name__)


def _parse_cron_field(field: str, min_val: int, max_val: int) -> set[int]:
    values: set[int] = set()
    for part in field.split(","):
        part = part.strip()
        if part == "*":
            values.update(range(min_val, max_val + 1))
        elif "/" in part:
            base, step_str = part.split("/", 1)
            step = int(step_str)
            if base == "*":
                start = min_val
            else:
                start = int(base)
            values.update(range(start, max_val + 1, step))
        elif "-" in part:
            low, high = part.split("-", 1)
            values.update(range(int(low), int(high) + 1))
        else:
            values.add(int(part))
    return values


def parse_cron_expression(expression: str) -> dict[str, set[int]]:
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {expression}. Expected 5 fields.")
    return {
        "minute": _parse_cron_field(parts[0], 0, 59),
        "hour": _parse_cron_field(parts[1], 0, 23),
        "day_of_month": _parse_cron_field(parts[2], 1, 31),
        "month": _parse_cron_field(parts[3], 1, 12),
        "day_of_week": _parse_cron_field(parts[4], 0, 6),
    }


def cron_matches(expression: str, dt: datetime) -> bool:
    try:
        parsed = parse_cron_expression(expression)
    except ValueError:
        return False
    return (
        dt.minute in parsed["minute"]
        and dt.hour in parsed["hour"]
        and dt.day in parsed["day_of_month"]
        and dt.month in parsed["month"]
        and dt.weekday() in parsed["day_of_week"]
    )


def next_cron_time(expression: str, after: datetime | None = None) -> datetime | None:
    if after is None:
        after = datetime.utcnow()
    candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(525960):
        if cron_matches(expression, candidate):
            return candidate
        candidate += timedelta(minutes=1)
    return None


class TaskScheduler:
    _instance: Optional["TaskScheduler"] = None

    @classmethod
    def get_instance(cls) -> "TaskScheduler":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self._check_interval = 60

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("TaskScheduler started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("TaskScheduler stopped")

    async def _scheduler_loop(self) -> None:
        while self._running:
            try:
                await self._check_schedules()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}", exc_info=True)
            try:
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break

    async def _check_schedules(self) -> None:
        now = datetime.utcnow()
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(TaskSchedule).where(
                    TaskSchedule.is_active,
                    TaskSchedule.next_run_at <= now,
                )
                result = await session.execute(stmt)
                schedules = result.scalars().all()

                for schedule in schedules:
                    try:
                        await self._execute_schedule(schedule, session)
                    except Exception as e:
                        logger.error(f"Failed to execute schedule {schedule.id}: {e}")

                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to check schedules: {e}")

    async def _execute_schedule(self, schedule: TaskSchedule, session: AsyncSession) -> None:
        from app.shared.async_processing.enhanced_task_manager import EnhancedTaskManager

        manager = EnhancedTaskManager.get_instance()
        from app.shared.async_processing.task_queue import TaskPriority

        priority_map = {0: TaskPriority.LOW, 1: TaskPriority.NORMAL, 2: TaskPriority.HIGH, 3: TaskPriority.URGENT}
        priority = priority_map.get(schedule.priority, TaskPriority.NORMAL)

        task_id = await manager.submit_task(
            domain_id=schedule.domain_id,
            action_id=schedule.action_id,
            params=schedule.params or {},
            user_id=schedule.user_id or "system",
            tenant_id=schedule.tenant_id,
            priority=priority,
            max_retries=schedule.max_retries or 2,
            metadata={"scheduled_by": schedule.id, "schedule_name": schedule.name},
        )

        schedule.last_run_at = datetime.utcnow()
        schedule.run_count = (schedule.run_count or 0) + 1
        schedule.next_run_at = next_cron_time(schedule.cron_expression)

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Schedule '{schedule.name}' triggered task {task_id}")

    async def add_schedule(
        self,
        name: str,
        domain_id: str,
        action_id: str,
        cron_expression: str,
        params: dict[str, Any] | None = None,
        priority: int = 1,
        tenant_id: str | None = None,
        user_id: str = "system",
        max_retries: int = 2,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        parse_cron_expression(cron_expression)
        schedule_id = str(uuid.uuid4())
        computed_next = next_cron_time(cron_expression)

        async with AsyncSessionLocal() as session:
            try:
                # RLS-EXEMPT: task_schedules has no company_id column and no RLS policy (global cron-like scheduler state, not tenant-scoped data).  WT-LEGACY-RLS-EXEMPT exp:2026-11-30
                record = TaskSchedule(
                    id=schedule_id,
                    name=name,
                    domain_id=domain_id,
                    action_id=action_id,
                    params=params or {},
                    cron_expression=cron_expression,
                    priority=priority,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    max_retries=max_retries,
                    metadata_=metadata or {},
                    next_run_at=computed_next,
                )
                session.add(record)
                await session.commit()
                await session.refresh(record)
                # pii-logs ok: nome de config (manager/schedule), nao PII pessoa natural
                logger.info(f"Schedule '{name}' created with id {schedule_id}")
                return record.to_dict()
            except Exception as e:
                await session.rollback()
                # pii-logs ok: nome de config (manager/schedule), nao PII pessoa natural
                logger.error(f"Failed to add schedule '{name}': {e}")
                raise

    async def remove_schedule(self, schedule_id: str) -> bool:
        async with AsyncSessionLocal() as session:
            try:
                stmt = delete(TaskSchedule).where(TaskSchedule.id == schedule_id)
                result = await session.execute(stmt)
                await session.commit()
                removed = result.rowcount > 0
                if removed:
                    logger.info(f"Schedule {schedule_id} removed")
                return removed
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to remove schedule {schedule_id}: {e}")
                return False

    async def list_schedules(
        self,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(TaskSchedule)
                if active_only:
                    stmt = stmt.where(TaskSchedule.is_active)
                stmt = stmt.order_by(TaskSchedule.created_at.desc()).limit(limit).offset(offset)
                result = await session.execute(stmt)
                records = result.scalars().all()
                return [r.to_dict() for r in records]
            except Exception as e:
                logger.error(f"Failed to list schedules: {e}")
                return []
