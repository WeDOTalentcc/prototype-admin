"""UserAgentPreferenceRepository — DB access for HITL auto_confirm preferences.

Extracted from app/domains/cv_screening/services/user_agent_preference_service.py
per ADR-001 (services do not run SQL inline).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.user_agent_preference import UserAgentPreference


class UserAgentPreferenceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(
        self,
        *,
        user_id: str,
        company_id: str,
        domain: str,
        action_type: str,
    ) -> UserAgentPreference | None:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        stmt = select(UserAgentPreference).where(
            UserAgentPreference.user_id == user_id,
            UserAgentPreference.company_id == company_id,
            UserAgentPreference.domain == domain,
            UserAgentPreference.action_type == action_type,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: str,
        company_id: str,
    ) -> list[UserAgentPreference]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        stmt = select(UserAgentPreference).where(
            UserAgentPreference.user_id == user_id,
            UserAgentPreference.company_id == company_id,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        *,
        user_id: str,
        company_id: str,
        domain: str,
        action_type: str,
        auto_confirm: bool,
    ) -> UserAgentPreference:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        pref = await self.get(
            user_id=user_id,
            company_id=company_id,
            domain=domain,
            action_type=action_type,
        )
        if pref:
            pref.auto_confirm = auto_confirm
            pref.updated_at = datetime.utcnow()
        else:
            pref = UserAgentPreference(
                user_id=user_id,
                company_id=company_id,
                domain=domain,
                action_type=action_type,
                auto_confirm=auto_confirm,
            )
            self.db.add(pref)
        await self.db.commit()
        await self.db.refresh(pref)
        return pref
