"""PolicyEngineRepository — ORM helpers for policy_engine_service.

Per ADR-001: services do not run select(Model) inline.

Companion to policy_repository.py — keeps engine-runtime queries
(scoped by company + active) separate from the CRUD admin endpoints
already in PolicyRepository.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.policy import (
    BusinessRule,
    EscalationRule,
    RateLimitCounter,
    RateLimitRule,
)


class PolicyEngineRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # BusinessRule (engine runtime)
    # ------------------------------------------------------------------

    async def list_active_business_rules_for_company(
        self,
        company_uuid: Optional[UUID],
    ) -> list[BusinessRule]:
        company_clause = (
            or_(
                BusinessRule.company_id.is_(None),
                BusinessRule.company_id == company_uuid,
            )
            if company_uuid
            else BusinessRule.company_id.is_(None)
        )
        query = (
            select(BusinessRule)
            .where(and_(BusinessRule.is_active, company_clause))
            .order_by(BusinessRule.priority.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_business_rule_by_name(self, name: str) -> Optional[BusinessRule]:
        result = await self.db.execute(
            select(BusinessRule).where(BusinessRule.name == name)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # RateLimitRule (engine runtime)
    # ------------------------------------------------------------------

    async def list_active_rate_limit_rules(
        self,
        target_type: str,
        company_uuid: Optional[UUID],
    ) -> list[RateLimitRule]:
        company_clause = (
            or_(
                RateLimitRule.company_id.is_(None),
                RateLimitRule.company_id == company_uuid,
            )
            if company_uuid
            else RateLimitRule.company_id.is_(None)
        )
        query = select(RateLimitRule).where(
            and_(
                RateLimitRule.is_active,
                RateLimitRule.target_type == target_type,
                company_clause,
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_rate_limit_rule_by_name(self, name: str) -> Optional[RateLimitRule]:
        result = await self.db.execute(
            select(RateLimitRule).where(RateLimitRule.name == name)
        )
        return result.scalar_one_or_none()

    async def list_rate_limit_counters_in_window(
        self,
        rule_id: UUID,
        target_key: str,
        window_start: datetime,
    ) -> list[RateLimitCounter]:
        query = select(RateLimitCounter).where(
            and_(
                RateLimitCounter.rule_id == rule_id,
                RateLimitCounter.target_key == target_key,
                RateLimitCounter.window_start >= window_start,
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # EscalationRule (engine runtime)
    # ------------------------------------------------------------------

    async def get_active_escalation_rule_by_id(
        self, rule_id: UUID
    ) -> Optional[EscalationRule]:
        result = await self.db.execute(
            select(EscalationRule).where(
                and_(
                    EscalationRule.id == rule_id,
                    EscalationRule.is_active,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_escalation_rules_by_trigger(
        self,
        trigger_type: str,
        company_uuid: Optional[UUID],
    ) -> list[EscalationRule]:
        company_clause = (
            or_(
                EscalationRule.company_id.is_(None),
                EscalationRule.company_id == company_uuid,
            )
            if company_uuid
            else EscalationRule.company_id.is_(None)
        )
        query = (
            select(EscalationRule)
            .where(
                and_(
                    EscalationRule.trigger_type == trigger_type,
                    EscalationRule.is_active,
                    company_clause,
                )
            )
            .order_by(EscalationRule.priority.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_escalation_rule_by_name(self, name: str) -> Optional[EscalationRule]:
        result = await self.db.execute(
            select(EscalationRule).where(EscalationRule.name == name)
        )
        return result.scalar_one_or_none()
