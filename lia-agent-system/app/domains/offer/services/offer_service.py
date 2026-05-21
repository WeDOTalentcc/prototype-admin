"""
OfferService — state machine + business logic for offer proposals.

Sprint F.4 #42 canonical-remap (2026-05-20):
- All OfferProposal attribute access uses canonical column names
  (job_vacancy_id, salary, currency, bonus_pct, bonus_target, benefits,
  start_date, response_deadline, custom_clauses, sent_via, created_by,
  decline_reason, template_version).
- Wire-level names (offered_salary, validity_days, recruiter_notes, expires_at,
  send_mode, email_log_id, sent_by_user_id) are NO LONGER columns; they are
  derived/translated for FE compat at the service boundary.
"""
import logging
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


def compute_response_deadline(validity_days: int) -> datetime:
    """Sprint F.4 #42 canonical-remap: canonical column is ``response_deadline``
    (absolute DateTime), not ``expires_at``/``validity_days``."""
    return datetime.utcnow() + timedelta(days=validity_days)


# Legacy alias for callers expecting the old name (back-compat shim).
compute_expires_at = compute_response_deadline


def _recruiter_notes_from_custom_clauses(custom_clauses: list[dict] | None) -> str:
    """Sprint F.4 #42: read free-form recruiter_notes back out of canonical
    custom_clauses JSONB structure."""
    if not custom_clauses:
        return ""
    return next(
        (
            c.get("content", "")
            for c in custom_clauses
            if isinstance(c, dict) and c.get("clause_type") == "recruiter_notes"
        ),
        "",
    )


def _set_recruiter_notes_in_custom_clauses(
    proposal: OfferProposal, content: str
) -> None:
    """Sprint F.4 #42: write/replace recruiter_notes clause in custom_clauses JSONB."""
    clauses = list(proposal.custom_clauses or [])
    # Drop any existing recruiter_notes clause
    clauses = [
        c for c in clauses
        if not (isinstance(c, dict) and c.get("clause_type") == "recruiter_notes")
    ]
    if content:
        clauses.append({"clause_type": "recruiter_notes", "content": content})
    proposal.custom_clauses = clauses


def _email_log_id_from_sent_via(sent_via: list[dict] | None) -> UUID | None:
    """Sprint F.4 #42: extract email log id from canonical sent_via JSONB."""
    if not sent_via:
        return None
    for item in sent_via:
        if isinstance(item, dict) and item.get("channel") == "email":
            log_id = item.get("log_id")
            if log_id:
                try:
                    return UUID(str(log_id))
                except (TypeError, ValueError):
                    return None
    return None


def _validity_days_from_deadline(
    proposal: OfferProposal, default: int = _DEFAULT_VALIDITY_DAYS
) -> int:
    """Sprint F.4 #42: derive synthetic validity_days from canonical
    response_deadline (DateTime). Fallback to default if missing."""
    if proposal.response_deadline and proposal.created_at:
        try:
            delta = proposal.response_deadline - proposal.created_at
            return max(int(delta.days), 1)
        except Exception:
            pass
    return default


