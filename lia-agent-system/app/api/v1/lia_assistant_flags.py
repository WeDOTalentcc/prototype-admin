"""
LIA Assistant — Feature Flags endpoints.

Extracted from lia_assistant.py (Phase 5 decomposition).
All routes share prefix="/lia" to preserve existing /api/v1/lia/feature-flags/* URLs.
"""
from app.middleware.request_id import get_correlation_id
import logging
import uuid
from datetime import datetime as dt
from typing import Any

# Imported at module level to keep audit log path explicit; the call site
# uses uuid_uuid4 alias to avoid colliding with any local 'uuid' name.
uuid_uuid4 = uuid.uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User, UserRole
from app.core.database import get_db
from app.shared.governance.feature_flag_service import FeatureFlagService, get_feature_flag_service
from app.shared.pii_masking import mask_pii as _mask_pii  # P1-3: LGPD redaction on free-text fields
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia", tags=["lia-feature-flags"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FeatureFlagRequest(WeDoBaseModel):
    flag_key: str
    is_enabled: bool
    company_id: str | None = None
    rollout_percentage: int = 100
    description: str | None = None
    category: str | None = None
    metadata: dict[str, Any] | None = None
    expires_at: str | None = None
    created_by: str | None = None


class FeatureFlagResponse(BaseModel):
    success: bool
    flag_id: str | None = None
    flag_key: str | None = None
    is_enabled: bool | None = None
    company_id: str | None = None
    rollout_percentage: int | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# HITL gate (Sprint B P1-9, post-audit hardening)
# ---------------------------------------------------------------------------
#
# Per CLAUDE.md compliance-risk + LGPD Art. 20: 'Decisão automatizada (Art. 20)
# exige direito de revisão humana'. The audit log is forensics — it records
# what happened, not gating who can flip it.
#
# Until the full second-actor approval UI ships, sensitive flags route through
# admins (UserRole.admin). Admins ARE the human reviewer for these toggles.
# Non-admin users get HTTP 403 with a message directing them to a DPO/admin.
#
# Sensitive flag list is canonical — must include any flag whose ON state
# triggers population-level LGPD-risky behaviors (homogeneity bias, learning
# loops over candidate-derived data, etc.).
SENSITIVE_FLAGS_REQUIRING_HITL: frozenset[str] = frozenset({
    # Phase 2 / ADR-LGPD-001 — drives bigfive_department_profiles aggregation
    # over hire outcomes; homogeneity bias risk.
    "learning_loops.bigfive_department_history",
    # Phase 3 — drives wsi_question_effectiveness aggregation; bias-aware
    # ranking of behavioral questions.
    "learning_loops.wsi_question_effectiveness",
})


def _is_sensitive_flag(flag_key: str) -> bool:
    """True if the flag_key matches a sensitive flag (HITL required).

    Matches both the bare key ('learning_loops.bigfive_department_history')
    and templated forms used by policy_sync_service that prefix the
    company_id (e.g., 'company:co-A.learning_loops.bigfive_department_history').
    """
    if not flag_key:
        return False
    if flag_key in SENSITIVE_FLAGS_REQUIRING_HITL:
        return True
    # Templated forms: any sensitive key as a suffix match
    for sensitive in SENSITIVE_FLAGS_REQUIRING_HITL:
        if flag_key.endswith(sensitive):
            return True
    return False


def _enforce_hitl_gate(flag_key: str, current_user: User) -> None:
    """Raise HTTP 403 if a non-admin user tries to flip a sensitive flag.

    Admins are unaffected — they are the human reviewer per ADR-LGPD-001
    Art. 20 contract.
    """
    if not _is_sensitive_flag(flag_key):
        return
    # PERM-EXEMPT: feature flag sensitivity, context-specific
    # PERM-EXEMPT: feature flag sensitivity gate, context-specific
    if getattr(current_user, "role", None) == UserRole.admin:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            f"Flag '{flag_key}' requires DPO/admin approval (LGPD Art. 20 "
            f"human-review). Please contact your administrator to flip this "
            f"sensitive learning-loop flag."
        ),
    )


# ---------------------------------------------------------------------------
# Multi-tenancy enforcement (Sprint B P0-1, post-audit hardening)
# ---------------------------------------------------------------------------


