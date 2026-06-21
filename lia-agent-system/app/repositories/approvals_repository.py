from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.approval import ApprovalRequest, ApprovalStatus
from app.models.company import CompanyProfile
import uuid
from uuid import UUID
from typing import Optional


class ApprovalsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_and_flush(self, approval: ApprovalRequest) -> ApprovalRequest:
        self.db.add(approval)
        await self.db.flush()
        await self.db.refresh(approval)
        return approval

    async def flush_and_refresh(self, approval: ApprovalRequest) -> ApprovalRequest:
        await self.db.flush()
        await self.db.refresh(approval)
        return approval

    async def get_by_id(self, approval_id: UUID) -> Optional[ApprovalRequest]:
        result = await self.db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
        )
        return result.scalar_one_or_none()

    async def list_by_company(
        self,
        company_id: UUID,
        status: Optional[str] = None,
        request_type: Optional[str] = None,
        approver_email: Optional[str] = None,
        requester_email: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ApprovalRequest]:
        query = select(ApprovalRequest).where(
            ApprovalRequest.company_id == company_id
        )
        if status:
            query = query.where(ApprovalRequest.status == status)
        if request_type:
            query = query.where(ApprovalRequest.request_type == request_type)
        if approver_email:
            query = query.where(ApprovalRequest.approver_email == approver_email)
        if requester_email:
            query = query.where(ApprovalRequest.requester_email == requester_email)
        query = query.order_by(ApprovalRequest.created_at.desc())
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_pending_by_company(
        self,
        company_id: UUID,
        approver_email: Optional[str] = None,
        request_type: Optional[str] = None,
    ) -> list[ApprovalRequest]:
        # Phase B fix (Sprint B post-audit): the previous version
        # referenced an undefined `pending` identifier and crashed at
        # call time with NameError. Replaced with the canonical
        # ApprovalStatus.PENDING.value. Added request_type filter for
        # the feature_flag_toggle workflow.
        query = select(ApprovalRequest).where(
            and_(
                ApprovalRequest.company_id == company_id,
                ApprovalRequest.status == ApprovalStatus.PENDING.value,
            )
        )
        if approver_email:
            query = query.where(ApprovalRequest.approver_email == approver_email)
        if request_type:
            query = query.where(ApprovalRequest.request_type == request_type)
        query = query.order_by(ApprovalRequest.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())


    async def find_pending_duplicate(
        self,
        company_id: str,
        flag_key: str,
        requester_id,
    ) -> "Optional[ApprovalRequest]":
        """P1-1 idempotency: return existing PENDING feature_flag_toggle
        request for (company_id, flag_key, requester_id) or None.

        target_name stores the flag_key (set in request_feature_flag_toggle).
        Status filter is PENDING only — resolved requests allow re-submission.
        """
        from app.models.approval import ApprovalType
        result = await self.db.execute(
            select(ApprovalRequest).where(
                and_(
                    ApprovalRequest.company_id == company_id,
                    ApprovalRequest.request_type == ApprovalType.FEATURE_FLAG_TOGGLE.value,
                    ApprovalRequest.target_name == flag_key,
                    ApprovalRequest.requester_id == requester_id,
                    ApprovalRequest.status == ApprovalStatus.PENDING.value,
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_default_company_id(self):
        from sqlalchemy import select
        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.is_default).limit(1)
        )
        default = result.scalar_one_or_none()
        return default.id if default else None


    async def get_pending_by_target(
        self,
        target_id: UUID,
        request_type: str,
    ) -> list[ApprovalRequest]:
        """Return pending ApprovalRequests for a specific target (job, candidate).

        Used by approval_trigger_service for idempotency check and by
        assert_can_publish gate. Ordered by approval_level asc (level 1 first).

        Multi-tenancy: caller must ensure target_id belongs to the correct
        company (verified upstream via job/company_id JWT-derived load).
        """
        result = await self.db.execute(
            select(ApprovalRequest).where(
                and_(
                    ApprovalRequest.target_id == target_id,
                    ApprovalRequest.request_type == request_type,
                    ApprovalRequest.status == ApprovalStatus.PENDING.value,
                )
            ).order_by(ApprovalRequest.approval_level)
        )
        return list(result.scalars().all())

    async def get_by_magic_token(self, token: str) -> "Optional[ApprovalRequest]":
        """Return ApprovalRequest for a magic token. None if not found.

        Used by public resolve-by-token endpoint (no JWT auth).
        Caller must verify magic_token_used=False and magic_token_expires_at > now().
        """
        result = await self.db.execute(
            select(ApprovalRequest).where(ApprovalRequest.magic_token == token).limit(1)
        )
        return result.scalar_one_or_none()
