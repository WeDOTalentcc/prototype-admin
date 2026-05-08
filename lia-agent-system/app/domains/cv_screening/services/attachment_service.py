"""
Attachment Service

Manages candidate file attachments including CVs, documents, certificates, videos, and transcripts.
"""

import logging
from datetime import datetime
from typing import Any

from app.core.database import AsyncSessionLocal
from app.domains.cv_screening.repositories.candidate_attachment_repository import (
    CandidateAttachmentRepository,
)
from lia_models.candidate_attachment import CandidateAttachment

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
        """Create a new attachment record."""
        async with AsyncSessionLocal() as session:
            repo = CandidateAttachmentRepository(session)
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
            attachment = await repo.add(attachment)
            logger.info(f"Attachment created: {attachment.id}")
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
        """List attachments with optional filters."""
        async with AsyncSessionLocal() as session:
            repo = CandidateAttachmentRepository(session)
            attachments, total = await repo.list_with_filters(
                company_id=company_id,
                candidate_id=candidate_id,
                file_type=file_type,
                upload_source=upload_source,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )
            logger.info(f"Retrieved {len(attachments)} attachments (total: {total})")
            return {
                "attachments": [att.to_dict() for att in attachments],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    async def get_attachment_by_id(
        self,
        attachment_id: str,
    ) -> CandidateAttachment | None:
        """Get a single attachment by ID."""
        async with AsyncSessionLocal() as session:
            repo = CandidateAttachmentRepository(session)
            attachment = await repo.get_by_id(attachment_id)
            if attachment:
                logger.info(f"Retrieved attachment: {attachment.id}")
            else:
                logger.warning(f"Attachment not found: {attachment_id}")
            return attachment

    async def get_candidate_attachments(
        self,
        candidate_id: str,
        company_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get all attachments for a specific candidate."""
        async with AsyncSessionLocal() as session:
            repo = CandidateAttachmentRepository(session)
            attachments, total = await repo.list_for_candidate(
                candidate_id=candidate_id,
                company_id=company_id,
                limit=limit,
                offset=offset,
            )
            logger.info(f"Retrieved {len(attachments)} attachments for candidate {candidate_id}")
            return {
                "attachments": [att.to_dict() for att in attachments],
                "total": total,
            }

    async def deactivate_attachment(
        self,
        attachment_id: str,
    ) -> CandidateAttachment | None:
        """Soft delete an attachment by setting is_active=False."""
        async with AsyncSessionLocal() as session:
            repo = CandidateAttachmentRepository(session)
            attachment = await repo.get_by_id(attachment_id)
            if not attachment:
                logger.warning(f"Attachment not found for deactivation: {attachment_id}")
                return None
            attachment.is_active = False
            attachment.updated_at = datetime.utcnow()
            attachment = await repo.commit_changes(attachment)
            logger.info(f"Attachment deactivated: {attachment_id}")
            return attachment


attachment_service = AttachmentService()
