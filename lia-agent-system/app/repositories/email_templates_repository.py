"""EmailTemplatesRepository — multi-tenant safe."""
import logging
import uuid as uuid_module
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.email_template import EmailLog, EmailTemplate

logger = logging.getLogger(__name__)


class EmailTemplatesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── EmailTemplate CRUD ────────────────────────────────────────────────

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
        """Return (items, total) with all filters applied."""
        # TENANT-EXEMPT: marketplace pattern — or_(company_id, IS NULL) aplicado abaixo quando company_id provided;
        # IS NULL = system templates marketplace; sensor AST não infere or_(...)
        query = select(EmailTemplate)

        if company_id:
            query = query.where(
                or_(
                    EmailTemplate.company_id == company_id,
                    EmailTemplate.company_id.is_(None),
                )
            )

        if visibility == "recruiter":
            query = query.where(
                or_(
                    EmailTemplate.visibility == "recruiter",
                    EmailTemplate.visibility == "all",
                )
            )
            query = query.where(~EmailTemplate.channel.in_(["bell", "teams"]))
        elif visibility == "admin":
            query = query.where(
                or_(
                    EmailTemplate.visibility == "admin",
                    EmailTemplate.visibility == "all",
                )
            )

        if category:
            query = query.where(EmailTemplate.category == category)
        if channel:
            query = query.where(EmailTemplate.channel == channel)
        if situation:
            query = query.where(EmailTemplate.situation == situation)
        if is_active is not None:
            query = query.where(EmailTemplate.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    EmailTemplate.name.ilike(search_term),
                    EmailTemplate.subject.ilike(search_term),
                )
            )

        # Count total before pagination
        count_result = await self.db.execute(query)
        total = len(count_result.scalars().all())

        # Paginate
        query = query.offset(skip).limit(limit).order_by(EmailTemplate.created_at.desc())
        result = await self.db.execute(query)
        templates = list(result.scalars().all())

        return templates, total

    async def list_distinct_categories(
        self,
        company_id: str | None = None,
        visibility: str | None = None,
    ) -> list[str]:
        query = select(distinct(EmailTemplate.category)).where(
            EmailTemplate.category.isnot(None)
        )
        if company_id:
            query = query.where(
                or_(
                    EmailTemplate.company_id == company_id,
                    EmailTemplate.company_id.is_(None),
                )
            )
        if visibility == "recruiter":
            query = query.where(
                or_(
                    EmailTemplate.visibility == "recruiter",
                    EmailTemplate.visibility == "all",
                )
            )
            query = query.where(~EmailTemplate.channel.in_(["bell", "teams"]))
        elif visibility == "admin":
            query = query.where(
                or_(
                    EmailTemplate.visibility == "admin",
                    EmailTemplate.visibility == "all",
                )
            )
        query = query.order_by(EmailTemplate.category)
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]

    async def get_by_id(
        self,
        template_id: uuid_module.UUID,
        company_id: str | None = None,
    ) -> EmailTemplate | None:
        """Lookup EmailTemplate por id.

        Sprint B.1 tail (2026-05-22): company_id opcional pra defense-in-depth.
        Prefer get_by_id_for_company para tenant-aware lookup canonical.
        """
        # TENANT-EXEMPT: defense-in-depth optional company_id; get_by_id_for_company (L141) é canonical tenant-aware getter; este metodo mantido pra backwards-compat
        if company_id is not None:
            result = await self.db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.id == template_id,
                    or_(
                        EmailTemplate.company_id == company_id,
                        EmailTemplate.company_id.is_(None),
                    ),
                )
            )
        else:
            # TENANT-EXEMPT: backwards-compat — caller responsavel pelo tenant gate
            result = await self.db.execute(
                select(EmailTemplate).where(EmailTemplate.id == template_id)
            )
        return result.scalar_one_or_none()

    async def get_by_id_str(self, template_id: str) -> EmailTemplate | None:
        return await self.get_by_id(uuid_module.UUID(template_id))

    async def get_by_id_for_company(
        self, template_id: str, company_id: str
    ) -> EmailTemplate | None:
        """Tenant-aware getter: return template only if owned by company OR is system template (company_id IS NULL).

        Wave 3 audit 2026-05-21 P0.TPL1 fix: previously get_by_id_str returned ANY template
        regardless of tenant, allowing cross-tenant read/write/delete on /email-templates/{id}
        endpoints. This canonical getter enforces multi-tenancy at the data layer.

        Returns None when template does not exist OR belongs to another company.
        Endpoint MUST raise 404 (NOT 403) to avoid leaking existence of foreign templates.
        """
        try:
            uuid_val = uuid_module.UUID(template_id)
        except (ValueError, TypeError):
            return None

        result = await self.db.execute(
            select(EmailTemplate).where(
                EmailTemplate.id == uuid_val,
                or_(
                    EmailTemplate.company_id == company_id,
                    EmailTemplate.company_id.is_(None),
                ),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, template: EmailTemplate) -> EmailTemplate:
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def update(self, template: EmailTemplate) -> EmailTemplate:
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def delete(self, template: EmailTemplate) -> None:
        await self.db.delete(template)

    async def rollback(self) -> None:
        await self.db.rollback()

    # ── EmailLog ──────────────────────────────────────────────────────────

    async def list_logs(
        self,
        template_id: str | None = None,
        candidate_id: str | None = None,
        status: str | None = None,
        recipient_email: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[EmailLog], int]:
        """Return (items, total) with all filters applied."""
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

    # ── Rate limiting / candidate validation ─────────────────────────────

    async def count_recent_emails_by_user(
        self, user_id: uuid_module.UUID, since: datetime
    ) -> int:
        result = await self.db.execute(
            select(func.count(EmailLog.id)).where(
                EmailLog.created_at >= since,
                EmailLog.created_by == str(user_id),
            )
        )
        return result.scalar() or 0

    async def candidate_email_exists(
        self, email: str, company_id: str | None = None,
    ) -> bool:
        """Check if email belongs to a known active candidate.

        Onda 4.2e-P0-8 (2026-05-23): company_id filter — antes atacante A
        enviava email pra candidato empresa B via template empresa B
        (cross-tenant + branding hijack). LGPD Art. 33.
        """
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        from sqlalchemy import or_
        email_hash = _sha256_hash(email)
        query = select(Candidate.id).where(
            or_(
                Candidate.email_hash == email_hash,
                Candidate._email_raw == email,
            ),
            Candidate.is_active,
        )
        if company_id:
            query = query.where(Candidate.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
