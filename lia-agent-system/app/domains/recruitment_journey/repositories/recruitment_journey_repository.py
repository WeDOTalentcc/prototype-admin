"""
Repository for RecruitmentTemplate, RecruitmentSLA, RecruitmentAutomation, and SLAViolation models.
All database access for the recruitment_journey domain is centralised here.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recruitment_journey import (
    DEFAULT_AUTOMATIONS,
    DEFAULT_SLAS,
    DEFAULT_TEMPLATES,
    RecruitmentAutomation,
    RecruitmentSLA,
    RecruitmentTemplate,
    SLAViolation,
)


class RecruitmentJourneyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    async def list_templates(
        self,
        company_id: uuid.UUID,
        template_type: str | None = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[RecruitmentTemplate]:
        conditions = [
            RecruitmentTemplate.company_id == company_id,
            RecruitmentTemplate.is_active == is_active,
        ]
        if template_type:
            conditions.append(RecruitmentTemplate.template_type == template_type)

        query = (
            select(RecruitmentTemplate)
            .where(and_(*conditions))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_template(self, template_id: uuid.UUID) -> RecruitmentTemplate | None:
        result = await self.db.execute(
            select(RecruitmentTemplate).where(RecruitmentTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_default_templates_for_company(
        self, company_id: uuid.UUID
    ) -> list[RecruitmentTemplate]:
        result = await self.db.execute(
            select(RecruitmentTemplate).where(
                RecruitmentTemplate.company_id == company_id,
                RecruitmentTemplate.is_default == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def get_templates_for_company(
        self, company_id: uuid.UUID
    ) -> list[RecruitmentTemplate]:
        """Return all templates (any status) for a company — used for init checks."""
        result = await self.db.execute(
            select(RecruitmentTemplate).where(
                RecruitmentTemplate.company_id == company_id
            )
        )
        return list(result.scalars().all())

    async def get_active_template_by_type(
        self, company_id: uuid.UUID, template_type: str
    ) -> RecruitmentTemplate | None:
        result = await self.db.execute(
            select(RecruitmentTemplate).where(
                RecruitmentTemplate.company_id == company_id,
                RecruitmentTemplate.template_type == template_type,
                RecruitmentTemplate.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def create_template(
        self, company_id: uuid.UUID, data: dict[str, Any], is_default: bool = False
    ) -> RecruitmentTemplate:
        """Unset existing defaults if new template is marked default, then create."""
        if is_default:
            existing_defaults = await self.get_default_templates_for_company(company_id)
            for t in existing_defaults:
                t.is_default = False

        template = RecruitmentTemplate(company_id=company_id, **data)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update_template(
        self, template: RecruitmentTemplate, update_data: dict[str, Any]
    ) -> RecruitmentTemplate:
        for field, value in update_data.items():
            setattr(template, field, value)
        template.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def soft_delete_template(self, template: RecruitmentTemplate) -> None:
        template.is_active = False
        template.updated_at = datetime.utcnow()
        await self.db.commit()

    async def initialize_templates(
        self, company_id: uuid.UUID
    ) -> list[str]:
        """
        Create default templates for a company.
        Returns list of created template names.
        Callers should check get_templates_for_company first to avoid duplication.
        """
        names: list[str] = []
        for template_data in DEFAULT_TEMPLATES:
            template = RecruitmentTemplate(
                company_id=company_id,
                **template_data,
                is_default=template_data.get("template_type") == "technical",
            )
            self.db.add(template)
            names.append(template_data["name"])
        await self.db.commit()
        return names

    # ------------------------------------------------------------------
    # SLAs
    # ------------------------------------------------------------------

    async def list_slas(
        self,
        company_id: uuid.UUID,
        stage_name: str | None = None,
        is_active: bool = True,
    ) -> list[RecruitmentSLA]:
        conditions = [
            RecruitmentSLA.company_id == company_id,
            RecruitmentSLA.is_active == is_active,
        ]
        if stage_name:
            conditions.append(RecruitmentSLA.stage_name == stage_name)

        result = await self.db.execute(
            # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter
            select(RecruitmentSLA).where(and_(*conditions))
        )
        return list(result.scalars().all())

    async def get_sla(self, sla_id: uuid.UUID) -> RecruitmentSLA | None:
        result = await self.db.execute(
            select(RecruitmentSLA).where(RecruitmentSLA.id == sla_id)
        )
        return result.scalar_one_or_none()

    async def get_slas_for_company(
        self, company_id: uuid.UUID
    ) -> list[RecruitmentSLA]:
        result = await self.db.execute(
            select(RecruitmentSLA).where(RecruitmentSLA.company_id == company_id)
        )
        return list(result.scalars().all())

    async def get_active_slas_for_company(
        self, company_id: uuid.UUID
    ) -> list[RecruitmentSLA]:
        result = await self.db.execute(
            select(RecruitmentSLA).where(
                RecruitmentSLA.company_id == company_id,
                RecruitmentSLA.is_active == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def create_sla(
        self, company_id: uuid.UUID, data: dict[str, Any]
    ) -> RecruitmentSLA:
        sla = RecruitmentSLA(company_id=company_id, **data)
        self.db.add(sla)
        await self.db.commit()
        await self.db.refresh(sla)
        return sla

    async def update_sla(
        self, sla: RecruitmentSLA, update_data: dict[str, Any]
    ) -> RecruitmentSLA:
        for field, value in update_data.items():
            setattr(sla, field, value)
        sla.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(sla)
        return sla

    async def soft_delete_sla(self, sla: RecruitmentSLA) -> None:
        sla.is_active = False
        sla.updated_at = datetime.utcnow()
        await self.db.commit()

    async def initialize_slas(self, company_id: uuid.UUID) -> list[str]:
        """
        Create default SLAs for a company.
        Callers should check get_slas_for_company first to avoid duplication.
        """
        names: list[str] = []
        for sla_data in DEFAULT_SLAS:
            sla = RecruitmentSLA(company_id=company_id, **sla_data)
            self.db.add(sla)
            names.append(sla_data["name"])
        await self.db.commit()
        return names

    # ------------------------------------------------------------------
    # SLA Violations
    # ------------------------------------------------------------------

    async def list_violations(
        self,
        company_id: uuid.UUID,
        job_id: uuid.UUID | None = None,
        violation_type: str | None = None,
        resolved: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SLAViolation], int]:
        """Returns (violations, total_count)."""
        conditions = [SLAViolation.company_id == company_id]

        if job_id:
            conditions.append(SLAViolation.job_id == job_id)
        if violation_type:
            conditions.append(SLAViolation.violation_type == violation_type)
        if resolved is not None:
            conditions.append(SLAViolation.resolved == resolved)

        total = (
            await self.db.execute(
                select(func.count(SLAViolation.id)).where(and_(*conditions))
            )
        ).scalar()

        result = await self.db.execute(
            select(SLAViolation)
            .where(and_(*conditions))
            .order_by(SLAViolation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        violations = list(result.scalars().all())
        return violations, total

    async def get_violations_for_company(
        self, company_id: uuid.UUID
    ) -> list[SLAViolation]:
        result = await self.db.execute(
            select(SLAViolation).where(SLAViolation.company_id == company_id)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Automations
    # ------------------------------------------------------------------

    async def list_automations(
        self,
        company_id: uuid.UUID,
        automation_type: str | None = None,
        trigger_event: str | None = None,
        is_enabled: bool | None = None,
    ) -> list[RecruitmentAutomation]:
        conditions = [RecruitmentAutomation.company_id == company_id]

        if automation_type:
            conditions.append(RecruitmentAutomation.automation_type == automation_type)
        if trigger_event:
            conditions.append(RecruitmentAutomation.trigger_event == trigger_event)
        if is_enabled is not None:
            conditions.append(RecruitmentAutomation.is_enabled == is_enabled)

        result = await self.db.execute(
            # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter
            select(RecruitmentAutomation).where(and_(*conditions))
        )
        return list(result.scalars().all())

    async def get_automation(
        self, automation_id: uuid.UUID
    ) -> RecruitmentAutomation | None:
        result = await self.db.execute(
            select(RecruitmentAutomation).where(
                RecruitmentAutomation.id == automation_id
            )
        )
        return result.scalar_one_or_none()

    async def get_automations_for_company(
        self, company_id: uuid.UUID
    ) -> list[RecruitmentAutomation]:
        result = await self.db.execute(
            select(RecruitmentAutomation).where(
                RecruitmentAutomation.company_id == company_id
            )
        )
        return list(result.scalars().all())

    async def create_automation(
        self, company_id: uuid.UUID, data: dict[str, Any]
    ) -> RecruitmentAutomation:
        automation = RecruitmentAutomation(company_id=company_id, **data)
        self.db.add(automation)
        await self.db.commit()
        await self.db.refresh(automation)
        return automation

    async def update_automation(
        self,
        automation: RecruitmentAutomation,
        update_data: dict[str, Any],
    ) -> RecruitmentAutomation:
        for field, value in update_data.items():
            setattr(automation, field, value)
        automation.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(automation)
        return automation

    async def delete_automation(self, automation: RecruitmentAutomation) -> None:
        await self.db.delete(automation)
        await self.db.commit()

    async def initialize_automations(self, company_id: uuid.UUID) -> list[str]:
        """
        Create default automations for a company.
        Callers should check get_automations_for_company first to avoid duplication.
        """
        names: list[str] = []
        for automation_data in DEFAULT_AUTOMATIONS:
            automation = RecruitmentAutomation(
                company_id=company_id, **automation_data
            )
            self.db.add(automation)
            names.append(automation_data["name"])
        await self.db.commit()
        return names
