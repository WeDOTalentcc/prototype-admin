"""CommunicationMatrixRepository — DB operations for CommunicationMatrixEntry.

Extracted from app/api/v1/communication_matrix.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication_matrix import CommunicationMatrixEntry

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
        # TENANT-EXEMPT: dynamic builder — company_id filter is applied via
        # query.where() below (either CommunicationMatrixEntry.company_id == company_id
        # or CommunicationMatrixEntry.company_id.is_(None) for platform defaults).
        # Sensor cannot trace chain across variable reassignment.
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

    async def get_by_id(
        self,
        entry_id: UUID,
        company_id: str | None = None,
    ) -> CommunicationMatrixEntry | None:
        """Get matrix entry by id.

        Multi-tenancy defense-in-depth: pass company_id to scope to current tenant
        (or to None for platform defaults). When None, returns row regardless of
        tenant — only safe for admin paths.
        """
        conditions = [CommunicationMatrixEntry.id == entry_id]
        if company_id:
            conditions.append(CommunicationMatrixEntry.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(CommunicationMatrixEntry).where(*conditions)
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


    async def get_by_trigger_name(
        self,
        *,
        trigger_name: str,
        company_id: str | None,
    ) -> CommunicationMatrixEntry | None:
        """Find matrix entry by trigger_name.

        Priority: company-specific entry, falling back to platform default
        (company_id IS NULL) when no company-specific record matches.
        """
        if not trigger_name:
            return None

        if company_id:
            result = await self.db.execute(
                select(CommunicationMatrixEntry).where(
                    CommunicationMatrixEntry.trigger_name == trigger_name,
                    CommunicationMatrixEntry.company_id == company_id,
                )
            )
            entry = result.scalars().first()
            if entry:
                return entry

        # Platform default fallback
        result = await self.db.execute(
            select(CommunicationMatrixEntry).where(
                CommunicationMatrixEntry.trigger_name == trigger_name,
                CommunicationMatrixEntry.company_id.is_(None),
            )
        )
        return result.scalars().first()
