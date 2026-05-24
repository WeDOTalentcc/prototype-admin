"""
WSI Triagem Abandonada — Passo 7A do Fluxo Alpha 1.

Lógica:
  - Sessões WSI com status='in_progress' sem atividade há >48h recebem 1º lembrete.
  - Sessões sem atividade há >96h recebem 2º lembrete + alerta Bell/Teams ao recruiter.
  - Progresso parcial preservado (sem modificação do estado da sessão).

Fail-safe: exceções por sessão são logadas e não interrompem o batch.
"""
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

FIRST_REMINDER_HOURS = 48   # 1º lembrete ao candidato
SECOND_REMINDER_HOURS = 96  # 2º lembrete + alerta recruiter
CONSULTANT_ALERT_HOURS = 120  # +24h após 2º lembrete → alerta consultor/gestor


async def check_abandoned_sessions(db: AsyncSession) -> dict[str, int]:
    """
    Verifica sessões WSI abandonadas e envia lembretes.

    Returns:
        dict com first_reminders, second_reminders, consultant_alerts, errors
    """
    first_reminders = second_reminders = consultant_alerts = errors = 0
    now = datetime.now(UTC)

    try:
        cutoff_first = now - timedelta(hours=FIRST_REMINDER_HOURS)
        result = await db.execute(text("""
            SELECT
                s.id              AS session_id,
                s.candidate_id    AS candidate_id,
                s.job_vacancy_id  AS job_vacancy_id,
                COALESCE(s.updated_at, s.created_at) AS last_activity,
                COALESCE(s.voice_session_state->>'reminder_count', '0')::int AS reminder_count
            FROM wsi_sessions s
            WHERE s.status = 'in_progress'
              AND COALESCE(s.updated_at, s.created_at) < :cutoff_first
        """), {"cutoff_first": cutoff_first})
        rows = result.fetchall()
    except Exception as exc:
        logger.error("[wsi-abandoned] erro ao buscar sessões: %s", exc)
        return {"first_reminders": 0, "second_reminders": 0, "consultant_alerts": 0, "errors": 1}

    for row in rows:
        session_id = str(row.session_id)
        candidate_id = str(row.candidate_id)
        job_vacancy_id = str(row.job_vacancy_id) if row.job_vacancy_id else None
        reminder_count: int = row.reminder_count
        last_activity = row.last_activity
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=UTC)
        age_hours = (now - last_activity).total_seconds() / 3600

        try:
            if reminder_count >= 3:
                continue

            if age_hours >= CONSULTANT_ALERT_HOURS and reminder_count == 2:
                await _notify_consultant_escalation(db, candidate_id, job_vacancy_id, session_id)
                await _increment_reminder_count(db, session_id, 3)
                consultant_alerts += 1
                logger.info(
                    "[wsi-abandoned] consultor escalado session=%s candidate=%s", session_id, candidate_id
                )
                continue

            if age_hours >= SECOND_REMINDER_HOURS and reminder_count < 2:
                await _send_candidate_reminder(db, candidate_id, job_vacancy_id, session_id, reminder_num=2)
                await _notify_recruiter_abandoned(db, candidate_id, job_vacancy_id, session_id)
                await _send_teams_timeout_notification(candidate_id, job_vacancy_id, session_id, age_hours)
                await _increment_reminder_count(db, session_id, 2)
                second_reminders += 1
                logger.info(
                    "[wsi-abandoned] 2º lembrete + Teams timeout session=%s candidate=%s", session_id, candidate_id
                )

            elif age_hours >= FIRST_REMINDER_HOURS and reminder_count < 1:
                # 1º lembrete: apenas candidato
                await _send_candidate_reminder(db, candidate_id, job_vacancy_id, session_id, reminder_num=1)
                await _increment_reminder_count(db, session_id, 1)
                first_reminders += 1
                logger.info(
                    "[wsi-abandoned] 1º lembrete session=%s candidate=%s", session_id, candidate_id
                )

        except Exception as exc:
            errors += 1
            logger.error(
                "[wsi-abandoned] erro session=%s candidate=%s: %s",
                session_id, candidate_id, exc,
            )
            try:
                await db.rollback()
            except Exception:
                pass

    logger.info(
        "[wsi-abandoned] batch completo first=%d second=%d consultant=%d errors=%d",
        first_reminders, second_reminders, consultant_alerts, errors,
    )
    return {
        "first_reminders": first_reminders,
        "second_reminders": second_reminders,
        "consultant_alerts": consultant_alerts,
        "errors": errors,
    }


