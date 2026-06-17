import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_, desc, select, update

from app.core.database import AsyncSessionLocal
from app.models.task_record import DeadLetterRecord, TaskRecord

logger = logging.getLogger(__name__)


class TaskPersistenceService:
    _instance: Optional["TaskPersistenceService"] = None

    @classmethod
    def get_instance(cls) -> "TaskPersistenceService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def save_task(
        self,
        task_id: str,
        domain_id: str,
        action_id: str,
        params: dict[str, Any] | None = None,
        priority: int = 1,
        state: str = "queued",
        user_id: str = "",
        tenant_id: str | None = None,
        max_retries: int = 2,
        callback: str | None = None,
        metadata: dict[str, Any] | None = None,
        scheduled_at: datetime | None = None,
    ) -> TaskRecord:
        async with AsyncSessionLocal() as session:
            try:
                # RLS-EXEMPT: task_records has no company_id column and no RLS policy (global async-job persistence, not tenant-scoped data).  WT-LEGACY-RLS-EXEMPT exp:2026-11-30
                record = TaskRecord(
                    id=task_id,
                    domain_id=domain_id,
                    action_id=action_id,
                    params=params or {},
                    priority=priority,
                    state=state,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    max_retries=max_retries,
                    callback=callback,
                    metadata_=metadata or {},
                    scheduled_at=scheduled_at,
                )
                session.add(record)
                await session.commit()
                await session.refresh(record)
                logger.debug(f"Task {task_id} persisted to database")
                return record
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to persist task {task_id}: {e}")
                raise

    async def update_task_state(
        self,
        task_id: str,
        state: str,
        result: Any | None = None,
        error: str | None = None,
        retry_count: int | None = None,
    ) -> None:
        async with AsyncSessionLocal() as session:
            try:
                values: dict[str, Any] = {"state": state}
                if state == "running":
                    values["started_at"] = datetime.utcnow()
                if state in ("completed", "failed", "cancelled"):
                    values["completed_at"] = datetime.utcnow()
                if result is not None:
                    values["result"] = result
                if error is not None:
                    values["error"] = error
                if retry_count is not None:
                    values["retry_count"] = retry_count

                stmt = update(TaskRecord).where(TaskRecord.id == task_id).values(**values)
                await session.execute(stmt)
                await session.commit()
                logger.debug(f"Task {task_id} state updated to {state}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update task {task_id} state: {e}")

    async def load_pending_tasks(self) -> list[TaskRecord]:
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(TaskRecord).where(
                    TaskRecord.state.in_(["queued", "running", "retrying"])
                ).order_by(TaskRecord.created_at)
                result = await session.execute(stmt)
                records = result.scalars().all()
                logger.info(f"Loaded {len(records)} pending tasks from database")
                return list(records)
            except Exception as e:
                logger.error(f"Failed to load pending tasks: {e}")
                return []

    async def get_task_history(
        self,
        domain_id: str | None = None,
        state: str | None = None,
        user_id: str | None = None,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            try:
                conditions = []
                if domain_id:
                    conditions.append(TaskRecord.domain_id == domain_id)
                if state:
                    conditions.append(TaskRecord.state == state)
                if user_id:
                    conditions.append(TaskRecord.user_id == user_id)
                if tenant_id:
                    conditions.append(TaskRecord.tenant_id == tenant_id)

                stmt = select(TaskRecord)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
                stmt = stmt.order_by(desc(TaskRecord.created_at)).limit(limit).offset(offset)

                result = await session.execute(stmt)
                records = result.scalars().all()
                return [r.to_dict() for r in records]
            except Exception as e:
                logger.error(f"Failed to get task history: {e}")
                return []

    async def get_task_record(self, task_id: str) -> dict[str, Any] | None:
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(TaskRecord).where(TaskRecord.id == task_id)
                result = await session.execute(stmt)
                record = result.scalar_one_or_none()
                if record:
                    return record.to_dict()
                return None
            except Exception as e:
                logger.error(f"Failed to get task record {task_id}: {e}")
                return None

    async def move_to_dlq(
        self,
        task_id: str,
        domain_id: str,
        action_id: str,
        params: dict[str, Any] | None = None,
        error: str = "",
        retry_count: int = 0,
        original_created_at: datetime | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        dlq_id = str(uuid.uuid4())
        async with AsyncSessionLocal() as session:
            try:
                record = DeadLetterRecord(
                    id=dlq_id,
                    original_task_id=task_id,
                    domain_id=domain_id,
                    action_id=action_id,
                    params=params or {},
                    error=error,
                    retry_count=retry_count,
                    original_created_at=original_created_at,
                    tenant_id=tenant_id,
                    metadata_=metadata or {},
                )
                session.add(record)
                await session.commit()
                logger.info(f"Task {task_id} moved to dead letter queue as {dlq_id}")
                return dlq_id
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to move task {task_id} to DLQ: {e}")
                raise

    async def list_dlq(
        self,
        resolved: bool | None = None,
        domain_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            try:
                conditions = []
                if resolved is not None:
                    conditions.append(DeadLetterRecord.resolved == resolved)
                if domain_id:
                    conditions.append(DeadLetterRecord.domain_id == domain_id)

                stmt = select(DeadLetterRecord)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
                stmt = stmt.order_by(desc(DeadLetterRecord.moved_at)).limit(limit).offset(offset)

                result = await session.execute(stmt)
                records = result.scalars().all()
                return [r.to_dict() for r in records]
            except Exception as e:
                logger.error(f"Failed to list DLQ: {e}")
                return []

    async def get_dlq_record(self, dlq_id: str) -> DeadLetterRecord | None:
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(DeadLetterRecord).where(DeadLetterRecord.id == dlq_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                logger.error(f"Failed to get DLQ record {dlq_id}: {e}")
                return None

    async def resolve_dlq(self, dlq_id: str) -> bool:
        async with AsyncSessionLocal() as session:
            try:
                stmt = (
                    update(DeadLetterRecord)
                    .where(DeadLetterRecord.id == dlq_id)
                    .values(resolved=True, resolved_at=datetime.utcnow())
                )
                await session.execute(stmt)
                await session.commit()
                logger.info(f"DLQ entry {dlq_id} resolved")
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to resolve DLQ entry {dlq_id}: {e}")
                return False

    async def get_db_stats(self) -> dict[str, Any]:
        async with AsyncSessionLocal() as session:
            try:
                from sqlalchemy import func

                total_stmt = select(func.count(TaskRecord.id))
                total_result = await session.execute(total_stmt)
                total = total_result.scalar() or 0

                by_state_stmt = select(
                    TaskRecord.state, func.count(TaskRecord.id)
                ).group_by(TaskRecord.state)
                by_state_result = await session.execute(by_state_stmt)
                by_state = {row[0]: row[1] for row in by_state_result.all()}

                dlq_stmt = select(func.count(DeadLetterRecord.id)).where(
                    not DeadLetterRecord.resolved
                )
                dlq_result = await session.execute(dlq_stmt)
                dlq_unresolved = dlq_result.scalar() or 0

                return {
                    "total_records": total,
                    "by_state": by_state,
                    "dlq_unresolved": dlq_unresolved,
                }
            except Exception as e:
                logger.error(f"Failed to get DB stats: {e}")
                return {"total_records": 0, "by_state": {}, "dlq_unresolved": 0}
