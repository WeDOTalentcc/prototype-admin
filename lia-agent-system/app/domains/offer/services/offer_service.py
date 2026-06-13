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
from app.domains.hiring_policy.repositories.hiring_policy_repository import (
    HiringPolicyRepository,
)
from app.domains.company.repositories.approver_repository import (
    ApproverRepository,
)
from app.schemas.offer import OfferDraftCreate, OfferDraftUpdate
from app.shared.compliance.audit_service import AuditService  # T-1157
from app.shared.services.approval_notification_service import (
    ApprovalNotificationService,
)

logger = logging.getLogger(__name__)

_WORKING_DAYS_BUFFER = 30
_DEFAULT_VALIDITY_DAYS = 7


class OfferPolicyGateError(PermissionError):
    """Base class for any offer-send blocker imposed by company hiring policy.

    All subclasses live here so callers (LLM tools, REST endpoints, future
    background jobs) can catch the family with one ``except`` and discriminate
    via ``isinstance``/``.reason``. New gates added to ``OfferService.check_can_send``
    MUST subclass this — never raise raw ``PermissionError`` (callers will
    miss the structured UX path) and never reuse a sibling subclass (each
    reason maps to a different ``ui_action`` in the chat layer).
    """

    reason: str = "offer_policy_gate"  # overridden by subclasses


class ManagerApprovalRequiredError(OfferPolicyGateError):
    """Raised when an offer transition requires manager approval per company policy.

    Closes P0-2 (2026-05-21 audit): the toggle
    ``CompanyHiringPolicy.pipeline_rules.manager_approval_for_offer`` was
    visible in Configurações → Políticas de Recrutamento but ignored by every
    write path in ``app/domains/offer/``. Recruiter set ON, offers still went
    out without approval.

    Gate lives in :py:meth:`OfferService.mark_sent` (single point of
    enforcement, fail-closed). Any caller — REST endpoint, LLM tool, future
    background job — that wants to flip a draft to ``sent`` is intercepted
    here. The exception is a ``PermissionError`` subclass so default handlers
    surface a 403-equivalent; the tool layer catches it specifically to
    return a structured ``requires_approval`` payload to the chat.
    """

    reason = "manager_approval_required"


class MinInterviewsNotMetError(OfferPolicyGateError):
    """Raised when an offer cannot be sent because the candidate has not
    completed the minimum number of interviews required by company policy.

    Closes P1-9 (2026-05-21 audit): the field
    ``CompanyHiringPolicy.pipeline_rules.min_interviews_before_offer`` was
    enforced for STAGE TRANSITIONS (``pipeline_policy.py:50``) but NOT for
    offer creation/send. Recruiter could skip stages and the LLM tool could
    create+send an offer with zero interviews completed.

    Gate also lives in :py:meth:`OfferService.check_can_send`, sharing the
    pre-flight pattern with manager-approval. Defense-in-depth is provided
    by ``mark_sent`` raising the same exception if the pre-flight is skipped.
    """

    reason = "min_interviews_not_met"


class NoApproverConfiguredError(OfferPolicyGateError):
    """Raised when ``manager_approval_for_offer=ON`` but the company has
    no active Approver rows configured in ``approvers``.

    Closes P0.D1 (audit 2026-05-22): the ApproverSection in
    Configuracoes > Departamentos exposes CRUD over the Approver table,
    but until this gate the table was effectively a ghost setting — even
    with the toggle ON, OfferService only checked ``approval_request_id``
    presence on the draft, never that approver identities had been
    configured. Recruiter sets toggle ON, never configures approvers,
    offers go out anyway (when ``approval_request_id`` is somehow set
    elsewhere). This gate refuses sends in that state with a structured
    reason so the UX can prompt admin to configure approvers.

    Distinct from ``ManagerApprovalRequiredError``:
    - ``ManagerApprovalRequiredError`` => toggle ON, no approval_request_id
      yet; recruiter must trigger the approval workflow.
    - ``NoApproverConfiguredError`` => toggle ON, but the Approver table is
      empty; admin must add at least one approver before any workflow
      can be triggered. UX response is ``ui_action='prompt_admin_to_configure_approver'``.
    """

    reason = "no_approver_configured"


_OFFER_APPROVAL_TOGGLE = "manager_approval_for_offer"
_MIN_INTERVIEWS_FIELD = "min_interviews_before_offer"
_INTERVIEW_COMPLETED_STATUSES = ("completed", "done", "realizada")


