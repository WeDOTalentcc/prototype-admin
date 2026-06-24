"""
ManagerAlignmentRepository — ADR-001 canonical repository.

Apply to: lia-agent-system/app/domains/approvals/repositories/manager_alignment_repository.py
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.manager_alignment import ManagerAlignment


_TOKEN_BYTES = 32
_DEFAULT_TTL_HOURS = 72


class ManagerAlignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> str:
        if not company_id:
            raise ValueError("company_id is required")
        return company_id

    async def create(
        self,
        company_id: str,
        job_vacancy_id: str,
        manager_email: str,
        manager_name: Optional[str] = None,
        created_by: Optional[str] = None,
        ttl_hours: int = _DEFAULT_TTL_HOURS,
    ) -> ManagerAlignment:
        cid = self._require_company_id(company_id)
        token = secrets.token_urlsafe(_TOKEN_BYTES)
        alignment = ManagerAlignment(
            id=str(uuid.uuid4()),
            company_id=cid,
            job_vacancy_id=job_vacancy_id,
            manager_email=manager_email,
            manager_name=manager_name,
            token=token,
            status="pending",
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
            created_by=created_by,
        )
        self.db.add(alignment)
        await self.db.flush()
        await self.db.refresh(alignment)
        return alignment

    async def get_by_id(self, alignment_id: str, company_id: str) -> Optional[ManagerAlignment]:
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            select(ManagerAlignment).where(
                and_(
                    ManagerAlignment.id == alignment_id,
                    ManagerAlignment.company_id == cid,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> Optional[ManagerAlignment]:
        """Public lookup — no company_id required (token is the auth proof)."""
        result = await self.db.execute(
            select(ManagerAlignment).where(ManagerAlignment.token == token)
        )
        return result.scalar_one_or_none()

    async def get_pending_for_job(
        self, company_id: str, job_vacancy_id: str
    ) -> Optional[ManagerAlignment]:
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            select(ManagerAlignment).where(
                and_(
                    ManagerAlignment.company_id == cid,
                    ManagerAlignment.job_vacancy_id == job_vacancy_id,
                    ManagerAlignment.status == "pending",
                    ManagerAlignment.expires_at > datetime.utcnow(),
                )
            ).order_by(ManagerAlignment.created_at.desc())
        )
        return result.scalars().first()

    async def list_for_job(
        self, company_id: str, job_vacancy_id: str, limit: int = 20
    ) -> list[ManagerAlignment]:
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            select(ManagerAlignment)
            .where(
                and_(
                    ManagerAlignment.company_id == cid,
                    ManagerAlignment.job_vacancy_id == job_vacancy_id,
                )
            )
            .order_by(ManagerAlignment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def respond(
        self,
        alignment: ManagerAlignment,
        status: str,
        response_notes: Optional[str] = None,
    ) -> ManagerAlignment:
        """Record manager response. status must be 'approved' or 'rejected'."""
        if status not in ("approved", "rejected"):
            raise ValueError(f"Invalid status: {status}")
        alignment.status = status
        alignment.response_notes = response_notes
        alignment.responded_at = datetime.utcnow()
        alignment.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(alignment)
        return alignment

    async def expire_stale(self, company_id: str) -> int:
        """Mark expired pending alignments. Returns count updated."""
        from sqlalchemy import update
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            update(ManagerAlignment)
            .where(
                and_(
                    ManagerAlignment.company_id == cid,
                    ManagerAlignment.status == "pending",
                    ManagerAlignment.expires_at <= datetime.utcnow(),
                )
            )
            .values(status="expired", updated_at=datetime.utcnow())
        )
        await self.db.flush()
        return result.rowcount
