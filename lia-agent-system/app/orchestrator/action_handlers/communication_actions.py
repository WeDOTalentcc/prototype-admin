"""
Communication Actions — closed-loop communication and scheduling actions.

Handles: send_email, schedule_interview, create_generic_event
"""
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


async def execute_communication_action(
    action_id: str,
    params: dict[str, Any],
    context: dict[str, Any],
):
    """Route communication actions to specific handler."""
    if action_id == "send_email":
        return await _send_email(params, context)
    elif action_id == "schedule_interview":
        return await _schedule_interview(params, context)
    elif action_id == "create_generic_event":
        return await _create_generic_event(params, context)
    return None


async def _send_email(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        import html as html_module

        from app.domains.communication.services.email_providers import get_email_provider

        provider = get_email_provider()
        status = provider.get_status()
        if status.get("configured") and status.get("healthy"):
            candidate_name = params.get("candidate_name", "")
            to_email = params.get("email", params.get("candidate_email", ""))
            subject = params.get("subject", "")
            body = params.get("body", "")
            if to_email and subject:
                safe_body = html_module.escape(body)
                result = await provider.send_email(
                    to=to_email,
                    subject=subject,
                    html_content=f"<p>{safe_body}</p>",
                    text_content=body,
                )
                if result.success:
                    return ActionResult(
                        status="executed",
                        message=f'Email enviado para **{candidate_name}** com assunto "{subject}".',
                        data={
                            "candidate_id": params.get("candidate_id", ""),
                            "candidate_name": candidate_name,
                            "subject": subject,
                            "to_email": to_email,
                            "message_id": result.message_id,
                            "sent_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                            "provider": result.provider,
                        },
                        action_type="send_email",
                    )
    except Exception as e:
        logger.warning(f"Direct email sending failed, falling back to domain: {e}")
    return None


async def _schedule_interview(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        import uuid as uuid_mod

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            interview_id = str(uuid_mod.uuid4())
            candidate_name = params.get("candidate_name", "")
            dt = params.get("datetime", "")
            interviewer = params.get("interviewer", "")
            candidate_id = params.get("candidate_id", "")

            await db.execute(text("""
                INSERT INTO interviews (id, candidate_id, interviewer_name, start_time, status, created_at, updated_at)
                VALUES (:id, CAST(:candidate_id AS uuid), :interviewer, :start_time, 'scheduled', NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {
                "id": interview_id,
                "candidate_id": candidate_id,
                "start_time": dt,
                "interviewer": interviewer,
            })
            await db.commit()

            return ActionResult(
                status="executed",
                message=f"Entrevista agendada com **{candidate_name}** para **{dt}**.",
                data={
                    "interview_id": interview_id,
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "datetime": dt,
                    "interviewer": interviewer,
                    "scheduled_at": datetime.utcnow().isoformat(),
                    "simulated": False,
                },
                action_type="schedule_interview",
            )
    except Exception as e:
        logger.warning(f"Direct scheduling failed, falling back to domain: {e}")
    return None


async def _create_generic_event(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.domains.interview_scheduling.services.calendar_service import calendar_service

        title = params.get("title", "")
        dt_str = params.get("datetime", "")
        description = params.get("description", "")
        location = params.get("location", "")
        duration = params.get("duration_minutes", 60)
        user_id = context.get("user_id") if context else None

        if not user_id:
            return ActionResult(
                status="error",
                message="Usuário não identificado para criar o compromisso.",
                action_type="create_generic_event",
            )

        event_data = await calendar_service.create_generic_event(
            title=title,
            start_time=dt_str,
            organizer_id=user_id,
            description=description,
            location=location,
            duration_minutes=int(duration) if duration else 60,
        )

        return ActionResult(
            status="executed",
            message=f"Compromisso **\"{title}\"** registrado para **{dt_str}**.",
            data={**event_data, "simulated": False},
            action_type="create_generic_event",
        )
    except Exception as e:
        logger.warning(f"create_generic_event failed: {e}")
        return ActionResult(
            status="error",
            message="Não foi possível criar o compromisso. Tente novamente.",
            error_detail=str(e),
            action_type="create_generic_event",
        )
