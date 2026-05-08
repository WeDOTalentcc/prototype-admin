"""
EmailTemplate Repository — data access for system + tenant email templates
managed by template_seeder.

Per ADR-001 extracted from app/domains/job_management/services/template_seeder.py.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.email_template import EmailTemplate


class EmailTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_system_template(
        self, *, situation: str, channel: str
    ) -> EmailTemplate | None:
        result = await self.db.execute(
            select(EmailTemplate).where(
                EmailTemplate.situation == situation,
                EmailTemplate.channel == channel,
                EmailTemplate.is_system_template,
                EmailTemplate.company_id.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_active_system_templates(self) -> list[EmailTemplate]:
        result = await self.db.execute(
            select(EmailTemplate).where(
                EmailTemplate.is_system_template,
                EmailTemplate.company_id.is_(None),
                EmailTemplate.is_active,
            )
        )
        return list(result.scalars().all())

    async def find_for_client(
        self, *, company_id: str, situation: str, channel: str
    ) -> EmailTemplate | None:
        result = await self.db.execute(
            select(EmailTemplate).where(
                EmailTemplate.company_id == company_id,
                EmailTemplate.situation == situation,
                EmailTemplate.channel == channel,
            )
        )
        return result.scalar_one_or_none()
