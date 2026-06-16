"""WT-2022 P0.TENANT: FeatureFlagRepository canonical.

Wrapper canonical pra leituras de feature_flags. Modelo FeatureFlag declara
TENANT-NULLABLE-DELIBERATE em company_id (NULL = global rollout pra todas
companies, UUID = enabled per-company). Sensor secundario
`scripts/check_tenant_nullable_has_repo_enforcement.py` exige que o repository
canonical em app/domains/ filtre por company_id em pelo menos um metodo OU
declare CROSS-TENANT-INTENTIONAL marker.

Service legado `app/shared/governance/feature_flag_service.py` ainda faz
select direto (ADR-001-EXEMPT). Sprint follow-up migra service pra usar este
repo (delete `select(FeatureFlag)` inline). Por enquanto este repo serve como
SSoT canonical pra novas chamadas.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import or_, select

from app.models.company_learning import FeatureFlag

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FeatureFlagRepository:
    """Read/write canonical de FeatureFlag.

    Multi-tenancy pattern:
    - Per-company flag: FeatureFlag.company_id == <company_id>
    - Global flag: FeatureFlag.company_id IS NULL (cross-tenant deliberado)
    - Resolution: per-company override > global > default-disabled
    """

    def __init__(self, db: "AsyncSession") -> None:
        self.db = db

    async def get_active_for_company(
        self,
        company_id: str | UUID,
        flag_key: str,
    ) -> FeatureFlag | None:
        """Resolve flag pra (company_id, flag_key) com fallback global.

        Returns first row matching:
        - FeatureFlag.flag_key == flag_key
        - FeatureFlag.company_id == <id> OR FeatureFlag.company_id IS NULL

        Per-company override prefere global (ORDER BY company_id NULLS LAST).
        """
        company_id_str = str(company_id) if isinstance(company_id, UUID) else company_id
        result = await self.db.execute(
            select(FeatureFlag)
            .where(
                FeatureFlag.flag_key == flag_key,
                or_(
                    FeatureFlag.company_id == company_id_str,
                    FeatureFlag.company_id.is_(None),
                ),
            )
            .order_by(FeatureFlag.company_id.is_(None).asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_for_company_only(
        self,
        company_id: str | UUID,
        flag_key: str,
    ) -> FeatureFlag | None:
        """Le APENAS flag per-company (sem fallback global).

        Util para set_flag / delete_flag onde precisamos saber se ja
        existe override per-company (vs herdar do global).
        """
        company_id_str = str(company_id) if isinstance(company_id, UUID) else company_id
        result = await self.db.execute(
            select(FeatureFlag).where(
                FeatureFlag.flag_key == flag_key,
                FeatureFlag.company_id == company_id_str,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_company(
        self,
        company_id: str | UUID,
        category: str | None = None,
        include_globals: bool = True,
    ) -> list[FeatureFlag]:
        """List flags visiveis pra company (per-company + globals optional).

        # CROSS-TENANT-INTENTIONAL: globals (company_id IS NULL) sao leitura
        # cross-tenant deliberada per ADR-LGPD-001 - flags globais representam
        # rollout para TODAS companies (sem PII exposure, schema-only).
        """
        company_id_str = str(company_id) if isinstance(company_id, UUID) else company_id
        conditions: list = []
        if include_globals:
            conditions.append(
                or_(
                    FeatureFlag.company_id == company_id_str,
                    FeatureFlag.company_id.is_(None),
                )
            )
        else:
            conditions.append(FeatureFlag.company_id == company_id_str)
        if category:
            conditions.append(FeatureFlag.category == category)

        result = await self.db.execute(
            # TENANT-EXEMPT: feature_flag is global system table; queries filter by flag_key, not tenant; T-RATCHET tenant_filter
            select(FeatureFlag).where(*conditions).order_by(FeatureFlag.flag_key.asc())
        )
        return list(result.scalars().all())