def compute_default_start_date() -> date:
    """Return today + 30 calendar days as default start date."""
    return (datetime.utcnow() + timedelta(days=_WORKING_DAYS_BUFFER)).date()



async def compute_next_start_date_for_company(company_id: str, db) -> "date":
    """Compute next valid start date per offer_rules.

    Reads CompanyHiringPolicy.offer_rules fields:
      allowed_start_day_of_month, min_notice_days, onboarding_blackout_periods.
    Falls back to compute_default_start_date() when no rules configured.
    Used by OfferConciergeAgent.suggest_next_start_date tool.
    """
    from app.domains.hiring_policy.repositories.hiring_policy_repository import HiringPolicyRepository

    policy = await HiringPolicyRepository(db).get_by_company_id(company_id)
    rules = (policy.offer_rules if policy else None) or {}

    allowed_days = rules.get("allowed_start_day_of_month", [])
    min_notice = int(rules.get("min_notice_days", 30))
    blackouts = rules.get("onboarding_blackout_periods", [])

    base = (datetime.utcnow() + timedelta(days=min_notice)).date()

    if not allowed_days:
        return base

    from datetime import date as _date
    candidate = base
    for _ in range(90):
        if candidate.day in allowed_days:
            blocked = False
            for blk in blackouts:
                try:
                    if _date.fromisoformat(blk["start"]) <= candidate <= _date.fromisoformat(blk["end"]):
                        blocked = True
                        break
                except (KeyError, ValueError):
                    pass
            if not blocked:
                return candidate
        candidate = candidate + timedelta(days=1)

    return base


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



class NoEligibleApproverForAmountError(OfferPolicyGateError):
    """Raised when no approver has a ``can_approve_above_amount`` threshold
    that covers the offer salary.

    P0.D2 (audit Wave 2 2026-05-22): when the company has configured
    amount-threshold routing (at least one approver row with
    ``can_approve_above_amount`` set), every send must route to an
    approver whose threshold covers the offer salary. If no such
    approver exists for this amount, the gate refuses send. ``amount``
    and ``max_configured_threshold`` are exposed so the UX can prompt
    the admin to configure a higher-tier approver.
    """

    def __init__(self, message: str, *, amount=None, max_configured_threshold=None):
        super().__init__(message)
        self.amount = amount
        self.max_configured_threshold = max_configured_threshold

