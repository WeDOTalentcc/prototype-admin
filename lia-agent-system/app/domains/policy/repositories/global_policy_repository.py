"""GlobalPolicyRepository — DB operations for GlobalPolicy model.

Extracted from app/api/v1/policies.py as part of Phase 2 refactor.
Note: policy_repository.py covers BusinessRule/EscalationRule (different models).
"""
import logging
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_policy import GlobalPolicy, PolicyScope

logger = logging.getLogger(__name__)


class GlobalPolicyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_policies(
        self,
        *,
        policy_type: str | None = None,
        scope: str | None = None,
        is_active: bool | None = None,
        company_id: str | None = None,
        user_company_id: str | None = None,
        is_admin: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GlobalPolicy], int]:
        """List policies with filters. Returns (items, total)."""
        conditions = []

        if policy_type:
            conditions.append(GlobalPolicy.policy_type == policy_type)
        if scope:
            conditions.append(GlobalPolicy.scope == scope)
        if is_active is not None:
            conditions.append(GlobalPolicy.is_active == is_active)
        if company_id and is_admin:
            conditions.append(GlobalPolicy.company_id == company_id)
        elif not is_admin and user_company_id:
            conditions.append(
                or_(
                    GlobalPolicy.company_id == user_company_id,
                    GlobalPolicy.scope == PolicyScope.PLATFORM.value,
                )
            )

        query = select(GlobalPolicy)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(GlobalPolicy.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        policies = list(result.scalars().all())

        count_query = select(func.count(GlobalPolicy.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0

        return policies, total

    async def get_by_id(self, policy_id: UUID) -> GlobalPolicy | None:
        result = await self.db.execute(
            select(GlobalPolicy).where(GlobalPolicy.id == policy_id)
        )
        return result.scalar_one_or_none()

    async def create(self, policy: GlobalPolicy) -> GlobalPolicy:
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def update(self, policy: GlobalPolicy, update_data: dict) -> GlobalPolicy:
        for field, value in update_data.items():
            setattr(policy, field, value)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def delete(self, policy: GlobalPolicy) -> None:
        await self.db.delete(policy)
