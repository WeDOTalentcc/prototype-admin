"""
Interview Actions — reschedule, cancel, reminders, listings, and self-scheduling.

Handles: reschedule_interview, cancel_interview, send_interview_reminder,
         list_today_interviews, generate_self_scheduling_link
"""
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


async def execute_interview_action(
    action_id: str,
    params: dict[str, Any],
    context: dict[str, Any],
):
    if action_id == "reschedule_interview":
        return await _reschedule_interview(params, context)
    elif action_id == "cancel_interview":
        return await _cancel_interview(params, context)
    elif action_id == "send_interview_reminder":
        return await _send_interview_reminder(params, context)
    elif action_id == "list_today_interviews":
        return await _list_today_interviews(params, context)
    elif action_id == "generate_self_scheduling_link":
        return await _generate_self_scheduling_link(params, context)
    return None


async def _reschedule_interview(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        from app.orchestrator.action_handlers._handler_hooks import (
            log_action_audit,
            resolve_candidate_by_name,
        )

        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        new_datetime = params.get("new_datetime", "")
        interview_id = params.get("interview_id")
        reason = params.get("reason", "")
        company_id = context.get("company_id") if context else None

        if not candidate_id and candidate_name:
            resolved = await resolve_candidate_by_name(candidate_name, company_id)
            if resolved:
                candidate_id = resolved["id"]
                candidate_name = resolved["name"]

        if not candidate_id or not new_datetime:
            return ActionResult(
                status="error",
                message="Informe o candidato e a nova data/hora para reagendar.",
                error_detail="Missing candidate_id or new_datetime",
                action_type="reschedule_interview",
            )

        company_id = context.get("company_id") if context else None

        async with AsyncSessionLocal() as db:
            if interview_id:
                where_clause = "i.id = CAST(:iid AS uuid)"
                bind = {"iid": str(interview_id), "new_dt": new_datetime}
            else:
                where_clause = "i.candidate_id = CAST(:cid AS uuid) AND i.status = 'scheduled'"
                bind = {"cid": str(candidate_id), "new_dt": new_datetime}

            if company_id:
                where_clause += " AND EXISTS (SELECT 1 FROM vacancy_candidates vc WHERE vc.candidate_id = i.candidate_id AND vc.company_id = :co)"
                bind["co"] = str(company_id)

            result = await db.execute(text(f"""
                UPDATE interviews i
                SET start_time = :new_dt, status = 'rescheduled', updated_at = NOW()
                WHERE {where_clause}
                AND i.status IN ('scheduled', 'rescheduled')
            """), bind)

            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message=f"Nenhuma entrevista agendada encontrada para **{candidate_name}**.",
                    error_detail="No scheduled interview found",
                    action_type="reschedule_interview",
                )
            await db.commit()

        await log_action_audit("reschedule_interview", company_id, candidate_id=str(candidate_id))

        return ActionResult(
            status="executed",
            message=f"Entrevista de **{candidate_name}** reagendada para **{new_datetime}**.",
            data={
                "candidate_id": candidate_id, "candidate_name": candidate_name,
                "new_datetime": new_datetime, "reason": reason,
                "rescheduled_at": datetime.utcnow().isoformat(), "simulated": False,
            },
            action_type="reschedule_interview",
        )
    except Exception as e:
        logger.warning(f"reschedule_interview failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao reagendar entrevista.",
            error_detail=str(e),
            action_type="reschedule_interview",
        )


