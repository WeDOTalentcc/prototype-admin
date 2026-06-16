"""Tool: prepare_offer_manual_send — pre-fill template for manual send via SendEmailModal."""
import logging
from typing import Any
from uuid import UUID

from app.domains.base import DomainContext

logger = logging.getLogger(__name__)


async def run(params: dict[str, Any], context: DomainContext) -> dict[str, Any]:
    try:
        company_id = context.tenant_id or context.metadata.get("company_id", "")
        offer_id = UUID(str(params["offer_id"]))

        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            from app.domains.offer.services.offer_service import OfferService
            from sqlalchemy import select
            from lia_models.email_template import EmailTemplate

            svc = OfferService(db)
            draft = await svc.get_draft(offer_id, company_id)
            if not draft:
                return {"success": False, "error": "Proposta nao encontrada"}

            variables = svc.render_offer_template_variables(draft)

            # Find template
            result = await db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.situation == "proposta",
                    EmailTemplate.is_active == True,
                ).limit(1)
            )
            template = result.scalar_one_or_none()

            subject = "Carta Oferta — {job_title}".format(**variables)
            body_html = "<p>Prezado(a) {candidate_name},</p>".format(**variables)
            template_id = None

            if template:
                subject = template.subject or subject
                body_html = template.body_html or body_html
                template_id = template.id
                for k, v in variables.items():
                    body_html = body_html.replace("{{" + k + "}}", v)
                    subject = subject.replace("{{" + k + "}}", v)

        return {
            "success": True,
            "offer_id": str(offer_id),
            "template_id": str(template_id) if template_id else None,
            "subject_pre_filled": subject,
            "body_pre_filled": body_html,
            "variables": variables,
            "message": "Template preparado para envio manual",
            "ui_action": "open_send_email_modal",
            "ui_action_params": {
                "template_id": str(template_id) if template_id else None,
                "subject_override": subject,
                "body_override": body_html,
                "recipient_email": variables.get("candidate_email", ""),
                "recipient_name": variables.get("candidate_name", ""),
                "offer_id": str(offer_id),
            },
        }
    except Exception as exc:
        logger.error("[OFFER-TOOL] prepare_offer_manual_send failed: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc)}
