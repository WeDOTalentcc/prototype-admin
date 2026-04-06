from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.screening import ScreeningTask
import uuid


class ScreeningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task: ScreeningTask) -> ScreeningTask:
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_task_by_id(self, task_uuid: uuid.UUID) -> ScreeningTask | None:
        result = await self.db.execute(
            select(ScreeningTask).where(ScreeningTask.id == task_uuid)
        )
        return result.scalar_one_or_none()

    async def list_tasks_by_job(self, job_id: str) -> list[ScreeningTask]:
        result = await self.db.execute(
            select(ScreeningTask)
            .where(ScreeningTask.job_id == job_id)
            .order_by(ScreeningTask.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_task_status(self, task: ScreeningTask, status: str) -> ScreeningTask:
        task.status = status
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def rollback(self) -> None:
        await self.db.rollback()
