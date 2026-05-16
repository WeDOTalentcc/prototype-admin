"""
OfferService — state machine + business logic for offer proposals.
"""
import logging
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.offer_proposal import OfferProposal

from app.domains.offer.repositories.offer_repository import OfferRepository
from app.schemas.offer import OfferDraftCreate, OfferDraftUpdate
from app.shared.compliance.audit_service import AuditService  # T-1157

logger = logging.getLogger(__name__)

_WORKING_DAYS_BUFFER = 30
_DEFAULT_VALIDITY_DAYS = 7


def compute_default_start_date() -> date:
    """Return today + 30 calendar days as default start date."""
    return (datetime.utcnow() + timedelta(days=_WORKING_DAYS_BUFFER)).date()


def compute_expires_at(validity_days: int) -> datetime:
    return datetime.utcnow() + timedelta(days=validity_days)


def prefill_from_snapshots(
    job_snapshot: dict[str, Any],
    candidate_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute pre-fill values for offer fields from job + candidate snapshots.
    Returns partial dict for offer fields (caller merges).
    """
    fields: dict[str, Any] = {}

    # Salary: mid-point of job salary range
    salary_range = job_snapshot.get("salary_range") or {}
    min_sal = salary_range.get("min")
    max_sal = salary_range.get("max")
    if min_sal and max_sal:
        try:
            fields["offered_salary"] = Decimal(str((float(min_sal) + float(max_sal)) / 2))
        except Exception:
            pass
    elif candidate_snapshot.get("desired_salary_min"):
        try:
            fields["offered_salary"] = Decimal(str(candidate_snapshot["desired_salary_min"]))
        except Exception:
            pass

    # INT:004 — hydrate offered_benefits: prefer structured data from linked compensation policy,
    # then fall back to job_snapshot benefits (already set by wizard or manual edit).
    # compensation_policy is pre-loaded by OfferService._enrich_job_snapshot_compensation()
    # and merged into job_snapshot before this function is called.
    _comp_policy = job_snapshot.get("compensation_policy") or {}
    _policy_benefits_pkg = _comp_policy.get("benefits_package") or {}
    _policy_benefit_names: list[str] = _policy_benefits_pkg.get("included", []) if isinstance(_policy_benefits_pkg, dict) else []

    if job_snapshot.get("benefits"):
        benefits = job_snapshot["benefits"]
        if isinstance(benefits, list):
            fields["offered_benefits"] = [
                {"name": b} if isinstance(b, str) else b for b in benefits
            ]
            # Merge in any policy benefits not already listed (no duplicates)
            existing_names = {
                (b if isinstance(b, str) else b.get("name", "")).lower()
                for b in benefits
            }
            for pname in _policy_benefit_names:
                if pname.lower() not in existing_names:
                    fields["offered_benefits"].append({"name": pname, "source": "compensation_policy"})
    elif _policy_benefit_names:
        # No job benefits yet — inherit from policy
        fields["offered_benefits"] = [
            {"name": n, "source": "compensation_policy"} for n in _policy_benefit_names
        ]

    # Expose compensation_policy summary in offer fields for FE display
    if _comp_policy.get("id"):
        fields["compensation_policy_snapshot"] = {
            "id": _comp_policy["id"],
            "name": _comp_policy.get("name", ""),
            "variable_compensation": _comp_policy.get("variable_compensation", {}),
        }

    # Currency from salary_range
    fields["offered_salary_currency"] = salary_range.get("currency", "BRL")

    # Start date
    fields["offered_start_date"] = compute_default_start_date()

    return fields


def check_salary_warnings(
    offered_salary: Decimal | None,
    job_snapshot: dict[str, Any],
) -> list[dict[str, str]]:
    """Return list of warning dicts {level, message} for FE display."""
    warnings = []
    if offered_salary is None:
        return warnings
    salary_range = job_snapshot.get("salary_range") or {}
    min_sal = salary_range.get("min")
    max_sal = salary_range.get("max")
    if max_sal:
        try:
            if float(offered_salary) > float(max_sal) * 1.1:
                warnings.append({
                    "level": "warning",
                    "message": f"Salario acima de 110% do maximo da faixa (R$ {max_sal:,.2f})",
                })
        except Exception:
            pass
    if min_sal:
        try:
            if float(offered_salary) < float(min_sal):
                warnings.append({
                    "level": "info",
                    "message": f"Salario abaixo do minimo da faixa (R$ {min_sal:,.2f})",
                })
        except Exception:
            pass
    return warnings


class OfferService:

    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = OfferRepository(db)

    async def _enrich_job_snapshot_compensation(self, job_snapshot: dict[str, Any]) -> None:
        """Load CompensationPolicy linked to job and merge structured data into job_snapshot.

        Mutates job_snapshot in-place. No-op if no compensation_policy_id or policy not found.
        Fail-open: any DB error is logged and silently ignored.
        """
        policy_id = job_snapshot.get("compensation_policy_id")
        if not policy_id:
            return
        try:
            from lia_models.compensation_policy import CompensationPolicy
            from sqlalchemy import select as _select
            result = await self._db.execute(
                _select(CompensationPolicy).where(CompensationPolicy.id == policy_id)
            )
            policy = result.scalar_one_or_none()
            if policy:
                job_snapshot["compensation_policy"] = {
                    "id": str(policy.id),
                    "name": policy.name,
                    "policy_type": policy.policy_type,
                    "variable_compensation": policy.variable_compensation or {},
                    "salary_bands": policy.salary_bands or [],
                    "benefits_package": policy.benefits_package or {},
                }
                logger.info(
                    "[offer] compensation_policy %s (%s) merged into job_snapshot",
                    policy.id, policy.name,
                )
        except Exception as exc:
            logger.warning(
                "[offer] Could not load compensation_policy %s: %s", policy_id, exc
            )

    async def create_or_get_draft(
        self,
        data: OfferDraftCreate,
        company_id: str,
        user_id: str,
        job_snapshot: dict[str, Any],
        candidate_snapshot: dict[str, Any],
    ) -> OfferProposal:
        # Idempotent: return existing draft if present
        existing = await self._repo.get_active_draft(
            company_id, data.candidate_id, data.job_id
        )
        if existing:
            return existing

        # INT:004 — load PRV policy before prefill so prefill_from_snapshots can hydrate benefits
        await self._enrich_job_snapshot_compensation(job_snapshot)
        prefill = prefill_from_snapshots(job_snapshot, candidate_snapshot)
        validity = _DEFAULT_VALIDITY_DAYS

        proposal = OfferProposal(
            company_id=company_id,
            candidate_id=data.candidate_id,
            job_id=data.job_id,
            template_id=data.template_id,
            job_data_snapshot=job_snapshot,
            candidate_data_snapshot=candidate_snapshot,
            validity_days=validity,
            expires_at=compute_expires_at(validity),
            created_by_user_id=user_id,
            **prefill,
        )
        return await self._repo.create(proposal)

    async def update_draft(
        self,
        offer_id: UUID,
        company_id: str,
        updates: OfferDraftUpdate,
    ) -> OfferProposal | None:
        proposal = await self._repo.get_by_id(offer_id, company_id)
        if not proposal:
            return None
        if proposal.status != "draft":
            raise ValueError(f"Cannot update proposal in status '{proposal.status}'")

        data = updates.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(proposal, field, value)

        if "validity_days" in data:
            proposal.expires_at = compute_expires_at(proposal.validity_days)

        return await self._repo.update(proposal)

    async def cancel_draft(
        self,
        offer_id: UUID,
        company_id: str,
        user_id: str,
        reason: str | None = None,
    ) -> OfferProposal | None:
        proposal = await self._repo.get_by_id(offer_id, company_id)
        if not proposal:
            return None
        if proposal.status not in ("draft",):
            raise ValueError(f"Cannot cancel proposal in status '{proposal.status}'")
        proposal.status = "cancelled"
        proposal.cancelled_at = datetime.utcnow()
        proposal.cancelled_by_user_id = user_id
        if reason:
            proposal.recruiter_notes = (proposal.recruiter_notes or "") + f"\n[cancelled: {reason}]"
        updated = await self._repo.update(proposal)
        # T-1157 audit (SOX retention; mutation em offer_proposal)
        try:
            await AuditService().log_decision_in_session(
                session=self._db,
                company_id=company_id,
                agent_name="offer_service",
                decision_type="approve_hiring",
                action="cancel_offer_draft",
                decision="cancelled",
                reasoning=[reason or "no reason provided"],
                criteria_used=["offer_status_transition"],
                candidate_id=str(proposal.candidate_id) if proposal.candidate_id else None,
                job_vacancy_id=str(proposal.job_id) if proposal.job_id else None,
            )
        except Exception as audit_err:
            logger.warning(f"[T-1157] offer cancel audit failed: {audit_err}")
        return updated

    async def get_draft(
        self, offer_id: UUID, company_id: str
    ) -> OfferProposal | None:
        return await self._repo.get_by_id(offer_id, company_id)

    async def mark_sent(
        self,
        offer_id: UUID,
        company_id: str,
        user_id: str,
        send_mode: str,
        email_log_id: UUID | None = None,
    ) -> OfferProposal | None:
        proposal = await self._repo.get_by_id(offer_id, company_id)
        if not proposal:
            return None
        if proposal.status != "draft":
            raise ValueError(f"Cannot send proposal in status '{proposal.status}'")
        proposal.status = "sent"
        proposal.send_mode = send_mode
        proposal.sent_by_user_id = user_id
        proposal.sent_at = datetime.utcnow()
        proposal.email_log_id = email_log_id
        updated = await self._repo.update(proposal)
        # T-1157 audit (SOX retention; offer enviada formalmente ao candidato)
        try:
            await AuditService().log_decision_in_session(
                session=self._db,
                company_id=company_id,
                agent_name="offer_service",
                decision_type="approve_hiring",
                action="mark_offer_sent",
                decision="sent",
                reasoning=[f"send_mode={send_mode}"],
                criteria_used=["offer_status_transition", "send_mode"],
                candidate_id=str(proposal.candidate_id) if proposal.candidate_id else None,
                job_vacancy_id=str(proposal.job_id) if proposal.job_id else None,
            )
        except Exception as audit_err:
            logger.warning(f"[T-1157] offer mark_sent audit failed: {audit_err}")
        return updated

    def render_offer_template_variables(
        self, proposal: OfferProposal
    ) -> dict[str, str]:
        """Build variable map for email template interpolation."""
        job = proposal.job_data_snapshot or {}
        candidate = proposal.candidate_data_snapshot or {}
        salary = proposal.offered_salary
        currency = proposal.offered_salary_currency or "BRL"
        return {
            "candidate_name": candidate.get("name", ""),
            "candidate_email": candidate.get("email", ""),
            "job_title": job.get("title", ""),
            "department": job.get("department", ""),
            "manager_name": job.get("manager", ""),
            "company_name": job.get("company_name", "WeDOTalent"),
            "offered_salary_formatted": (
                f"{currency} {float(salary):,.2f}" if salary else ""
            ),
            "offered_start_date": (
                str(proposal.offered_start_date) if proposal.offered_start_date else ""
            ),
            "validity_days": str(proposal.validity_days or _DEFAULT_VALIDITY_DAYS),
            "bonus_admission": (
                f"{currency} {float(proposal.offered_bonus_admission):,.2f}"
                if proposal.offered_bonus_admission
                else ""
            ),
            "contract_type": job.get("contract_type", ""),
            "work_model": job.get("work_model", ""),
        }
