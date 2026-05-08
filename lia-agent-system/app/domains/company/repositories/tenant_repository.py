"""TenantRepository - for WorkOS/ClientAccount tenant resolution."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.workos_models import CompanyWorkOSConfig
from app.models.client_account import ClientAccount
from app.models.company import CompanyProfile

logger = logging.getLogger(__name__)


class TenantRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_workos_config(self, workos_org_id: str) -> CompanyWorkOSConfig | None:
        result = await self.db.execute(
            select(CompanyWorkOSConfig).where(
                CompanyWorkOSConfig.workos_organization_id == workos_org_id
            )
        )
        return result.scalars().first()

    async def get_client_account(self, client_account_id: str) -> ClientAccount | None:
        result = await self.db.execute(
            select(ClientAccount).where(ClientAccount.id == client_account_id)
        )
        return result.scalars().first()

    async def get_company_by_client_account(self, client_account_id: str) -> CompanyProfile | None:
        result = await self.db.execute(
            select(CompanyProfile).where(
                CompanyProfile.client_account_id == client_account_id
            )
        )
        return result.scalars().first()


    # ── Sprint Q2 ADR-001 cleanup ──────

    async def get_workos_config_by_company(
        self, company_id: str
    ) -> CompanyWorkOSConfig | None:
        """Lookup CompanyWorkOSConfig by tenant company_id (post-update fetch)."""
        result = await self.db.execute(
            select(CompanyWorkOSConfig).where(
                CompanyWorkOSConfig.company_id == company_id
            )
        )
        return result.scalar_one_or_none()
