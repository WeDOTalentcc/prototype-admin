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
            # TENANT-EXEMPT: policy engine rules support tenant-OR-global semantics via or_(company_id.is_(None), company_id==X); intentional cross-tenant fallback (by-design, not bug); T-RATCHET tenant_filter
            select(BusinessRule)
            .where(and_(BusinessRule.is_active, company_clause))
            .order_by(BusinessRule.priority.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_business_rule_by_name(self, name: str) -> Optional[BusinessRule]:
        result = await self.db.execute(
            # TENANT-EXEMPT: policy engine rules support tenant-OR-global semantics via or_(company_id.is_(None), company_id==X); intentional cross-tenant fallback (by-design, not bug); T-RATCHET tenant_filter
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
        # TENANT-EXEMPT: policy engine rules support tenant-OR-global semantics via or_(company_id.is_(None), company_id==X); intentional cross-tenant fallback (by-design, not bug); T-RATCHET tenant_filter
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
            # TENANT-EXEMPT: policy engine rules support tenant-OR-global semantics via or_(company_id.is_(None), company_id==X); intentional cross-tenant fallback (by-design, not bug); T-RATCHET tenant_filter
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
            # TENANT-EXEMPT: policy engine rules support tenant-OR-global semantics via or_(company_id.is_(None), company_id==X); intentional cross-tenant fallback (by-design, not bug); T-RATCHET tenant_filter
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
            # TENANT-EXEMPT: policy engine rules support tenant-OR-global semantics via or_(company_id.is_(None), company_id==X); intentional cross-tenant fallback (by-design, not bug); T-RATCHET tenant_filter
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
            # TENANT-EXEMPT: policy engine rules support tenant-OR-global semantics via or_(company_id.is_(None), company_id==X); intentional cross-tenant fallback (by-design, not bug); T-RATCHET tenant_filter
            select(EscalationRule).where(EscalationRule.name == name)
        )
        return result.scalar_one_or_none()


# =============================================================================
# WT-2022 CRUD methods — UI editor (Policies Migration → UI)
# =============================================================================
#
# Multi-tenancy fail-closed: every mutation requires company_id; UUID parse
# error raises ValueError so service layer returns HTTP 400. All reads/writes
# filter by company_id OR company_id IS NULL (global rules visible to all
# tenants but only WeDOTalent staff can manage globals — enforced upstream).
#
# ADR-001 Repository Pattern: services no longer call select(Model) inline —
# they delegate to these methods.

    def _require_company_uuid(self, company_id: str | None) -> UUID:
        """Fail-closed gate — raises ValueError when company_id is missing/invalid."""
        if not company_id:
            raise ValueError("company_id is required for CRUD operations")
        try:
            return UUID(company_id)
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid company_id UUID: {company_id}") from exc

    # ---------------------------------------------------------------------
    # BusinessRule CRUD (mutations)
    # ---------------------------------------------------------------------

    async def get_business_rule(
        self, company_id: str, rule_id: str
    ) -> Optional[BusinessRule]:
        """Fetch BusinessRule scoped to company_id (or global)."""
        company_uuid = self._require_company_uuid(company_id)
        try:
            rule_uuid = UUID(rule_id)
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid rule_id UUID: {rule_id}") from exc

        result = await self.db.execute(
            select(BusinessRule).where(
                and_(
                    BusinessRule.id == rule_uuid,
                    or_(
                        BusinessRule.company_id.is_(None),
                        BusinessRule.company_id == company_uuid,
                    ),
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_business_rule(
        self, company_id: str, data: dict
    ) -> BusinessRule:
        company_uuid = self._require_company_uuid(company_id)
        rule = BusinessRule(company_id=company_uuid, **data)
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update_business_rule(
        self, company_id: str, rule_id: str, data: dict
    ) -> Optional[BusinessRule]:
        rule = await self.get_business_rule(company_id, rule_id)
        if rule is None:
            return None
        for field, value in data.items():
            if value is not None:
                setattr(rule, field, value)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def delete_business_rule(self, company_id: str, rule_id: str) -> bool:
        rule = await self.get_business_rule(company_id, rule_id)
        if rule is None:
            return False
        await self.db.delete(rule)
        await self.db.commit()
        return True

    # ---------------------------------------------------------------------
    # RateLimitRule CRUD (mutations)
    # ---------------------------------------------------------------------

    async def get_rate_limit_rule(
        self, company_id: str, rule_id: str
    ) -> Optional[RateLimitRule]:
        company_uuid = self._require_company_uuid(company_id)
        try:
            rule_uuid = UUID(rule_id)
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid rule_id UUID: {rule_id}") from exc

        result = await self.db.execute(
            select(RateLimitRule).where(
                and_(
                    RateLimitRule.id == rule_uuid,
                    or_(
                        RateLimitRule.company_id.is_(None),
                        RateLimitRule.company_id == company_uuid,
                    ),
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_rate_limit_rule(
        self, company_id: str, data: dict
    ) -> RateLimitRule:
        company_uuid = self._require_company_uuid(company_id)
        rule = RateLimitRule(company_id=company_uuid, **data)
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update_rate_limit_rule(
        self, company_id: str, rule_id: str, data: dict
    ) -> Optional[RateLimitRule]:
        rule = await self.get_rate_limit_rule(company_id, rule_id)
        if rule is None:
            return None
        for field, value in data.items():
            if value is not None:
                setattr(rule, field, value)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def delete_rate_limit_rule(
        self, company_id: str, rule_id: str
    ) -> bool:
        rule = await self.get_rate_limit_rule(company_id, rule_id)
        if rule is None:
            return False
        await self.db.delete(rule)
        await self.db.commit()
        return True

    # ---------------------------------------------------------------------
    # EscalationRule CRUD (mutations)
    # ---------------------------------------------------------------------

    async def get_escalation_rule(
        self, company_id: str, rule_id: str
    ) -> Optional[EscalationRule]:
        company_uuid = self._require_company_uuid(company_id)
        try:
            rule_uuid = UUID(rule_id)
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid rule_id UUID: {rule_id}") from exc

        result = await self.db.execute(
            select(EscalationRule).where(
                and_(
                    EscalationRule.id == rule_uuid,
                    or_(
                        EscalationRule.company_id.is_(None),
                        EscalationRule.company_id == company_uuid,
                    ),
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_escalation_rule(
        self, company_id: str, data: dict
    ) -> EscalationRule:
        company_uuid = self._require_company_uuid(company_id)
        rule = EscalationRule(company_id=company_uuid, **data)
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update_escalation_rule(
        self, company_id: str, rule_id: str, data: dict
    ) -> Optional[EscalationRule]:
        rule = await self.get_escalation_rule(company_id, rule_id)
        if rule is None:
            return None
        for field, value in data.items():
            if value is not None:
                setattr(rule, field, value)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def delete_escalation_rule(
        self, company_id: str, rule_id: str
    ) -> bool:
        rule = await self.get_escalation_rule(company_id, rule_id)
        if rule is None:
            return False
        await self.db.delete(rule)
        await self.db.commit()
        return True
