import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Department, DepartmentMember

logger = logging.getLogger(__name__)


class DepartmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self, company_id: UUID, search: str | None = None
    ) -> list[Department]:
        query = select(Department).where(Department.company_id == company_id)
        if search:
            query = query.where(Department.name.ilike(f"%{search}%"))
        query = query.order_by(Department.order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_active_for_company(self, company_id: UUID) -> list[Department]:
        """Active departments for a company, ordered by display order."""
        result = await self.db.execute(
            select(Department)
            .where(
                Department.company_id == company_id,
                Department.is_active,
            )
            .order_by(Department.order)
        )
        return list(result.scalars().all())

    async def list_filtered(
        self,
        company_id: UUID | None = None,
        include_inactive: bool = False,
    ) -> list[Department]:
        """List departments with optional company scoping and active filter."""
        # TENANT-EXEMPT: dynamic builder — Department.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Department)
        if company_id:
            query = query.where(Department.company_id == company_id)
        if not include_inactive:
            query = query.where(Department.is_active)
        query = query.order_by(Department.order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        dept_id: UUID,
        company_id: UUID | None = None,
    ) -> Department | None:
        """Get department by id. Multi-tenancy defense-in-depth via company_id
        filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — Department.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Department).where(Department.id == dept_id)
        if company_id:
            query = query.where(Department.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Department:
        dept = Department(**data)
        self.db.add(dept)
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def update(
        self,
        dept_id: UUID,
        data: dict,
        company_id: UUID | None = None,
    ) -> Department | None:
        """Update department. Onda 4.2a-P0.1 (2026-05-23): adicionado
        company_id pra defense-in-depth multi-tenancy. Quando passado,
        rejeita update se dept pertence a outro tenant (cross-tenant guard).
        """
        dept = await self.get_by_id(dept_id, company_id=company_id)
        if not dept:
            return None
        for key, value in data.items():
            if hasattr(dept, key):
                setattr(dept, key, value)
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def delete(
        self,
        dept_id: UUID,
        company_id: UUID | None = None,
    ) -> bool:
        """Soft delete. Onda 4.2a-P0.1 (2026-05-23): adicionado company_id
        pra prevenir cross-tenant deletes (user empresa A nao deve poder
        deletar dept_id da empresa B).
        """
        dept = await self.get_by_id(dept_id, company_id=company_id)
        if not dept:
            return False
        dept.is_active = False
        await self.db.commit()
        return True

    async def count_members(self, dept_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(DepartmentMember.id)).where(
                DepartmentMember.department_id == dept_id,
                DepartmentMember.is_active,
            )
        )
        return result.scalar() or 0

    async def list_members(
        self,
        dept_id: UUID,
        company_id: UUID | None = None,
    ) -> list[DepartmentMember]:
        """List active members of a department. Multi-tenancy defense-in-depth
        via company_id filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — DepartmentMember.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = (
            select(DepartmentMember)
            .where(
                DepartmentMember.department_id == dept_id,
                DepartmentMember.is_active,
            )
            .order_by(DepartmentMember.order, DepartmentMember.name)
        )
        if company_id:
            query = query.where(DepartmentMember.company_id == company_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_member(self, data: dict) -> DepartmentMember:
        member = DepartmentMember(**data)
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def get_member(
        self,
        member_id: UUID,
        company_id: UUID | None = None,
    ) -> DepartmentMember | None:
        """Fetch single department member by id. Multi-tenancy defense-in-depth
        via company_id filter quando passado. Used by Sprint 7.4 mutation gate
        fetch-first pattern before delete."""
        # TENANT-EXEMPT: dynamic builder — DepartmentMember.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(DepartmentMember).where(DepartmentMember.id == member_id)
        if company_id:
            query = query.where(DepartmentMember.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_member(
        self,
        member_id: UUID,
        data: dict,
        company_id: UUID | None = None,
    ) -> DepartmentMember | None:
        """Update department member. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — DepartmentMember.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(DepartmentMember).where(DepartmentMember.id == member_id)
        if company_id:
            query = query.where(DepartmentMember.company_id == company_id)
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()
        if not member:
            return None
        for key, value in data.items():
            if hasattr(member, key):
                setattr(member, key, value)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(
        self,
        member_id: UUID,
        company_id: UUID | None = None,
    ) -> bool:
        """Remove (soft-delete) member. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — DepartmentMember.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(DepartmentMember).where(DepartmentMember.id == member_id)
        if company_id:
            query = query.where(DepartmentMember.company_id == company_id)
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()
        if not member:
            return False
        member.is_active = False
        await self.db.commit()
        return True
