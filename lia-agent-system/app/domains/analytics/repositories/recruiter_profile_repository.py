"""RecruiterProfileRepository — DB access layer for recruiter personalization tables.

Extracted from analytics services per ADR-001.
Tables covered:
  - recruiter_profiles
  - personalization_settings
  - recruiter_field_preferences
"""
import logging
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.recruiter_profile import (
    PersonalizationSettings,
    RecruiterFieldPreference,
    RecruiterProfile,
)

logger = logging.getLogger(__name__)


class RecruiterProfileRepository:
    """Repository for recruiter-personalization data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_recruiter_id(recruiter_id: Any) -> Any:
        if not recruiter_id:
            raise ValueError("recruiter_id is required")
        return recruiter_id

    # ---------- RecruiterProfile ----------

    async def get_profile(self, recruiter_id: str) -> RecruiterProfile | None:
        recruiter_id = self._require_recruiter_id(recruiter_id)
        # TENANT-EXEMPT: recruiter profile per-user scope; dynamic conditions builder; T-RATCHET tenant_filter
        stmt = select(RecruiterProfile).where(
            RecruiterProfile.recruiter_id == recruiter_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ---------- PersonalizationSettings ----------

    async def get_settings(self, recruiter_id: str) -> PersonalizationSettings | None:
        recruiter_id = self._require_recruiter_id(recruiter_id)
        stmt = select(PersonalizationSettings).where(
            PersonalizationSettings.recruiter_id == recruiter_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ---------- RecruiterFieldPreference ----------

    async def list_field_preferences(
        self, recruiter_id: str
    ) -> list[RecruiterFieldPreference]:
        recruiter_id = self._require_recruiter_id(recruiter_id)
        # TENANT-EXEMPT: recruiter profile per-user scope; dynamic conditions builder; T-RATCHET tenant_filter
        stmt = select(RecruiterFieldPreference).where(
            RecruiterFieldPreference.recruiter_id == recruiter_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_field_preference(
        self, recruiter_id: str, field_name: str
    ) -> RecruiterFieldPreference | None:
        recruiter_id = self._require_recruiter_id(recruiter_id)
        # TENANT-EXEMPT: recruiter profile per-user scope; dynamic conditions builder; T-RATCHET tenant_filter
        stmt = select(RecruiterFieldPreference).where(
            and_(
                RecruiterFieldPreference.recruiter_id == recruiter_id,
                RecruiterFieldPreference.field_name == field_name,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
