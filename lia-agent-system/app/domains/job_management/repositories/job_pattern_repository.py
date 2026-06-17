"""
JobPattern Repository — data access for learned hiring patterns / salary benchmarks /
job outcomes used by JobPatternService.

Per ADR-001 extracted from app/domains/job_management/services/job_pattern_service.py.
"""
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.feedback_learning import JobOutcome
from lia_models.job_pattern import JobPattern, SalaryBenchmark


class JobPatternRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_patterns_with_conditions(
        self, conditions: list[Any], limit: int
    ) -> list[JobPattern]:
        # TENANT-EXEMPT: dynamic builder — caller (job_pattern_service)
        # composes ``conditions`` list always starting with
        # JobPattern.company_id == X; AST sensor cannot trace upstream gate.
        result = await self.db.execute(
            select(JobPattern)
            .where(and_(*conditions))
            .order_by(
                JobPattern.confidence.desc(), JobPattern.sample_count.desc()
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_salary_benchmark(
        self, conditions: list[Any]
    ) -> SalaryBenchmark | None:
        # TENANT-EXEMPT: dynamic builder — caller composes ``conditions``
        # list always starting with SalaryBenchmark.company_id == X; AST
        # sensor cannot trace upstream gate.
        result = await self.db.execute(
            select(SalaryBenchmark)
            .where(and_(*conditions))
            .order_by(SalaryBenchmark.sample_count.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_successful_outcomes(
        self,
        *,
        company_id: UUID,
        job_title_normalized: str,
        min_quality: float = 4.0,
        limit: int = 10,
    ) -> list[JobOutcome]:
        result = await self.db.execute(
            select(JobOutcome)
            .where(
                and_(
                    JobOutcome.company_id == company_id,
                    JobOutcome.outcome_status.in_(["filled", "hired"]),
                    JobOutcome.hire_quality_score >= min_quality,
                    JobOutcome.job_title_normalized == job_title_normalized,
                )
            )
            .order_by(JobOutcome.hire_quality_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_pattern_by_key(
        self, *, company_id: Any, pattern_key: str
    ) -> JobPattern | None:
        result = await self.db.execute(
            select(JobPattern).where(
                and_(
                    JobPattern.company_id == company_id,
                    JobPattern.pattern_key == pattern_key,
                    JobPattern.is_active,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_salary_benchmark_for_outcome(
        self, *, company_id: Any, job_title_normalized: str, seniority: str | None
    ) -> SalaryBenchmark | None:
        result = await self.db.execute(
            select(SalaryBenchmark).where(
                and_(
                    SalaryBenchmark.company_id == company_id,
                    SalaryBenchmark.job_title_normalized == job_title_normalized,
                    SalaryBenchmark.seniority == seniority,
                )
            )
        )
        return result.scalar_one_or_none()
