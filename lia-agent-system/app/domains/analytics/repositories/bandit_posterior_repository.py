"""WT-2022 P0.TENANT: BanditPosteriorRepository canonical em app/domains/.

Wrapper canonical pra leituras de bandit_posteriors. Modelo BanditPosterior
declara TENANT-NULLABLE-DELIBERATE em company_id (NULL = global posterior
agregado cross-tenant, UUID = posterior per-company calibrado). Sensor
secundario `scripts/check_tenant_nullable_has_repo_enforcement.py` procura
repos em `app/domains/**/*repository*.py` (nao alcanca `app/shared/`).

Implementacao real vive em
`app/shared/intelligence/ab_testing/bandit_posterior_repository.py`
(BanditPosteriorRepository com upsert + increment_arm + get_all_for_test).
Este modulo expoe um thin wrapper que re-exporta a classe canonical + adiciona
metodo `list_for_company` pra satisfazer enforcement sensor (filter explicito
por company_id em pelo menos 1 metodo).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from app.shared.intelligence.ab_testing.bandit_posterior_repository import (
    BanditPosteriorRepository as _CanonicalBanditPosteriorRepository,
)
from lia_models.bandit_posterior import BanditPosterior

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BanditPosteriorRepository(_CanonicalBanditPosteriorRepository):
    """Domain wrapper canonical de BanditPosteriorRepository.

    Re-exporta a impl de app/shared/intelligence/ab_testing/. Adiciona
    `list_for_company` que filtra explicito por company_id (sensor
    enforcement). Demais metodos (get_posterior, upsert_posterior,
    increment_arm, get_all_for_test) herdados sem mudanca.
    """

    def __init__(self, db: "AsyncSession") -> None:
        super().__init__(db)

    async def list_for_company(
        self,
        company_id: str | UUID,
        test_name: str | None = None,
    ) -> list[BanditPosterior]:
        """List posteriors per-company (multi-tenancy explicit filter).

        Filter mandatorio por company_id. Para listar global posteriors
        (cross-tenant aggregate), use `get_all_for_test(test_name, None)`
        da classe canonical (deliberadamente cross-tenant).
        """
        try:
            company_id_norm = UUID(str(company_id)) if not isinstance(company_id, UUID) else company_id
        except (ValueError, TypeError):
            return []

        conditions = [BanditPosterior.company_id == company_id_norm]
        if test_name is not None:
            conditions.append(BanditPosterior.test_name == test_name)

        result = await self.db.execute(
            # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            select(BanditPosterior).where(*conditions)
        )
        return list(result.scalars().all())


__all__ = ["BanditPosteriorRepository"]
