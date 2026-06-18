"""Tool: send_offer — send auto via email template tpl-offer-sent."""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domains.base import DomainContext

logger = logging.getLogger(__name__)

_OFFER_TEMPLATE_SLUG = "tpl-offer-sent"


async def run(params: dict[str, Any], context: DomainContext) -> dict[str, Any]:
    try:
        company_id = context.tenant_id or context.metadata.get("company_id", "")
        user_id = context.user_id or ""
        offer_id = UUID(str(params["offer_id"]))
        send_mode = params.get("send_mode", "auto")

        from app.core.database import AsyncSessionLocal
        # P0-2 + P1-9 policy gates (audit 2026-05-21): import the parent
        # exception class so we can catch the whole family in one block and
        # discriminate via ``.reason`` to surface the right next-action UI
        # (request_offer_approval, schedule_more_interviews, ...).
        from app.domains.offer.services.offer_service import (
            OfferPolicyGateError,
            OfferService,
        )
        async with AsyncSessionLocal() as db:
            svc = OfferService(db)
            draft = await svc.get_draft(offer_id, company_id)
            if not draft:
                return {"success": False, "error": "Proposta nao encontrada"}
            if draft.status != "draft":
                return {"success": False, "error": f"Proposta ja esta em status '{draft.status}'"}

            # P0-2 + P1-9 pre-flight gates: refuse to dispatch the email if
            # any company hiring policy gate refuses this send. Runs BEFORE
            # side effects so the candidate never receives a draft that the
            # policy did not authorize. The gate family is unified under
            # OfferPolicyGateError; we discriminate via .reason to route the
            # recruiter to the correct next action.
            try:
                await svc.check_can_send(offer_id, company_id)
            except OfferPolicyGateError as gate_exc:
                ui_action_by_reason = {
                    "manager_approval_required": "request_offer_approval",
                    "min_interviews_not_met": "schedule_more_interviews",
                }
                logger.info(
                    "[OFFER-TOOL] send_offer blocked pre-flight. reason=%s "
                    "offer_id=%s company_id=%s",
                    gate_exc.reason, offer_id, company_id,
                )
                return {
                    "success": False,
                    "error": str(gate_exc),
                    "requires_approval": gate_exc.reason == "manager_approval_required",
                    "policy_gate": gate_exc.reason,
                    "ui_action": ui_action_by_reason.get(gate_exc.reason, "open_offer_review"),
                    "ui_action_params": {"modal_id": "offer_approval", "offer_id": str(offer_id)},
                }

            variables = svc.render_offer_template_variables(draft)
            email_log_id, delivery_ok = await _send_via_provider(
                company_id=company_id,
                recipient_email=variables["candidate_email"],
                candidate_name=variables["candidate_name"],
                template_slug=_OFFER_TEMPLATE_SLUG,
                variables=variables,
                context=context,
                db=db,
                draft=draft,
            )
            if not delivery_ok:
                return {
                    "success": False,
                    "error": "Falha no envio do email. A proposta foi mantida como rascunho.",
                    "delivery_failed": True,
                    "email_log_id": str(email_log_id) if email_log_id else None,
                }

            try:
                updated = await svc.mark_sent(
                    offer_id, company_id, user_id, send_mode, email_log_id
                )
            except OfferPolicyGateError as gate_exc:
                # Roll back: the email was already dispatched in the lines
                # above. The send is recorded in the EmailLog but the offer
                # status stays "draft" — recruiter must request manager
                # approval before retrying. Tradeoff acknowledged: in the
                # rare race where the policy was toggled ON between draft
                # creation and send, the candidate receives the offer email
                # but the offer remains "draft" in the system. Sentry
                # logging surfaces this so ops can decide whether to recall.
                logger.warning(
                    "[OFFER-TOOL] send_offer blocked by manager-approval gate "
                    "AFTER email dispatched. offer_id=%s company_id=%s",
                    offer_id, company_id,
                )
                return {
                    "success": False,
                    "error": str(gate_exc),
                    "requires_approval": True,
                    "ui_action": "open_modal",
                    "ui_action_params": {"offer_id": str(offer_id)},
                }
            await db.commit()

        return {
            "success": True,
            "offer_id": str(offer_id),
            "status": "sent",
            "email_log_id": str(email_log_id) if email_log_id else None,
            "sent_at": datetime.utcnow().isoformat(),
            "message": f"Proposta enviada para {variables['candidate_name']}",
            "offer_link": variables.get("offer_link", ""),
        }
    except Exception as exc:
        logger.error("[OFFER-TOOL] send_offer failed: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc)}


async def _send_via_provider(
    company_id: str,
    recipient_email: str,
    candidate_name: str,
    template_slug: str,
    variables: dict[str, str],
    context: DomainContext,
    db,
    draft,
) -> tuple["UUID | None", bool]:
    from sqlalchemy import select
    from lia_models.email_template import EmailTemplate, EmailLog

    # Find the offer template
    result = await db.execute(
        select(EmailTemplate).where(
            EmailTemplate.situation == "proposta",
            EmailTemplate.is_active == True,
        ).limit(1)
    )
    template = result.scalar_one_or_none()

    subject = "Carta Oferta — {job_title}".format(**variables)
    body_html = "<p>Prezado(a) {candidate_name},</p>".format(**variables)

    if template:
        subject = template.subject or subject
        body_html = template.body_html or body_html
        # Interpolate variables
        for k, v in variables.items():
            body_html = body_html.replace("{{" + k + "}}", v)
            subject = subject.replace("{{" + k + "}}", v)
        # Sprint F.4 #42 canonical-remap: canonical OfferProposal has no
        # ``template_id`` (UUID FK); it has ``template_version`` (VARCHAR(32)).
        # We stringify the UUID so the offer still records WHICH template was
        # used. A future migration could add a proper template_id FK or move
        # to a versioned-template lookup table.
        # TODO Sprint F.4 #42: canonical-remap — replace with template.version if EmailTemplate gains one.
        draft.template_version = str(template.id)

    if not recipient_email:
        logger.warning("[OFFER-TOOL] No recipient email for candidate %s", draft.candidate_id)
        return None, False

    delivery_ok = True
    try:
        from app.domains.communication.services.email_providers import get_email_provider
        provider = get_email_provider()
        await provider.send_email(
            to=recipient_email,
            subject=subject,
            html=body_html,
        )
    except Exception as exc:
        logger.warning("[OFFER-TOOL] Email provider failed: %s", exc)
        delivery_ok = False

    # Create audit log entry
    log_entry = EmailLog(
        template_id=template.id if template else None,
        candidate_id=draft.candidate_id,
        recipient_email=recipient_email,
        subject=subject,
        body_html=body_html,
        status="sent" if delivery_ok else "failed",
        sent_at=datetime.utcnow(),
        variables_used=variables,
        created_by=context.user_id,
    )
    db.add(log_entry)
    await db.flush()
    return log_entry.id, delivery_ok
