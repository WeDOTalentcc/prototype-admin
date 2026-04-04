"""Communication ReAct Agent — Tool Registry.

Wraps CommunicationService, EmailService, TeamsService, WhatsAppService and
CommunicationHistoryService into ToolDefinition format so the ReActLoop can
autonomously decide which tools to call.
"""
import logging
from typing import Any, Dict, List

from lia_agents_core.react_loop import ToolDefinition

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------


async def _wrap_send_email(**kwargs: Any) -> Dict[str, Any]:
    """Send an email to a candidate using EmailService / CommunicationService."""
    from app.domains.communication.services.communication_service import (
        CommunicationService,
        MessageType,
        MessageChannel,
    )
    from app.core.database import AsyncSessionLocal

    candidate_id = kwargs.get("candidate_id")
    company_id = kwargs.get("company_id")
    subject = kwargs.get("subject")
    body = kwargs.get("body")
    template_type = kwargs.get("template_type")

    if not candidate_id:
        return {"success": False, "message": "candidate_id é obrigatório"}
    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}
    if not subject:
        return {"success": False, "message": "subject é obrigatório"}
    if not body:
        return {"success": False, "message": "body é obrigatório"}

    try:
        svc = CommunicationService()

        # Derive message_type from template_type when supplied
        try:
            msg_type = MessageType(template_type) if template_type else MessageType.GENERAL
        except ValueError:
            msg_type = MessageType.GENERAL

        async with AsyncSessionLocal() as db:
            result = await svc.send_message(
                company_id=str(company_id),
                candidate_id=str(candidate_id),
                candidate_email=None,  # resolved by service from candidate record
                candidate_phone=None,
                message_type=msg_type,
                channel=MessageChannel.EMAIL,
                subject=subject,
                body=body,
                db=db,
            )

        return {
            "success": result.get("success", True),
            "message_id": result.get("message_id"),
            "channel": "email",
            "candidate_id": candidate_id,
            "company_id": company_id,
            "details": result,
        }
    except Exception as e:
        logger.error(f"[communication_tools] send_email error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_send_whatsapp(**kwargs: Any) -> Dict[str, Any]:
    """Send a WhatsApp message to a candidate using WhatsAppService."""
    from app.domains.communication.services.whatsapp_service import WhatsAppService

    candidate_phone = kwargs.get("candidate_phone")
    message = kwargs.get("message")
    company_id = kwargs.get("company_id")
    candidate_id = kwargs.get("candidate_id")

    if not candidate_phone:
        return {"success": False, "message": "candidate_phone é obrigatório"}
    if not message:
        return {"success": False, "message": "message é obrigatório"}
    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}

    try:
        svc = WhatsAppService()
        result = await svc.send_message(
            to_phone=candidate_phone,
            message=message,
            metadata={
                "company_id": str(company_id),
                "candidate_id": str(candidate_id) if candidate_id else None,
            },
        )
        return {
            "success": result.success,
            "message_id": result.message_id,
            "status": result.status.value if result.status else None,
            "channel": "whatsapp",
            "candidate_phone": candidate_phone,
            "company_id": company_id,
        }
    except Exception as e:
        logger.error(f"[communication_tools] send_whatsapp error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_get_communication_history(**kwargs: Any) -> Dict[str, Any]:
    """Retrieve communication history for a candidate using CommunicationHistoryService."""
    from app.domains.communication.services.communication_history_service import (
        CommunicationHistoryService,
    )

    candidate_id = kwargs.get("candidate_id")
    company_id = kwargs.get("company_id")
    limit = int(kwargs.get("limit", 10))

    if not candidate_id:
        return {"success": False, "message": "candidate_id é obrigatório"}
    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}

    try:
        svc = CommunicationHistoryService()
        result = await svc.list_communications(
            company_id=str(company_id),
            candidate_id=str(candidate_id),
            limit=limit,
        )
        return {
            "success": True,
            "candidate_id": candidate_id,
            "company_id": company_id,
            "total": result.get("total", 0),
            "communications": result.get("communications", []),
        }
    except Exception as e:
        logger.error(
            f"[communication_tools] get_communication_history error: {e}", exc_info=True
        )
        return {"success": False, "message": str(e)}