def prefill_from_snapshots(
    job_snapshot: dict[str, Any],
    candidate_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute pre-fill values for offer fields from job + candidate snapshots.
    Returns partial dict for offer fields (caller merges).

    Sprint F.4 #42 canonical-remap: keys are canonical column names.
    """
    fields: dict[str, Any] = {}

    # Salary: mid-point of job salary range
    salary_range = job_snapshot.get("salary_range") or {}
    min_sal = salary_range.get("min")
    max_sal = salary_range.get("max")
    if min_sal and max_sal:
        try:
            fields["salary"] = Decimal(str((float(min_sal) + float(max_sal)) / 2))
        except Exception:
            pass
    elif candidate_snapshot.get("desired_salary_min"):
        try:
            fields["salary"] = Decimal(str(candidate_snapshot["desired_salary_min"]))
        except Exception:
            pass

    # INT:004 — hydrate benefits: prefer structured data from linked compensation policy,
    # then fall back to job_snapshot benefits (already set by wizard or manual edit).
    _comp_policy = job_snapshot.get("compensation_policy") or {}
    _policy_benefits_pkg = _comp_policy.get("benefits_package") or {}
    _policy_benefit_names: list[str] = (
        _policy_benefits_pkg.get("included", [])
        if isinstance(_policy_benefits_pkg, dict)
        else []
    )

    if job_snapshot.get("benefits"):
        benefits = job_snapshot["benefits"]
        if isinstance(benefits, list):
            fields["benefits"] = [
                {"name": b} if isinstance(b, str) else b for b in benefits
            ]
            existing_names = {
                (b if isinstance(b, str) else b.get("name", "")).lower()
                for b in benefits
            }
            for pname in _policy_benefit_names:
                if pname.lower() not in existing_names:
                    fields["benefits"].append(
                        {"name": pname, "source": "compensation_policy"}
                    )
    elif _policy_benefit_names:
        fields["benefits"] = [
            {"name": n, "source": "compensation_policy"} for n in _policy_benefit_names
        ]

    # Expose compensation_policy summary — stored under custom_clauses (canonical JSONB).
    # TODO Sprint F.4 #42: canonical-remap — the old code stored a separate
    # ``compensation_policy_snapshot`` key; canonical model has no such column.
    # Until a dedicated field exists, this is dropped (snapshot already
    # captured in job_data_snapshot for LGPD purposes).

    # Currency from salary_range
    fields["currency"] = salary_range.get("currency", "BRL")

    # Start date
    fields["start_date"] = compute_default_start_date()

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
        # Idempotent: return existing draft if present (job_id wire-level -> job_vacancy_id internal)
        existing = await self._repo.get_active_draft(
            company_id, data.candidate_id, data.job_id
        )
        if existing:
            return existing

        # INT:004 — load PRV policy before prefill so prefill_from_snapshots can hydrate benefits
        await self._enrich_job_snapshot_compensation(job_snapshot)
        prefill = prefill_from_snapshots(job_snapshot, candidate_snapshot)
        validity = _DEFAULT_VALIDITY_DAYS

        # TODO Sprint F.4 #42: canonical-remap — denormalized display fields
        # (candidate_name, candidate_email, job_title) are NOT NULL on the
        # canonical table; populate from snapshots so insert doesn't fail.
        proposal = OfferProposal(
            company_id=company_id,
            candidate_id=data.candidate_id,
            job_vacancy_id=data.job_id,
            candidate_name=candidate_snapshot.get("name", ""),
            candidate_email=candidate_snapshot.get("email"),
            job_title=job_snapshot.get("title"),
            job_data_snapshot=job_snapshot,
            candidate_data_snapshot=candidate_snapshot,
            response_deadline=compute_response_deadline(validity),
            created_by=user_id,
            **prefill,
        )
        # TODO Sprint F.4 #42: template_version is VARCHAR(32) in canonical;
        # the wire payload sends UUID template_id. For now we stringify it so
        # the offer can still be linked back to a template by id at the
        # application layer. A proper lookup table (template_id -> version)
        # would replace this.
        if data.template_id is not None:
            proposal.template_version = str(data.template_id)
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

        # ``by_alias=False`` ensures we receive canonical attribute names
        # (salary, currency, bonus_pct, ...) regardless of wire payload keys.
        data = updates.model_dump(exclude_unset=True, by_alias=False)

        # Sprint F.4 #42: bonus_target may arrive as OfferBonusVariable (dict
        # with "value"); canonical column expects Numeric. Extract numeric.
        if "bonus_target" in data and isinstance(data["bonus_target"], dict):
            try:
                data["bonus_target"] = Decimal(str(data["bonus_target"]["value"]))
            except (KeyError, TypeError, ValueError):
                # TODO Sprint F.4 #42: canonical-remap — full bonus structure
                # would need a JSONB column; for now store target Decimal only.
                data["bonus_target"] = None

        # Sprint F.4 #42: validity_days has no canonical column. Translate to
        # response_deadline = utcnow() + delta. Pop from data before setattr loop.
        validity_days = data.pop("validity_days", None)

        # Sprint F.4 #42: recruiter_notes is a wire-level alias of
        # custom_clauses[?clause_type=recruiter_notes]. Pop + apply specially.
        recruiter_notes = data.pop("recruiter_notes", None)

        # Sprint F.4 #42: template_id (UUID FK) is no longer a canonical column.
        # Stringify to template_version for back-compat.
        template_id = data.pop("template_id", None)

        for field, value in data.items():
            setattr(proposal, field, value)

        if validity_days is not None:
            proposal.response_deadline = compute_response_deadline(validity_days)

        if recruiter_notes is not None:
            _set_recruiter_notes_in_custom_clauses(proposal, recruiter_notes)

        if template_id is not None:
            proposal.template_version = str(template_id)

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
            # Sprint F.4 #42: canonical recruiter_notes lives in custom_clauses JSONB.
            existing = _recruiter_notes_from_custom_clauses(proposal.custom_clauses)
            _set_recruiter_notes_in_custom_clauses(
                proposal, (existing or "") + f"\n[cancelled: {reason}]"
            )
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
                job_vacancy_id=str(proposal.job_vacancy_id) if proposal.job_vacancy_id else None,
                demographic_proxies={},
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
        # Sprint F.4 #42: send_mode + sent_by_user_id + email_log_id have NO
        # direct canonical columns. Append a multi-channel record to sent_via
        # JSONB array (canonical pattern for multi-channel send tracking).
        now = datetime.utcnow()
        proposal.sent_at = now
        sent_via = list(proposal.sent_via or [])
        sent_via.append({
            "channel": "email",
            "send_mode": send_mode,
            "sent_by_user_id": user_id,
            "log_id": str(email_log_id) if email_log_id else None,
            "sent_at": now.isoformat(),
        })
        proposal.sent_via = sent_via
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
                job_vacancy_id=str(proposal.job_vacancy_id) if proposal.job_vacancy_id else None,
                demographic_proxies={},
            )
        except Exception as audit_err:
            logger.warning(f"[T-1157] offer mark_sent audit failed: {audit_err}")
        return updated

    def render_offer_template_variables(
        self, proposal: OfferProposal
    ) -> dict[str, str]:
        """Build variable map for email template interpolation.

        Sprint F.4 #42 canonical-remap: reads canonical columns (salary, currency,
        start_date) but exposes wire-level template var names for FE/template
        backward compatibility (``offered_salary_formatted``, ``offered_start_date``,
        ``validity_days``, ``bonus_admission``).
        """
        job = proposal.job_data_snapshot or {}
        candidate = proposal.candidate_data_snapshot or {}
        salary = proposal.salary
        currency = proposal.currency or "BRL"
        validity_days = _validity_days_from_deadline(proposal)
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
                str(proposal.start_date) if proposal.start_date else ""
            ),
            "validity_days": str(validity_days),
            "bonus_admission": (
                f"{currency} {float(proposal.bonus_pct):,.2f}"
                if proposal.bonus_pct
                else ""
            ),
            "contract_type": job.get("contract_type", ""),
            "work_model": job.get("work_model", ""),
        }
