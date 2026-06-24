"""
Approval Trigger Service — canonical producer for vacancy approval flow.

Single source of truth for stamping approval_requested_at on a JobVacancy
and creating the corresponding ApprovalRequest rows.

Harness classification:
  Guide (computacional): UNICO servico autorizado a setar job.approval_requested_at
  + criar ApprovalRequest de tipo VACANCY_APPROVAL.
  Sensor: test_approval_trigger_p0_gates.py (5 contract tests).

Ponto de chamada:
  - Wizard: tool request_business_approval em wizard_tool_registry.py
  - Manual: endpoint POST /job-vacancies/{id}/request-approval em lifecycle.py

Principios (REGRA #0 + CLAUDE.md canonical-fix):
  1. Falhar alto, nunca silenciosamente.
  2. Fix no produtor — esta funcao E o produtor.
  3. Idempotente — chamada dupla nao cria duplicata.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.company.repositories.approver_repository import ApproverRepository
from app.repositories.approvals_repository import ApprovalsRepository
from lia_models.approval import ApprovalRequest, ApprovalStatus, ApprovalType

logger = logging.getLogger(__name__)

DEFAULT_APPROVAL_DEADLINE_DAYS = 7


class ApprovalPendingError(Exception):
    """Raised by assert_can_publish when vacancy has a pending approval request."""

    def __init__(self, approver_name: str, approver_email: str) -> None:
        self.approver_name = approver_name
        self.approver_email = approver_email
        super().__init__(
            f"Vaga aguardando aprovacao de {approver_name} ({approver_email}). "
            "Aprovacao necessaria antes de publicar."
        )


async def trigger_approval_if_required(
    job: object,
    *,
    requested_by_name: str,
    requested_by_email: str,
    db: AsyncSession,
) -> list[ApprovalRequest]:
    """
    Create ApprovalRequest rows for a vacancy and stamp approval_requested_at.

    Idempotent: if approval already pending for this vacancy, returns [].
    No-op: if company has no approvers configured, returns [].

    Sends email only to level-1 approver; fails gracefully on email error
    (approval rows are created regardless).

    Multi-tenancy: company_id comes from job.company_id (JWT-derived at
    creation — never from request payload per REGRA ZERO multi-tenancy).
    """
    company_id = job.company_id
    job_id = str(job.id)

    approver_repo = ApproverRepository(db)
    approvers = await approver_repo.list_for_company(UUID(str(company_id)))
    if not approvers:
        logger.info(
            "[approval_trigger] no approvers configured company_id=%s job_id=%s — noop",
            company_id,
            job_id,
        )
        return []

    approvals_repo = ApprovalsRepository(db)
    existing = await approvals_repo.get_pending_by_target(
        target_id=UUID(str(job.id)),
        request_type=ApprovalType.VACANCY_APPROVAL.value,
    )
    if existing:
        logger.info(
            "[approval_trigger] approval already pending job_id=%s — noop (idempotent)",
            job_id,
        )
        return []

    now = datetime.utcnow()
    job.approval_requested_at = now
    job.approval_requested_by = requested_by_email
    job.approval_status = "pendente"

    deadline = now + timedelta(days=DEFAULT_APPROVAL_DEADLINE_DAYS)
    created: list[ApprovalRequest] = []
    for approver in approvers:
        # Sprint 2: TIPO B (email_link) gets a cryptographic magic token for link-based approval.
        # TIPO A (platform) has user_id → logs in and approves via UI (no magic token).
        approver_method = getattr(approver, "approval_method", "email_link") or "email_link"
        token = None
        token_expires = None
        if approver_method == "email_link":
            token = secrets.token_urlsafe(32)
            token_expires = deadline  # same 7-day window as approval deadline

        req = ApprovalRequest(
            company_id=company_id,
            request_type=ApprovalType.VACANCY_APPROVAL.value,
            requester_name=requested_by_name,
            requester_email=requested_by_email,
            target_id=job.id,
            target_type="job_vacancy",
            target_name=getattr(job, "title", "") or "",
            approver_id=getattr(approver, "user_id", None),
            approver_name=approver.user_name,
            approver_email=approver.email,
            approval_level=approver.level,
            status=ApprovalStatus.PENDING.value,
            expires_at=deadline,
            magic_token=token,
            magic_token_expires_at=token_expires,
            magic_token_used=False,
        )
        created_req = await approvals_repo.add_and_flush(req)
        created.append(created_req)

    await db.flush()

    logger.info(
        "[approval_trigger] created %d ApprovalRequest(s) job_id=%s company_id=%s",
        len(created),
        job_id,
        company_id,
    )

    # Sprint 2: LGPD Art.37V audit trail for approval request
    try:
        from app.shared.compliance.audit_service import AuditService
        audit = AuditService(db)
        await audit.log_action(
            trace_id=f"approval-trigger-{job_id}",
            company_id=str(company_id),
            action_type="approval_requested",
            actor=requested_by_email,
            target_id=str(job.id),
            target_type="job_vacancy",
            metadata={
                "approvers_count": len(created),
                "approval_level_range": f"1-{max(a.level for a in approvers)}",
                "requested_by_name": requested_by_name,
                "job_title": getattr(job, "title", "") or "",
            },
        )
    except Exception as audit_exc:
        logger.warning("[approval_trigger] audit log failed — non-blocking. err=%s", audit_exc)

    # Send email to first (level-1) approver using canonical email function
    first_created = created[0] if created else None
    try:
        if first_created:
            from app.api.v1.approvals import send_approval_request_email

            # For TIPO B (email_link): append magic link to the email body via target_description
            first_method = getattr(approvers[0], "approval_method", "email_link") or "email_link"
            if first_method == "email_link" and first_created.magic_token:
                try:
                    from app.core.config import settings
                    base_url = getattr(settings, "FRONTEND_BASE_URL", "https://app.wedotalent.cc")
                except Exception:
                    base_url = "https://app.wedotalent.cc"
                magic_link = f"{base_url}/approve/{first_created.magic_token}"
                # Store magic link in target_description for email function to pick up
                first_created.target_description = (
                    f"Link para aprovar/rejeitar (válido por {DEFAULT_APPROVAL_DEADLINE_DAYS} dias):\n"
                    f"{magic_link}"
                )
            await send_approval_request_email(db, first_created)
    except Exception as exc:
        logger.warning(
            "[approval_trigger] email send failed — approval rows created, email skipped. err=%s",
            exc,
        )

    return created


async def assert_can_publish(job: object, *, db: AsyncSession) -> None:
    """
    Gate: raise ApprovalPendingError if the vacancy has a pending approval.

    Call BEFORE any publish side effects. Multi-tenancy safe: reads only
    from ApprovalRequest filtered by target_id (job-scoped).
    """
    if not getattr(job, "approval_requested_at", None):
        return
    if (getattr(job, "approval_status", "") or "").lower() != "pendente":
        return

    approvals_repo = ApprovalsRepository(db)
    pending = await approvals_repo.get_pending_by_target(
        target_id=UUID(str(job.id)),
        request_type=ApprovalType.VACANCY_APPROVAL.value,
    )
    if not pending:
        return

    raise ApprovalPendingError(
        approver_name=pending[0].approver_name,
        approver_email=pending[0].approver_email,
    )
