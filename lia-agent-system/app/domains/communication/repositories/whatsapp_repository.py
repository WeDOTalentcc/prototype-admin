"""WhatsappRepository — DB access layer for WhatsApp conversation queries.

Extracted from app/api/v1/whatsapp.py as part of Phase 2 refactor.
Tables covered:
  - companies (phone number mappings)
  - whatsapp_conversations
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class WhatsappRepository:
    """Repository for WhatsApp conversation and company mapping data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_company_id_by_meta_phone(self, phone_number_id: str) -> str | None:
        """Return company_id for a given Meta WhatsApp phone_number_id, or None."""
        try:
            from app.models.company import Company
            result = await self.db.execute(
                select(Company.id).where(Company.whatsapp_phone_number_id == phone_number_id)
            )
            company = result.scalar_one_or_none()
            if company:
                return str(company)
        except Exception as exc:
            logger.warning(f"[WhatsappRepository] Could not query company mapping: {exc}")
        return None

    async def get_company_id_by_twilio_number(self, twilio_number: str) -> str | None:
        """Return company_id for a given Twilio WhatsApp number, or None."""
        try:
            from app.models.company import Company
            result = await self.db.execute(
                select(Company.id).where(Company.twilio_whatsapp_number == twilio_number)
            )
            company = result.scalar_one_or_none()
            if company:
                return str(company)
        except Exception as exc:
            logger.warning(f"[WhatsappRepository] Could not query Twilio number mapping: {exc}")
        return None

    async def list_conversations(
        self,
        company_id: str,
        status: str | None = None,
        limit: int = 50,
    ) -> list:
        """Return WhatsApp conversations for a company, optionally filtered by status."""
        from app.models.whatsapp_conversation import ConversationState, WhatsAppConversation

        query = (
            select(WhatsAppConversation)
            .where(WhatsAppConversation.company_id == company_id)
            .order_by(WhatsAppConversation.created_at.desc())
            .limit(limit)
        )

        if status:
            query = query.where(WhatsAppConversation.state == ConversationState(status))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── Cross-domain reads (used by automation_handlers — ADR-001) ──────────

    async def get_latest_awaiting_screening_for_candidate_vacancy(
        self,
        candidate_id,
        job_vacancy_id,
        company_id: str | None = None,
    ):
        """Return the most-recent AWAITING_SCREENING conversation for (candidate, vacancy).

        Used by automation_handlers.process_screening_queue and
        handle_recruiter_override_approve to flip the conversation state to
        SCREENING when promoting a queued candidate.

        Multi-tenancy defense-in-depth: pass company_id to filter at query level.
        """
        from sqlalchemy import and_

        from app.models.whatsapp_conversation import (
            ConversationState,
            WhatsAppConversation,
        )

        conditions = [
            WhatsAppConversation.candidate_id == candidate_id,
            WhatsAppConversation.job_vacancy_id == job_vacancy_id,
            WhatsAppConversation.state == ConversationState.AWAITING_SCREENING,
        ]
        if company_id:
            conditions.append(WhatsAppConversation.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # WhatsAppConversation.company_id filter (conditional, above).
        result = await self.db.execute(
            select(WhatsAppConversation)
            .where(and_(*conditions))
            .order_by(WhatsAppConversation.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
