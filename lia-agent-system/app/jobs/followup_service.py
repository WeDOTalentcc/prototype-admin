"""
Follow-up Automático de Convites WSI — Passo 6B do Fluxo Alpha 1.

Lógica:
  - A cada execução, consulta notificações do tipo 'wsi_invite' enviadas há
    mais de 24h que NÃO tiveram evento 'open' no email_tracking_events.
  - Reenvia a notificação (Bell + email) incrementando followup_count.
  - Após MAX_FOLLOWUPS (7 dias): marca candidato como 'sem_resposta' e
    notifica o recruiter via Bell.

Fail-safe: exceções por candidato são logadas e não interrompem o batch.
LGPD: stoplist opt-out verificada antes de cada reenvio.
"""
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

MAX_FOLLOWUPS = 7          # reenvios máximos (= 7 dias)
FOLLOWUP_INTERVAL_HOURS = 24


async def process_email_followups(db: AsyncSession) -> dict[str, int]:
    """
    Processa reenvios de convites WSI não abertos.

    Returns:
        dict com sent, skipped, errors, marked_no_response
    """
    sent = skipped = errors = marked_no_response = 0

    try:
        # Bug D fix (2026-05-24): strip tzinfo for asyncpg compat.
        # notifications.created_at é `timestamp without time zone` (naive).
        # `cutoff` precisa ser naive para evitar:
        #   "can't subtract offset-naive and offset-aware datetimes"
        # Mantém UTC semantics (server roda UTC).
        cutoff = (datetime.now(UTC) - timedelta(hours=FOLLOWUP_INTERVAL_HOURS)).replace(tzinfo=None)
        result = await db.execute(text("""
            SELECT
                n.id           AS notification_id,
                n.user_id      AS user_id,
                n.related_candidate_id AS candidate_id,
                n.related_job_id       AS job_id,
                n.extra_data           AS extra_data,
                n.created_at           AS sent_at
            FROM notifications n
            WHERE n.source_trigger = 'wsi_invite'
              AND n.created_at < :cutoff
              AND NOT EXISTS (
                  SELECT 1 FROM email_tracking_events e
                  WHERE (
                      e.notification_id = n.id
                      OR e.notification_id IN (
                          SELECT fn.id::text FROM notifications fn
                          WHERE fn.source_trigger = 'wsi_followup'
                            AND fn.extra_data->>'parent_notification_id' = n.id::text
                      )
                  )
                  AND e.event_type IN ('open', 'click', 'unsubscribe')
              )
              AND COALESCE(n.extra_data->>'opted_out', 'false') != 'true'
              AND COALESCE(n.extra_data->>'status', '') != 'sem_resposta'
              AND (
                  n.extra_data->>'last_followup_at' IS NULL
                  OR (n.extra_data->>'last_followup_at')::timestamp < :last_followup_cutoff
              )
        """), {"cutoff": cutoff, "last_followup_cutoff": cutoff})
        rows = result.fetchall()
    except Exception as exc:
        logger.error("[followup] erro ao buscar notificações pendentes: %s", exc)
        return {"sent": 0, "skipped": 0, "errors": 1, "marked_no_response": 0}

    for row in rows:
        notification_id = str(row.notification_id)
        candidate_id = row.candidate_id
        job_id = row.job_id
        extra_data: dict[str, Any] = row.extra_data or {}
        followup_count: int = int(extra_data.get("followup_count", 0))

        try:
            if followup_count >= MAX_FOLLOWUPS:
                # 7 dias sem resposta — marcar e notificar recruiter
                await _mark_no_response(db, candidate_id, job_id, notification_id)
                marked_no_response += 1
                skipped += 1
                continue

            # Verificar opt-out LGPD
            if extra_data.get("opted_out"):
                logger.info(
                    "[followup] candidato opt-out ignorado candidate=%s", candidate_id
                )
                skipped += 1
                continue

            # Reenvia notificação Bell (fail-safe)
            try:
                from app.services.notification_service import notification_service
                await notification_service.create_notification(
                    user_id=str(row.user_id),
                    title="Lembrete: Sua triagem está aguardando",
                    message=(
                        "Você recebeu um convite para a triagem que ainda não foi iniciado. "
                        "Clique para continuar."
                    ),
                    category="wsi_reminder",
                    source_trigger="wsi_followup",
                    related_candidate_id=candidate_id,
                    related_job_id=job_id,
                    channels=["bell", "email"],
                    metadata={"parent_notification_id": notification_id, "followup_count": followup_count + 1},
                    db=db,
                )
            except Exception as notif_exc:
                logger.warning(
                    "[followup] erro ao reenviar notificação notification=%s: %s",
                    notification_id, notif_exc,
                )

            # Atualiza followup_count na notificação original
            new_extra = {**extra_data, "followup_count": followup_count + 1, "last_followup_at": datetime.now(UTC).isoformat()}
            await db.execute(text("""
                UPDATE notifications
                SET extra_data = :extra_data
                WHERE id = :notification_id
            """), {"extra_data": new_extra, "notification_id": notification_id})

            await db.commit()
            sent += 1
            logger.info(
                "[followup] reenvio #%d candidate=%s job=%s notification=%s",
                followup_count + 1, candidate_id, job_id, notification_id,
            )

        except Exception as exc:
            errors += 1
            logger.error(
                "[followup] erro candidate=%s notification=%s: %s",
                candidate_id, notification_id, exc,
            )
            try:
                await db.rollback()
            except Exception:
                pass

    logger.info(
        "[followup] batch completo sent=%d skipped=%d errors=%d marked_no_response=%d",
        sent, skipped, errors, marked_no_response,
    )
    return {"sent": sent, "skipped": skipped, "errors": errors, "marked_no_response": marked_no_response}


async def _mark_no_response(
    db: AsyncSession,
    candidate_id: str | None,
    job_id: str | None,
    notification_id: str,
) -> None:
    """Marca candidato como sem_resposta e notifica recruiter."""
    # Atualiza extra_data da notificação
    await db.execute(text("""
        UPDATE notifications
        SET extra_data = jsonb_set(COALESCE(extra_data, '{}'), '{status}', '"sem_resposta"')
        WHERE id = :notification_id
    """), {"notification_id": notification_id})

    # Notifica recruiter via Bell (busca recruiter responsável pela vaga)
    try:
        recruiter_result = await db.execute(text("""
            SELECT created_by FROM job_vacancies WHERE id = :job_id LIMIT 1
        """), {"job_id": job_id})
        recruiter_row = recruiter_result.fetchone()
        if recruiter_row and recruiter_row.created_by:
            from app.services.notification_service import notification_service
            await notification_service.create_notification(
                user_id=str(recruiter_row.created_by),
                title="Candidato sem resposta após 7 dias",
                message=f"O candidato {candidate_id} não respondeu ao convite WSI em 7 dias.",
                category="candidate_alert",
                source_trigger="wsi_no_response",
                related_candidate_id=candidate_id,
                related_job_id=job_id,
                channels=["bell"],
                db=db,
            )
    except Exception as exc:
        logger.warning("[followup] erro ao notificar recruiter job=%s: %s", job_id, exc)

    await db.commit()
    logger.info(
        "[followup] sem_resposta marcado candidate=%s job=%s", candidate_id, job_id
    )
