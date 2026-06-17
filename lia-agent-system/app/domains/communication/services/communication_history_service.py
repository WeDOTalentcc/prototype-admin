"""
Communication History Service — multi-tenant safe.

Manages communication history records for tracking all candidate communications
including emails, WhatsApp messages, screening invites, and feedback.
"""

import logging
from datetime import datetime
from typing import Any

from app.core.database import AsyncSessionLocal
from app.domains.communication.repositories.communication_history_repository import (
    CommunicationHistoryRepository,
)
from app.models import (
    CommunicationHistory,
    CommunicationStatus,
)

logger = logging.getLogger(__name__)


class CommunicationHistoryService:
    """Service for managing communication history records"""

    async def log_communication(
        self,
        candidate_id: str,
        candidate_name: str,
        communication_type: str,
        channel: str,
        direction: str,
        message_content: str,
        sent_by: str,
        company_id: str,
        candidate_email: str | None = None,
        candidate_phone: str | None = None,
        vacancy_id: str | None = None,
        vacancy_title: str | None = None,
        subject: str | None = None,
        template_id: str | None = None,
        template_name: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
        sent_by_name: str | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> CommunicationHistory:
        """Create a new communication history record."""
        message_preview = message_content[:200] if message_content else None

        async with AsyncSessionLocal() as session:
            repo = CommunicationHistoryRepository(session)
            communication = CommunicationHistory(
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone,
                vacancy_id=vacancy_id,
                vacancy_title=vacancy_title,
                communication_type=communication_type,
                channel=channel,
                direction=direction,
                subject=subject,
                message_content=message_content,
                message_preview=message_preview,
                template_id=template_id,
                template_name=template_name,
                attachments=attachments or [],
                status=CommunicationStatus.PENDING,
                sent_by=sent_by,
                sent_by_name=sent_by_name,
                company_id=company_id,
                extra_data=extra_data or {},
            )
            communication = await repo.add(communication)
            logger.info(
                f"Communication logged: {communication_type} via {channel} to {candidate_name}"
            )
            return communication

    async def list_communications(
        self,
        company_id: str,
        candidate_id: str | None = None,
        vacancy_id: str | None = None,
        communication_type: str | None = None,
        channel: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List communications with optional filters."""
        async with AsyncSessionLocal() as session:
            repo = CommunicationHistoryRepository(session)
            communications, total = await repo.list_with_filters(
                company_id=company_id,
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                communication_type=communication_type,
                channel=channel,
                status=status,
                limit=limit,
                offset=offset,
            )
            logger.info(f"Retrieved {len(communications)} communications (total: {total})")
            return {
                "communications": [comm.to_dict() for comm in communications],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    async def get_communication_by_id(
        self,
        communication_id: str,
        company_id: str | None = None,
    ) -> CommunicationHistory | None:
        """Get a single communication record by ID.

        Onda 4.2e-P0-3 (2026-05-23): company_id pre-check — antes vazava
        outbound message (subject/body/email/phone) cross-tenant.
        """
        async with AsyncSessionLocal() as session:
            repo = CommunicationHistoryRepository(session)
            communication = await repo.get_by_id(communication_id)
            # Onda 4.2e-P0-3: tenant guard.
            if communication and company_id and str(communication.company_id) != str(company_id):
                logger.warning(
                    f"Cross-tenant access blocked: communication {communication_id}"
                )
                return None
            if communication:
                logger.info(f"Retrieved communication: {communication.id}")
            else:
                logger.warning(f"Communication not found: {communication_id}")
            return communication

    async def update_communication_status(
        self,
        communication_id: str,
        new_status: str,
        error_message: str | None = None,
        company_id: str | None = None,
    ) -> CommunicationHistory | None:
        """Update communication status with appropriate timestamps.

        Onda 4.2e-P0-4 (2026-05-23): company_id pre-check.
        """
        async with AsyncSessionLocal() as session:
            repo = CommunicationHistoryRepository(session)
            communication = await repo.get_by_id(communication_id)
            if not communication:
                logger.warning(
                    f"Communication not found for status update: {communication_id}"
                )
                return None
            # Onda 4.2e-P0-4: tenant guard.
            if company_id and str(communication.company_id) != str(company_id):
                logger.warning(
                    f"Cross-tenant update blocked: communication {communication_id}"
                )
                return None

            now = datetime.utcnow()
            communication.status = new_status
            if new_status == CommunicationStatus.SENT:
                communication.sent_at = now
            elif new_status == CommunicationStatus.DELIVERED:
                communication.delivered_at = now
            elif new_status == CommunicationStatus.READ:
                communication.read_at = now
            elif new_status == CommunicationStatus.FAILED:
                communication.failed_at = now
                if error_message:
                    communication.error_message = error_message
            communication = await repo.commit_changes(communication)
            logger.info(
                f"Communication {communication_id} status updated to: {new_status}"
            )
            return communication

    async def get_candidate_communications(
        self,
        candidate_id: str,
        company_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get all communications for a specific candidate."""
        async with AsyncSessionLocal() as session:
            repo = CommunicationHistoryRepository(session)
            communications, total = await repo.list_for_candidate(
                candidate_id=candidate_id,
                company_id=company_id,
                limit=limit,
                offset=offset,
            )
            logger.info(
                f"Retrieved {len(communications)} communications for candidate {candidate_id}"
            )
            return {
                "communications": [comm.to_dict() for comm in communications],
                "total": total,
            }

    async def transfer_communications_ownership(
        self,
        job_id: str,
        from_user_ids: list[str],
        to_user_id: str,
        company_id: str,
    ) -> dict[str, Any]:
        """Transfer ownership of PENDING communications from users to a new user.

        Used when reassigning jobs to new recruiters.
        """
        if not from_user_ids:
            return {"success": True, "transferred": 0, "job_id": job_id, "to_user_id": to_user_id}

        async with AsyncSessionLocal() as session:
            try:
                repo = CommunicationHistoryRepository(session)
                pending_statuses = [
                    CommunicationStatus.pending,
                    CommunicationStatus.scheduled,
                ]
                transferred = await repo.transfer_pending_ownership(
                    job_id=job_id,
                    from_user_ids=from_user_ids,
                    to_user_id=to_user_id,
                    company_id=company_id,
                    pending_statuses=pending_statuses,
                )
                logger.info(
                    f"Transferred {transferred} communications for job {job_id} to user {to_user_id}"
                )
                return {
                    "success": True,
                    "transferred": transferred,
                    "job_id": job_id,
                    "to_user_id": to_user_id,
                }
            except Exception as e:
                logger.error(f"Error transferring communications: {e}")
                return {
                    "success": False,
                    "transferred": 0,
                    "error": str(e),
                }


communication_history_service = CommunicationHistoryService()
