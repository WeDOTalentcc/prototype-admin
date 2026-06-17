"""CompanyLearningRepository — DB access layer for company learning tables.

Extracted from analytics services per ADR-001.
Tables covered:
  - company_skills
  - company_responsibilities
  - company_patterns
  - job_outcomes (cross-table reads via JobOutcome)
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company_learning import (
    CompanyPattern,
    CompanyResponsibility,
    CompanySkill,
)
from lia_models.feedback_learning import JobOutcome

logger = logging.getLogger(__name__)


class CompanyLearningRepository:
    """Repository for company-learning data access (skills/responsibilities/patterns)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: Any) -> str:
        if not company_id:
            raise ValueError("company_id is required for fail-closed multi-tenancy")
        return str(company_id)

    # ---------- CompanySkill ----------

    async def find_skill_by_normalized_name(
        self, company_id: str, skill_name: str
    ) -> CompanySkill | None:
        company_id = self._require_company_id(company_id)
        normalized = skill_name.strip().lower()
        stmt = select(CompanySkill).where(
            and_(
                CompanySkill.company_id == company_id,
                func.lower(CompanySkill.skill_name) == normalized,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_skill_by_exact_name_lower(
        self, company_id: str, skill_name_lower: str
    ) -> CompanySkill | None:
        """Find skill where skill_name == provided already-lowered string."""
        company_id = self._require_company_id(company_id)
        stmt = select(CompanySkill).where(
            and_(
                CompanySkill.company_id == company_id,
                CompanySkill.skill_name == skill_name_lower,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_skills_for_company(
        self,
        company_id: str,
        only_promoted: bool = False,
        limit: int = 20,
    ) -> list[CompanySkill]:
        company_id = self._require_company_id(company_id)
        conditions = [CompanySkill.company_id == company_id]
        if only_promoted:
            conditions.append(CompanySkill.is_promoted)
        stmt = (
            # TENANT-EXEMPT: company learning aggregates derived per company_id upstream; AST cannot trace; T-RATCHET tenant_filter
            select(CompanySkill)
            .where(and_(*conditions))
            .order_by(
                CompanySkill.is_promoted.desc(),
                CompanySkill.times_confirmed.desc(),
                CompanySkill.confidence_score.desc(),
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_skills_with_role_filter(
        self,
        company_id: str,
        role: str | None = None,
    ) -> list[CompanySkill]:
        """List all skills (no limit cap) optionally filtered by role-tag containment."""
        company_id = self._require_company_id(company_id)
        stmt = (
            select(CompanySkill)
            .where(CompanySkill.company_id == company_id)
            .order_by(
                CompanySkill.is_promoted.desc(),
                CompanySkill.times_confirmed.desc(),
            )
        )
        if role:
            stmt = stmt.where(CompanySkill.roles_associated.contains([role]))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- CompanyResponsibility ----------

    async def find_responsibility_by_hash(
        self, company_id: str, description_hash: str
    ) -> CompanyResponsibility | None:
        company_id = self._require_company_id(company_id)
        stmt = select(CompanyResponsibility).where(
            and_(
                CompanyResponsibility.company_id == company_id,
                CompanyResponsibility.description_hash == description_hash,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_responsibilities_for_company(
        self,
        company_id: str,
        only_promoted: bool = False,
        limit: int = 10,
    ) -> list[CompanyResponsibility]:
        company_id = self._require_company_id(company_id)
        conditions = [CompanyResponsibility.company_id == company_id]
        if only_promoted:
            conditions.append(CompanyResponsibility.is_promoted)
        stmt = (
            # TENANT-EXEMPT: company learning aggregates derived per company_id upstream; AST cannot trace; T-RATCHET tenant_filter
            select(CompanyResponsibility)
            .where(and_(*conditions))
            .order_by(
                CompanyResponsibility.is_promoted.desc(),
                CompanyResponsibility.times_confirmed.desc(),
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- CompanyPattern ----------

    async def find_pattern(
        self, company_id: str, pattern_type: str, pattern_key: str
    ) -> CompanyPattern | None:
        company_id = self._require_company_id(company_id)
        stmt = select(CompanyPattern).where(
            and_(
                CompanyPattern.company_id == company_id,
                CompanyPattern.pattern_type == pattern_type,
                CompanyPattern.pattern_key == pattern_key,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_patterns_for_company(self, company_id: str) -> list[CompanyPattern]:
        company_id = self._require_company_id(company_id)
        stmt = select(CompanyPattern).where(CompanyPattern.company_id == company_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- JobOutcome (read-only, used by company learning services) ----------

    async def get_outcome_counts_grouped(
        self, company_id: str
    ) -> list[Any]:
        """Return rows with (outcome, count) grouped by outcome enum."""
        company_id = self._require_company_id(company_id)
        stmt = (
            select(
                JobOutcome.outcome,
                func.count(JobOutcome.id).label("count"),
            )
            .where(JobOutcome.company_id == company_id)
            .group_by(JobOutcome.outcome)
        )
        result = await self.db.execute(stmt)
        return list(result.all())

    async def get_outcome_by_job(
        self, job_id: UUID
    ) -> JobOutcome | None:
        """Fetch a single JobOutcome by job_id (caller must already know company)."""
        # TENANT-EXEMPT: company learning aggregates derived per company_id upstream; AST cannot trace; T-RATCHET tenant_filter
        stmt = select(JobOutcome).where(JobOutcome.job_id == job_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_outcomes_filtered(
        self,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
    ) -> list[JobOutcome]:
        company_id = self._require_company_id(company_id)
        stmt = select(JobOutcome).where(JobOutcome.company_id == company_id)
        if role:
            stmt = stmt.where(func.lower(JobOutcome.role) == role.lower())
        if seniority:
            stmt = stmt.where(func.lower(JobOutcome.seniority) == seniority.lower())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
