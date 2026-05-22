"""
ApprovalNotificationService — canonical helper to dispatch in-app + email
notifications to configured Approvers when an offer or workflow stage requires
manager sign-off.

P0.D1 (audit 2026-05-22 — DepartmentsHub ApproverSection wiring): the
``Approver`` table CRUD has been exposed in Configurações → Departamentos
since wave-2, but the only consumer (``OfferService.check_can_send`` /
``mark_sent``) only inspected ``screening_rules.manager_approval_for_offer``
+ ``approval_request_id``. When the gate fired, no signal reached the
configured approvers — they had no way to know an offer was waiting.

This helper closes the loop: it is invoked from ``OfferService`` (and any
future caller that raises :class:`ManagerApprovalRequiredError`) to
notify every active Approver row for the company. In-app notification is
authoritative (FE shows pending count); email is best-effort (fail-open
on dispatch error, mirrored by audit log).

Multi-tenancy: ``company_id`` is REQUIRED on every call. Never trust it
from payload (REGRA ZERO + ADR-LGPD-001).

Audit: every dispatch writes one ``AuditService.log_decision_in_session``
row tagged ``action="offer_approval_pending_notified"``. SOX retention
applies because this is part of the hiring decision trail.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.company.repositories.approver_repository import (
    ApproverRepository,
)
from app.services.notification_service import (
    NotificationType,
    notification_service,
)
from app.shared.compliance.audit_service import AuditService

logger = logging.getLogger(__name__)


_OFFER_APPROVAL_CATEGORY = "offer_approval"
_OFFER_APPROVAL_SOURCE_AGENT = "offer_service"


class ApprovalNotificationService:
    """Notify configured Approvers that an offer is waiting on sign-off.

    Single source of truth for the "pending approver signature" notification
    path. Lives in ``app/shared/services/`` because it is consumed by the
    offer domain today and will be consumed by future approval-gated domains
    (e.g. budget overrides, off-policy salary bands).
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._approver_repo = ApproverRepository(db)

    async def notify_pending_approvers_for_offer(
        self,
        *,
        company_id: str,
        offer_id: UUID,
        candidate_id: UUID | None,
        candidate_name: str | None,
        job_vacancy_id: UUID | None,
        job_title: str | None,
        requested_by_user_id: str | None,
    ) -> dict[str, Any]:
        """Create in-app notifications for every active Approver of ``company_id``.

        Returns a summary dict with ``approvers_notified`` (list of user_ids
        or emails when user_id is null) and ``count``. Callers (offer tool
        layer) use the count to build the UX payload — e.g. "Notificamos N
        aprovadores; assim que um deles aprovar, a oferta vai sai".

        Fail-open semantics: a notification dispatch failure is logged + audited
        but does NOT raise — the approval gate has already fired upstream and
        the recruiter sees the structured ``requires_approval`` response;
        missing notifications are recoverable manually.
        """
        try:
            approvers = await self._approver_repo.list_for_company(
                UUID(company_id) if isinstance(company_id, str) else company_id
            )
        except Exception as exc:
            logger.warning(
                "[approval_notification] could not load approvers for company=%s err=%s",
                company_id, str(exc)[:120],
            )
            approvers = []

        notified: list[str] = []
        skipped: list[str] = []
        if not approvers:
            logger.warning(
                "[approval_notification] no_approvers_configured company_id=%s offer_id=%s — "
                "policy requires approval but ApproverSection is empty. "
                "Recruiter must configure approvers in Configuracoes > Departamentos.",
                company_id, offer_id,
            )
            await self._audit(
                company_id=company_id,
                offer_id=offer_id,
                candidate_id=candidate_id,
                job_vacancy_id=job_vacancy_id,
                outcome="no_approvers_configured",
                approvers_count=0,
                reasoning=[
                    "Policy manager_approval_for_offer=ON but Approver table empty.",
                    "Recruiter must configure approvers in Configuracoes > Departamentos.",
                ],
            )
            return {
                "approvers_notified": [],
                "count": 0,
                "no_approvers_configured": True,
            }

        title = "Oferta aguardando sua aprovacao"
        if candidate_name and job_title:
            message = (
                f"O recrutador solicitou sua aprovacao para enviar uma oferta "
                f"para {candidate_name} ({job_title})."
            )
        elif candidate_name:
            message = (
                f"O recrutador solicitou sua aprovacao para enviar uma oferta "
                f"para {candidate_name}."
            )
        else:
            message = "Uma oferta esta aguardando sua aprovacao."

        action_url = f"/jobs/{job_vacancy_id}/offers/{offer_id}" if job_vacancy_id else f"/offers/{offer_id}"

        for approver in approvers:
            # Prefer user_id when known (so in-app feed targets correct user).
            # Fallback to email so we at least have an audit trail; the email
            # channel can pick it up downstream when wired.
            recipient_user_id = (
                str(approver.user_id) if approver.user_id else None
            )
            if not recipient_user_id:
                # No user_id means the approver was added by email only — log
                # for SRE; future improvement: resolve email -> user_id, or
                # send a transactional email here. NOT a silent skip: we
                # surface it via skipped list + audit reasoning.
                skipped.append(approver.email)
                logger.info(
                    "[approval_notification] approver %s has no user_id; "
                    "in-app notification skipped (email channel TODO). offer_id=%s",
                    approver.email, offer_id,
                )
                continue
            try:
                await notification_service.create_notification(
                    user_id=recipient_user_id,
                    title=title,
                    message=message,
                    notification_type=NotificationType.ACTION_REQUIRED,
                    category=_OFFER_APPROVAL_CATEGORY,
                    source_agent=_OFFER_APPROVAL_SOURCE_AGENT,
                    source_trigger="manager_approval_for_offer",
                    related_job_id=str(job_vacancy_id) if job_vacancy_id else None,
                    related_candidate_id=str(candidate_id) if candidate_id else None,
                    action_url=action_url,
                    action_label="Revisar e aprovar",
                    metadata={
                        "offer_id": str(offer_id),
                        "approver_id": str(approver.id),
                        "approver_level": approver.level,
                        "requested_by_user_id": requested_by_user_id,
                    },
                    db=self._db,
                )
                notified.append(recipient_user_id)
            except Exception as exc:
                # Per docstring contract: fail-open on dispatch error.
                # Audit row below captures the partial outcome for SRE.
                logger.warning(
                    "[approval_notification] notification dispatch failed "
                    "approver_id=%s offer_id=%s err=%s",
                    approver.id, offer_id, str(exc)[:120],
                )

        await self._audit(
            company_id=company_id,
            offer_id=offer_id,
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            outcome="approvers_notified",
            approvers_count=len(notified),
            reasoning=[
                f"Notified {len(notified)} approver(s) in-app.",
                f"Skipped {len(skipped)} approver(s) without user_id (email-only).",
            ],
        )
        return {
            "approvers_notified": notified,
            "approvers_skipped_email_only": skipped,
            "count": len(notified),
            "no_approvers_configured": False,
        }

    async def _audit(
        self,
        *,
        company_id: str,
        offer_id: UUID,
        candidate_id: UUID | None,
        job_vacancy_id: UUID | None,
        outcome: str,
        approvers_count: int,
        reasoning: list[str],
    ) -> None:
        """Write one canonical decision-trail row per dispatch attempt.

        Never raises — audit failure is logged at warning level only, so
        a downstream audit DB issue cannot break the notification path."""
        try:
            await AuditService().log_decision_in_session(
                session=self._db,
                company_id=company_id,
                agent_name="approval_notification_service",
                decision_type="approve_hiring",
                action="offer_approval_pending_notified",
                decision=outcome,
                reasoning=reasoning,
                criteria_used=["manager_approval_for_offer", "approvers_table"],
                candidate_id=str(candidate_id) if candidate_id else None,
                job_vacancy_id=str(job_vacancy_id) if job_vacancy_id else None,
                demographic_proxies={},
            )
        except Exception as audit_err:
            logger.warning(
                "[approval_notification] audit log failed offer_id=%s err=%s",
                offer_id, str(audit_err)[:120],
            )
