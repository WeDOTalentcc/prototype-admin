"""BigFiveDepartmentProfileRepository - Sprint B Phase 2.

ADR-001: unico lugar onde queries SQL contra bigfive_department_profiles rodam.
Multi-tenancy: company_id obrigatorio (fail-closed).
LGPD: armazena apenas scores agregados. Stability semantics (alto = bom).
"""
from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.bigfive_department_profile import BigFiveDepartmentProfile
# P1-2 canonical fix: ALLOWED_TRAITS moved to shared single source of truth
from app.shared.ocean_constants import ALLOWED_TRAITS

logger = logging.getLogger(__name__)


class BigFiveDepartmentProfileRepository:
    """Repository para BigFiveDepartmentProfile.

    Todas queries scopadas em company_id (multi-tenancy).
    Stability nomenclature consistente com CompanyCultureProfile.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy enforcement)")

    @staticmethod
    def _validate_trait_keys(trait_delta: dict[str, Any]) -> None:
        unknown = set(trait_delta.keys()) - ALLOWED_TRAITS
        if unknown:
            raise ValueError(
                f"trait_delta has invalid keys {sorted(unknown)} - "
                f"only OCEAN traits allowed: {sorted(ALLOWED_TRAITS)}",
            )

    async def get_or_none(
        self,
        company_id: str,
        department: str,
        seniority_level: str,
    ) -> BigFiveDepartmentProfile | None:
        self._require_company_id(company_id)
        stmt = select(BigFiveDepartmentProfile).where(
            and_(
                BigFiveDepartmentProfile.company_id == company_id,
                BigFiveDepartmentProfile.department == department,
                BigFiveDepartmentProfile.seniority_level == seniority_level,
            ),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_for_company(
        self,
        company_id: str,
    ) -> list[BigFiveDepartmentProfile]:
        self._require_company_id(company_id)
        stmt = select(BigFiveDepartmentProfile).where(
            BigFiveDepartmentProfile.company_id == company_id,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        company_id: str,
        department: str,
        seniority_level: str,
        trait_delta: dict[str, float],
        sample_weight: float = 1.0,
        existing_profile: BigFiveDepartmentProfile | None = None,
    ) -> BigFiveDepartmentProfile:
        self._require_company_id(company_id)
        self._validate_trait_keys(trait_delta)

        profile = existing_profile
        if profile is None:
            # P1-Race: SELECT FOR UPDATE serializes concurrent hires to the same
            # (company, dept, seniority) row. Without this, two concurrent
            # transactions both read None → both INSERT → UniqueConstraint violation.
            stmt = (
                select(BigFiveDepartmentProfile)
                .where(
                    and_(
                        BigFiveDepartmentProfile.company_id == company_id,
                        BigFiveDepartmentProfile.department == department,
                        BigFiveDepartmentProfile.seniority_level == seniority_level,
                    )
                )
                .with_for_update()
            )
            result = await self.db.execute(stmt)
            profile = result.scalar_one_or_none()

        if profile is None:
            profile = BigFiveDepartmentProfile(
                company_id=company_id,
                department=department,
                seniority_level=seniority_level,
                sample_count=0,
            )
            self.db.add(profile)

        old_n = profile.sample_count or 0
        new_n = old_n + sample_weight

        if new_n > 0:
            for trait in ALLOWED_TRAITS:
                old_val = getattr(profile, f"{trait}_score", None) or 0.0
                if trait in trait_delta:
                    new_val = trait_delta[trait]
                    updated = (old_val * old_n + new_val * sample_weight) / new_n
                    setattr(profile, f"{trait}_score", round(updated, 4))

        profile.sample_count = int(math.ceil(new_n))
        profile.last_updated_at = datetime.utcnow()

        try:
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

        logger.info(
            "[BigFiveRepo] upsert company_hash=%s seniority=%s n=%d",
            hash(company_id) % 100000,
            seniority_level,
            profile.sample_count,
        )
        return profile
