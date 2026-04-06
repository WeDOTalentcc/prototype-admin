"""
Data Subject domain repository — all SQLAlchemy operations for data_subject_requests.py.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import DataSubjectRequest


class DataSubjectRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_request(self, data: dict) -> DataSubjectRequest:
        """Create a new DataSubjectRequest and persist it."""
        request = DataSubjectRequest(
            company_id=data["company_id"],
            request_type=data["request_type"],
            status=data["status"],
            subject_name=data.get("subject_name"),
            subject_email=data.get("subject_email"),
            subject_phone=data.get("subject_phone"),
            subject_identifier=data.get("subject_identifier"),
            description=data.get("description"),
            source_channel=data["source_channel"],
            data_categories=data.get("data_categories", []),
            sla_deadline=data.get("sla_deadline"),
            audit_trail=data.get("audit_trail", []),
        )
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_id(self, request_id: uuid.UUID) -> DataSubjectRequest | None:
        """Fetch a request by primary key (no company filter — public tracking)."""
        result = await self.db.execute(
            select(DataSubjectRequest).where(DataSubjectRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_company(
        self, request_id: uuid.UUID, company_id: uuid.UUID
    ) -> DataSubjectRequest | None:
        """Fetch a request by id scoped to a company (authenticated endpoints)."""
        result = await self.db.execute(
            select(DataSubjectRequest).where(
                and_(
                    DataSubjectRequest.id == request_id,
                    DataSubjectRequest.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_requests(
        self,
        company_id: uuid.UUID,
        status_filter: str | None,
        request_type: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        subject_email: str | None,
        skip: int,
        limit: int,
    ) -> tuple[list[DataSubjectRequest], int]:
        """List requests with optional filters; returns (rows, total_count)."""
        conditions = [DataSubjectRequest.company_id == company_id]

        if status_filter:
            conditions.append(DataSubjectRequest.status == status_filter)
        if request_type:
            conditions.append(DataSubjectRequest.request_type == request_type)
        if date_from:
            conditions.append(DataSubjectRequest.created_at >= date_from)
        if date_to:
            conditions.append(DataSubjectRequest.created_at <= date_to)
        if subject_email:
            conditions.append(DataSubjectRequest.subject_email.ilike(f"%{subject_email}%"))

        query = (
            select(DataSubjectRequest)
            .where(and_(*conditions))
            .order_by(desc(DataSubjectRequest.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        requests = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(DataSubjectRequest.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return requests, total

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_stats(self, company_id: uuid.UUID) -> dict:
        """Return aggregated statistics for all DSR endpoints."""
        total_result = await self.db.execute(
            select(func.count(DataSubjectRequest.id)).where(
                DataSubjectRequest.company_id == company_id
            )
        )
        total = total_result.scalar() or 0

        status_counts: dict[str, int] = {}
        for status_val in ["pending", "in_review", "processing", "completed", "rejected", "cancelled"]:
            count_result = await self.db.execute(
                select(func.count(DataSubjectRequest.id)).where(
                    and_(
                        DataSubjectRequest.company_id == company_id,
                        DataSubjectRequest.status == status_val,
                    )
                )
            )
            status_counts[status_val] = count_result.scalar() or 0

        overdue_result = await self.db.execute(
            select(func.count(DataSubjectRequest.id)).where(
                and_(
                    DataSubjectRequest.company_id == company_id,
                    DataSubjectRequest.status.in_(["pending", "in_review", "processing"]),
                    DataSubjectRequest.sla_deadline < datetime.utcnow(),
                )
            )
        )
        overdue = overdue_result.scalar() or 0

        sla_met_result = await self.db.execute(
            select(func.count(DataSubjectRequest.id)).where(
                and_(
                    DataSubjectRequest.company_id == company_id,
                    DataSubjectRequest.sla_met,
                )
            )
        )
        sla_met = sla_met_result.scalar() or 0

        type_counts: dict[str, int] = {}
        for type_val in ["access", "correction", "deletion", "portability", "objection", "restriction", "explanation"]:
            type_result = await self.db.execute(
                select(func.count(DataSubjectRequest.id)).where(
                    and_(
                        DataSubjectRequest.company_id == company_id,
                        DataSubjectRequest.request_type == type_val,
                    )
                )
            )
            type_counts[type_val] = type_result.scalar() or 0

        channel_counts: dict[str, int] = {}
        for channel_val in ["portal", "email", "whatsapp", "phone", "in_person", "api"]:
            channel_result = await self.db.execute(
                select(func.count(DataSubjectRequest.id)).where(
                    and_(
                        DataSubjectRequest.company_id == company_id,
                        DataSubjectRequest.source_channel == channel_val,
                    )
                )
            )
            channel_counts[channel_val] = channel_result.scalar() or 0

        return {
            "total": total,
            "status_counts": status_counts,
            "overdue": overdue,
            "sla_met": sla_met,
            "type_counts": type_counts,
            "channel_counts": channel_counts,
        }

    # ------------------------------------------------------------------
    # Mutations (assign, verify, process, complete, reject)
    # ------------------------------------------------------------------

    async def assign_request(
        self,
        request: DataSubjectRequest,
        assigned_to: uuid.UUID,
        audit_entry: dict,
    ) -> DataSubjectRequest:
        """Assign request to a user; advances status from pending to in_review."""
        request.assigned_to = assigned_to
        if request.status == "pending":
            request.status = "in_review"
        request.audit_trail = (request.audit_trail or []) + [audit_entry]
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def verify_identity(
        self,
        request: DataSubjectRequest,
        verified: bool,
        method: str,
        audit_entry: dict,
    ) -> DataSubjectRequest:
        """Record identity verification result."""
        request.identity_verified = verified
        request.identity_verification_method = method
        request.identity_verified_at = datetime.utcnow() if verified else None
        request.audit_trail = (request.audit_trail or []) + [audit_entry]
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def start_processing(
        self,
        request: DataSubjectRequest,
        audit_entry: dict,
    ) -> DataSubjectRequest:
        """Transition request to processing state."""
        request.status = "processing"
        request.audit_trail = (request.audit_trail or []) + [audit_entry]
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def complete_request(
        self,
        request: DataSubjectRequest,
        response: str,
        evidence_files: list,
        audit_entry: dict,
    ) -> DataSubjectRequest:
        """Mark request as completed with response and optional evidence files."""
        now = datetime.utcnow()
        request.status = "completed"
        request.response = response
        request.completed_at = now
        request.evidence_files = evidence_files
        request.sla_met = now <= request.sla_deadline if request.sla_deadline else True
        request.audit_trail = (request.audit_trail or []) + [audit_entry]
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def reject_request(
        self,
        request: DataSubjectRequest,
        rejection_reason: str,
        audit_entry: dict,
    ) -> DataSubjectRequest:
        """Reject request with a stated reason."""
        now = datetime.utcnow()
        request.status = "rejected"
        request.rejection_reason = rejection_reason
        request.completed_at = now
        request.sla_met = now <= request.sla_deadline if request.sla_deadline else True
        request.audit_trail = (request.audit_trail or []) + [audit_entry]
        await self.db.commit()
        await self.db.refresh(request)
        return request

    # ------------------------------------------------------------------
    # Rollback helper (used by controller exception handlers)
    # ------------------------------------------------------------------

    async def rollback(self) -> None:
        await self.db.rollback()
