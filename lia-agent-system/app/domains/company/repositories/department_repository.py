"""
DepartmentRepository - session-in-constructor pattern.
"""
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

    async def get_by_id(self, dept_id: UUID) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.id == dept_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Department:
        dept = Department(**data)
        self.db.add(dept)
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def update(self, dept_id: UUID, data: dict) -> Department | None:
        dept = await self.get_by_id(dept_id)
        if not dept:
            return None
        for key, value in data.items():
            if hasattr(dept, key):
                setattr(dept, key, value)
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def delete(self, dept_id: UUID) -> bool:
        dept = await self.get_by_id(dept_id)
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

    async def list_members(self, dept_id: UUID) -> list[DepartmentMember]:
        result = await self.db.execute(
            select(DepartmentMember)
            .where(
                DepartmentMember.department_id == dept_id,
                DepartmentMember.is_active,
            )
            .order_by(DepartmentMember.order, DepartmentMember.name)
        )
        return list(result.scalars().all())

    async def add_member(self, data: dict) -> DepartmentMember:
        member = DepartmentMember(**data)
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def update_member(
        self, member_id: UUID, data: dict
    ) -> DepartmentMember | None:
        result = await self.db.execute(
            select(DepartmentMember).where(DepartmentMember.id == member_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return None
        for key, value in data.items():
            if hasattr(member, key):
                setattr(member, key, value)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(self, member_id: UUID) -> bool:
        result = await self.db.execute(
            select(DepartmentMember).where(DepartmentMember.id == member_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        member.is_active = False
        await self.db.commit()
        return True
