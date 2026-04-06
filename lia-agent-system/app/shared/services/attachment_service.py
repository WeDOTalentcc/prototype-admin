"""
Attachment Service

Manages candidate file attachments including CVs, documents, certificates, videos, and transcripts.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, select

from app.core.database import AsyncSessionLocal
from app.models.candidate_attachment import CandidateAttachment

logger = logging.getLogger(__name__)


class AttachmentService:
    """Service for managing candidate attachments"""
    
    async def create_attachment(
        self,
        candidate_id: str,
        candidate_name: str,
        file_name: str,
        file_type: str,
        file_url: str,
        upload_source: str,
        uploaded_by: str,
        company_id: str,
        file_size: int | None = None,
        mime_type: str | None = None,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
        description: str | None = None,
        uploaded_by_name: str | None = None,
    ) -> CandidateAttachment:
        """
        Create a new attachment record.
        
        Args:
            candidate_id: ID of the candidate
            candidate_name: Name of the candidate
            file_name: Original file name
            file_type: Type of file (cv, document, certificate, video, transcript, other)
            file_url: URL where file is stored
            upload_source: Source of upload (candidate, recruiter, lia, ats)
            uploaded_by: ID of who uploaded the file
            company_id: Company ID for multi-tenancy
            file_size: File size in bytes (optional)
            mime_type: MIME type of file (optional)
            related_entity_type: Type of related entity (optional)
            related_entity_id: ID of related entity (optional)
            description: Description of the attachment (optional)
            uploaded_by_name: Display name of uploader (optional)
            
        Returns:
            Created CandidateAttachment instance
        """
        async with AsyncSessionLocal() as session:
            attachment = CandidateAttachment(
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                file_name=file_name,
                file_type=file_type,
                file_url=file_url,
                file_size=file_size,
                mime_type=mime_type,
                upload_source=upload_source,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                description=description,
                uploaded_by=uploaded_by,
                uploaded_by_name=uploaded_by_name,
                company_id=company_id,
                is_active=True,
            )
            
            session.add(attachment)
            await session.commit()
            await session.refresh(attachment)
            
            logger.info(f"✅ Attachment created: {attachment.id} - {file_name} for candidate {candidate_name}")
            return attachment
    
    async def list_attachments(
        self,
        company_id: str,
        candidate_id: str | None = None,
        file_type: str | None = None,
        upload_source: str | None = None,
        is_active: bool | None = True,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List attachments with optional filters.
        
        Args:
            company_id: Company ID (required for multi-tenancy)
            candidate_id: Filter by candidate ID (optional)
            file_type: Filter by file type (optional)
            upload_source: Filter by upload source (optional)
            is_active: Filter by active status (default: True)
            limit: Max number of results (default: 50)
            offset: Offset for pagination (default: 0)
            
        Returns:
            Dict with attachments list, total count, limit, offset
        """
        async with AsyncSessionLocal() as session:
            where_conditions = [CandidateAttachment.company_id == company_id]
            
            if candidate_id:
                where_conditions.append(CandidateAttachment.candidate_id == candidate_id)
            
            if file_type:
                where_conditions.append(CandidateAttachment.file_type == file_type)
            
            if upload_source:
                where_conditions.append(CandidateAttachment.upload_source == upload_source)
            
            if is_active is not None:
                where_conditions.append(CandidateAttachment.is_active == is_active)
            
            count_query = (
                select(func.count())
                .select_from(CandidateAttachment)
                .where(and_(*where_conditions))
            )
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0
            
            data_query = (
                select(CandidateAttachment)
                .where(and_(*where_conditions))
                .order_by(desc(CandidateAttachment.created_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(data_query)
            attachments = result.scalars().all()
            
            logger.info(f"📋 Retrieved {len(attachments)} attachments (total: {total})")
            
            return {
                "attachments": [att.to_dict() for att in attachments],
                "total": total,
                "limit": limit,
                "offset": offset,
            }
    
    async def get_attachment_by_id(
        self,
        attachment_id: str
    ) -> CandidateAttachment | None:
        """
        Get a single attachment by ID.
        
        Args:
            attachment_id: Attachment UUID
            
        Returns:
            CandidateAttachment instance or None if not found
        """
        async with AsyncSessionLocal() as session:
            query = select(CandidateAttachment).where(
                CandidateAttachment.id == attachment_id
            )
            result = await session.execute(query)
            attachment = result.scalar_one_or_none()
            
            if attachment:
                logger.info(f"📋 Retrieved attachment: {attachment.id}")
            else:
                logger.warning(f"⚠️ Attachment not found: {attachment_id}")
            
            return attachment
    
    async def get_candidate_attachments(
        self,
        candidate_id: str,
        company_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get all attachments for a specific candidate.
        
        Args:
            candidate_id: Candidate ID
            company_id: Company ID (for multi-tenancy)
            limit: Max number of results (default: 100)
            offset: Offset for pagination (default: 0)
            
        Returns:
            Dict with attachments list and total count
        """
        async with AsyncSessionLocal() as session:
            where_conditions = [
                CandidateAttachment.candidate_id == candidate_id,
                CandidateAttachment.company_id == company_id,
                CandidateAttachment.is_active == True,
            ]
            
            count_query = (
                select(func.count())
                .select_from(CandidateAttachment)
                .where(and_(*where_conditions))
            )
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0
            
            data_query = (
                select(CandidateAttachment)
                .where(and_(*where_conditions))
                .order_by(desc(CandidateAttachment.created_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(data_query)
            attachments = result.scalars().all()
            
            logger.info(f"📋 Retrieved {len(attachments)} attachments for candidate {candidate_id}")
            
            return {
                "attachments": [att.to_dict() for att in attachments],
                "total": total,
            }
    
    async def deactivate_attachment(
        self,
        attachment_id: str
    ) -> CandidateAttachment | None:
        """
        Soft delete an attachment by setting is_active=False.
        
        Args:
            attachment_id: Attachment UUID
            
        Returns:
            Updated CandidateAttachment instance or None if not found
        """
        async with AsyncSessionLocal() as session:
            query = select(CandidateAttachment).where(
                CandidateAttachment.id == attachment_id
            )
            result = await session.execute(query)
            attachment = result.scalar_one_or_none()
            
            if not attachment:
                logger.warning(f"⚠️ Attachment not found for deactivation: {attachment_id}")
                return None
            
            attachment.is_active = False
            attachment.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(attachment)
            
            logger.info(f"✅ Attachment deactivated: {attachment_id}")
            return attachment


attachment_service = AttachmentService()
