"""
Communication History Service

Manages communication history records for tracking all candidate communications
including emails, WhatsApp messages, screening invites, and feedback.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, select

from app.core.database import AsyncSessionLocal
from lia_models import (
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
        """
        Create a new communication history record.
        
        Args:
            candidate_id: ID of the candidate
            candidate_name: Name of the candidate
            communication_type: Type of communication (email, whatsapp, etc.)
            channel: Communication channel
            direction: Direction (outbound/inbound)
            message_content: Full message content
            sent_by: ID of who sent the communication
            company_id: Company ID for multi-tenancy
            candidate_email: Candidate email address (optional)
            candidate_phone: Candidate phone number (optional)
            vacancy_id: Related vacancy ID (optional)
            vacancy_title: Related vacancy title (optional)
            subject: Message subject (optional)
            template_id: Template ID if used (optional)
            template_name: Template name if used (optional)
            attachments: List of attachments (optional)
            sent_by_name: Display name of sender (optional)
            extra_data: Additional metadata (optional)
            
        Returns:
            Created CommunicationHistory instance
        """
        message_preview = message_content[:200] if message_content else None
        
        async with AsyncSessionLocal() as session:
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
            
            session.add(communication)
            await session.commit()
            await session.refresh(communication)
            
            logger.info(f"✅ Communication logged: {communication_type} via {channel} to {candidate_name}")
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
        """
        List communications with optional filters.
        
        Args:
            company_id: Company ID (required for multi-tenancy)
            candidate_id: Filter by candidate ID (optional)
            vacancy_id: Filter by vacancy ID (optional)
            communication_type: Filter by communication type (optional)
            channel: Filter by channel (optional)
            status: Filter by status (optional)
            limit: Max number of results (default: 50)
            offset: Offset for pagination (default: 0)
            
        Returns:
            Dict with communications list, total count, limit, offset
        """
        async with AsyncSessionLocal() as session:
            where_conditions = [CommunicationHistory.company_id == company_id]
            
            if candidate_id:
                where_conditions.append(CommunicationHistory.candidate_id == candidate_id)
            
            if vacancy_id:
                where_conditions.append(CommunicationHistory.vacancy_id == vacancy_id)
            
            if communication_type:
                where_conditions.append(CommunicationHistory.communication_type == communication_type)
            
            if channel:
                where_conditions.append(CommunicationHistory.channel == channel)
            
            if status:
                where_conditions.append(CommunicationHistory.status == status)
            
            count_query = (
                select(func.count())
                .select_from(CommunicationHistory)
                .where(and_(*where_conditions))
            )
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0
            
            data_query = (
                select(CommunicationHistory)
                .where(and_(*where_conditions))
                .order_by(desc(CommunicationHistory.created_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(data_query)
            communications = result.scalars().all()
            
            logger.info(f"📋 Retrieved {len(communications)} communications (total: {total})")
            
            return {
                "communications": [comm.to_dict() for comm in communications],
                "total": total,
                "limit": limit,
                "offset": offset,
            }
    
    async def get_communication_by_id(
        self,
        communication_id: str
    ) -> CommunicationHistory | None:
        """
        Get a single communication record by ID.
        
        Args:
            communication_id: Communication UUID
            
        Returns:
            CommunicationHistory instance or None if not found
        """
        async with AsyncSessionLocal() as session:
            query = select(CommunicationHistory).where(
                CommunicationHistory.id == communication_id
            )
            result = await session.execute(query)
            communication = result.scalar_one_or_none()
            
            if communication:
                logger.info(f"📋 Retrieved communication: {communication.id}")
            else:
                logger.warning(f"⚠️ Communication not found: {communication_id}")
            
            return communication
    
    async def update_communication_status(
        self,
        communication_id: str,
        new_status: str,
        error_message: str | None = None,
    ) -> CommunicationHistory | None:
        """
        Update communication status with appropriate timestamps.
        
        Args:
            communication_id: Communication UUID
            new_status: New status (sent, delivered, read, failed)
            error_message: Error message for failed status (optional)
            
        Returns:
            Updated CommunicationHistory instance or None if not found
        """
        async with AsyncSessionLocal() as session:
            query = select(CommunicationHistory).where(
                CommunicationHistory.id == communication_id
            )
            result = await session.execute(query)
            communication = result.scalar_one_or_none()
            
            if not communication:
                logger.warning(f"⚠️ Communication not found for status update: {communication_id}")
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
            
            await session.commit()
            await session.refresh(communication)
            
            logger.info(f"✅ Communication {communication_id} status updated to: {new_status}")
            return communication
    
    async def get_candidate_communications(
        self,
        candidate_id: str,
        company_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get all communications for a specific candidate.
        
        Args:
            candidate_id: Candidate ID
            company_id: Company ID for multi-tenancy
            limit: Max number of results (default: 100)
            offset: Offset for pagination (default: 0)
            
        Returns:
            Dict with communications list and total count
        """
        async with AsyncSessionLocal() as session:
            where_conditions = [
                CommunicationHistory.candidate_id == candidate_id,
                CommunicationHistory.company_id == company_id,
            ]
            
            count_query = (
                select(func.count())
                .select_from(CommunicationHistory)
                .where(and_(*where_conditions))
            )
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0
            
            data_query = (
                select(CommunicationHistory)
                .where(and_(*where_conditions))
                .order_by(desc(CommunicationHistory.created_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(data_query)
            communications = result.scalars().all()
            
            logger.info(f"📋 Retrieved {len(communications)} communications for candidate {candidate_id}")
            
            return {
                "communications": [comm.to_dict() for comm in communications],
                "total": total,
            }

    async def transfer_communications_ownership(
        self,
        job_id: str,
        from_user_ids: list[str],
        to_user_id: str,
        company_id: str
    ) -> dict[str, Any]:
        """
        Transfer ownership of PENDING communications from one or more users to a new user.
        
        This updates the sent_by field for pending/scheduled communications related to a specific job.
        Used when reassigning jobs to new recruiters.
        """
        if not from_user_ids:
            return {"success": True, "transferred": 0, "job_id": job_id, "to_user_id": to_user_id}
            
        async with AsyncSessionLocal() as session:
            try:
                from sqlalchemy import update
                
                pending_statuses = [CommunicationStatus.pending, CommunicationStatus.scheduled]
                
                stmt = (
                    update(CommunicationHistory)
                    .where(
                        and_(
                            CommunicationHistory.vacancy_id == job_id,
                            CommunicationHistory.sent_by.in_(from_user_ids),
                            CommunicationHistory.company_id == company_id,
                            CommunicationHistory.status.in_(pending_statuses)
                        )
                    )
                    .values(sent_by=to_user_id)
                )
                
                result = await session.execute(stmt)
                await session.commit()
                
                transferred = result.rowcount
                logger.info(f"🔄 Transferred {transferred} communications for job {job_id} to user {to_user_id}")
                
                return {
                    "success": True,
                    "transferred": transferred,
                    "job_id": job_id,
                    "to_user_id": to_user_id
                }
            except Exception as e:
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.error(f"❌ Error transferring communications: {e}")
                return {
                    "success": False,
                    "transferred": 0,
                    "error": str(e)
                }


communication_history_service = CommunicationHistoryService()


def _strip_meta(p: dict) -> dict:
    return {k: v for k, v in p.items() if not k.startswith("_")}


async def get_history(**params):
    """Wrapper para o chat. Delega para list_communications."""
    p = _strip_meta(params)
    if "candidate_id" in p and hasattr(communication_history_service, "get_candidate_communications"):
        return await communication_history_service.get_candidate_communications(**p)
    return await communication_history_service.list_communications(**p)
