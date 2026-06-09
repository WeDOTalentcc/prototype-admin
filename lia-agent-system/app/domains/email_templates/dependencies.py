"""
Dependency injection for email_templates domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.email_templates_repository import (
    EmailTemplatesRepository,
)


def get_email_templates_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> EmailTemplatesRepository:
    return EmailTemplatesRepository(db)
