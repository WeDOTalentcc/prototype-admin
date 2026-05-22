"""EmailTemplateRepository — DB access for lia_models.email_template.EmailTemplate.

Extracted from app/domains/communication/services/template_service.py and
app/domains/communication/services/transition_dispatch_service.py per ADR-001.

Distinct from RecruitmentEmailTemplateRepository (different model — that one
handles RecruitmentEmailTemplate; this one handles EmailTemplate keyed by
situation/channel for transactional automation flows).
"""
from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.email_template import EmailTemplate


class EmailTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_by_id(
        self,
        template_id,
        company_id: str | None = None,
    ) -> EmailTemplate | None:
        """Get active EmailTemplate by id.

        Multi-tenancy defense-in-depth: pass company_id to scope to current tenant.
        Templates may be tenant-specific OR system templates (cross-tenant).
        """
        conditions = [
            EmailTemplate.id == template_id,
            EmailTemplate.is_active,
        ]
        if company_id:
            conditions.append(EmailTemplate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # EmailTemplate.company_id filter (conditional, above). Sensor cannot
        # trace through and_(*conditions) spread.
        result = await self.db.execute(
            select(EmailTemplate).where(and_(*conditions)).limit(1)
        )
        return result.scalar_one_or_none()

    async def find_active_by_situation_channel(
        self,
        *,
        situation: str,
        channel: str,
        company_id: str | None = None,
    ) -> EmailTemplate | None:
        """Find active EmailTemplate by (situation, channel).

        Multi-tenancy defense-in-depth: pass company_id to prefer tenant template.
        Use find_active_by_situation_channel_company for strict tenant-only lookup
        and find_system_template for explicit cross-tenant system templates.
        """
        conditions = [
            EmailTemplate.situation == situation,
            EmailTemplate.is_active,
            EmailTemplate.channel == channel,
        ]
        if company_id:
            conditions.append(EmailTemplate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # EmailTemplate.company_id filter (conditional, above). Sensor cannot
        # trace through and_(*conditions) spread.
        result = await self.db.execute(
            select(EmailTemplate).where(and_(*conditions)).limit(1)
        )
        return result.scalar_one_or_none()

    async def find_active_by_situation(
        self,
        *,
        situation: str,
        company_id: str | None = None,
    ) -> EmailTemplate | None:
        """Match by situation only (used when channel is implicit).

        Multi-tenancy defense-in-depth: pass company_id to scope to current tenant.
        """
        conditions = [
            EmailTemplate.situation == situation,
            EmailTemplate.is_active,
        ]
        if company_id:
            conditions.append(EmailTemplate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # EmailTemplate.company_id filter (conditional, above). Sensor cannot
        # trace through and_(*conditions) spread.
        result = await self.db.execute(
            select(EmailTemplate).where(and_(*conditions)).limit(1)
        )
        return result.scalar_one_or_none()


    async def find_active_by_situation_channel_company(
        self,
        *,
        situation: str,
        channel: str,
        company_id: str,
    ) -> EmailTemplate | None:
        """Company-specific active template lookup."""
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(EmailTemplate).where(
                EmailTemplate.situation == situation,
                EmailTemplate.channel == channel,
                EmailTemplate.is_active,
                EmailTemplate.company_id == company_id,
            )
        )
        return result.scalars().first()

    async def find_system_template(
        self,
        *,
        situation: str,
        channel: str,
    ) -> EmailTemplate | None:
        """System (platform-wide) template lookup."""
        # TENANT-EXEMPT: system templates are platform-wide (is_system_template=True),
        # intentionally cross-tenant — used as fallback when no tenant-specific
        # template exists. Filter by is_system_template flag bounds the rowset.
        result = await self.db.execute(
            select(EmailTemplate).where(
                EmailTemplate.situation == situation,
                EmailTemplate.channel == channel,
                EmailTemplate.is_active,
                EmailTemplate.is_system_template,
            )
        )
        return result.scalars().first()

    async def find_any_active_for_situation_channel(
        self,
        *,
        situation: str,
        channel: str,
    ) -> EmailTemplate | None:
        """Last-resort fallback: any active template for situation+channel."""
        # TENANT-EXEMPT: last-resort fallback intentionally cross-tenant (returns
        # FIRST matching template platform-wide). Only invoked after tenant-specific
        # and system-template lookups fail — see template_service caller.
        result = await self.db.execute(
            select(EmailTemplate).where(
                EmailTemplate.situation == situation,
                EmailTemplate.channel == channel,
                EmailTemplate.is_active,
            )
        )
        return result.scalars().first()
