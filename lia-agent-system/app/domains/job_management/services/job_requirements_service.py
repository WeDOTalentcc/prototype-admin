"""
JobRequirementsService — Persist and retrieve JobRequirement rubric records.

Extracted from JobIntakeAgent._save_requirements_to_db (Sprint 5).
Callers should use this service instead of the deprecated agent.
"""
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.job_requirement_repository import JobRequirementRepository

from app.core.database import AsyncSessionLocal
from lia_models.rubric import JobRequirement
from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

logger = logging.getLogger(__name__)


class JobRequirementsService:
    """Handles persistence of job requirements for the rubric evaluation system."""

    async def save_requirements(
        self,
        job_id: str,
        requirements: list[JobRequirementCreate],
        db: AsyncSession | None = None,
    ) -> int:
        """
        Persist a list of JobRequirementCreate objects for *job_id*.

        Opens its own session if *db* is not provided.
        Returns the count of saved records.
        """
        job_uuid = UUID(job_id) if isinstance(job_id, str) else job_id

        async def _persist(session: AsyncSession) -> int:
            count = 0
            for req in requirements:
                session.add(
                    JobRequirement(
                        job_vacancy_id=job_uuid,
                        requirement=req.requirement,
                        description=req.description,
                        priority=req.priority.value,
                        category=req.category,
                    )
                )
                count += 1
            await session.commit()
            logger.info(f"Saved {count} requirements for job {job_id}")
            return count

        if db is not None:
            return await _persist(db)

        async with AsyncSessionLocal() as session:
            return await _persist(session)

    def parse_requirements_from_raw(
        self, requirements_data: list[Any]
    ) -> list[JobRequirementCreate]:
        """
        Convert a mixed list (str | dict) of requirement specs into typed objects.

        Used by endpoints that accept flexible input.
        """
        result = []
        for req in requirements_data:
            if isinstance(req, str):
                result.append(
                    JobRequirementCreate(
                        requirement=req,
                        priority=RequirementPriorityEnum.IMPORTANT,
                    )
                )
            elif isinstance(req, dict):
                priority = RequirementPriorityEnum.IMPORTANT
                if req.get("priority"):
                    try:
                        priority = RequirementPriorityEnum(req["priority"])
                    except ValueError:
                        pass
                result.append(
                    JobRequirementCreate(
                        requirement=req.get("requirement", req.get("text", "")),
                        description=req.get("description"),
                        priority=priority,
                        category=req.get("category"),
                    )
                )
        return result

    async def get_requirements_for_job(
        self, job_id: str, db: AsyncSession
    ) -> list[dict[str, Any]]:
        """Return all requirements for a job as serialisable dicts."""
        job_uuid = UUID(job_id) if isinstance(job_id, str) else job_id
        reqs = await JobRequirementRepository(db).list_for_job(job_uuid)
        return [
            {
                "id": str(r.id),
                "requirement": r.requirement,
                "description": r.description,
                "priority": r.priority,
                "category": r.category,
            }
            for r in reqs
        ]


job_requirements_service = JobRequirementsService()
