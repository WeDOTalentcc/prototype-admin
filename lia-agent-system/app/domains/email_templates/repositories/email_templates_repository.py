"""
EmailTemplatesRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/email_templates.py.
"""
import logging
import uuid as uuid_module
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.email_template import EmailLog, EmailTemplate

logger = logging.getLogger(__name__)

RATE_LIMIT_EMAILS_PER_MINUTE = 10


class EmailTemplatesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── EmailTemplate queries ────────────────────────────────────────────────

    async def list_templates(
        self,
        company_id: str | None = None,
        visibility: str | None = None,
        category: str | None = None,
        channel: str | None = None,
        situation: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[EmailTemplate], int]:
        """Return (templates, total_count) applying all filters."""
        base = select(EmailTemplate)

        if company_id:
            base = base.where(
                or_(
                    EmailTemplate.company_id == company_id,
                    EmailTemplate.company_id.is_(None),
                )
            )

        if visibility == "recruiter":
            base = base.where(
                or_(
                    EmailTemplate.visibility == "recruiter",
                    EmailTemplate.visibility == "all",
                )
            )
            base = base.where(~EmailTemplate.channel.in_(["bell", "teams"]))
        elif visibility == "admin":
            base = base.where(
                or_(
                    EmailTemplate.visibility == "admin",
                    EmailTemplate.visibility == "all",
                )
            )

        if category:
            base = base.where(EmailTemplate.category == category)

        if channel:
            base = base.where(EmailTemplate.channel == channel)

        if situation:
            base = base.where(EmailTemplate.situation == situation)

        if is_active is not None:
            base = base.where(EmailTemplate.is_active == is_active)

        if search:
            search_term = f"%{search}%"
            base = base.where(
                or_(
                    EmailTemplate.name.ilike(search_term),
                    EmailTemplate.subject.ilike(search_term),
                )
            )

        count_result = await self.db.execute(base)
        total = len(count_result.scalars().all())

        query = base.offset(skip).limit(limit).order_by(EmailTemplate.created_at.desc())
        result = await self.db.execute(query)
        templates = list(result.scalars().all())

        return templates, total

    async def get_by_id(self, template_id: uuid_module.UUID) -> EmailTemplate | None:
        result = await self.db.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_str(self, template_id: str) -> EmailTemplate | None:
        return await self.get_by_id(uuid_module.UUID(template_id))

    async def create_template(self, template: EmailTemplate) -> EmailTemplate:
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def update_template(self, template: EmailTemplate) -> EmailTemplate:
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def delete_template(self, template: EmailTemplate) -> None:
        await self.db.delete(template)

    async def rollback(self) -> None:
        await self.db.rollback()

    # ── EmailLog queries ─────────────────────────────────────────────────────

    async def list_logs(
        self,
        template_id: str | None = None,
        candidate_id: str | None = None,
        status: str | None = None,
        recipient_email: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[EmailLog], int]:
        """Return (logs, total_count) applying all filters."""
        query = select(EmailLog)

        if template_id:
            query = query.where(EmailLog.template_id == uuid_module.UUID(template_id))

        if candidate_id:
            query = query.where(EmailLog.candidate_id == candidate_id)

        if status:
            query = query.where(EmailLog.status == status)

        if recipient_email:
            query = query.where(EmailLog.recipient_email.ilike(f"%{recipient_email}%"))

        count_result = await self.db.execute(query)
        total = len(count_result.scalars().all())

        query = query.offset(skip).limit(limit).order_by(EmailLog.created_at.desc())
        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total

    # ── Rate limit / validation helpers ────────────────────────────────────

    async def count_recent_emails_by_user(self, user_id: uuid_module.UUID) -> int:
        """Count emails sent by a user in the last minute."""
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        result = await self.db.execute(
            select(func.count(EmailLog.id)).where(
                EmailLog.created_at >= one_minute_ago,
                EmailLog.created_by == str(user_id),
            )
        )
        return result.scalar() or 0

    async def is_known_active_candidate(self, email: str) -> bool:
        """Return True if email belongs to an active candidate."""
        result = await self.db.execute(
            select(Candidate.id).where(
                Candidate.email == email,
                Candidate.is_active,
            )
        )
        return result.scalar_one_or_none() is not None
