import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Approver

logger = logging.getLogger(__name__)


class ApproverRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(self, company_id: UUID) -> list[Approver]:
        result = await self.db.execute(
            select(Approver)
            .where(Approver.company_id == company_id, Approver.is_active)
            .order_by(Approver.level)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        approver_id: UUID,
        company_id: UUID | str | None = None,
    ) -> Approver | None:
        """Get approver by id. Multi-tenancy defense-in-depth via company_id
        filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — Approver.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Approver).where(Approver.id == approver_id)
        if company_id:
            query = query.where(Approver.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Approver:
        approver = Approver(**data)
        self.db.add(approver)
        await self.db.commit()
        await self.db.refresh(approver)
        return approver

    async def update(
        self,
        approver_id: UUID,
        data: dict,
        company_id: UUID | str | None = None,
    ) -> Approver | None:
        """Update approver. Onda 4.2a-P0.2 (2026-05-23): adicionado
        company_id pra defense-in-depth multi-tenancy. Cross-tenant write
        em approval workflow = LGPD critical (afeta offer flow).
        """
        approver = await self.get_by_id(approver_id, company_id=company_id)
        if not approver:
            return None
        for key, value in data.items():
            if hasattr(approver, key):
                setattr(approver, key, value)
        await self.db.commit()
        await self.db.refresh(approver)
        return approver

    async def list_for_department(
        self,
        company_id: UUID,
        department_id: UUID | None = None,
        is_active: bool = True,
    ) -> list[Approver]:
        """List approvers per-department OR company-wide.

        P0.D2 (audit Wave 2 2026-05-22): a company-wide approver
        (``department_id IS NULL``) is always returned regardless of the
        ``department_id`` filter — they approve across all departments.
        Per-department approvers are returned only when matched.

        Multi-tenancy: ``company_id`` filter is fail-closed (REGRA 1).
        Sort by ``level`` (ascending) preserves seniority ordering.
        """
        stmt = select(Approver).where(
            Approver.company_id == company_id,
            Approver.is_active == is_active,
            or_(
                Approver.department_id == department_id,
                Approver.department_id.is_(None),
            ),
        ).order_by(Approver.level)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_eligible_for_amount(
        self,
        company_id: UUID,
        department_id: UUID | None,
        amount: Decimal,
    ) -> list[Approver]:
        """Return approvers eligible to approve a given offer amount.

        P0.D2 (audit Wave 2 2026-05-22): amount-threshold routing.
        ``can_approve_above_amount IS NULL`` = approver pode aprovar
        qualquer valor (backward-compat). Caso contrário, approver é
        elegível só quando ``can_approve_above_amount <= amount``
        (i.e., o threshold dele cobre o valor da oferta).

        Filtering is done in Python (not SQL) because the per-department
        composition is already in-memory after ``list_for_department``,
        and the result set is small (< 50 per company in practice).
        """
        approvers = await self.list_for_department(
            company_id, department_id
        )
        return [
            a
            for a in approvers
            if a.can_approve_above_amount is None
            or a.can_approve_above_amount <= amount
        ]

    async def delete(
        self,
        approver_id: UUID,
        company_id: UUID | str | None = None,
    ) -> bool:
        """Soft delete approver. Onda 4.2a-P0.2 (2026-05-23): cross-tenant
        delete guard via company_id (LGPD critical — approval workflow).
        """
        approver = await self.get_by_id(approver_id, company_id=company_id)
        if not approver:
            return False
        approver.is_active = False
        await self.db.commit()
        return True