def _enforce_flag_tenant(
    request_company_id: str | None,
    current_user: User,
) -> str | None:
    """Resolve canonical company_id for a feature-flag mutation.

    Closes the IDOR vulnerability identified by Sprint B post-implementation
    audit: previously, set_feature_flag passed `request.company_id` straight
    to ff_svc.set_flag, allowing an attacker in tenant A to flip flags in
    tenant B by spoofing the body. Per CLAUDE.md non-negotiable rule #1,
    company_id must always come from JWT/session, never trusted from the
    payload.

    Behavior:
    - Admin (UserRole.admin): pass-through. Admins manage global flags
      (company_id=None) and cross-tenant operations explicitly.
    - Non-admin: payload must either be omitted (defaults to JWT) or
      exactly match the JWT tenant; cross-tenant attempts raise 403.

    Args:
      request_company_id: company_id field from the request body.
      current_user: authenticated user from get_current_user_or_demo.

    Returns:
      The company_id to actually use in ff_svc.set_flag (None for global
      admin sets; otherwise a non-empty tenant string).

    Raises:
      HTTPException(403) when a non-admin sends a mismatched company_id.
    """
    # PERM-EXEMPT: feature flag sensitivity, context-specific
    # Admins keep their full powers (global flags + cross-tenant)
    # PERM-EXEMPT: feature flag sensitivity gate, context-specific
    if getattr(current_user, "role", None) == UserRole.admin:
        return str(request_company_id) if request_company_id else None

    jwt_company = str(get_user_company_id(current_user))
    # Non-admin: omitted body defaults to JWT
    if request_company_id is None:
        return jwt_company
    requested = str(request_company_id)
    if requested != jwt_company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="company_id does not match authenticated tenant",
        )
    return jwt_company


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/feature-flags/set", response_model=FeatureFlagResponse)
async def set_feature_flag(
    request: FeatureFlagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    ff_svc: FeatureFlagService = Depends(get_feature_flag_service),
company_id: str = Depends(require_company_id)) -> FeatureFlagResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    # P1-9: HITL gate FIRST — sensitive flags require admin/DPO. Short-
    # circuits BEFORE any DB mutation or tenant enforcement.
    _enforce_hitl_gate(request.flag_key, current_user)

    # P0-1: enforce tenant, before any DB mutation. Raises 403 on
    # non-admin cross-tenant attempts; otherwise returns the canonical
    # company_id (None allowed only for admins setting global flags).
    enforced_company_id = _enforce_flag_tenant(request.company_id, current_user)

    try:
        expires = None
        if request.expires_at:
            expires = dt.fromisoformat(request.expires_at)

        result = await ff_svc.set_flag(
            db=db,
            flag_key=request.flag_key,
            is_enabled=request.is_enabled,
            company_id=enforced_company_id,
            rollout_percentage=request.rollout_percentage,
            description=request.description,
            category=request.category,
            metadata=request.metadata,
            expires_at=expires,
            created_by=request.created_by
        )

        # Sprint B Phase 4 (gap C2): LGPD Art. 20 trail. Every feature flag
        # toggle must be logged so the regulator/recruiter can later inspect
        # who flipped what and when. Sensitive flags like
        # learning_loops.bigfive_department_history especially benefit from
        # this. Fail-soft: a missing audit row should not flip the user's
        # toggle response to failure (matches AuditService.log_action's own
        # internal try/except behavior).
        #
        # P0-1: tenant_id derived from enforced_company_id (the same canonical
        # value passed to ff_svc.set_flag), NEVER from request.company_id.
        # The original payload value is preserved in metadata for forensics.
        if result.get("success"):
            try:
                from app.shared.compliance.audit_service import AuditService
                actor_id = (
                    getattr(current_user, "id", None)
                    or getattr(current_user, "email", None)
                    or "unknown"
                )
                tenant_id = (
                    enforced_company_id
                    or getattr(current_user, "company_id", None)
                    or ""
                )
                if tenant_id:
                    await AuditService().log_action(
                        trace_id=get_correlation_id(),
                        company_id=str(tenant_id),
                        action_type="feature_flag_change",
                        actor=str(actor_id),
                        target_id=request.flag_key,
                        target_type="feature_flag",
                        metadata={
                            "flag_key": request.flag_key,
                            "is_enabled": request.is_enabled,
                            "rollout_percentage": request.rollout_percentage,
                            "category": request.category,
                            "company_id_payload": request.company_id,
                            "company_id_enforced": enforced_company_id,
                        },
                    )
            except Exception as audit_exc:
                logger.warning(
                    "[FeatureFlag] audit log failed (fail-soft) flag=%s: %s",
                    request.flag_key, str(audit_exc)[:200],
                )

        return FeatureFlagResponse(
            success=result.get("success", False),
            flag_id=result.get("flag_id"),
            flag_key=result.get("flag_key"),
            is_enabled=result.get("is_enabled"),
            company_id=result.get("company_id"),
            rollout_percentage=result.get("rollout_percentage"),
            error=result.get("error")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting feature flag: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/feature-flags", response_model=None)
async def get_feature_flags(
    company_id: str | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    ff_svc: FeatureFlagService = Depends(get_feature_flag_service),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        flags = await ff_svc.get_all_flags(
            db=db,
            company_id=company_id,
            category=category
        )
        return {
            "flags": flags,
            "total": len(flags),
            "company_id": company_id,
            "category": category
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature flags: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/feature-flags/check/{flag_key}", response_model=None)
async def check_feature_flag(
    flag_key: str,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    ff_svc: FeatureFlagService = Depends(get_feature_flag_service),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        is_enabled = await ff_svc.is_enabled(
            db=db,
            flag_key=flag_key,
            company_id=company_id
        )
        return {
            "flag_key": flag_key,
            "is_enabled": is_enabled,
            "company_id": company_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking feature flag: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Phase B (post-Sprint-B): second-actor approval workflow for sensitive flags
# ---------------------------------------------------------------------------
#
# The P1-9 HITL gate above (set_feature_flag) returns 403 to non-admin users
# attempting to flip flags in SENSITIVE_FLAGS_REQUIRING_HITL. That gate
# remains as the immediate fallback. Phase B adds a parallel path where the
# non-admin user can REQUEST a toggle, an admin/DPO reviews + approves, and
# the system commits the toggle on their behalf.
#
# Reuses canonical ApprovalRequest infrastructure (lia_models/approval.py +
# ApprovalsRepository + EmailService). No new tables, no migration.
#
# Decisions Paulo 2026-05-10: B1 7-day expiry hardcoded, B2 email-only,
# B3 self-approval hard-block, B4 broadcast to all admins, B5 forever
# retention.


_APPROVAL_EXPIRY_DAYS = 7


class FeatureFlagToggleRequest(WeDoBaseModel):
    """Body for POST /lia/feature-flags/request-toggle.

    Non-admins use this when the direct /feature-flags/set path is
    blocked by the P1-9 HITL gate. Admins/DPOs receive an email and
    review via /pending-approvals + /approve.
    """
    flag_key: str = Field(..., min_length=1)
    requested_value: bool
    rollout_percentage: int = Field(100, ge=0, le=100)
    category: str | None = None
    justification: str | None = Field(
        None, description="Optional rationale shown to the approver",
    )


class FeatureFlagToggleApprovalResponse(BaseModel):
    request_id: str
    status: str
    flag_key: str
    requested_value: bool
    expires_at: str | None = None


class FeatureFlagToggleRejectRequest(WeDoBaseModel):
    """Body for POST /lia/feature-flags/reject/{request_id}.

    Admin/DPO denies a pending toggle with an explanatory reason that
    becomes part of the LGPD Art. 20 forensic trail. Reason is stored
    on approval.rejection_reason and surfaced in the result email.
    """
    rejection_reason: str = Field(
        ..., min_length=1,
        description="Required explanation for the rejection (forensic trail)",
    )


def _build_approvals_repo(db: AsyncSession):
    """Lazy import + builder so the module-level imports don't pull
    approvals into every consumer of feature-flag endpoints."""
    from app.repositories.approvals_repository import (
        ApprovalsRepository,
    )
    return ApprovalsRepository(db)


async def _send_approval_request_email(*, db, approval) -> None:
    """Phase B B2: notify when a sensitive flag toggle request is created.

    P0-B fix (post-audit): the canonical sender is a MODULE-LEVEL
    function in app.api.v1.approvals, not a method on EmailService. The
    previous getattr(EmailService(), 'send_approval_request_email', None)
    returned None and silently skipped notifications. Delegating to the
    canonical sender keeps a single source of truth for the email
    template + provider plumbing.

    Broadcast caveat (B4): approval.approver_email is "" placeholder
    today, so the canonical sender will currently no-op at the
    `_send_email_provider(to_email='')` step. Real broadcast (resolve
    all admins) is a follow-up. Until then this records the intent +
    audit trail; emails resume the moment broadcast resolution lands.

    Fail-soft: never raises.
    """
    try:
        from app.api.v1.approvals import send_approval_request_email
        await send_approval_request_email(db, approval)
    except Exception as exc:
        logger.warning(
            "[FeatureFlagApproval] approval request email failed (fail-soft): %s",
            str(exc)[:200],
        )


async def _send_approval_result_email(*, db, approval, approved: bool) -> None:
    """Notify requester after admin approves/rejects. Fail-soft.

    P0-B fix: delegates to canonical module-level
    app.api.v1.approvals.send_approval_result_email. The requester_email
    is set on the approval row, so this path delivers correctly.
    """
    try:
        from app.api.v1.approvals import send_approval_result_email
        await send_approval_result_email(db, approval, approved=approved)
    except Exception as exc:
        logger.warning(
            "[FeatureFlagApproval] approval result email failed (fail-soft): %s",
            str(exc)[:200],
        )


@router.post(
    "/feature-flags/request-toggle",
    response_model=FeatureFlagToggleApprovalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_feature_flag_toggle(
    request: FeatureFlagToggleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)) -> FeatureFlagToggleApprovalResponse:
    """Phase B: non-admin requests a toggle for a sensitive flag.

    Flow:
    1. Reject if flag is not in SENSITIVE_FLAGS_REQUIRING_HITL — direct
       /feature-flags/set is the right path for those.
    2. Multi-tenancy: company_id derived from current_user (never payload).
    3. Persist ApprovalRequest with request_type=feature_flag_toggle and
       target_data carrying flag_key + requested_value + rollout_percentage.
    4. Send notification email to admins (fail-soft).
    5. Audit log via canonical action_type=feature_flag_change with
       metadata.workflow_state=request_created.
    """
    if not _is_sensitive_flag(request.flag_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Flag '{request.flag_key}' is not sensitive — use "
                f"/feature-flags/set directly. The approval workflow is "
                f"reserved for SENSITIVE_FLAGS_REQUIRING_HITL."
            ),
        )

    company_id = str(get_user_company_id(current_user))
    requester_id = getattr(current_user, "id", None) or "unknown"
    requester_email = getattr(current_user, "email", "") or ""
    requester_name = (
        getattr(current_user, "first_name", None)
        or getattr(current_user, "email", None)
        or "Recruiter"
    )

    from app.models.approval import ApprovalRequest, ApprovalStatus, ApprovalType
    from datetime import datetime as _dt, timedelta as _td

    # P0-A fix (post-audit): approver_name/approver_email are NOT NULL on
    # ApprovalRequest. Decision B4 (broadcast — no specific approver) needs
    # placeholder values that PG accepts AND remain readable in admin UI.
    # P0-A` fix: target_id is UUID(as_uuid=True); flag_key is a free-text
    # string and lives in target_data. Pass target_id=None.

    # P1-DPO: Look up company DPO from DPORegistry so approval emails go to
    # the right person (LGPD Art. 41 — DPO must be notified of sensitive
    # automated-decision requests). Falls back to empty string if company
    # hasn't configured a DPO yet (backwards-compatible, fail-open).
    _dpo_email = ""
    _dpo_name = "Pending DPO Approval"
    try:
        from app.domains.lgpd.repositories.lgpd_repository import LgpdRepository
        _lgpd_repo = LgpdRepository(db)
        _dpo_record = await _lgpd_repo.get_dpo_by_company(
            uuid.UUID(str(company_id)) if company_id else None
        )
        if _dpo_record is not None:
            _dpo_email = _dpo_record.dpo_email or ""
            _dpo_name = _dpo_record.dpo_name or "DPO"
    except Exception:
        pass  # fail-open: missing DPO registry never blocks feature request

    approval = ApprovalRequest(
        company_id=company_id,
        request_type=ApprovalType.FEATURE_FLAG_TOGGLE.value,
        requester_id=getattr(current_user, "id", None),  # UUID-native, not str()
        requester_name=str(requester_name),
        requester_email=str(requester_email),
        # P0-A: NOT NULL columns must be populated even in broadcast flow
        # P1-DPO: resolved from DPORegistry when company has one configured
        approver_name=_dpo_name,
        approver_email=_dpo_email,  # real DPO email when configured
        target_id=None,  # P0-A`: column is UUID; flag_key kept in target_data only
        target_type="feature_flag",
        target_name=request.flag_key,
        # P1-3: LGPD Art.11 — redact PII from free-text justification (stored forever per B5)
        target_description=_mask_pii(request.justification) if request.justification else request.justification,
        target_data={
            "flag_key": request.flag_key,
            "requested_value": request.requested_value,
            "rollout_percentage": request.rollout_percentage,
            "category": request.category,
            "company_id_enforced": company_id,
        },
        status=ApprovalStatus.PENDING.value,
        expires_at=_dt.utcnow() + _td(days=_APPROVAL_EXPIRY_DAYS),
    )
    repo = _build_approvals_repo(db)

    # P1-1 idempotency: 409 when same (company_id, flag_key, requester_id)
    # already has a PENDING request. Prevents audit log bloat + UX confusion.
    existing = await repo.find_pending_duplicate(
        company_id=company_id,
        flag_key=request.flag_key,
        requester_id=getattr(current_user, 'id', None),
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A pending approval for flag '{request.flag_key}' already "
                f"exists (id={existing.id}). Wait for admin resolution."
            ),
        )

    await repo.add_and_flush(approval)

    # Fail-soft email + audit (LGPD Art. 20 trail)
    await _send_approval_request_email(db=db, approval=approval)
    try:
        from app.shared.compliance.audit_service import AuditService
        await AuditService().log_action(
            trace_id=get_correlation_id(),
            company_id=company_id,
            action_type="feature_flag_change",
            actor=str(requester_id),
            target_id=request.flag_key,
            target_type="feature_flag",
            metadata={
                "workflow_state": "request_created",
                "approval_request_id": str(approval.id),
                "flag_key": request.flag_key,
                "requested_value": request.requested_value,
                "category": request.category,
            },
        )
    except Exception as audit_exc:
        logger.warning(
            "[FeatureFlagApproval] audit on request_created failed (fail-soft): %s",
            str(audit_exc)[:200],
        )

    return FeatureFlagToggleApprovalResponse(
        request_id=str(approval.id),
        status=approval.status,
        flag_key=request.flag_key,
        requested_value=request.requested_value,
        expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
    )


@router.get("/feature-flags/pending-approvals", response_model=None)
async def list_pending_feature_flag_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # PERM-EXEMPT: feature flag sensitivity, context-specific
    """Admin-only: list pending feature_flag_toggle approval requests
    for the user's company. Non-admin returns 403."""
    # PERM-EXEMPT: feature flag sensitivity gate, context-specific
    if getattr(current_user, "role", None) != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin role required to view pending feature flag approvals",
        )

    company_id = str(get_user_company_id(current_user))
    repo = _build_approvals_repo(db)
    pending = await repo.list_pending_by_company(
        company_id=company_id,
        request_type="feature_flag_toggle",
    )
    return {
        "items": [
            {
                "request_id": str(p.id),
                "flag_key": (p.target_data or {}).get("flag_key"),
                "requested_value": (p.target_data or {}).get("requested_value"),
                "requester_email": p.requester_email,
                "requester_name": p.requester_name,
                "justification": p.target_description,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "expires_at": p.expires_at.isoformat() if p.expires_at else None,
            }
            for p in pending
        ],
        "total": len(pending),
    }


@router.post(
    "/feature-flags/approve/{request_id}",
    response_model=FeatureFlagToggleApprovalResponse,
)
async def approve_feature_flag_toggle(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    ff_svc: FeatureFlagService = Depends(get_feature_flag_service),
company_id: str = Depends(require_company_id)) -> FeatureFlagToggleApprovalResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Phase B: admin approves a pending feature flag toggle request.

    Guards (in order):
    1. Admin role required.
    2. Self-approval blocked (current_user.id != approval.requester_id).
    3. Approval must be in pending state.

    On approve: invokes ff_svc.set_flag with admin context (bypassing
    # PERM-EXEMPT: feature flag sensitivity, context-specific
    HITL) using the payload stored in target_data. Status flips to
    approved. Audit + email notify.
    """
    # PERM-EXEMPT: feature flag sensitivity gate, context-specific
    if getattr(current_user, "role", None) != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin role required to approve feature flag toggles",
        )

    repo = _build_approvals_repo(db)
    approval = await repo.get_by_id(request_id)
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="approval request not found",
        )

    # Self-approval block
    if str(getattr(approval, "requester_id", "")) == str(getattr(current_user, "id", "")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "self-approval not allowed — the approver must differ from "
                "the requester (second-actor invariant)"
            ),
        )

    if approval.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"approval is already {approval.status}; cannot approve again",
        )

    payload = approval.target_data or {}
    flag_key = payload.get("flag_key")
    requested_value = payload.get("requested_value")
    if flag_key is None or requested_value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="approval target_data missing flag_key or requested_value",
        )

    # Commit the toggle via canonical set_flag with admin company context
    try:
        await ff_svc.set_flag(
            db=db,
            flag_key=str(flag_key),
            is_enabled=bool(requested_value),
            company_id=payload.get("company_id_enforced") or str(approval.company_id),
            rollout_percentage=int(payload.get("rollout_percentage") or 100),
            description=None,
            category=payload.get("category"),
            metadata={"approval_request_id": str(approval.id)},
            expires_at=None,
            created_by=f"approval:{getattr(current_user, 'id', 'admin')}",
        )
    except Exception as set_exc:
        logger.error(
            "[FeatureFlagApproval] set_flag failed during approve: %s",
            str(set_exc)[:200],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"approval recorded but set_flag failed: {set_exc}",
        )

    from datetime import datetime as _dt
    approval.status = "approved"
    approval.resolved_at = _dt.utcnow()
    approval.resolved_by = str(getattr(current_user, "id", "")) or None

    await _send_approval_result_email(db=db, approval=approval, approved=True)
    try:
        from app.shared.compliance.audit_service import AuditService
        await AuditService().log_action(
            trace_id=get_correlation_id(),
            company_id=str(approval.company_id),
            action_type="feature_flag_change",
            actor=str(getattr(current_user, "id", "admin")),
            target_id=str(flag_key),
            target_type="feature_flag",
            metadata={
                "workflow_state": "approved",
                "approval_request_id": str(approval.id),
                "flag_key": str(flag_key),
                "requested_value": bool(requested_value),
                "approver_id": str(getattr(current_user, "id", "")),
                "requester_id": str(getattr(approval, "requester_id", "")),
            },
        )
    except Exception as audit_exc:
        logger.warning(
            "[FeatureFlagApproval] audit on approve failed (fail-soft): %s",
            str(audit_exc)[:200],
        )

    return FeatureFlagToggleApprovalResponse(
        request_id=str(approval.id),
        status=approval.status,
        flag_key=str(flag_key),
        requested_value=bool(requested_value),
        expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
    )


@router.post(
    "/feature-flags/reject/{request_id}",
    response_model=FeatureFlagToggleApprovalResponse,
)
async def reject_feature_flag_toggle(
    request_id: str,
    request: FeatureFlagToggleRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    ff_svc: FeatureFlagService = Depends(get_feature_flag_service),
company_id: str = Depends(require_company_id)) -> FeatureFlagToggleApprovalResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Phase B: admin rejects a pending feature flag toggle request.

    Mirrors approve_feature_flag_toggle's guards:
    1. Admin role required
    2. Self-rejection blocked
    3. Approval must be in pending state (else 409)

    # PERM-EXEMPT: feature flag sensitivity, context-specific
    On reject: status flips to rejected, rejection_reason persisted,
    audit log fires workflow_state=rejected, requester emailed (fail-soft).
    ff_svc.set_flag is NEVER called.
    """
    # PERM-EXEMPT: feature flag sensitivity gate, context-specific
    if getattr(current_user, "role", None) != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin role required to reject feature flag toggles",
        )

    repo = _build_approvals_repo(db)
    approval = await repo.get_by_id(request_id)
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="approval request not found",
        )

    if str(getattr(approval, "requester_id", "")) == str(getattr(current_user, "id", "")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "self-rejection not allowed — the rejector must differ "
                "from the requester (second-actor invariant)"
            ),
        )

    if approval.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"approval is already {approval.status}; cannot reject",
        )

    from datetime import datetime as _dt

    approval.status = "rejected"
    approval.rejection_reason = request.rejection_reason
    approval.resolved_at = _dt.utcnow()
    approval.resolved_by = str(getattr(current_user, "id", "")) or None

    await _send_approval_result_email(db=db, approval=approval, approved=False)

    payload = approval.target_data or {}
    flag_key = payload.get("flag_key")
    try:
        from app.shared.compliance.audit_service import AuditService
        await AuditService().log_action(
            trace_id=get_correlation_id(),
            company_id=str(approval.company_id),
            action_type="feature_flag_change",
            actor=str(getattr(current_user, "id", "admin")),
            target_id=str(flag_key) if flag_key else None,
            target_type="feature_flag",
            metadata={
                "workflow_state": "rejected",
                "approval_request_id": str(approval.id),
                "flag_key": flag_key,
                "requested_value": payload.get("requested_value"),
                "rejector_id": str(getattr(current_user, "id", "")),
                "requester_id": str(getattr(approval, "requester_id", "")),
                "rejection_reason": request.rejection_reason,
            },
        )
    except Exception as audit_exc:
        logger.warning(
            "[FeatureFlagApproval] audit on reject failed (fail-soft): %s",
            str(audit_exc)[:200],
        )

    return FeatureFlagToggleApprovalResponse(
        request_id=str(approval.id),
        status=approval.status,
        flag_key=str(flag_key) if flag_key else "",
        requested_value=bool(payload.get("requested_value", False)),
        expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
    )


