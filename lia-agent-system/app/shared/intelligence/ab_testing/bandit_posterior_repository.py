"""T-19 Fase 2: BanditPosteriorRepository canonical (ADR-AB-001).

Repository pattern (ADR-001) para BanditPosterior CRUD.
Pattern UPSERT canonical: get_or_create + update_posterior atomic.
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.bandit_posterior import BanditPosterior


logger = logging.getLogger(__name__)


class BanditPosteriorRepository:
    """Canonical repo BanditPosterior (T-19 Fase 2 ADR-AB-001)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _normalize_company_id(self, company_id) -> Optional[UUID]:
        """Normalize company_id: None → None (global), str → UUID, UUID → UUID."""
        if company_id is None:
            return None
        if isinstance(company_id, str):
            return UUID(company_id)
        return company_id

    async def get_posterior(
        self,
        test_name: str,
        arm: str,
        company_id=None,
    ) -> Optional[BanditPosterior]:
        """Get posterior por (test_name, arm, company_id). None se não existe."""
        company_id_norm = self._normalize_company_id(company_id)
        conditions = [
            BanditPosterior.test_name == test_name,
            BanditPosterior.arm == arm,
        ]
        if company_id_norm is None:
            conditions.append(BanditPosterior.company_id.is_(None))
        else:
            conditions.append(BanditPosterior.company_id == company_id_norm)

        # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter
        stmt = select(BanditPosterior).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all_for_test(
        self, test_name: str, company_id=None
    ) -> list[BanditPosterior]:
        """Get all posteriors para test_name + company (canonical bandit choice)."""
        company_id_norm = self._normalize_company_id(company_id)
        conditions = [BanditPosterior.test_name == test_name]
        if company_id_norm is None:
            conditions.append(BanditPosterior.company_id.is_(None))
        else:
            conditions.append(BanditPosterior.company_id == company_id_norm)

        # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter
        stmt = select(BanditPosterior).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert_posterior(
        self,
        test_name: str,
        arm: str,
        alpha: float,
        beta: float,
        company_id=None,
        n_observations: Optional[int] = None,
    ) -> BanditPosterior:
        """UPSERT canonical: criar ou atualizar posterior atomically.

        Args:
            test_name: experiment identifier
            arm: variant identifier
            alpha: Beta posterior α parameter (successes + 1)
            beta: Beta posterior β parameter (failures + 1)
            company_id: None for global, UUID per-tenant
            n_observations: total samples observed (audit aid)

        Returns:
            BanditPosterior canonical row (created or updated).
        """
        if alpha < 0 or beta < 0:
            raise ValueError(
                f"alpha and beta must be non-negative (got α={alpha}, β={beta})"
            )

        existing = await self.get_posterior(test_name, arm, company_id)
        company_id_norm = self._normalize_company_id(company_id)

        if existing is None:
            # INSERT
            record = BanditPosterior(
                test_name=test_name,
                arm=arm,
                alpha=alpha,
                beta=beta,
                n_observations=n_observations or 0,
                company_id=company_id_norm,
            )
            self.db.add(record)
            await self.db.flush()
            logger.info(
                "[BanditPosteriorRepository] INSERTED %s:%s α=%.2f β=%.2f company=%s",
                test_name, arm, alpha, beta, company_id_norm,
            )
            return record

        # UPDATE
        existing.alpha = alpha
        existing.beta = beta
        if n_observations is not None:
            existing.n_observations = n_observations
        await self.db.flush()
        logger.info(
            "[BanditPosteriorRepository] UPDATED %s:%s α=%.2f β=%.2f company=%s",
            test_name, arm, alpha, beta, company_id_norm,
        )
        return existing

    async def increment_arm(
        self,
        test_name: str,
        arm: str,
        success: bool,
        company_id=None,
    ) -> BanditPosterior:
        """Incremental update canonical: success += 1 ou failure += 1.

        Pattern: alpha += 1 if success else beta += 1.
        n_observations += 1 sempre.

        Returns:
            BanditPosterior pós-update.
        """
        existing = await self.get_posterior(test_name, arm, company_id)
        if existing is None:
            # Initial Beta(1,1) prior + 1 observation
            new_alpha = 2.0 if success else 1.0
            new_beta = 1.0 if success else 2.0
            return await self.upsert_posterior(
                test_name=test_name,
                arm=arm,
                alpha=new_alpha,
                beta=new_beta,
                company_id=company_id,
                n_observations=1,
            )

        if success:
            existing.alpha += 1.0
        else:
            existing.beta += 1.0
        existing.n_observations += 1
        await self.db.flush()
        logger.info(
            "[BanditPosteriorRepository] INCREMENT %s:%s success=%s "
            "α=%.2f β=%.2f n=%d",
            test_name, arm, success,
            existing.alpha, existing.beta, existing.n_observations,
        )
        return existing
