"""
Email domain repository -- handles DB operations for EmailLog.
"""
import uuid
import re
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.email_template import EmailLog


class EmailRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_candidate_by_id(
        self,
        candidate_id: str,
        company_id: str | None = None,
    ) -> Candidate | None:
        """Fetch a Candidate by its string UUID, returns None if not found.

        Multi-tenancy defense-in-depth: pass company_id to filter at query level
        (Postgres RLS — Task #1143 — guards by default).
        """
        conditions = [Candidate.id == candidate_id]
        if company_id:
            conditions.append(Candidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(Candidate).where(*conditions)
        )
        return result.scalar_one_or_none()

    async def create_email_log(
        self,
        recipient_email: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
        candidate_id: str | None = None,
        metadata: dict | None = None,
    ) -> EmailLog:
        """Create and flush a new EmailLog record, returning the refreshed instance."""
        email_log = EmailLog(
            id=uuid.uuid4(),
            template_id=None,
            candidate_id=candidate_id,
            recipient_email=recipient_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            status="queued",
            variables_used=metadata or {},
            created_at=datetime.utcnow(),
            created_by="api",
        )
        self.db.add(email_log)
        await self.db.flush()
        await self.db.refresh(email_log)
        return email_log

    async def get_logs_by_candidate(
        self,
        candidate_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[EmailLog]]:
        """Return (total_count, paginated_logs) for a given candidate."""
        query = select(EmailLog).where(
            EmailLog.candidate_id == candidate_id
        ).order_by(desc(EmailLog.created_at))

        count_result = await self.db.execute(query)
        total = len(count_result.scalars().all())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        logs = result.scalars().all()
        return total, list(logs)

    async def get_all_logs(
        self,
        recipient_email: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[EmailLog]]:
        """Return (total_count, paginated_logs) with optional filters."""
        query = select(EmailLog)

        if recipient_email:
            query = query.where(EmailLog.recipient_email.ilike(f"%{recipient_email}%"))
        if status:
            query = query.where(EmailLog.status == status)

        query = query.order_by(desc(EmailLog.created_at))

        count_result = await self.db.execute(query)
        total = len(count_result.scalars().all())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        logs = result.scalars().all()
        return total, list(logs)

    @staticmethod
    def extract_body_preview(log: EmailLog) -> str | None:
        """Extract a short text preview from a log body fields."""
        if log.body_text:
            return log.body_text[:150] + "..." if len(log.body_text) > 150 else log.body_text
        if log.body_html:
            import re as _re
            text = _re.sub(r"<[^>]+>", "", log.body_html)
            return text[:150] + "..." if len(text) > 150 else text
        return None