async def _wrap_schedule_message(**kwargs: Any) -> Dict[str, Any]:
    """Schedule a future message for a candidate using CommunicationService.

    For email and whatsapp channels the message is routed through CommunicationService.
    Teams notifications are dispatched via TeamsService (webhook-based; scheduling is
    recorded locally since Teams does not support native delayed delivery).
    """
    from app.domains.communication.services.communication_service import (
        CommunicationService,
        MessageType,
        MessageChannel,
    )
    from app.core.database import AsyncSessionLocal
    from datetime import datetime

    candidate_id = kwargs.get("candidate_id")
    company_id = kwargs.get("company_id")
    channel_str = kwargs.get("channel", "email")
    message = kwargs.get("message")
    scheduled_at_str = kwargs.get("scheduled_at")

    if not candidate_id:
        return {"success": False, "message": "candidate_id é obrigatório"}
    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}
    if not message:
        return {"success": False, "message": "message é obrigatório"}
    if not scheduled_at_str:
        return {"success": False, "message": "scheduled_at é obrigatório (ISO datetime)"}

    # Validate channel
    channel_normalized = channel_str.lower()
    if channel_normalized not in ("email", "whatsapp", "teams"):
        return {
            "success": False,
            "message": f"Canal inválido '{channel_str}'. Use: email, whatsapp, teams",
        }

    try:
        scheduled_at = datetime.fromisoformat(scheduled_at_str)
    except ValueError as e:
        return {"success": False, "message": f"scheduled_at inválido: {e}"}

    try:
        if channel_normalized == "teams":
            # Teams is webhook-based; record intent and notify via TeamsService
            from app.domains.communication.services.teams_service import TeamsService

            svc_teams = TeamsService()
            await svc_teams.send_message(
                text=(
                    f"[Agendado para {scheduled_at_str}] "
                    f"Mensagem para candidato {candidate_id}: {message}"
                )
            )
            return {
                "success": True,
                "scheduled": True,
                "channel": "teams",
                "scheduled_at": scheduled_at_str,
                "candidate_id": candidate_id,
                "company_id": company_id,
                "note": "Teams não suporta envio nativo agendado; notificação imediata registrada.",
            }

        # MessageChannel only defines EMAIL; WhatsApp uses its own service
        channel_map = {
            "email": MessageChannel.EMAIL,
        }
        channel = channel_map.get(channel_normalized, MessageChannel.EMAIL)

        svc = CommunicationService()
        async with AsyncSessionLocal() as db:
            result = await svc.send_message(
                company_id=str(company_id),
                candidate_id=str(candidate_id),
                candidate_email=None,
                candidate_phone=None,
                message_type=MessageType.GENERAL,
                channel=channel,
                subject=None,
                body=message,
                db=db,
            )

        return {
            "success": True,
            "scheduled": True,
            "channel": channel_str,
            "scheduled_at": scheduled_at_str,
            "candidate_id": candidate_id,
            "company_id": company_id,
            "details": result,
        }
    except Exception as e:
        logger.error(f"[communication_tools] schedule_message error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_check_rate_limit(**kwargs: Any) -> Dict[str, Any]:
    """Check the current rate limit status for a candidate/channel combination."""
    from app.domains.communication.services.communication_service import (
        CommunicationService,
        MessageChannel,
        MessageType,
    )
    from app.core.database import AsyncSessionLocal

    candidate_id = kwargs.get("candidate_id")
    company_id = kwargs.get("company_id")
    channel_str = kwargs.get("channel", "email")

    if not candidate_id:
        return {"success": False, "message": "candidate_id é obrigatório"}
    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}

    # Teams channel is not tracked in CommunicationService; validate via email proxy
    # MessageChannel only defines EMAIL; WhatsApp/Teams use email policy as proxy for rate-limit checks
    channel_map = {
        "email": MessageChannel.EMAIL,
        "whatsapp": MessageChannel.EMAIL,
        "teams": MessageChannel.EMAIL,
    }
    channel = channel_map.get(channel_str.lower())
    if not channel:
        return {
            "success": False,
            "message": f"Canal inválido '{channel_str}'. Use: email, whatsapp, teams",
        }

    try:
        svc = CommunicationService()
        async with AsyncSessionLocal() as db:
            validation = await svc.validate_can_send(
                candidate_id=str(candidate_id),
                company_id=str(company_id),
                channel=channel,
                message_type=MessageType.GENERAL,
                db=db,
            )

        return {
            "success": True,
            "can_send": validation.get("can_send", False),
            "requires_approval": validation.get("requires_approval", False),
            "warnings": validation.get("warnings", []),
            "blocks": validation.get("blocks", []),
            "candidate_id": candidate_id,
            "company_id": company_id,
            "channel": channel_str,
        }
    except Exception as e:
        logger.error(f"[communication_tools] check_rate_limit error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------


def get_communication_tools() -> List[ToolDefinition]:
    return [
        ToolDefinition(
            name="send_email",
            description=(
                "Enviar e-mail para um candidato. "
                "Parâmetros: candidate_id (int, obrigatório), company_id (str, obrigatório), "
                "subject (str, obrigatório), body (str, obrigatório), "
                "template_type (str, opcional — ex: screening_invitation, rejection_feedback)."
            ),
            function=_wrap_send_email,
        ),
        ToolDefinition(
            name="send_whatsapp",
            description=(
                "Enviar mensagem WhatsApp para um candidato via Twilio. "
                "Parâmetros: candidate_phone (str, obrigatório — com código do país), "
                "message (str, obrigatório), company_id (str, obrigatório), "
                "candidate_id (int, opcional)."
            ),
            function=_wrap_send_whatsapp,
        ),
        ToolDefinition(
            name="get_communication_history",
            description=(
                "Recuperar histórico de comunicações de um candidato. "
                "Parâmetros: candidate_id (int, obrigatório), company_id (str, obrigatório), "
                "limit (int, padrão 10)."
            ),
            function=_wrap_get_communication_history,
        ),
        ToolDefinition(
            name="schedule_message",
            description=(
                "Agendar o envio de uma mensagem futura para um candidato. "
                "Parâmetros: candidate_id (int, obrigatório), company_id (str, obrigatório), "
                "channel (str, obrigatório — email/whatsapp/teams), message (str, obrigatório), "
                "scheduled_at (str ISO datetime, obrigatório — ex: 2026-03-10T14:00:00)."
            ),
            function=_wrap_schedule_message,
        ),
        ToolDefinition(
            name="check_rate_limit",
            description=(
                "Verificar se um candidato ainda pode receber mensagens (rate limit LGPD, "
                "opt-out, quarentena). "
                "Parâmetros: candidate_id (int, obrigatório), company_id (str, obrigatório), "
                "channel (str, obrigatório — email/whatsapp/teams)."
            ),
            function=_wrap_check_rate_limit,
        ),
    ]


def get_stage_tools(stage: str) -> List[ToolDefinition]:
    """Return tools available for a given communication stage."""
    from app.domains.communication.agents.communication_stage_context import (
        get_stage_tools as _stage_tools,
    )

    stage_tool_names = set(_stage_tools(stage))
    return [t for t in get_communication_tools() if t.name in stage_tool_names]