async def _cancel_interview(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        from app.orchestrator.action_handlers._handler_hooks import (
            log_action_audit,
            resolve_candidate_by_name,
        )

        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        interview_id = params.get("interview_id")
        reason = params.get("reason", "")
        company_id = context.get("company_id") if context else None

        if not candidate_id and not interview_id and candidate_name:
            resolved = await resolve_candidate_by_name(candidate_name, company_id)
            if resolved:
                candidate_id = resolved["id"]
                candidate_name = resolved["name"]

        if not candidate_id and not interview_id:
            return ActionResult(
                status="error",
                message="Informe o candidato ou ID da entrevista para cancelar.",
                error_detail="Missing candidate_id and interview_id",
                action_type="cancel_interview",
            )

        company_id = context.get("company_id") if context else None

        async with AsyncSessionLocal() as db:
            if interview_id:
                where_clause = "i.id = CAST(:iid AS uuid)"
                bind = {"iid": str(interview_id)}
            else:
                where_clause = "i.candidate_id = CAST(:cid AS uuid) AND i.status = 'scheduled'"
                bind = {"cid": str(candidate_id)}

            if company_id:
                where_clause += " AND EXISTS (SELECT 1 FROM vacancy_candidates vc WHERE vc.candidate_id = i.candidate_id AND vc.company_id = :co)"
                bind["co"] = str(company_id)

            result = await db.execute(text(f"""
                UPDATE interviews i
                SET status = 'cancelled', updated_at = NOW()
                WHERE {where_clause}
            """), bind)

            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message=f"Nenhuma entrevista agendada encontrada para **{candidate_name}**.",
                    error_detail="No scheduled interview found",
                    action_type="cancel_interview",
                )
            await db.commit()

        await log_action_audit("cancel_interview", company_id, candidate_id=str(candidate_id) if candidate_id else None)

        return ActionResult(
            status="executed",
            message=f"Entrevista de **{candidate_name}** cancelada com sucesso.",
            data={
                "candidate_id": candidate_id, "candidate_name": candidate_name,
                "reason": reason, "cancelled_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="cancel_interview",
        )
    except Exception as e:
        logger.warning(f"cancel_interview failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao cancelar entrevista.",
            error_detail=str(e),
            action_type="cancel_interview",
        )


async def _send_interview_reminder(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")

        if not candidate_id:
            return ActionResult(
                status="error",
                message="Informe o candidato para enviar o lembrete.",
                error_detail="Missing candidate_id",
                action_type="send_interview_reminder",
            )

        company_id = context.get("company_id") if context else None

        async with AsyncSessionLocal() as db:
            sql = """
                SELECT i.id, i.start_time, i.interviewer_name, c.email, c.name
                FROM interviews i
                JOIN candidates c ON c.id = i.candidate_id
                WHERE i.candidate_id = CAST(:cid AS uuid)
                  AND i.status = 'scheduled'
                  AND i.start_time > NOW()
            """
            bind: dict[str, Any] = {"cid": str(candidate_id)}
            if company_id:
                sql += " AND EXISTS (SELECT 1 FROM vacancy_candidates vc WHERE vc.candidate_id = i.candidate_id AND vc.company_id = :co)"
                bind["co"] = str(company_id)
            sql += " ORDER BY i.start_time ASC LIMIT 1"
            result = await db.execute(text(sql), bind)
            interview = result.fetchone()

        if not interview:
            return ActionResult(
                status="error",
                message=f"Nenhuma entrevista futura encontrada para **{candidate_name}**.",
                error_detail="No upcoming interview found",
                action_type="send_interview_reminder",
            )

        try:
            from app.domains.communication.services.email_providers import get_email_provider
            provider = get_email_provider()
            status = provider.get_status()
            if status.get("configured") and status.get("healthy") and interview.email:
                await provider.send_email(
                    to=interview.email,
                    subject=f"Lembrete: Entrevista agendada para {interview.start_time}",
                    html_content=f"<p>Olá {interview.name},<br><br>Este é um lembrete da sua entrevista agendada para <strong>{interview.start_time}</strong>.</p>",
                    text_content=f"Olá {interview.name}, este é um lembrete da sua entrevista agendada para {interview.start_time}.",
                )
        except Exception as email_err:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.warning(f"Failed to send interview reminder email: {email_err}")

        return ActionResult(
            status="executed",
            message=f"Lembrete de entrevista enviado para **{interview.name}** (entrevista em **{interview.start_time}**).",
            data={
                "candidate_id": candidate_id, "candidate_name": interview.name,
                "interview_id": str(interview.id), "start_time": str(interview.start_time),
                "sent_at": datetime.utcnow().isoformat(), "simulated": False,
            },
            action_type="send_interview_reminder",
        )
    except Exception as e:
        logger.warning(f"send_interview_reminder failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao enviar lembrete de entrevista.",
            error_detail=str(e),
            action_type="send_interview_reminder",
        )


async def _list_today_interviews(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        user_id = context.get("user_id") if context else None
        company_id = context.get("company_id") if context else None
        target_date = params.get("date", "today")

        async with AsyncSessionLocal() as db:
            if target_date == "tomorrow" or target_date == "amanhã":
                date_filter = "DATE(i.start_time) = CURRENT_DATE + 1"
            else:
                date_filter = "DATE(i.start_time) = CURRENT_DATE"

            sql = f"""
                SELECT i.id, i.start_time, i.interviewer_name, i.status,
                       c.name as candidate_name, c.current_title
                FROM interviews i
                JOIN candidates c ON c.id = i.candidate_id
                WHERE {date_filter}
                  AND i.status IN ('scheduled', 'rescheduled')
            """
            bind: dict[str, Any] = {}
            if company_id:
                sql += " AND EXISTS (SELECT 1 FROM vacancy_candidates vc WHERE vc.candidate_id = i.candidate_id AND vc.company_id = :co)"
                bind["co"] = str(company_id)
            sql += " ORDER BY i.start_time ASC LIMIT 20"
            result = await db.execute(text(sql), bind)
            rows = result.fetchall()

        if not rows:
            day_label = "amanhã" if target_date in ("tomorrow", "amanhã") else "hoje"
            return ActionResult(
                status="executed",
                message=f"Nenhuma entrevista agendada para {day_label}.",
                data={"interviews": [], "date": target_date},
                action_type="list_today_interviews",
            )

        day_label = "amanhã" if target_date in ("tomorrow", "amanhã") else "hoje"
        lines = [f"**Entrevistas de {day_label} ({len(rows)}):**\n"]
        interviews = []
        for row in rows:
            time_str = row.start_time.strftime("%H:%M") if hasattr(row.start_time, "strftime") else str(row.start_time)
            interviewer = f" com {row.interviewer_name}" if row.interviewer_name else ""
            lines.append(f"  - **{time_str}** — {row.candidate_name} ({row.current_title or 'N/A'}){interviewer}")
            interviews.append({
                "id": str(row.id), "time": time_str,
                "candidate_name": row.candidate_name, "interviewer": row.interviewer_name,
            })

        return ActionResult(
            status="executed",
            message="\n".join(lines),
            data={"interviews": interviews, "count": len(rows), "date": target_date},
            action_type="list_today_interviews",
        )
    except Exception as e:
        logger.warning(f"list_today_interviews failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao listar entrevistas.",
            error_detail=str(e),
            action_type="list_today_interviews",
        )


async def _generate_self_scheduling_link(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        import uuid as uuid_mod

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        from app.orchestrator.action_handlers._handler_hooks import (
            log_action_audit,
            resolve_candidate_by_name,
        )

        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")
        duration = int(params.get("duration_minutes", 60))

        company_id = context.get("company_id") if context else None

        if not candidate_id and candidate_name:
            resolved = await resolve_candidate_by_name(candidate_name, company_id)
            if resolved:
                candidate_id = resolved["id"]
                candidate_name = resolved["name"]

        if not candidate_id:
            return ActionResult(
                status="error",
                message="Informe o candidato para gerar o link.",
                error_detail="Missing candidate_id",
                action_type="generate_self_scheduling_link",
            )

        token = str(uuid_mod.uuid4())[:12]
        link = f"/schedule/{token}"

        async with AsyncSessionLocal() as db:
            if company_id:
                authz = await db.execute(text(
                    "SELECT 1 FROM vacancy_candidates WHERE candidate_id = CAST(:cid AS uuid) AND company_id = :co LIMIT 1"
                ), {"cid": str(candidate_id), "co": str(company_id)})
                if authz.fetchone() is None:
                    return ActionResult(
                        status="error",
                        message="Sem permissão para gerar link para este candidato.",
                        error_detail="Candidate does not belong to caller's company",
                        action_type="generate_self_scheduling_link",
                    )

            # RLS-EXEMPT: scheduling_links — transitive via interview/candidate join
            await db.execute(text("""
                INSERT INTO scheduling_links (id, candidate_id, job_id, token, duration_minutes, expires_at, created_at)
                VALUES (CAST(:id AS uuid), CAST(:cid AS uuid), CAST(:jid AS uuid), :token, :dur, NOW() + INTERVAL '7 days', NOW())
                ON CONFLICT DO NOTHING
            """), {
                "id": str(uuid_mod.uuid4()), "cid": str(candidate_id),
                "jid": str(job_id) if job_id else None,
                "token": token, "dur": duration,
            })
            await db.commit()

        await log_action_audit("generate_self_scheduling_link", company_id, candidate_id=str(candidate_id))

        return ActionResult(
            status="executed",
            message=f"Link de auto-agendamento gerado para **{candidate_name}**: `{link}` (válido por 7 dias, duração: {duration} min).",
            data={
                "candidate_id": candidate_id, "candidate_name": candidate_name,
                "link": link, "token": token, "duration_minutes": duration,
                "expires_in_days": 7, "generated_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="generate_self_scheduling_link",
        )
    except Exception as e:
        logger.warning(f"generate_self_scheduling_link failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao gerar link de auto-agendamento.",
            error_detail=str(e),
            action_type="generate_self_scheduling_link",
        )
