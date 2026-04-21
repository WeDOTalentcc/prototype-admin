"""
E10 — Offer Proposals API.

Endpoints
---------
POST   /api/v1/offer-proposals                         → generate + persist a draft offer
POST   /api/v1/offer-proposals/{id}/approval           → kick off the internal approval chain
POST   /api/v1/offer-proposals/{id}/approval/decision  → record approver decision (approve/reject)
POST   /api/v1/offer-proposals/{id}/send               → send the letter to the candidate
POST   /api/v1/offer-proposals/{id}/negotiate          → log a negotiation round
POST   /api/v1/offer-proposals/{id}/accept             → candidate accepts → triggers E11
POST   /api/v1/offer-proposals/{id}/decline            → candidate declines → triggers E12
POST   /api/v1/offer-proposals/{id}/withdraw           → company withdraws the offer
GET    /api/v1/offer-proposals/{id}                    → fetch a proposal + audit trail
GET    /api/v1/offer-proposals                         → list proposals for a company

Security
--------
All endpoints resolve and verify the caller's company_id through
``get_verified_company_id`` (JWT-backed TenantGuard) and explicitly
reject access to proposals owned by a different company (IDOR guard).

Approval gate
-------------
``/send`` is only allowed when the proposal is APPROVED *or* its
required approval level is "manager" (the lowest tier, which is the
implicit-auto-approve case for low-value offers). The workflow is
synced with the underlying ``ApprovalRequest`` via the
``/approval/decision`` endpoint, so if procurement / leadership uses
the existing approvals UI, the offer status follows along.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._path_patterns import (
    DUAL_ID_PATH_PATTERN,
    reorder_collection_before_item as _reorder_collection_before_item,
)
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.services.offer_letter_service import OfferLetterService, offer_letter_service
from app.shared.tenant_guard import get_verified_company_id
from lia_models.offer_proposal import OfferProposal, OfferRoundType, OfferStatus

logger = logging.getLogger(__name__)

_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

router = APIRouter(prefix="/offer-proposals", tags=["offer-proposals"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────


class OfferCreateRequest(BaseModel):
    candidate_name: str
    candidate_email: str | None = None
    job_title: str
    job_vacancy_id: str | None = None
    candidate_id: str | None = None
    vacancy_candidate_id: str | None = None
    manager_name: str | None = None
    company_name: str | None = None
    currency: str = "BRL"
    salary: float | None = None
    bonus_pct: float | None = None
    bonus_target: float | None = None
    benefits: list[str] | None = None
    start_date: datetime | None = None
    response_deadline: datetime | None = None
    custom_clauses: list[str] | None = None
    created_by: str | None = None
    use_llm: bool = True


class OfferRoundRequest(BaseModel):
    actor_name: str
    actor_email: str | None = None
    actor: str = Field(default="candidate", description="company | candidate | approver")
    salary: float | None = None
    bonus_pct: float | None = None
    benefits: list[str] | None = None
    message: str | None = None


class OfferDeclineRequest(OfferRoundRequest):
    decline_reason: str | None = None


class OfferSendRequest(BaseModel):
    channels: list[str] = Field(default_factory=lambda: ["email"])
    candidate_phone: str | None = None


class OfferApprovalRequestBody(BaseModel):
    requester_name: str
    requester_email: str
    # Approver is optional — when omitted the service auto-resolves the
    # right person by required approval level (chain by value).
    approver_name: str | None = None
    approver_email: str | None = None


class OfferApprovalDecisionBody(BaseModel):
    decision: str = Field(..., description="approved | rejected")
    notes: str | None = None
    rejection_reason: str | None = None


class OfferProposalResponse(BaseModel):
    proposal: dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _looks_like_uuid(value: str | None) -> bool:
    if not value:
        return False
    try:
        UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False


async def _get_proposal_or_404(
    db: AsyncSession, proposal_id: str, company_id: str
) -> OfferProposal:
    """Fetch + verify ownership in one place. Returns 404 even when the
    proposal exists but belongs to another tenant (no enumeration leak)."""
    try:
        pid = UUID(proposal_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid proposal id")
    result = await db.execute(select(OfferProposal).where(OfferProposal.id == pid))
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Offer proposal not found")
    if str(proposal.company_id) != str(company_id):
        logger.warning(
            "[OfferProposals] cross-tenant access blocked: proposal=%s owner=%s caller=%s",
            proposal.id, proposal.company_id, company_id,
        )
        raise HTTPException(status_code=404, detail="Offer proposal not found")
    return proposal


def _ensure_status(proposal: OfferProposal, allowed: set[str]) -> None:
    if proposal.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Proposal in status '{proposal.status}' cannot transition; "
                f"expected one of {sorted(allowed)}"
            ),
        )


def _is_send_allowed(proposal: OfferProposal) -> bool:
    """The send gate: explicit approval OR low-value (manager-level) offer."""
    if proposal.status == OfferStatus.APPROVED.value:
        return True
    if (
        proposal.status == OfferStatus.DRAFT.value
        and (proposal.approval_required_level or "manager") == "manager"
    ):
        return True
    return False


async def _audit_safe(
    *,
    company_id: str,
    action: str,
    decision: str,
    proposal_id: str,
    reasoning: list[str],
) -> None:
    """Write to AuditService when present; never break the main flow."""
    try:
        from app.shared.compliance.audit_service import get_audit_service  # type: ignore

        audit_svc = get_audit_service()
        if audit_svc is None:
            return
        await audit_svc.log_decision(
            company_id=company_id,
            agent_name="offer_letter_service",
            decision_type="offer_proposal",
            action=action,
            decision=decision,
            reasoning=[*reasoning, f"proposal_id={proposal_id}"],
            criteria_used=["offer_workflow", "approval_chain", "negotiation_round"],
            job_vacancy_id=None,
            human_review_required=False,
        )
    except Exception as exc:  # pragma: no cover - audit is best-effort
        logger.debug("Audit log skipped for offer %s: %s", proposal_id, exc)


async def _trigger_e11(db: AsyncSession, proposal: OfferProposal) -> bool:
    """Move the candidate to E11 (hire & pré-onboarding) when accepted."""
    if not proposal.vacancy_candidate_id:
        return False
    try:
        from app.api.v1.recruitment_stages._shared import (  # type: ignore
            pipeline_stage_service,
        )

        await pipeline_stage_service.transition_candidate(
            vacancy_candidate_id=str(proposal.vacancy_candidate_id),
            to_stage="hired",
            to_sub_status=None,
            triggered_by="offer_letter_service",
            triggered_by_user_id=None,
            source_agent="offer_letter_service",
            reason="Offer accepted by candidate (E10 → E11)",
            notes=f"Offer proposal {proposal.id} accepted",
            context={"company_id": proposal.company_id, "offer_proposal_id": str(proposal.id)},
            force=False,
            db=db,
        )
        return True
    except Exception as exc:
        logger.warning("E11 hire trigger failed for offer %s: %s", proposal.id, exc)
        return False


async def _trigger_e12(db: AsyncSession, proposal: OfferProposal, reason: str | None) -> bool:
    """Send the candidate to E12 (talent pool) when the offer is declined."""
    if not proposal.vacancy_candidate_id:
        return False
    try:
        from app.api.v1.recruitment_stages._shared import (  # type: ignore
            pipeline_stage_service,
        )

        await pipeline_stage_service.transition_candidate(
            vacancy_candidate_id=str(proposal.vacancy_candidate_id),
            to_stage="offer_declined",
            to_sub_status=None,
            triggered_by="offer_letter_service",
            triggered_by_user_id=None,
            source_agent="offer_letter_service",
            reason=reason or "Offer declined by candidate (E10 → E12)",
            notes=f"Offer proposal {proposal.id} declined",
            context={"company_id": proposal.company_id, "offer_proposal_id": str(proposal.id)},
            force=False,
            db=db,
        )
        return True
    except Exception as exc:
        logger.warning("E12 talent-pool trigger failed for offer %s: %s", proposal.id, exc)
        return False


async def _send_via_communication(
    db: AsyncSession,
    proposal: OfferProposal,
    channels: list[str],
    candidate_phone: str | None,
) -> list[str]:
    """
    Hand the letter off to Ag.7's CommunicationDispatcher (multi-channel,
    same path used by the CommunicationReActAgent). Returns the channels
    that actually got dispatched. We only mark a channel as sent when the
    dispatcher acks success — never on a swallowed exception.
    """
    delivered: list[str] = []
    if not proposal.candidate_email and not candidate_phone:
        return delivered

    try:
        from app.domains.communication.services.communication_dispatcher import (
            communication_dispatcher,
        )

        wants_multi = len(set(channels)) > 1 or "all" in channels
        single_channel = None if wants_multi else (channels[0] if channels else "email")

        result = await communication_dispatcher.dispatch_message(
            company_id=str(proposal.company_id),
            recipient_email=proposal.candidate_email if "email" in channels or wants_multi else None,
            recipient_phone=candidate_phone if "whatsapp" in channels or wants_multi else None,
            subject=f"[LIA] Carta-proposta — {proposal.job_title}",
            message=proposal.letter_markdown or proposal.letter_html or "",
            channel=single_channel,
            candidate_name=proposal.candidate_name,
            db=db,
            multi_channel=wants_multi,
        )

        # Per-channel accounting: only mark a channel as delivered when the
        # dispatcher reports per-channel success=true. Single-channel mode
        # exposes success at the top level; multi-channel mode exposes it
        # inside ``results[channel].success``.
        per_channel = result.get("results") or {}
        if per_channel:
            for ch, ch_res in per_channel.items():
                if isinstance(ch_res, dict) and ch_res.get("success") and ch not in delivered:
                    delivered.append(ch)
        elif result.get("success") and single_channel:
            delivered.append(single_channel)
    except Exception as exc:
        logger.warning("CommunicationDispatcher failed for offer %s: %s", proposal.id, exc)

    return delivered


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("", response_model=OfferProposalResponse, status_code=201)
async def create_offer_proposal(
    payload: OfferCreateRequest,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
    service: OfferLetterService = Depends(lambda: offer_letter_service),
):
    """Generate a new offer letter and persist it as a DRAFT."""
    rendered = await service.build_letter(
        company_id=company_id,
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        job_title=payload.job_title,
        manager_name=payload.manager_name,
        company_name=payload.company_name,
        currency=payload.currency,
        salary=payload.salary,
        bonus_pct=payload.bonus_pct,
        bonus_target=payload.bonus_target,
        benefits=payload.benefits,
        start_date=payload.start_date.strftime("%d/%m/%Y") if payload.start_date else None,
        response_deadline=payload.response_deadline.strftime("%d/%m/%Y") if payload.response_deadline else None,
        custom_clauses=payload.custom_clauses,
        job_vacancy_id=payload.job_vacancy_id,
        db=db,
        use_llm=payload.use_llm,
    )
    effective_salary = rendered.get("salary")
    effective_currency = rendered.get("currency") or payload.currency

    rounds = service.append_round(
        [],
        round_type=OfferRoundType.INITIAL.value,
        actor="company",
        actor_name=payload.created_by or payload.manager_name,
        actor_email=None,
        salary=effective_salary,
        bonus_pct=payload.bonus_pct,
        currency=effective_currency,
        benefits=rendered["merged_benefits"],
        message="Offer drafted",
    )

    proposal = OfferProposal(
        id=uuid.uuid4(),
        company_id=str(company_id),
        job_vacancy_id=UUID(payload.job_vacancy_id) if _looks_like_uuid(payload.job_vacancy_id) else None,
        candidate_id=UUID(payload.candidate_id) if _looks_like_uuid(payload.candidate_id) else None,
        vacancy_candidate_id=UUID(payload.vacancy_candidate_id) if _looks_like_uuid(payload.vacancy_candidate_id) else None,
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        job_title=payload.job_title,
        currency=effective_currency,
        salary=effective_salary,
        bonus_pct=payload.bonus_pct,
        bonus_target=payload.bonus_target,
        benefits=rendered["merged_benefits"],
        start_date=payload.start_date,
        response_deadline=payload.response_deadline,
        custom_clauses=rendered.get("merged_clauses") or [],
        letter_markdown=rendered["markdown"],
        letter_html=rendered["html"],
        template_version=rendered["template_version"],
        llm_provider=rendered["llm_provider"],
        llm_model=rendered["llm_model"],
        status=OfferStatus.DRAFT.value,
        current_round=1,
        rounds=rounds,
        approval_required_level=service.required_approval_level(
            salary=effective_salary, bonus_target=payload.bonus_target
        ),
        created_by=payload.created_by,
    )
    db.add(proposal)
    await db.flush()
    await db.refresh(proposal)

    await _audit_safe(
        company_id=str(company_id),
        action="offer_proposal_drafted",
        decision="drafted",
        proposal_id=str(proposal.id),
        reasoning=[
            f"Candidate: {payload.candidate_name}",
            f"Job: {payload.job_title}",
            f"Approval level: {proposal.approval_required_level}",
        ],
    )

    return OfferProposalResponse(proposal=proposal.to_dict())


@router.post("/{proposal_id}/approval", response_model=OfferProposalResponse)
async def submit_for_approval(
    proposal_id: _DualId,
    body: OfferApprovalRequestBody,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
    service: OfferLetterService = Depends(lambda: offer_letter_service),
):
    """Create the matching ApprovalRequest using the chain-by-value rule.

    When the caller does not supply an approver, the service resolves one
    from the company's active users based on the required approval level.
    """
    proposal = await _get_proposal_or_404(db, proposal_id, company_id)
    _ensure_status(proposal, {OfferStatus.DRAFT.value, OfferStatus.REJECTED.value})

    approver_name = body.approver_name
    approver_email = body.approver_email
    if not approver_email:
        resolved = await service.resolve_approver(
            db, str(company_id), proposal.approval_required_level or "manager"
        )
        if not resolved:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No approver configured for required level "
                    f"'{proposal.approval_required_level}'. Pass approver_email "
                    "explicitly or configure a company user with the matching role."
                ),
            )
        approver_name = approver_name or resolved["name"]
        approver_email = resolved["email"]

    # Linked ApprovalRequest is the source of truth for the approval gate.
    # If it cannot be created, refuse the transition — we never want a proposal
    # stuck in PENDING_APPROVAL without a backing approval row.
    try:
        from app.domains.approvals.repositories.approvals_repository import (
            ApprovalsRepository,
        )
        from lia_models.approval import ApprovalRequest, ApprovalType

        repo = ApprovalsRepository(db)
        approval = ApprovalRequest(
            id=uuid.uuid4(),
            company_id=UUID(str(company_id)) if _looks_like_uuid(str(company_id)) else None,
            request_type=ApprovalType.OFFER_APPROVAL.value,
            requester_name=body.requester_name,
            requester_email=body.requester_email,
            target_id=proposal.id,
            target_type="offer_proposal",
            target_name=f"Carta-proposta — {proposal.candidate_name} ({proposal.job_title})",
            target_description=(
                f"Salário: {proposal.currency} {proposal.salary}/mês · "
                f"Nível de aprovação: {proposal.approval_required_level}"
            ),
            target_data={
                "salary": proposal.salary,
                "currency": proposal.currency,
                "bonus_target": proposal.bonus_target,
                "approval_level": proposal.approval_required_level,
            },
            approver_name=approver_name,
            approver_email=approver_email,
            approval_level=1,
            status="pending",
            priority="high" if proposal.approval_required_level == "vp_or_cfo" else "normal",
        )
        approval = await repo.add_and_flush(approval)
        proposal.approval_request_id = approval.id

        # Notification parity with the generic /approvals create route:
        # send the approver an email so the approval queue isn't silent.
        # Best-effort: failure here must NOT roll back the approval row.
        try:
            from app.api.v1.approvals import send_approval_request_email
            from app.domains.communication.services.email_service import (
                get_email_service,
            )

            email_svc = get_email_service()
            await send_approval_request_email(db, approval, email_svc=email_svc)
            approval.email_sent = True
            approval.email_sent_at = datetime.utcnow()
        except Exception as notify_err:
            logger.warning(
                "Approver notification email failed for offer %s: %s",
                proposal.id,
                notify_err,
            )
            approval.email_sent = False
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Could not create ApprovalRequest for offer %s: %s", proposal.id, exc)
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not open the approval request — refusing to mark the "
                "proposal as pending_approval without a backing approval row."
            ),
        )

    proposal.status = OfferStatus.PENDING_APPROVAL.value
    proposal.rounds = OfferLetterService.append_round(
        proposal.rounds,
        round_type=OfferRoundType.APPROVAL.value,
        actor="approver",
        actor_name=approver_name,
        actor_email=approver_email,
        message=f"Approval request opened (level={proposal.approval_required_level})",
    )
    proposal.current_round = len(proposal.rounds)
    proposal.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(proposal)

    await _audit_safe(
        company_id=str(company_id),
        action="offer_approval_requested",
        decision="pending",
        proposal_id=str(proposal.id),
        reasoning=[f"Approver: {approver_email}", f"Level: {proposal.approval_required_level}"],
    )
    return OfferProposalResponse(proposal=proposal.to_dict())


@router.post("/{proposal_id}/approval/decision", response_model=OfferProposalResponse)
async def record_approval_decision(
    proposal_id: _DualId,
    body: OfferApprovalDecisionBody,
    company_id: str = Depends(get_verified_company_id),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
):
    """Record an approver's decision (auth-bound) and sync the ApprovalRequest.

    Authorisation rule (defense-in-depth on top of TenantGuard):
    the caller's identity (from the JWT, never from the body) must
    match the approver bound to the linked ApprovalRequest, OR the
    caller must hold an admin/owner role in the tenant. The decision
    metadata persisted on the proposal/approval row always uses the
    authenticated user's email — body-supplied identity is rejected.
    """
    proposal = await _get_proposal_or_404(db, proposal_id, company_id)
    _ensure_status(proposal, {OfferStatus.PENDING_APPROVAL.value})

    decision = (body.decision or "").strip().lower()
    if decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'")

    caller_email = (getattr(current_user, "email", None) or "").strip().lower()
    caller_role = getattr(current_user, "role", None)
    role_value = (caller_role.value if hasattr(caller_role, "value") else str(caller_role or "")).lower()
    is_admin_role = role_value in {"admin", "owner"}

    # Bind to the linked ApprovalRequest — required for audit + auth.
    if not proposal.approval_request_id:
        raise HTTPException(
            status_code=409,
            detail="Proposal has no linked approval request; cannot record a decision.",
        )

    try:
        from lia_models.approval import ApprovalRequest
    except Exception as exc:
        logger.error("ApprovalRequest model unavailable: %s", exc)
        raise HTTPException(status_code=500, detail="Approvals subsystem unavailable")

    ar_result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == proposal.approval_request_id)
    )
    approval_row = ar_result.scalar_one_or_none()
    if approval_row is None:
        raise HTTPException(
            status_code=409,
            detail="Linked approval request not found; refusing to record decision.",
        )

    expected_email = (approval_row.approver_email or "").strip().lower()
    if not caller_email or (caller_email != expected_email and not is_admin_role):
        logger.warning(
            "[OfferProposals] approval decision rejected: caller=%s expected=%s admin=%s",
            caller_email, expected_email, is_admin_role,
        )
        raise HTTPException(
            status_code=403,
            detail="Only the assigned approver (or a tenant admin) may decide this approval.",
        )

    # Canonical ApprovalRequest fields: status, resolved_at, resolved_by,
    # approval_notes (approve), rejection_reason (reject).
    approval_row.status = decision
    approval_row.resolved_at = datetime.utcnow()
    approval_row.resolved_by = caller_email
    if decision == "approved":
        approval_row.approval_notes = body.notes
    else:
        approval_row.rejection_reason = body.rejection_reason or body.notes

    proposal.status = (
        OfferStatus.APPROVED.value if decision == "approved" else OfferStatus.REJECTED.value
    )
    proposal.rounds = OfferLetterService.append_round(
        proposal.rounds,
        round_type=OfferRoundType.APPROVAL.value,
        actor="approver",
        actor_name=getattr(current_user, "name", None) or caller_email,
        actor_email=caller_email,
        message=(
            f"Approval {decision}"
            + (f": {body.notes}" if decision == "approved" and body.notes else "")
            + (
                f": {body.rejection_reason or body.notes}"
                if decision == "rejected" and (body.rejection_reason or body.notes)
                else ""
            )
        ),
    )
    proposal.current_round = len(proposal.rounds)
    proposal.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(proposal)

    await _audit_safe(
        company_id=str(company_id),
        action="offer_approval_decision",
        decision=decision,
        proposal_id=str(proposal.id),
        reasoning=[
            f"Decided by: {caller_email}",
            f"Bound approver: {expected_email}",
            f"Admin override: {is_admin_role and caller_email != expected_email}",
        ],
    )
    return OfferProposalResponse(proposal=proposal.to_dict())


@router.post("/{proposal_id}/send", response_model=OfferProposalResponse)
async def send_offer(
    proposal_id: _DualId,
    body: OfferSendRequest,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Dispatch the letter to the candidate (only when approval gate passes)."""
    proposal = await _get_proposal_or_404(db, proposal_id, company_id)

    if not _is_send_allowed(proposal):
        raise HTTPException(
            status_code=409,
            detail=(
                "Approval required before sending. Submit the proposal for approval and "
                "wait for an approved decision (only 'manager'-level offers may be sent "
                "directly from DRAFT)."
            ),
        )

    delivered = await _send_via_communication(db, proposal, body.channels, body.candidate_phone)
    if not delivered:
        raise HTTPException(
            status_code=502,
            detail=(
                "No channel could deliver the offer. Check candidate contact details "
                "and the configured email/WhatsApp providers."
            ),
        )

    proposal.status = OfferStatus.SENT.value
    proposal.sent_at = datetime.utcnow()
    proposal.sent_via = delivered
    proposal.rounds = OfferLetterService.append_round(
        proposal.rounds,
        round_type=OfferRoundType.INITIAL.value,
        actor="company",
        message=f"Letter sent via {', '.join(delivered)}",
    )
    proposal.current_round = len(proposal.rounds)
    proposal.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(proposal)

    await _audit_safe(
        company_id=str(company_id),
        action="offer_proposal_sent",
        decision="sent",
        proposal_id=str(proposal.id),
        reasoning=[f"Channels: {', '.join(delivered)}"],
    )
    return OfferProposalResponse(proposal=proposal.to_dict())