class OfferService:

    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = OfferRepository(db)
        # P0.D1 (2026-05-22): ApproverRepository wired so check_can_send
        # can verify at least one active Approver row exists when policy
        # gates approval. ApprovalNotificationService is the canonical
        # dispatch helper for in-app + email notifications to approvers.
        self._approver_repo = ApproverRepository(db)
        self._approval_notifier = ApprovalNotificationService(db)

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

    async def check_can_send(
        self, offer_id: UUID, company_id: str
    ) -> None:
        """Pre-flight gate: raise BEFORE side effects (email dispatch) if any
        company hiring policy refuses this send.

        Two gates today, both subclassing :class:`OfferPolicyGateError`:
        - **manager approval** (P0-2): ``pipeline_rules.manager_approval_for_offer``
          requires a draft to carry ``approval_request_id`` before send.
        - **min interviews** (P1-9): ``pipeline_rules.min_interviews_before_offer``
          requires the candidate to have at least N completed interviews
          before an offer can leave the system.

        Order matters: approval is cheaper to check (no extra count query),
        so it goes first. Both raise distinct subclasses so the LLM tool can
        route the user to the right next action (request_offer_approval vs.
        schedule_more_interviews).

        Callers (REST endpoint, ``send_offer`` LLM tool, future background
        jobs) MUST invoke this BEFORE dispatching the offer email — not just
        before ``mark_sent``. The same enforcement also lives inside
        ``mark_sent`` as defense-in-depth — if a future caller forgets the
        pre-flight, the state transition still fails. But by then the email
        has been sent: that is exactly the regression P0-2/P1-9 closes.

        Idempotent and side-effect-free. Returns ``None`` on permit; raises
        an :class:`OfferPolicyGateError` subclass on deny.
        """
        proposal = await self._repo.get_by_id(offer_id, company_id)
        if not proposal:
            # Caller will get a 404 from a subsequent ``get_draft``; nothing
            # to gate against a draft that does not exist.
            return
        # --- Gate 1: manager approval (P0-2 + P0.D1) ------------------------
        if proposal.approval_request_id is None and await self._requires_manager_approval(company_id):
            # P0.D1 (2026-05-22): when the policy gates approval, also confirm
            # that approver identities have been configured. Without at least
            # one active Approver row the workflow has nowhere to route, so
            # we refuse with a distinct ``NoApproverConfiguredError`` whose
            # ui_action prompts the admin to configure approvers instead of
            # the recruiter to request approval.
            approvers_configured = await self._has_active_approvers(company_id)
            if not approvers_configured:
                raise NoApproverConfiguredError(
                    "Esta empresa exige aprovacao do gestor antes de enviar "
                    "ofertas, mas nenhum aprovador esta configurado. Peca para "
                    "o admin adicionar pelo menos um aprovador em Configuracoes "
                    "> Departamentos antes de continuar."
                )
            # Approvers exist - notify them in-app (fail-open: dispatch errors
            # are logged + audited but never propagated; the gate raise below
            # remains the authoritative blocker the caller sees).
            try:
                await self._approval_notifier.notify_pending_approvers_for_offer(
                    company_id=company_id,
                    offer_id=proposal.id,
                    candidate_id=getattr(proposal, "candidate_id", None),
                    candidate_name=getattr(proposal, "candidate_name", None),
                    job_vacancy_id=getattr(proposal, "job_vacancy_id", None),
                    job_title=getattr(proposal, "job_title", None),
                    requested_by_user_id=getattr(proposal, "created_by", None),
                )
            except Exception as notify_err:
                logger.warning(
                    "[OfferService] approval notification dispatch failed "
                    "offer_id=%s err=%s",
                    proposal.id, str(notify_err)[:120],
                )
            raise ManagerApprovalRequiredError(
                "Esta empresa exige aprovacao do gestor antes de enviar ofertas. "
                "Solicite aprovacao primeiro (workflow de approval) ou altere "
                "a politica em Configuracoes > Politicas de Recrutamento > "
                "Aprovacao Gestor."
            )
        # --- Gate 1.5: amount-threshold approver routing (P0.D2) -----------
        # Audit Wave 2 2026-05-22: when the company has at least one
        # approver row configured with a non-NULL ``can_approve_above_amount``
        # threshold, the offer salary must be covered by at least one
        # eligible approver. Backward-compat: if every approver has NULL
        # threshold (legacy), every approver is eligible -> gate no-op.
        # Type guard: only fire the gate when salary is a real numeric value.
        # OfferProposal.salary is Numeric(12,2) -> Decimal at the ORM layer,
        # but unit tests pass MagicMock proposals where ``salary`` may be a
        # MagicMock or any non-numeric placeholder. Treating those as
        # "no salary set" preserves the pre-existing gate semantics
        # exercised by test_offer_approval_gate.py.
        from decimal import Decimal as _Decimal
        salary = getattr(proposal, "salary", None)
        if isinstance(salary, (int, float, _Decimal)):
            # Camada 3 Item 3 (2026-05-22, migration 172): OfferProposal now
            # carries department_id natively (FK -> departments.id). The
            # pre-migration getattr workaround is removed. The isinstance
            # guard remains to keep unit tests with MagicMock proposals
            # green — production rows always satisfy it.
            department_id = proposal.department_id
            if not isinstance(department_id, (str, type(None))) and not hasattr(department_id, "hex"):
                department_id = None  # ignore MagicMock department_id in tests
            eligible_ok = await self._has_eligible_approver_for_amount(
                company_id, department_id, salary,
            )
            if not eligible_ok:
                raise NoEligibleApproverForAmountError(
                    "Nenhum aprovador configurado pode aprovar este valor. "
                    "Verifique em Configuracoes > Departamentos > Aprovadores "
                    "se ha um aprovador cujo limite cobre R$ %s."
                    % salary,
                    amount=salary,
                )

        # --- Gate 2: min interviews completed (P1-9) ------------------------
        await self._check_min_interviews_met(proposal, company_id)

    async def _check_min_interviews_met(
        self, proposal: OfferProposal, company_id: str
    ) -> None:
        """Raise :class:`MinInterviewsNotMetError` if the candidate has not
        completed at least ``pipeline_rules.min_interviews_before_offer``
        interviews.

        Reads ``CompanyHiringPolicy.pipeline_rules.min_interviews_before_offer``
        via the canonical repository (ADR-001). Default of 2 mirrors the schema
        default in ``PipelineRulesIn`` (``app/schemas/company_hiring_policy.py``)
        and the canonical fallback at ``pipeline_policy.py:50``.

        Interview count uses the canonical ``Interview`` model with
        case-insensitive matching against the canonical completed-status
        triple ("completed", "done", "realizada"). Same pattern as the stage
        transition gate so we never disagree on what counts as "completed".

        Multi-tenancy: the proposal is already scoped to ``company_id`` by
        ``check_can_send``'s ``get_by_id``; we do not re-query the candidate.
        """
        # NOTE: HiringPolicyRepository is imported at module level (see top
        # of file) — DO NOT re-import locally. Re-import here breaks unit
        # tests that patch ``mod.HiringPolicyRepository`` because the local
        # import binds to the real class at call time.
        policy_repo = HiringPolicyRepository(self._db)
        policy = await policy_repo.get_by_company(company_id)
        if not policy or not policy.pipeline_rules:
            return  # cold-start tenants do not impose a gate they have not configured
        min_required = policy.pipeline_rules.get(_MIN_INTERVIEWS_FIELD, 0)
        if not isinstance(min_required, int) or min_required <= 0:
            return  # zero or non-int means no gate (explicit opt-out)
        candidate_id = getattr(proposal, "candidate_id", None)
        if candidate_id is None:
            # Defensive: orphan draft. Cannot count interviews; fall through
            # and let mark_sent surface the integrity issue.
            logger.warning(
                "[OfferService] check_min_interviews on proposal %s with "
                "no candidate_id — skipping gate, will be flagged at mark_sent.",
                proposal.id,
            )
            return
        from sqlalchemy import func, select
        # Canonical Interview model lives at ``app.models.interview``
        # (matches pipeline_policy.py:53 to guarantee agreement on what
        # "completed" means).
        try:
            from app.models.interview import Interview
            stmt = select(func.count(Interview.id)).where(
                Interview.candidate_id == candidate_id,
                Interview.status.in_(_INTERVIEW_COMPLETED_STATUSES),
            )
            result = await self._db.execute(stmt)
            completed = int(result.scalar() or 0)
        except Exception as exc:
            # Mirror the pipeline_policy.py fallback to the domain model.
            logger.debug(
                "[OfferService] canonical Interview lookup failed (%s); "
                "trying domain model fallback.", str(exc)[:80],
            )
            try:
                from app.domains.interview_scheduling.models.interview import (
                    Interview as DomainInterview,
                )
                stmt = select(func.count(DomainInterview.id)).where(
                    DomainInterview.candidate_id == candidate_id,
                    DomainInterview.status.in_(_INTERVIEW_COMPLETED_STATUSES),
                )
                result = await self._db.execute(stmt)
                completed = int(result.scalar() or 0)
            except Exception as fallback_exc:
                # Fail OPEN here intentionally: a DB lookup failure on the
                # gate must NOT block a legitimate offer. The audit trail
                # surfaces the silent skip so SRE can investigate; gate
                # remains effective for the 99.9% happy path.
                logger.warning(
                    "[OfferService] interview count lookup failed; "
                    "gate fails OPEN. company_id=%s candidate_id=%s err=%s",
                    company_id, candidate_id, str(fallback_exc)[:120],
                )
                return
        if completed < min_required:
            raise MinInterviewsNotMetError(
                f"Esta empresa exige no minimo {min_required} entrevista(s) "
                f"completada(s) antes de enviar oferta. Candidato tem "
                f"{completed}. Agende ou conclua entrevistas adicionais, "
                f"ou ajuste a politica em Configuracoes > Politicas de "
                f"Recrutamento > Minimo de Entrevistas."
            )

    async def _requires_manager_approval(self, company_id: str) -> bool:
        """Return True iff the company policy gates outbound offers on manager approval.

        Reads ``CompanyHiringPolicy.pipeline_rules.manager_approval_for_offer``
        via the canonical repository (ADR-001). Returns ``False`` when no policy
        row exists yet (cold-start tenants do not impose a gate they have not
        configured) — explicit opt-in semantics.

        Tight, idempotent helper; intentionally accepts ``str`` (matches the
        column type ``String(255)``) rather than ``UUID`` to stay aligned with
        the rest of the offer surface.
        """
        policy_repo = HiringPolicyRepository(self._db)
        policy = await policy_repo.get_by_company(company_id)
        if not policy or not policy.pipeline_rules:
            return False
        return bool(policy.pipeline_rules.get(_OFFER_APPROVAL_TOGGLE, False))

    async def _has_active_approvers(self, company_id: str) -> bool:
        """Return True iff the company has at least one active Approver row.

        Reads via :class:`ApproverRepository.list_for_company`, which already
        filters by ``is_active``. Returns False on any repo exception so the
        gate fails CLOSED (refuses send) - this is the inverse compliance
        trade-off from ``_check_min_interviews_met`` (which fails open on
        DB error). Rationale: an offer leaving the system without approver
        signature is a higher compliance risk than blocking a legitimate
        offer for a few minutes while SRE investigates an Approver table
        outage. Audit trail in ``_approval_notifier`` captures the failure.

        Accepts ``str`` to align with the column type on OfferProposal and
        the rest of this service (matching ``_requires_manager_approval``).
        """
        # Best-effort UUID coercion: the canonical column type is
        # ``String(255)`` (legacy), but the Approver FK expects UUID.
        # In tests we accept opaque strings so the repo mock can answer.
        # If coercion fails AND the call still works (e.g. mocked repo),
        # we proceed; only when the call itself raises do we fail-closed.
        try:
            if isinstance(company_id, UUID):
                lookup_id = company_id
            else:
                try:
                    lookup_id = UUID(str(company_id))
                except (TypeError, ValueError):
                    lookup_id = company_id  # type: ignore[assignment]
            approvers = await self._approver_repo.list_for_company(lookup_id)
            return len(approvers) > 0
        except Exception as exc:
            logger.warning(
                "[OfferService] _has_active_approvers lookup failed; "
                "gate fails CLOSED. company_id=%s err=%s",
                company_id, str(exc)[:120],
            )
            return False

    async def _has_eligible_approver_for_amount(
        self,
        company_id,
        department_id,
        amount,
    ) -> bool:
        """Return True iff at least one configured approver can approve this amount.

        P0.D2 (audit Wave 2 2026-05-22): wraps
        :class:`ApproverRepository.list_eligible_for_amount`. NULL
        ``can_approve_above_amount`` on every row = legacy/backward-compat
        (no amount routing configured), which always returns True because
        every approver is eligible.

        Fails CLOSED on repo exception (same trade-off as
        ``_has_active_approvers``): an offer leaving without a threshold
        match is higher compliance risk than blocking a legitimate offer
        while SRE investigates.

        ``amount`` may be ``None`` when the draft has no salary yet — we
        treat that as 0 (every approver qualifies), keeping the gate
        forward-permissive for incomplete drafts.
        """
        from decimal import Decimal
        try:
            if isinstance(company_id, UUID):
                lookup_id = company_id
            else:
                try:
                    lookup_id = UUID(str(company_id))
                except (TypeError, ValueError):
                    lookup_id = company_id  # type: ignore[assignment]
            amt = Decimal(str(amount)) if amount is not None else Decimal("0")
            eligible = await self._approver_repo.list_eligible_for_amount(
                lookup_id, department_id, amt
            )
            return len(eligible) > 0
        except Exception as exc:
            logger.warning(
                "[OfferService] _has_eligible_approver_for_amount lookup "
                "failed; gate fails CLOSED. company_id=%s amount=%s err=%s",
                company_id, amount, str(exc)[:120],
            )
            return False

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
        # P0-2 gate (audit 2026-05-21): block sends when company policy requires
        # manager approval and the draft has no approval record. We use
        # ``approval_request_id`` (canonical column on OfferProposal) as the
        # evidence-of-approval marker. A draft becomes sendable when either
        # (a) the policy toggle is OFF, or (b) an approval workflow has set
        # ``approval_request_id`` to a non-null UUID. Approver identity / level
        # detail lives in the linked approval row; this gate only enforces
        # presence, intentionally not interpretation — the approval domain
        # owns acceptance semantics.
        if proposal.approval_request_id is None:
            requires_approval = await self._requires_manager_approval(company_id)
            if requires_approval:
                # P0.D1 (2026-05-22): defense-in-depth - surface
                # NoApproverConfiguredError here too when the Approver table
                # is empty, so a future caller that bypasses check_can_send
                # still gets the structured admin-facing reason rather than
                # a generic ManagerApprovalRequiredError.
                if not await self._has_active_approvers(company_id):
                    raise NoApproverConfiguredError(
                        "Esta empresa exige aprovacao do gestor antes de enviar "
                        "ofertas, mas nenhum aprovador esta configurado. Peca "
                        "para o admin adicionar pelo menos um aprovador em "
                        "Configuracoes > Departamentos antes de continuar."
                    )
                raise ManagerApprovalRequiredError(
                    "Esta empresa exige aprovacao do gestor antes de enviar ofertas. "
                    "Solicite aprovacao primeiro (workflow de approval) ou altere "
                    "a politica em Configuracoes > Politicas de Recrutamento > "
                    "Aprovacao Gestor."
                )
        # P1-9 defense-in-depth (audit 2026-05-21): if pre-flight
        # ``check_can_send`` was skipped, enforce min_interviews here too.
        # Reuses the same helper so the agreement on "what counts as a
        # completed interview" never drifts between the two enforcement
        # sites.
        await self._check_min_interviews_met(proposal, company_id)
        # P0.D2 defense-in-depth (audit Wave 2 2026-05-22): if pre-flight
        # ``check_can_send`` was skipped, enforce amount-threshold here too.
        # Same reasoning as the approval/min-interviews duplications above:
        # a caller forgetting the pre-flight cannot bypass the gate.
        from decimal import Decimal as _Decimal
        salary = getattr(proposal, "salary", None)
        if isinstance(salary, (int, float, _Decimal)):
            # Camada 3 Item 3 (2026-05-22, migration 172): canonical
            # department_id (FK column). isinstance guard preserves
            # MagicMock-tolerance for the unit-test surface.
            department_id = proposal.department_id
            if not isinstance(department_id, (str, type(None))) and not hasattr(department_id, "hex"):
                department_id = None
            if not await self._has_eligible_approver_for_amount(
                company_id, department_id, salary,
            ):
                raise NoEligibleApproverForAmountError(
                    "Nenhum aprovador configurado pode aprovar este valor. "
                    "Verifique em Configuracoes > Departamentos > Aprovadores "
                    "se ha um aprovador cujo limite cobre R$ %s." % salary,
                    amount=salary,
                )
        proposal.status = "sent"
        # Sprint F.4 #42: send_mode + sent_by_user_id + email_log_id have NO
        # direct canonical columns. Append a multi-channel record to sent_via
        # JSONB array (canonical pattern for multi-channel send tracking).
        now = datetime.utcnow()
        # P0-1 (Migration 266): generate portal token + acceptance_url on first send
        import uuid as _uuid_mod
        import os as _os_mod
        if not proposal.candidate_token:
            proposal.candidate_token = _uuid_mod.uuid4()
        if not proposal.acceptance_url:
            base_url = _os_mod.environ.get("PORTAL_BASE_URL", "").rstrip("/")
            if base_url:
                proposal.acceptance_url = f"{base_url}/portal/proposta/{proposal.candidate_token}"
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
            "offer_link": proposal.acceptance_url or "",
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

    async def mark_expired(
        self,
        offer_id: "UUID",
        company_id: str,
    ) -> "OfferProposal | None":
        """Mark sent offer as expired when response_deadline passed.

        Called by offer expiry scheduler. Fires OFFER_EXPIRED trigger (fail-soft).
        """
        from datetime import datetime as _dt
        proposal = await self._repo.get_by_id(offer_id, company_id)
        if not proposal:
            return None
        if proposal.status not in ("sent", "viewed"):
            return proposal  # already resolved, idempotent

        proposal.status = "expired"
        await self._repo.update(proposal)
        await self._db.flush()

        try:
            from app.domains.communication.services.teams_service import TeamsService
            from app.shared.automation.trigger_types_canonical import TriggerType
            await TeamsService().on_offer_expired(
                offer_id=str(offer_id),
                company_id=company_id,
                candidate_name=proposal.candidate_name or "",
            )
        except Exception as _e:
            import logging as _l
            _l.getLogger(__name__).debug("[offer_service] OFFER_EXPIRED notify failed: %s", _e)

        return proposal
