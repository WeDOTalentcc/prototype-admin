"""
GlobalPolicy Repository — data access layer for platform policies and audit logs.
Extracted from app/api/v1/global_policies.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_policies import DEFAULT_POLICIES, PlatformPolicy, PlatformPolicyAuditLog

logger = logging.getLogger(__name__)


class GlobalPolicyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_policies(
        self, conditions: list, *, limit: int = 100, offset: int = 0
    ) -> tuple[list[PlatformPolicy], int]:
        q = select(PlatformPolicy)
        if conditions:
            q = q.where(and_(*conditions))
        q = q.order_by(PlatformPolicy.category, PlatformPolicy.name).limit(limit).offset(offset)
        result = await self.db.execute(q)
        items = list(result.scalars().all())

        cq = select(func.count(PlatformPolicy.id))
        if conditions:
            cq = cq.where(and_(*conditions))
        total = (await self.db.execute(cq)).scalar() or 0
        return items, total

    async def list_categories(self):
        q = select(
            PlatformPolicy.category,
            func.count(PlatformPolicy.id).label("count"),
            func.count(PlatformPolicy.id).filter(PlatformPolicy.is_active).label("active_count"),
        ).group_by(PlatformPolicy.category)
        result = await self.db.execute(q)
        return result.all()

    async def get_by_id(self, policy_id: UUID) -> PlatformPolicy | None:
        result = await self.db.execute(
            select(PlatformPolicy).where(PlatformPolicy.id == policy_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> PlatformPolicy | None:
        result = await self.db.execute(
            select(PlatformPolicy).where(PlatformPolicy.name == name)
        )
        return result.scalar_one_or_none()

    async def update_policy(
        self, policy: PlatformPolicy, new_value: str, user_id: UUID | None, change_reason: str | None
    ) -> PlatformPolicy:
        audit_log = PlatformPolicyAuditLog(
            policy_id=policy.id,
            previous_value=policy.current_value,
            new_value=new_value,
            changed_by=user_id,
            change_reason=change_reason,
        )
        self.db.add(audit_log)
        policy.current_value = new_value
        policy.updated_by = user_id
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def get_history(
        self, policy_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[PlatformPolicyAuditLog], int]:
        q = (
            select(PlatformPolicyAuditLog)
            .where(PlatformPolicyAuditLog.policy_id == policy_id)
            .order_by(desc(PlatformPolicyAuditLog.changed_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(q)
        logs = list(result.scalars().all())

        cq = select(func.count(PlatformPolicyAuditLog.id)).where(
            PlatformPolicyAuditLog.policy_id == policy_id
        )
        total = (await self.db.execute(cq)).scalar() or 0
        return logs, total

    async def seed_defaults(self) -> tuple[int, int]:
        created = skipped = 0
        for pdata in DEFAULT_POLICIES:
            if await self.get_by_name(pdata["name"]):
                skipped += 1
                continue
            policy = PlatformPolicy(
                name=pdata["name"],
                description=pdata.get("description"),
                category=pdata["category"],
                value_type=pdata["value_type"],
                current_value=pdata["current_value"],
                unit=pdata.get("unit"),
                min_value=pdata.get("min_value"),
                max_value=pdata.get("max_value"),
                options=pdata.get("options"),
                is_active=True,
            )
            self.db.add(policy)
            created += 1
        return created, skipped
