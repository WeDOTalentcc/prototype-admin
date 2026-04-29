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
        async with AsyncSessionLocal() as db:
            from app.domains.offer.services.offer_service import OfferService
            svc = OfferService(db)
            draft = await svc.get_draft(offer_id, company_id)
            if not draft:
                return {"success": False, "error": "Proposta nao encontrada"}
            if draft.status != "draft":
                return {"success": False, "error": f"Proposta ja esta em status '{draft.status}'"}

            variables = svc.render_offer_template_variables(draft)
            email_log_id = await _send_via_provider(
                company_id=company_id,
                recipient_email=variables["candidate_email"],
                candidate_name=variables["candidate_name"],
                template_slug=_OFFER_TEMPLATE_SLUG,
                variables=variables,
                context=context,
                db=db,
                draft=draft,
            )

            updated = await svc.mark_sent(
                offer_id, company_id, user_id, send_mode, email_log_id
            )
            await db.commit()

        return {
            "success": True,
            "offer_id": str(offer_id),
            "status": "sent",
            "email_log_id": str(email_log_id) if email_log_id else None,
            "sent_at": datetime.utcnow().isoformat(),
            "message": f"Proposta enviada para {variables['candidate_name']}",
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
) -> UUID | None:
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
        draft.template_id = template.id

    if not recipient_email:
        logger.warning("[OFFER-TOOL] No recipient email for candidate %s", draft.candidate_id)
        return None

    try:
        from app.domains.communication.services.email_providers import get_email_provider
        provider = get_email_provider()
        await provider.send_email(
            to=recipient_email,
            subject=subject,
            html=body_html,
        )
    except Exception as exc:
        logger.warning("[OFFER-TOOL] Email provider failed: %s — logging anyway", exc)

    # Create audit log entry
    log_entry = EmailLog(
        template_id=template.id if template else None,
        candidate_id=draft.candidate_id,
        recipient_email=recipient_email,
        subject=subject,
        body_html=body_html,
        status="sent",
        sent_at=datetime.utcnow(),
        variables_used=variables,
        created_by=context.user_id,
    )
    db.add(log_entry)
    await db.flush()
    return log_entry.id
