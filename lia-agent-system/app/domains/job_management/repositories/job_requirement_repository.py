"""
JobRequirement Repository — data access for JobRequirement rows.

Per ADR-001 extracted from app/domains/job_management/services/job_requirements_service.py.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.rubric import JobRequirement


class JobRequirementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_job(self, job_uuid: UUID) -> list[JobRequirement]:
        result = await self.db.execute(
            select(JobRequirement).where(JobRequirement.job_vacancy_id == job_uuid)
        )
        return list(result.scalars().all())
