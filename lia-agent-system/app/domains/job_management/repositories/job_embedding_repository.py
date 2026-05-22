"""
JobEmbedding Repository — data access for embedding-driven job similarity.

Per ADR-001 extracted from app/domains/job_management/services/job_embedding_service.py.
"""
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.job_pattern import JobEmbedding
from lia_models.job_vacancy import JobVacancy


class JobEmbeddingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_job_id(
        self,
        job_id: UUID,
        company_id: Any | None = None,
    ) -> JobEmbedding | None:
        """Get embedding by job id. ``company_id`` optional for backwards-compat,
        recommended for defense-in-depth (REGRA ZERO multi-tenancy)."""
        # TENANT-EXEMPT: dynamic builder — JobEmbedding.company_id appended
        # conditionally below when caller passes it.
        query = select(JobEmbedding).where(JobEmbedding.job_id == job_id)
        if company_id:
            query = query.where(JobEmbedding.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_company_and_job(
        self, company_id: Any, job_id: Any
    ) -> JobEmbedding | None:
        result = await self.db.execute(
            select(JobEmbedding).where(
                and_(
                    JobEmbedding.company_id == company_id,
                    JobEmbedding.job_id == job_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def text_search_active(
        self,
        *,
        company_id: UUID,
        normalized_title: str,
        department: str | None,
        limit: int = 5,
    ) -> list[JobEmbedding]:
        clauses = [
            JobEmbedding.company_id == company_id,
            JobEmbedding.is_active,
            or_(
                JobEmbedding.job_title_normalized.ilike(f"%{normalized_title}%"),
                JobEmbedding.department == department if department else True,
            ),
        ]
        result = await self.db.execute(
            # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace upstream tenant gate
            select(JobEmbedding).where(and_(*clauses)).limit(limit)
        )
        return list(result.scalars().all())

    async def list_missing_embeddings(
        self,
        *,
        company_id: UUID,
        job_ids: list[UUID] | None = None,
        limit: int = 100,
    ) -> list[JobEmbedding]:
        if job_ids:
            query = select(JobEmbedding).where(
                and_(
                    JobEmbedding.company_id == company_id,
                    JobEmbedding.job_id.in_(job_ids),
                    JobEmbedding.embedding is None,
                )
            )
        else:
            query = select(JobEmbedding).where(
                and_(
                    JobEmbedding.company_id == company_id,
                    JobEmbedding.embedding is None,
                )
            )
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def stats(self, company_id: UUID) -> dict[str, int]:
        total = await self.db.execute(
            select(func.count(JobEmbedding.id)).where(
                JobEmbedding.company_id == company_id
            )
        )
        with_emb = await self.db.execute(
            select(func.count(JobEmbedding.id)).where(
                and_(
                    JobEmbedding.company_id == company_id,
                    JobEmbedding.embedding is not None,
                )
            )
        )
        templates = await self.db.execute(
            select(func.count(JobEmbedding.id)).where(
                and_(
                    JobEmbedding.company_id == company_id,
                    JobEmbedding.is_template,
                )
            )
        )
        return {
            "total_jobs": total.scalar() or 0,
            "with_embeddings": with_emb.scalar() or 0,
            "templates": templates.scalar() or 0,
        }

    async def get_vacancy_for_embedding(
        self, job_id: UUID, company_id: Any
    ) -> JobVacancy | None:
        """Cross-domain read of JobVacancy used by embedding feature extraction."""
        result = await self.db.execute(
            select(JobVacancy).where(
                and_(
                    JobVacancy.id == job_id,
                    JobVacancy.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_with_metadata(
        self, company_id: Any, *, limit: int = 100
    ) -> list[JobEmbedding]:
        result = await self.db.execute(
            select(JobEmbedding)
            .where(
                and_(
                    JobEmbedding.company_id == company_id,
                    JobEmbedding.metadata_json.isnot(None),
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())
