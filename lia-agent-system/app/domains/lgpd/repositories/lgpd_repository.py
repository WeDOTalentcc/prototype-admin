"""
LGPD domain repository — all SQLAlchemy operations for lgpd_compliance.py.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import (
    AutomatedDecisionExplanation,
    BreachNotification,
    DPORegistry,
)


class LGPDRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # DPO Registry
    # ------------------------------------------------------------------

    async def get_dpo_by_company(self, company_id: uuid.UUID) -> DPORegistry | None:
        result = await self.db.execute(
            select(DPORegistry).where(DPORegistry.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def list_dpos(
        self,
        is_active: bool | None,
        limit: int,
        offset: int,
        company_id: uuid.UUID | None = None,
    ) -> tuple[list[DPORegistry], int]:
        """List DPO registry entries, optionally scoped to a tenant.

        Onda 4.2h-C5 (2026-05-24): company_id parameter pra evitar cross-tenant
        leak de DPO contact (name/email/phone — LGPD Art. 41 protected). Antes
        endpoint /dpo retornava DPOs de TODAS empresas. Marker TENANT-EXEMPT
        removido — agora é tenant-scoped por default (None só pra wedotalent_admin).
        """
        conditions = []
        if is_active is not None:
            conditions.append(DPORegistry.is_active == is_active)
        if company_id is not None:
            conditions.append(DPORegistry.company_id == company_id)

        query = select(DPORegistry)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(desc(DPORegistry.created_at)).limit(limit).offset(offset)

        result = await self.db.execute(query)
        dpos = list(result.scalars().all())

        count_query = select(func.count(DPORegistry.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return dpos, total

    async def upsert_dpo(self, company_id: uuid.UUID, data: dict) -> DPORegistry:
        """Create or update DPO entry; returns the persisted object."""
        existing = await self.get_dpo_by_company(company_id)
        if existing:
            existing.dpo_name = data["dpo_name"]
            existing.dpo_email = data["dpo_email"]
            existing.dpo_phone = data["dpo_phone"]
            existing.appointment_date = data["appointment_date"]
            existing.public_contact_url = data["public_contact_url"]
            existing.is_active = True
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        dpo = DPORegistry(
            company_id=company_id,
            dpo_name=data["dpo_name"],
            dpo_email=data["dpo_email"],
            dpo_phone=data["dpo_phone"],
            appointment_date=data["appointment_date"],
            public_contact_url=data["public_contact_url"],
            is_active=True,
        )
        self.db.add(dpo)
        await self.db.commit()
        await self.db.refresh(dpo)
        return dpo

    async def update_dpo(self, company_id: uuid.UUID, data: dict) -> DPORegistry | None:
        """Apply partial update to existing DPO; returns None if not found."""
        dpo = await self.get_dpo_by_company(company_id)
        if not dpo:
            return None

        if data.get("dpo_name") is not None:
            dpo.dpo_name = data["dpo_name"]
        if data.get("dpo_email") is not None:
            dpo.dpo_email = data["dpo_email"]
        if data.get("dpo_phone") is not None:
            dpo.dpo_phone = data["dpo_phone"]
        if data.get("is_active") is not None:
            dpo.is_active = data["is_active"]
        if data.get("public_contact_url") is not None:
            dpo.public_contact_url = data["public_contact_url"]

        await self.db.commit()
        await self.db.refresh(dpo)
        return dpo

    # ------------------------------------------------------------------
    # Breach Notifications
    # ------------------------------------------------------------------

    async def list_breaches(
        self,
        company_id: uuid.UUID,
        severity: str | None,
        status_filter: str | None,
        pending_anpd: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[BreachNotification], int]:
        conditions = [BreachNotification.company_id == company_id]

        if severity:
            conditions.append(BreachNotification.severity == severity)
        if status_filter:
            conditions.append(BreachNotification.status == status_filter)
        if pending_anpd is not None:
            conditions.append(BreachNotification.notification_sent_to_anpd == (not pending_anpd))

        # TENANT-EXEMPT: dynamic builder — conditions[0] is BreachNotification.company_id == company_id; sensor AST não traça
        query = (
            select(BreachNotification)
            .where(and_(*conditions))
            .order_by(desc(BreachNotification.breach_detected_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        breaches = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(BreachNotification.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return breaches, total

    async def get_breach_by_id(
        self, breach_id: uuid.UUID, company_id: uuid.UUID
    ) -> BreachNotification | None:
        result = await self.db.execute(
            select(BreachNotification).where(
                and_(
                    BreachNotification.id == breach_id,
                    BreachNotification.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_breach(self, company_id: uuid.UUID, data: dict) -> BreachNotification:
        breach = BreachNotification(
            company_id=company_id,
            breach_detected_at=data["breach_detected_at"],
            breach_description=data["breach_description"],
            affected_data_types=data["affected_data_types"],
            affected_count=data["affected_count"],
            severity=data["severity"],
            status="detected",
        )
        self.db.add(breach)
        await self.db.commit()
        await self.db.refresh(breach)
        return breach

    async def update_breach(
        self, breach_id: uuid.UUID, company_id: uuid.UUID, data: dict
    ) -> BreachNotification | None:
        breach = await self.get_breach_by_id(breach_id, company_id)
        if not breach:
            return None

        if data.get("breach_description") is not None:
            breach.breach_description = data["breach_description"]
        if data.get("affected_data_types") is not None:
            breach.affected_data_types = data["affected_data_types"]
        if data.get("affected_count") is not None:
            breach.affected_count = data["affected_count"]
        if data.get("severity") is not None:
            breach.severity = data["severity"]
        if data.get("remediation_actions") is not None:
            breach.remediation_actions = data["remediation_actions"]
        if data.get("status") is not None:
            breach.status = data["status"]
            if data["status"] == "resolved":
                breach.resolved_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(breach)
        return breach

    async def mark_breach_anpd_notified(
        self, breach_id: uuid.UUID, company_id: uuid.UUID
    ) -> BreachNotification | None:
        breach = await self.get_breach_by_id(breach_id, company_id)
        if not breach:
            return None

        breach.notification_sent_to_anpd = True
        breach.anpd_notification_at = datetime.utcnow()
        if breach.status == "detected":
            breach.status = "investigating"

        await self.db.commit()
        await self.db.refresh(breach)
        return breach

    async def mark_breach_subjects_notified(
        self, breach_id: uuid.UUID, company_id: uuid.UUID
    ) -> BreachNotification | None:
        breach = await self.get_breach_by_id(breach_id, company_id)
        if not breach:
            return None

        breach.notification_sent_to_subjects = True
        breach.subjects_notification_at = datetime.utcnow()
        if breach.notification_sent_to_anpd and breach.status in ["detected", "investigating"]:
            breach.status = "notified"

        await self.db.commit()
        await self.db.refresh(breach)
        return breach

    async def resolve_breach(
        self,
        breach_id: uuid.UUID,
        company_id: uuid.UUID,
        remediation_actions: str | None,
    ) -> BreachNotification | None:
        breach = await self.get_breach_by_id(breach_id, company_id)
        if not breach:
            return None

        if remediation_actions:
            breach.remediation_actions = remediation_actions
        breach.status = "resolved"
        breach.resolved_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(breach)
        return breach

    # ------------------------------------------------------------------
    # Automated Decision Explanations
    # ------------------------------------------------------------------

    async def list_decisions(
        self,
        company_id: uuid.UUID,
        decision_type: str | None,
        candidate_id: uuid.UUID | None,
        vacancy_id: uuid.UUID | None,
        pending_review: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[AutomatedDecisionExplanation], int]:
        conditions = [AutomatedDecisionExplanation.company_id == company_id]

        if decision_type:
            conditions.append(AutomatedDecisionExplanation.decision_type == decision_type)
        if candidate_id is not None:
            conditions.append(AutomatedDecisionExplanation.candidate_id == candidate_id)
        if vacancy_id is not None:
            conditions.append(AutomatedDecisionExplanation.vacancy_id == vacancy_id)
        if pending_review is not None:
            if pending_review:
                conditions.append(AutomatedDecisionExplanation.human_review_requested == True)
                conditions.append(AutomatedDecisionExplanation.human_review_completed_at == None)
            else:
                conditions.append(AutomatedDecisionExplanation.human_review_completed_at != None)

        # TENANT-EXEMPT: dynamic builder — conditions[0] is AutomatedDecisionExplanation.company_id == company_id (L268); sensor AST não traça
        query = (
            select(AutomatedDecisionExplanation)
            .where(and_(*conditions))
            .order_by(desc(AutomatedDecisionExplanation.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        decisions = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(AutomatedDecisionExplanation.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return decisions, total

    async def get_decision_by_id(
        self, decision_id: uuid.UUID, company_id: uuid.UUID
    ) -> AutomatedDecisionExplanation | None:
        result = await self.db.execute(
            select(AutomatedDecisionExplanation).where(
                and_(
                    AutomatedDecisionExplanation.id == decision_id,
                    AutomatedDecisionExplanation.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_decision(
        self, company_id: uuid.UUID, data: dict
    ) -> AutomatedDecisionExplanation:
        decision = AutomatedDecisionExplanation(
            company_id=company_id,
            decision_type=data["decision_type"],
            candidate_id=data.get("candidate_id"),
            vacancy_id=data.get("vacancy_id"),
            ai_model_used=data.get("ai_model_used"),
            input_criteria=data.get("input_criteria"),
            decision_criteria=data.get("decision_criteria"),
            explanation_text=data.get("explanation_text"),
        )
        self.db.add(decision)
        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    async def request_human_review(
        self, decision_id: uuid.UUID, company_id: uuid.UUID
    ) -> AutomatedDecisionExplanation | None:
        decision = await self.get_decision_by_id(decision_id, company_id)
        if not decision:
            return None

        decision.human_review_requested = True
        decision.explanation_requested_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    async def complete_human_review(
        self,
        decision_id: uuid.UUID,
        company_id: uuid.UUID,
        review_decision: str,
        reviewer_id: uuid.UUID,
    ) -> AutomatedDecisionExplanation | None:
        decision = await self.get_decision_by_id(decision_id, company_id)
        if not decision:
            return None

        decision.human_review_decision = review_decision
        decision.human_reviewer_id = reviewer_id
        decision.human_review_completed_at = datetime.utcnow()
        decision.explanation_provided_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    # ------------------------------------------------------------------
    # Stats (aggregate queries)
    # ------------------------------------------------------------------

    async def get_compliance_stats(self, company_id: uuid.UUID) -> dict:
        dpo = await self.get_dpo_by_company(company_id)

        breach_total = (
            await self.db.execute(
                select(func.count(BreachNotification.id)).where(
                    BreachNotification.company_id == company_id
                )
            )
        ).scalar() or 0

        open_breaches = (
            await self.db.execute(
                select(func.count(BreachNotification.id)).where(
                    and_(
                        BreachNotification.company_id == company_id,
                        BreachNotification.status != "resolved",
                    )
                )
            )
        ).scalar() or 0

        breaches_pending_anpd = (
            await self.db.execute(
                select(func.count(BreachNotification.id)).where(
                    and_(
                        BreachNotification.company_id == company_id,
                        BreachNotification.notification_sent_to_anpd == False,
                        BreachNotification.status != "resolved",
                    )
                )
            )
        ).scalar() or 0

        total_decisions = (
            await self.db.execute(
                select(func.count(AutomatedDecisionExplanation.id)).where(
                    AutomatedDecisionExplanation.company_id == company_id
                )
            )
        ).scalar() or 0

        pending_reviews = (
            await self.db.execute(
                select(func.count(AutomatedDecisionExplanation.id)).where(
                    and_(
                        AutomatedDecisionExplanation.company_id == company_id,
                        AutomatedDecisionExplanation.human_review_requested == True,
                        AutomatedDecisionExplanation.human_review_completed_at == None,
                    )
                )
            )
        ).scalar() or 0

        completed_reviews = (
            await self.db.execute(
                select(func.count(AutomatedDecisionExplanation.id)).where(
                    and_(
                        AutomatedDecisionExplanation.company_id == company_id,
                        AutomatedDecisionExplanation.human_review_completed_at != None,
                    )
                )
            )
        ).scalar() or 0

        return {
            "dpo": dpo,
            "total_breaches": breach_total,
            "open_breaches": open_breaches,
            "breaches_pending_anpd": breaches_pending_anpd,
            "total_decisions": total_decisions,
            "pending_reviews": pending_reviews,
            "completed_reviews": completed_reviews,
        }
