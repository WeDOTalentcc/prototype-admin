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


    async def get_pricing_tier(self, company_id: str) -> str | None:
        """F-13 (audit 2026-05-22): Lookup pricing_tier from companies table.

        Replaces inline SQL in voice_screening_orchestrator._resolve_pricing_tier.
        Returns None when company not found or column NULL; caller decides
        the default (currently 'pro' in voice path).

        Uses sa.text() because the `companies` table is Rails-owned and not
        modeled in SQLAlchemy on the Python side — same rationale as the
        rest of TenantRepository's cross-stack reads.
        """
        # ADR-001-EXEMPT: Rails-owned table not modeled in Python ORM;
        # tenant scoping enforced by parameter binding.
        from sqlalchemy import text
        result = await self.db.execute(
            text("SELECT pricing_tier FROM companies WHERE id = :cid LIMIT 1"),
            {"cid": company_id},
        )
        row = result.first()
        if row and row[0]:
            return str(row[0])
        return None

