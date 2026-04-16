"""CommunicationMatrixRepository — DB operations for CommunicationMatrixEntry.

Extracted from app/api/v1/communication_matrix.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.communication_matrix import CommunicationMatrixEntry

logger = logging.getLogger(__name__)


class CommunicationMatrixRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_entries(
        self,
        company_id: str | None,
        *,
        module: str | None = None,
        is_active: bool | None = None,
    ) -> list[CommunicationMatrixEntry]:
        """List matrix entries for a company (or platform defaults if company_id is None)."""
        query = select(CommunicationMatrixEntry)

        if company_id:
            query = query.where(CommunicationMatrixEntry.company_id == company_id)
        else:
            query = query.where(CommunicationMatrixEntry.company_id.is_(None))

        if module:
            query = query.where(CommunicationMatrixEntry.module == module)

        if is_active is not None:
            query = query.where(CommunicationMatrixEntry.is_active == is_active)

        query = query.order_by(
            CommunicationMatrixEntry.module,
            CommunicationMatrixEntry.display_order,
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, entry_id: UUID) -> CommunicationMatrixEntry | None:
        result = await self.db.execute(
            select(CommunicationMatrixEntry).where(
                CommunicationMatrixEntry.id == entry_id
            )
        )
        return result.scalar_one_or_none()

    async def update_entry(
        self,
        entry: CommunicationMatrixEntry,
        update_data: dict,
    ) -> CommunicationMatrixEntry:
        for field, value in update_data.items():
            setattr(entry, field, value)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def delete_for_company(self, company_id: str | None) -> None:
        """Delete all entries for a company (or platform defaults)."""
        if company_id:
            delete_query = delete(CommunicationMatrixEntry).where(
                CommunicationMatrixEntry.company_id == company_id
            )
        else:
            delete_query = delete(CommunicationMatrixEntry).where(
                CommunicationMatrixEntry.company_id.is_(None)
            )
        await self.db.execute(delete_query)

    async def create(self, entry: CommunicationMatrixEntry) -> None:
        """Add a matrix entry (does not flush; caller controls transaction)."""
        self.db.add(entry)

    async def count_for_company(self, company_id: str | None) -> int:
        """Count entries for a company (or platform defaults)."""
        entries = await self.list_entries(company_id)
        return len(entries)