async def sweep_expired_approvals(
    *,
    db: AsyncSession,
    company_id: str,
) -> int:
    """Phase B B1: cancel pending feature_flag_toggle requests past expires_at.

    Cron-friendly helper. Runs against ApprovalsRepository's
    list_pending_by_company filtered by request_type='feature_flag_toggle'
    (canonical filter added in the repo bug fix). Iterates pending rows,
    flips status to 'cancelled' when expires_at < utcnow, leaves fresh
    and no-expiry rows alone.

    Returns the count of cancelled rows. Audit log entry per cancelled
    row (workflow_state=expired). No email — auto-cancellation isn't a
    human decision.

    Multi-tenancy: company_id required from caller (cron job typically
    iterates per-company).
    """
    from datetime import datetime as _dt
    if not company_id:
        return 0

    repo = _build_approvals_repo(db)
    pending = await repo.list_pending_by_company(
        company_id=company_id,
        request_type="feature_flag_toggle",
    )
    now = _dt.utcnow()
    cancelled = 0
    for approval in pending:
        expires_at = getattr(approval, "expires_at", None)
        if expires_at is None or expires_at >= now:
            continue
        approval.status = "cancelled"
        approval.resolved_at = now
        approval.resolved_by = "system:expiry_sweep"
        cancelled += 1

        # Forensic audit per cancellation (LGPD Art. 20 trail)
        try:
            from app.shared.compliance.audit_service import AuditService
            payload = approval.target_data or {}
            await AuditService().log_action(
                trace_id=get_correlation_id(),
                company_id=str(company_id),
                action_type="feature_flag_change",
                actor="system:expiry_sweep",
                target_id=str(payload.get("flag_key")) if payload.get("flag_key") else None,
                target_type="feature_flag",
                metadata={
                    "workflow_state": "expired",
                    "approval_request_id": str(approval.id),
                    "flag_key": payload.get("flag_key"),
                    "requested_value": payload.get("requested_value"),
                    "expires_at": expires_at.isoformat(),
                    "cancelled_at": now.isoformat(),
                },
            )
        except Exception as audit_exc:
            logger.warning(
                "[FeatureFlagApproval] audit on expiry sweep failed "
                "(fail-soft) approval=%s: %s",
                approval.id, str(audit_exc)[:200],
            )

    if cancelled:
        logger.info(
            "[FeatureFlagApproval] expiry sweep cancelled %d row(s) for "
            "company=%s",
            cancelled, company_id,
        )
    return cancelled
