"""
AutomationRule Repository — data access layer for stage_automation_rules.
Extracted from app/api/v1/automation_rules.py as part of Phase 2 refactor.

WT-2022 P3.2 (2026-05-21): DEPRECATED — esta tabela é UI-legacy. Engine real
(`stage_automation_engine.py:198`) lê `communication_automations`. Adapter
`StageRuleAdapter` (em `app/domains/automation/services/stage_rule_adapter.py`)
faz dual-write entre os dois stores. Não criar novos consumers desta tabela
sem coordenar com o engine canonical.

Para novas features de automation, usar:
    from app.domains.automation.repositories.communication_automation_repository
        import CommunicationAutomationRepository
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import DEFAULT_STAGE_AUTOMATION_RULES, StageAutomationRule

logger = logging.getLogger(__name__)


class AutomationRuleRepository:
    """Data access para `stage_automation_rules` (UI legacy).

    WT-2022 P3.2 deprecated: dual-write canonical acontece no endpoint
    (`automation_rules.py`) via `StageRuleAdapter`. Este repo permanece
    sem mudança funcional para preservar contrato com UI legacy.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        is_active: bool | None = None,
        trigger_type: str | None = None,
    ) -> list[StageAutomationRule]:
        query = select(StageAutomationRule).where(
            StageAutomationRule.company_id == company_id
        )
        if is_active is not None:
            query = query.where(StageAutomationRule.is_active == is_active)
        if trigger_type:
            query = query.where(StageAutomationRule.trigger_type == trigger_type)
        query = query.order_by(StageAutomationRule.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, rule_id: str, company_id: str) -> StageAutomationRule | None:
        result = await self.db.execute(
            select(StageAutomationRule).where(
                StageAutomationRule.id == rule_id,
                StageAutomationRule.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, company_id: str, data: dict) -> StageAutomationRule:
        rule = StageAutomationRule(company_id=company_id, **data)
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def update(self, rule: StageAutomationRule, data: dict) -> StageAutomationRule:
        for key, value in data.items():
            setattr(rule, key, value)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def delete(self, rule: StageAutomationRule) -> None:
        await self.db.delete(rule)

    async def toggle(self, rule: StageAutomationRule) -> StageAutomationRule:
        rule.is_active = not rule.is_active
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def seed_defaults(self, company_id: str) -> list[str]:
        """Seed default rules; return list of created trigger_types."""
        created = []
        for rdata in DEFAULT_STAGE_AUTOMATION_RULES:
            rule = StageAutomationRule(
                company_id=company_id,
                trigger_type=rdata["trigger_type"],
                name=rdata.get("name"),
                auto_execute=rdata.get("auto_execute", False),
                is_active=True,
                conditions=rdata.get("conditions", {}),
                actions=rdata.get("actions", []),
                priority=rdata.get("priority", "normal"),
                confidence_threshold="0.8",
            )
            self.db.add(rule)
            created.append(rdata["trigger_type"])
        return created