@router.post("/{proposal_id}/negotiate", response_model=OfferProposalResponse)
async def negotiate_offer(
    proposal_id: _DualId,
    body: OfferRoundRequest,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Append a counter-proposal round (from candidate or company)."""
    proposal = await _get_proposal_or_404(db, proposal_id, company_id)
    _ensure_status(
        proposal,
        {OfferStatus.SENT.value, OfferStatus.NEGOTIATING.value},
    )

    actor = body.actor if body.actor in {"candidate", "company"} else "candidate"
    round_type = (
        OfferRoundType.COUNTER_FROM_CANDIDATE.value
        if actor == "candidate"
        else OfferRoundType.COUNTER_FROM_COMPANY.value
    )
    proposal.status = OfferStatus.NEGOTIATING.value
    proposal.rounds = OfferLetterService.append_round(
        proposal.rounds,
        round_type=round_type,
        actor=actor,
        actor_name=body.actor_name,
        actor_email=body.actor_email,
        salary=body.salary,
        bonus_pct=body.bonus_pct,
        currency=proposal.currency or "BRL",
        benefits=body.benefits,
        message=body.message,
    )
    if body.salary is not None:
        proposal.salary = body.salary
    if body.bonus_pct is not None:
        proposal.bonus_pct = body.bonus_pct
    if body.benefits is not None:
        proposal.benefits = body.benefits
    proposal.current_round = len(proposal.rounds)
    proposal.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(proposal)

    await _audit_safe(
        company_id=str(company_id),
        action="offer_negotiation_round",
        decision=actor,
        proposal_id=str(proposal.id),
        reasoning=[f"Round {proposal.current_round}", f"By: {body.actor_name}"],
    )
    return OfferProposalResponse(proposal=proposal.to_dict())


@router.post("/{proposal_id}/accept", response_model=OfferProposalResponse)
async def accept_offer(
    proposal_id: _DualId,
    body: OfferRoundRequest,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Candidate accepts the offer → mark accepted and trigger E11."""
    proposal = await _get_proposal_or_404(db, proposal_id, company_id)
    _ensure_status(
        proposal,
        {OfferStatus.SENT.value, OfferStatus.NEGOTIATING.value},
    )

    proposal.status = OfferStatus.ACCEPTED.value
    proposal.accepted_at = datetime.utcnow()
    proposal.candidate_responded_at = proposal.accepted_at
    proposal.rounds = OfferLetterService.append_round(
        proposal.rounds,
        round_type=OfferRoundType.ACCEPT.value,
        actor="candidate",
        actor_name=body.actor_name,
        actor_email=body.actor_email,
        salary=proposal.salary,
        bonus_pct=proposal.bonus_pct,
        currency=proposal.currency or "BRL",
        benefits=proposal.benefits or [],
        message=body.message or "Candidate accepted the offer",
    )
    proposal.current_round = len(proposal.rounds)
    proposal.e11_triggered = await _trigger_e11(db, proposal)
    proposal.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(proposal)

    await _audit_safe(
        company_id=str(company_id),
        action="offer_proposal_accepted",
        decision="accepted",
        proposal_id=str(proposal.id),
        reasoning=[
            f"Accepted by: {body.actor_name}",
            f"E11 trigger: {'ok' if proposal.e11_triggered else 'skipped'}",
        ],
    )
    return OfferProposalResponse(proposal=proposal.to_dict())


@router.post("/{proposal_id}/decline", response_model=OfferProposalResponse)
async def decline_offer(
    proposal_id: _DualId,
    body: OfferDeclineRequest,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Candidate declines → mark declined and trigger E12 (talent pool)."""
    proposal = await _get_proposal_or_404(db, proposal_id, company_id)
    _ensure_status(
        proposal,
        {OfferStatus.SENT.value, OfferStatus.NEGOTIATING.value},
    )

    proposal.status = OfferStatus.DECLINED.value
    proposal.declined_at = datetime.utcnow()
    proposal.candidate_responded_at = proposal.declined_at
    proposal.decline_reason = body.decline_reason or body.message
    proposal.rounds = OfferLetterService.append_round(
        proposal.rounds,
        round_type=OfferRoundType.DECLINE.value,
        actor="candidate",
        actor_name=body.actor_name,
        actor_email=body.actor_email,
        message=body.decline_reason or body.message or "Candidate declined the offer",
    )
    proposal.current_round = len(proposal.rounds)
    proposal.e12_triggered = await _trigger_e12(db, proposal, proposal.decline_reason)
    proposal.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(proposal)

    await _audit_safe(
        company_id=str(company_id),
        action="offer_proposal_declined",
        decision="declined",
        proposal_id=str(proposal.id),
        reasoning=[
            f"Declined by: {body.actor_name}",
            f"Reason: {proposal.decline_reason or 'n/a'}",
            f"E12 trigger: {'ok' if proposal.e12_triggered else 'skipped'}",
        ],
    )
    return OfferProposalResponse(proposal=proposal.to_dict())


@router.post("/{proposal_id}/withdraw", response_model=OfferProposalResponse)
async def withdraw_offer(
    proposal_id: _DualId,
    body: OfferRoundRequest,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    proposal = await _get_proposal_or_404(db, proposal_id, company_id)
    _ensure_status(
        proposal,
        {
            OfferStatus.DRAFT.value,
            OfferStatus.PENDING_APPROVAL.value,
            OfferStatus.APPROVED.value,
            OfferStatus.SENT.value,
            OfferStatus.NEGOTIATING.value,
        },
    )
    proposal.status = OfferStatus.WITHDRAWN.value
    proposal.rounds = OfferLetterService.append_round(
        proposal.rounds,
        round_type=OfferRoundType.WITHDRAW.value,
        actor="company",
        actor_name=body.actor_name,
        actor_email=body.actor_email,
        message=body.message or "Offer withdrawn by company",
    )
    proposal.current_round = len(proposal.rounds)
    proposal.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(proposal)

    await _audit_safe(
        company_id=str(company_id),
        action="offer_proposal_withdrawn",
        decision="withdrawn",
        proposal_id=str(proposal.id),
        reasoning=[f"By: {body.actor_name}"],
    )
    return OfferProposalResponse(proposal=proposal.to_dict())


@router.get("/{proposal_id}", response_model=OfferProposalResponse)
async def get_offer_proposal(
    proposal_id: _DualId,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    proposal = await _get_proposal_or_404(db, proposal_id, company_id)
    return OfferProposalResponse(proposal=proposal.to_dict())


@router.get("")
async def list_offer_proposals(
    status: str | None = Query(None),
    candidate_id: str | None = Query(None),
    job_vacancy_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    query = select(OfferProposal).where(OfferProposal.company_id == str(company_id))
    if status:
        query = query.where(OfferProposal.status == status)
    if candidate_id and _looks_like_uuid(candidate_id):
        query = query.where(OfferProposal.candidate_id == UUID(candidate_id))
    if job_vacancy_id and _looks_like_uuid(job_vacancy_id):
        query = query.where(OfferProposal.job_vacancy_id == UUID(job_vacancy_id))
    # Real total comes from a separate COUNT over the filtered set,
    # so the pagination contract isn't a lie about page size.
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one() or 0

    query = query.order_by(OfferProposal.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())
    return {
        "items": [p.to_dict() for p in items],
        "total": int(total),
        "limit": limit,
        "offset": offset,
    }


_reorder_collection_before_item(router)
