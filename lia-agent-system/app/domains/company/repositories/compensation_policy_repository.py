"""
CompensationPolicy Repository — data access layer for company PRV policies.

Multi-tenancy: all queries scope by company_id (RLS also enforced at DB level).
Versioning: every update increments version + appends to revision_history jsonb.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.compensation_policy import (
    DEFAULT_BR_COMPENSATION_TEMPLATES,
    CompensationPolicy,
)

logger = logging.getLogger(__name__)


class CompensationPolicyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        active_only: bool = True,
        policy_type: str | None = None,
        search: str | None = None,
    ) -> list[CompensationPolicy]:
        query = select(CompensationPolicy).where(
            CompensationPolicy.company_id == company_id
        )
        if active_only:
            query = query.where(CompensationPolicy.is_active.is_(True))
        if policy_type:
            query = query.where(CompensationPolicy.policy_type == policy_type)
        if search:
            term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(CompensationPolicy.name).like(term),
                    func.lower(CompensationPolicy.description).like(term),
                )
            )
        query = query.order_by(
            CompensationPolicy.is_default.desc(),
            CompensationPolicy.name,
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        policy_id: UUID,
        company_id: str | None = None,
    ) -> CompensationPolicy | None:
        """Get policy by id. Multi-tenancy defense-in-depth via company_id
        filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — CompensationPolicy.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(CompensationPolicy).where(CompensationPolicy.id == policy_id)
        if company_id:
            query = query.where(CompensationPolicy.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(
        self, company_id: str, name: str
    ) -> CompensationPolicy | None:
        result = await self.db.execute(
            select(CompensationPolicy).where(
                CompensationPolicy.company_id == company_id,
                CompensationPolicy.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self, company_id: str, data: dict, created_by: str | None = None
    ) -> CompensationPolicy:
        payload = {k: v for k, v in data.items() if k not in ("id", "company_id")}
        if created_by:
            payload["created_by"] = created_by
        policy = CompensationPolicy(company_id=company_id, **payload)
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def update(
        self,
        policy: CompensationPolicy,
        data: dict,
        updated_by: str | None = None,
    ) -> CompensationPolicy:
        now = datetime.utcnow()

        # Build revision entry before mutating
        revision_entry = {
            "version": policy.version,
            "updated_at": now.isoformat(),
            "updated_by": updated_by or policy.updated_by,
            "changes": list(data.keys()),
        }
        existing_history: list = list(policy.revision_history or [])
        existing_history.append(revision_entry)

        for key, value in data.items():
            if key not in ("id", "company_id", "version", "revision_history"):
                setattr(policy, key, value)

        policy.version = (policy.version or 1) + 1
        policy.revision_history = existing_history
        policy.updated_at = now
        if updated_by:
            policy.updated_by = updated_by

        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def deactivate(
        self, policy: CompensationPolicy, updated_by: str | None = None
    ) -> None:
        policy.is_active = False
        policy.updated_at = datetime.utcnow()
        if updated_by:
            policy.updated_by = updated_by

    async def hard_delete(self, policy: CompensationPolicy) -> None:
        await self.db.delete(policy)

    async def count_for_company(self, company_id: str) -> int:
        result = await self.db.execute(
            select(func.count(CompensationPolicy.id)).where(
                CompensationPolicy.company_id == company_id
            )
        )
        return result.scalar() or 0

    async def seed_defaults(
        self, company_id: str, created_by: str | None = None
    ) -> int:
        created = 0
        for tpl in DEFAULT_BR_COMPENSATION_TEMPLATES:
            if not await self.get_by_name(company_id, tpl["name"]):
                payload = dict(tpl)
                if created_by:
                    payload["created_by"] = created_by
                self.db.add(CompensationPolicy(company_id=company_id, **payload))
                created += 1
        return created
