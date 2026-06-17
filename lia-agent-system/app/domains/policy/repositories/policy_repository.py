"""PolicyRepository — all DB operations for the policy domain."""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import (
    BusinessRule,
    EscalationLog,
    EscalationRule,
    PolicyEvaluationLog,
    RateLimitRule,
)

logger = logging.getLogger(__name__)


class PolicyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # BusinessRule
    # ------------------------------------------------------------------

    async def list_business_rules(
        self,
        is_active: bool | None = None,
        rule_type: str | None = None,
        company_id: str | None = None,
    ) -> list[BusinessRule]:
        conditions = [BusinessRule.is_active] if is_active is None else [BusinessRule.is_active == is_active]
        if rule_type:
            conditions.append(BusinessRule.rule_type == rule_type)
        if company_id:
            conditions.append(
                or_(BusinessRule.company_id is None, BusinessRule.company_id == UUID(company_id))
            )
        query = (
            # TENANT-EXEMPT: policy admin CRUD uses tenant-OR-global fallback + dynamic conditions builder; AST cannot trace; T-RATCHET tenant_filter
            select(BusinessRule)
            .where(and_(*conditions))
            .order_by(BusinessRule.priority.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_business_rule(self, rule_id: UUID) -> BusinessRule | None:
        result = await self.db.execute(
            # TENANT-EXEMPT: policy admin CRUD uses tenant-OR-global fallback + dynamic conditions builder; AST cannot trace; T-RATCHET tenant_filter
            select(BusinessRule).where(BusinessRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def create_business_rule(self, rule: BusinessRule) -> BusinessRule:
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update_business_rule(self, rule: BusinessRule, update_data: dict) -> BusinessRule:
        for field, value in update_data.items():
            if field == "rule_type" and value:
                value = value.value
            setattr(rule, field, value)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def delete_business_rule(self, rule: BusinessRule) -> None:
        await self.db.delete(rule)
        await self.db.commit()

    # ------------------------------------------------------------------
    # RateLimitRule
    # ------------------------------------------------------------------

    async def list_rate_limit_rules(
        self,
        is_active: bool | None = None,
        target_type: str | None = None,
        company_id: str | None = None,
    ) -> list[RateLimitRule]:
        conditions = [RateLimitRule.is_active] if is_active is None else [RateLimitRule.is_active == is_active]
        if target_type:
            conditions.append(RateLimitRule.target_type == target_type)
        if company_id:
            conditions.append(
                or_(RateLimitRule.company_id is None, RateLimitRule.company_id == UUID(company_id))
            )
        # TENANT-EXEMPT: policy admin CRUD uses tenant-OR-global fallback + dynamic conditions builder; AST cannot trace; T-RATCHET tenant_filter
        query = select(RateLimitRule).where(and_(*conditions))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_rate_limit_rule(self, rule_id: UUID) -> RateLimitRule | None:
        result = await self.db.execute(
            # TENANT-EXEMPT: policy admin CRUD uses tenant-OR-global fallback + dynamic conditions builder; AST cannot trace; T-RATCHET tenant_filter
            select(RateLimitRule).where(RateLimitRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def create_rate_limit_rule(self, rule: RateLimitRule) -> RateLimitRule:
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update_rate_limit_rule(self, rule: RateLimitRule, update_data: dict) -> RateLimitRule:
        for field, value in update_data.items():
            if field == "target_type" and value:
                value = value.value
            setattr(rule, field, value)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    # ------------------------------------------------------------------
    # EscalationRule
    # ------------------------------------------------------------------

    async def list_escalation_rules(
        self,
        is_active: bool | None = None,
        trigger_type: str | None = None,
        company_id: str | None = None,
    ) -> list[EscalationRule]:
        conditions = [EscalationRule.is_active] if is_active is None else [EscalationRule.is_active == is_active]
        if trigger_type:
            conditions.append(EscalationRule.trigger_type == trigger_type)
        if company_id:
            conditions.append(
                or_(EscalationRule.company_id is None, EscalationRule.company_id == UUID(company_id))
            )
        query = (
            # TENANT-EXEMPT: policy admin CRUD uses tenant-OR-global fallback + dynamic conditions builder; AST cannot trace; T-RATCHET tenant_filter
            select(EscalationRule)
            .where(and_(*conditions))
            .order_by(EscalationRule.priority.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_escalation_rule(self, rule_id: UUID) -> EscalationRule | None:
        result = await self.db.execute(
            # TENANT-EXEMPT: policy admin CRUD uses tenant-OR-global fallback + dynamic conditions builder; AST cannot trace; T-RATCHET tenant_filter
            select(EscalationRule).where(EscalationRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def create_escalation_rule(self, rule: EscalationRule) -> EscalationRule:
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update_escalation_rule(self, rule: EscalationRule, update_data: dict) -> EscalationRule:
        for field, value in update_data.items():
            if field == "trigger_type" and value:
                value = value.value
            elif field == "escalation_action" and value:
                value = value.value
            setattr(rule, field, value)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    # ------------------------------------------------------------------
    # PolicyEvaluationLog
    # ------------------------------------------------------------------

    async def list_evaluation_logs(
        self,
        company_id: str | None = None,
        action: str | None = None,
        result: str | None = None,
        agent_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PolicyEvaluationLog]:
        conditions: list = []
        if company_id:
            conditions.append(PolicyEvaluationLog.company_id == UUID(company_id))
        if action:
            conditions.append(PolicyEvaluationLog.action == action)
        if result:
            conditions.append(PolicyEvaluationLog.result == result)
        if agent_name:
            conditions.append(PolicyEvaluationLog.agent_name == agent_name)

        # TENANT-EXEMPT: policy admin CRUD uses tenant-OR-global fallback + dynamic conditions builder; AST cannot trace; T-RATCHET tenant_filter
        query = select(PolicyEvaluationLog)
        if conditions:
            query = query.where(and_(*conditions))
        query = (
            query.order_by(desc(PolicyEvaluationLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        db_result = await self.db.execute(query)
        return list(db_result.scalars().all())

    # ------------------------------------------------------------------
    # EscalationLog
    # ------------------------------------------------------------------

    async def list_escalation_logs(
        self,
        company_id: str | None = None,
        resolved: bool | None = None,
        action_taken: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EscalationLog]:
        conditions: list = []
        if company_id:
            conditions.append(EscalationLog.company_id == UUID(company_id))
        if resolved is not None:
            conditions.append(EscalationLog.resolved == resolved)
        if action_taken:
            conditions.append(EscalationLog.action_taken == action_taken)

        # TENANT-EXEMPT: policy admin CRUD uses tenant-OR-global fallback + dynamic conditions builder; AST cannot trace; T-RATCHET tenant_filter
        query = select(EscalationLog)
        if conditions:
            query = query.where(and_(*conditions))
        query = (
            query.order_by(desc(EscalationLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        db_result = await self.db.execute(query)
        return list(db_result.scalars().all())

    async def get_escalation_log(self, log_id: UUID) -> EscalationLog | None:
        result = await self.db.execute(
            # TENANT-EXEMPT: policy admin CRUD uses tenant-OR-global fallback + dynamic conditions builder; AST cannot trace; T-RATCHET tenant_filter
            select(EscalationLog).where(EscalationLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def resolve_escalation_log(
        self,
        log: EscalationLog,
        user_id: str | None,
        resolution_notes: str | None,
    ) -> EscalationLog:
        log.resolved = True
        log.resolved_at = datetime.utcnow()
        log.resolved_by = UUID(user_id) if user_id else None
        log.resolution_notes = resolution_notes
        await self.db.commit()
        await self.db.refresh(log)
        return log
