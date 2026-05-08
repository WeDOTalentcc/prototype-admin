"""
Template Service — resolves and renders communication templates.

Extracted from CommunicationService to isolate template engine responsibilities:
- Maps MessageType → template situation strings
- Looks up active EmailTemplate records from the database
- Renders templates with variable substitution via EmailService.render_template
- Integrates with A/B testing and template learning services

Consumers should call ``render_message_template()`` to get a rendered
(subject, body_text, body_html) triple without any sending or approval logic.
"""
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.repositories.email_template_repository import EmailTemplateRepository

from app.enums.communication import ABTestName, MESSAGE_TYPE_TO_SITUATION, MessageChannel, MessageType
from app.templates.communication_templates import EmailTemplates, WhatsAppTemplates

logger = logging.getLogger(__name__)

_EMAIL_TEMPLATE_MAP: dict[MessageType, Any] = {
    MessageType.SCREENING_REMINDER: EmailTemplates.screening_reminder,
    MessageType.SCREENING_PASSED: EmailTemplates.screening_passed,
    MessageType.INTERVIEW_SCHEDULED: EmailTemplates.interview_scheduled,
    MessageType.PROCESS_CLOSED: EmailTemplates.process_closed,
}

_WHATSAPP_TEMPLATE_MAP: dict[MessageType, Any] = {
    MessageType.SCREENING_REMINDER: WhatsAppTemplates.screening_reminder,
    MessageType.SCREENING_PASSED: WhatsAppTemplates.screening_passed,
    MessageType.INTERVIEW_SCHEDULED: WhatsAppTemplates.interview_scheduled,
    MessageType.INTERVIEW_REMINDER: WhatsAppTemplates.interview_reminder,
    MessageType.PROCESS_CLOSED: WhatsAppTemplates.process_closed,
}

_AB_TEST_MAP: dict[MessageType, ABTestName] = {
    MessageType.SCREENING_INVITATION: ABTestName.SCREENING_INVITE,
    MessageType.SCREENING_REMINDER: ABTestName.FOLLOW_UP_REMINDER,
    MessageType.REJECTION_FEEDBACK: ABTestName.FEEDBACK_REJECTION,
}


def get_email_template_func(message_type: MessageType):
    """Return the static email template callable for a given message type, or None."""
    return _EMAIL_TEMPLATE_MAP.get(message_type)


def get_whatsapp_template_func(message_type: MessageType):
    """Return the static WhatsApp template callable for a given message type, or None."""
    return _WHATSAPP_TEMPLATE_MAP.get(message_type)


async def resolve_db_template(
    db: AsyncSession,
    message_type: MessageType,
    channel: MessageChannel,
    company_id: str,
    candidate_id: str,
) -> tuple[Any, str | None]:
    """
    Look up an active EmailTemplate from the database for the given message type and channel.

    Applies template-learning recommendation and A/B variant selection when available.

    Returns:
        (template_orm_object | None, ab_variant_prompt | None)
    """
    from lia_models.email_template import EmailTemplate

    situation = MESSAGE_TYPE_TO_SITUATION.get(message_type)
    if not situation:
        logger.warning("No situation mapping for message_type: %s", message_type)
        return None, None

    recommended_template_id = None
    try:
        from app.shared.intelligence.template_learning.template_learning_service import (
            template_learning_service,
        )
        recommended_template_id = await template_learning_service.recommend_template(
            db=db,
            company_id=company_id,
            context={"message_type": message_type.value, "situation": situation},
            fallback_template_id=None,
        )
    except Exception as exc:
        logger.debug("[TemplateLearning] recommend skipped: %s", exc)

    ab_variant_prompt: str | None = None
    ab_test_name = _AB_TEST_MAP.get(message_type)
    if ab_test_name:
        try:
            from app.shared.learning.ab_testing_service import ABTestingService
            ab_svc = ABTestingService()
            ab_variant_info = await ab_svc.get_variant(
                test_name=ab_test_name,
                session_id=candidate_id,
                db=db,
            )
            if ab_variant_info and ab_variant_info.get("prompt_template"):
                ab_variant_prompt = ab_variant_info["prompt_template"]
        except Exception as exc:
            logger.debug("[ABTesting] variant lookup skipped: %s", exc)

    repo = EmailTemplateRepository(db)
    template = None
    if recommended_template_id:
        template = await repo.get_active_by_id(recommended_template_id)
        if not template:
            recommended_template_id = None

    if not template:
        template = await repo.find_active_by_situation_channel(
            situation=situation, channel=channel.value
        )

    return template, ab_variant_prompt


async def render_message_template(
    db: AsyncSession,
    message_type: MessageType,
    channel: MessageChannel,
    company_id: str,
    candidate_id: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    """
    Resolve and render a communication template.

    Returns a dict with keys:
        success (bool)
        subject (str | None)
        body_text (str)
        body_html (str)
        template_name (str | None)
        template_situation (str | None)
        error (str | None) — only on failure

    Callers are responsible for the actual send + approval logic.
    """
    from app.domains.communication.services.email_service import email_service

    template, ab_variant_prompt = await resolve_db_template(
        db=db,
        message_type=message_type,
        channel=channel,
        company_id=company_id,
        candidate_id=candidate_id,
    )

    if not template:
        situation = MESSAGE_TYPE_TO_SITUATION.get(message_type, "<unknown>")
        logger.warning(
            "Template not found: situation='%s', channel=%s", situation, channel.value
        )
        return {
            "success": False,
            "error": "template_not_found",
            "message": f"Template não encontrado (situation='{situation}', channel='{channel.value}')",
        }

    subject, _ = email_service.render_template(
        str(template.subject) if template.subject else "", variables
    )
    body_html, _ = email_service.render_template(
        str(template.body_html) if template.body_html else "", variables
    )
    body_text, _ = email_service.render_template(
        str(template.body_text) if template.body_text else "", variables
    )

    if ab_variant_prompt:
        try:
            ab_body, _ = email_service.render_template(ab_variant_prompt, variables)
            body_text = ab_body
            body_html = ab_body.replace("\n", "<br>")
        except Exception as exc:
            logger.debug("[ABTesting] Variant render failed, using default: %s", exc)

    return {
        "success": True,
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "template_name": template.name,
        "template_id": str(template.id) if hasattr(template, "id") else template.name,
        "template_situation": MESSAGE_TYPE_TO_SITUATION.get(message_type),
    }