async def _send_candidate_reminder(
    db: AsyncSession,
    candidate_id: str,
    job_vacancy_id: str | None,
    session_id: str,
    reminder_num: int,
) -> None:
    """Envia lembrete de triagem pendente ao candidato via Bell."""
    try:
        from app.services.notification_service import notification_service
        await notification_service.create_notification(
            user_id=candidate_id,
            title="Sua triagem está aguardando" if reminder_num == 1 else "Último lembrete: triagem pendente",
            message=(
                "Você iniciou uma triagem que ainda não foi concluída. "
                "Retome de onde parou — seu progresso foi salvo."
            ),
            category="wsi_abandoned",
            source_trigger="wsi_abandoned_reminder",
            related_candidate_id=candidate_id,
            related_job_id=job_vacancy_id,
            channels=["bell", "email", "whatsapp"],
            metadata={"session_id": session_id, "reminder_num": reminder_num},
            db=db,
        )
        await db.commit()
    except Exception as exc:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning(
            "[wsi-abandoned] erro ao notificar candidato candidate=%s: %s", candidate_id, exc
        )


async def _notify_recruiter_abandoned(
    db: AsyncSession,
    candidate_id: str,
    job_vacancy_id: str | None,
    session_id: str,
) -> None:
    """Notifica recruiter via Bell+Teams após 2º lembrete sem retorno."""
    try:
        recruiter_result = await db.execute(text("""
            SELECT created_by FROM job_vacancies WHERE id = :job_id LIMIT 1
        """), {"job_id": job_vacancy_id})
        recruiter_row = recruiter_result.fetchone()
        if not recruiter_row or not recruiter_row.created_by:
            return

        from app.services.notification_service import notification_service
        await notification_service.create_notification(
            user_id=str(recruiter_row.created_by),
            title="Triagem abandonada após 96h",
            message=(
                f"O candidato {candidate_id} iniciou a triagem mas não respondeu "
                "em 96 horas. Considere tomar uma ação manual."
            ),
            category="candidate_alert",
            source_trigger="wsi_abandoned_alert",
            related_candidate_id=candidate_id,
            related_job_id=job_vacancy_id,
            channels=["bell", "teams"],
            metadata={"session_id": session_id},
            db=db,
        )
        await db.commit()
    except Exception as exc:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning(
            "[wsi-abandoned] erro ao notificar recruiter job=%s: %s", job_vacancy_id, exc
        )


async def _notify_consultant_escalation(
    db: AsyncSession,
    candidate_id: str,
    job_vacancy_id: str | None,
    session_id: str,
) -> None:
    """Escalation alert to consultant/manager +24h after 2nd reminder with no response."""
    try:
        recruiter_result = await db.execute(text("""
            SELECT created_by FROM job_vacancies WHERE id = :job_id LIMIT 1
        """), {"job_id": job_vacancy_id})
        recruiter_row = recruiter_result.fetchone()
        if not recruiter_row or not recruiter_row.created_by:
            return

        from app.services.notification_service import notification_service
        await notification_service.create_notification(
            user_id=str(recruiter_row.created_by),
            title="Escalação: candidato sem resposta há 5 dias",
            message=(
                f"O candidato {candidate_id} não respondeu após 2 lembretes (120h). "
                "Recomendação: contato telefônico ou remoção do pipeline."
            ),
            category="candidate_escalation",
            source_trigger="wsi_abandoned_consultant_alert",
            related_candidate_id=candidate_id,
            related_job_id=job_vacancy_id,
            channels=["bell", "email", "teams"],
            metadata={"session_id": session_id, "escalation": True},
            db=db,
        )
        await db.commit()
    except Exception as exc:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning(
            "[wsi-abandoned] erro ao escalar consultor job=%s: %s", job_vacancy_id, exc
        )


async def _increment_reminder_count(
    db: AsyncSession,
    session_id: str,
    new_count: int,
) -> None:
    """Atualiza reminder_count no metadata da sessão WSI."""
    try:
        await db.execute(text("""
            UPDATE wsi_sessions
            SET voice_session_state = jsonb_set(
                COALESCE(voice_session_state, '{}'),
                '{reminder_count}',
                :count::text::jsonb
            )
            WHERE id = :session_id
        """), {"count": new_count, "session_id": session_id})
        await db.commit()
    except Exception as exc:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning(
            "[wsi-abandoned] erro ao atualizar reminder_count session=%s: %s", session_id, exc
        )


async def _send_teams_timeout_notification(
    candidate_id: str,
    job_vacancy_id: str | None,
    session_id: str,
    age_hours: float,
) -> None:
    """Send a Teams notification when a candidate times out on WSI."""
    try:
        from app.domains.communication.services.teams_bot import teams_bot
        await teams_bot.notify_candidate_timeout(
            candidate_name=candidate_id,
            job_title=job_vacancy_id or "N/A",
            hours_elapsed=round(age_hours, 1),
        )
    except Exception as exc:
        logger.warning("[wsi-abandoned] Teams timeout notification failed session=%s: %s", session_id, exc)
