from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.billing.repositories.billing_repository import BillingRepository


def get_billing_repo(db: AsyncSession = Depends(get_tenant_db)) -> BillingRepository:
    return BillingRepository(db)
