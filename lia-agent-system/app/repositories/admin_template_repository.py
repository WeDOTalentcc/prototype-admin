"""
AdminTemplate Repository — data access layer for system email templates.
Extracted from app/api/v1/admin_templates.py as part of Phase 2 refactor.
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_template import EmailTemplate

logger = logging.getLogger(__name__)


class AdminTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_system_templates(
        self,
        *,
        category: str | None = None,
        channel: str | None = None,
        situation: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[EmailTemplate], int]:
        # TENANT-EXEMPT: system templates by definition têm company_id=NULL e são acessados
        # apenas por admin WeDOTalent (require_admin gate em app/api/v1/admin_templates.py).
        # Marketplace global pattern (audit 2026-05-22 tail sprint).
        query = select(EmailTemplate).where(EmailTemplate.is_system_template.is_(True))
        count_q = select(func.count(EmailTemplate.id)).where(EmailTemplate.is_system_template.is_(True))

        filters = []
        if category:
            filters.append(EmailTemplate.category == category)
        if channel:
            filters.append(EmailTemplate.channel == channel)
        if situation:
            filters.append(EmailTemplate.situation == situation)
        if is_active is not None:
            filters.append(EmailTemplate.is_active == is_active)
        if search:
            term = f"%{search}%"
            filters.append(
                or_(EmailTemplate.name.ilike(term), EmailTemplate.subject.ilike(term))
            )
        for f in filters:
            query = query.where(f)
            count_q = count_q.where(f)

        total = (await self.db.execute(count_q)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(EmailTemplate.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_system_template_by_id(self, template_id: uuid.UUID) -> EmailTemplate | None:
        # TENANT-EXEMPT: system template lookup (company_id=NULL by design) — admin-only.
        result = await self.db.execute(
            select(EmailTemplate).where(
                EmailTemplate.id == template_id,
                EmailTemplate.is_system_template.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_system_template_by_name(self, name: str, exclude_id: uuid.UUID | None = None) -> EmailTemplate | None:
        # TENANT-EXEMPT: system template lookup (company_id=NULL by design) — admin-only.
        q = select(EmailTemplate).where(
            EmailTemplate.name == name,
            EmailTemplate.is_system_template.is_(True),
        )
        if exclude_id:
            q = q.where(EmailTemplate.id != exclude_id)
        return (await self.db.execute(q)).scalar_one_or_none()

    async def create_system_template(self, data: dict) -> EmailTemplate:
        template = EmailTemplate(
            id=uuid.uuid4(),
            is_system_template=True,
            company_id=None,
            created_by="admin",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **data,
        )
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def update_system_template(self, template: EmailTemplate, data: dict) -> EmailTemplate:
        for field, value in data.items():
            if hasattr(template, field):
                setattr(template, field, value)
        template.version = (template.version or 1) + 1
        template.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def delete_system_template(self, template: EmailTemplate, *, hard: bool = False) -> str:
        if hard:
            await self.db.delete(template)
            return "permanently deleted"
        else:
            template.is_active = False
            template.updated_at = datetime.utcnow()
            return "deactivated"

    async def get_company_ids_with_active_users(self) -> list[str]:
        from app.auth.models import User as UserModel
        result = await self.db.execute(
            select(UserModel.company_id)
            .where(UserModel.company_id.isnot(None), UserModel.is_active.is_(True))
            .distinct()
        )
        return [c for c in result.scalars().all() if c]

    async def get_company_template_by_name(self, name: str, company_id: str) -> EmailTemplate | None:
        result = await self.db.execute(
            select(EmailTemplate).where(
                EmailTemplate.name == name,
                EmailTemplate.company_id == company_id,
                EmailTemplate.is_system_template.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def create_company_copy(
        self, source: EmailTemplate, company_id: str, created_by: str
    ) -> EmailTemplate:
        copy = EmailTemplate(
            id=uuid.uuid4(),
            name=source.name,
            subject=source.subject,
            body_html=source.body_html,
            body_text=source.body_text,
            category=source.category,
            channel=source.channel,
            situation=source.situation,
            variables=source.variables,
            is_active=True,
            is_system_template=False,
            version=1,
            company_id=company_id,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(copy)
        return copy
