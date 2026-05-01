"""
CalendarCredentialsRepository — data access for company OAuth calendar credentials.
Extracted from app/api/v1/calendar.py (Google OAuth callback) as part of Phase 2 refactor.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CalendarCredentialsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_credentials(self, company_id: uuid.UUID, provider: str):
        """Return CompanyCalendarCredentials for company+provider, or None."""
        from app.models.company_calendar_credentials import CompanyCalendarCredentials

        result = await self.db.execute(
            select(CompanyCalendarCredentials).where(
                CompanyCalendarCredentials.company_id == company_id,
                CompanyCalendarCredentials.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_credentials(
        self,
        company_id: uuid.UUID,
        provider: str,
        encrypted_credentials: str,
        is_active: bool = True,
        timezone: str = "America/Sao_Paulo",
    ):
        """Create or update calendar credentials record."""
        from app.models.company_calendar_credentials import CompanyCalendarCredentials

        record = await self.get_credentials(company_id, provider)
        if record:
            record.encrypted_credentials = encrypted_credentials
            record.is_active = is_active
        else:
            record = CompanyCalendarCredentials(
                id=uuid.uuid4(),
                company_id=company_id,
                provider=provider,
                encrypted_credentials=encrypted_credentials,
                is_active=is_active,
                timezone=timezone,
            )
            self.db.add(record)
        return record
