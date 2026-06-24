"""expurgo_gravacoes.py — Monthly audio recording expurgo (Phase 3b LGPD).

Retention policy (12 months from created_at / granted_at):
  - wsi_response_analyses.response_audio_url  → NULL + Twilio DELETE
  - triagem_messages.audio_base64             → NULL
  - interviews.recording_url                  → NULL + Twilio DELETE
  - voice_screening_calls.transcript + transcript_object → NULL

ConsentRecord rows are NEVER touched (5-year statutory retention).

Schedule: 1st of month 05:00 UTC = 02:00 BRT.
Idempotent: rows already NULL are skipped (RE-04).
Fail-open at batch level (RE-03): single-batch errors log + continue.

LGPD refs: Art. 16 (minimização), Art. 20 (audit trail), ANPD Guia §3.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any

from app.jobs.tasks._utils import (
    _celery_span,
    _emit_celery_retry,
    _emit_dlq_push,
    _finish_celery_failure,
    _finish_celery_success,
    celery_app,
    logger,
)
from app.jobs.tenant_aware_task import TenantAwareTask

_log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

RECORDING_RETENTION_MONTHS = 12
_EXPURGO_BATCH_SIZE = 100
# Cutoff uses 30-day months (conservative — purges at or after 12 months)
_RETENTION_DAYS = RECORDING_RETENTION_MONTHS * 30

# Twilio recording URL pattern: ...api.twilio.com/Recordings/RE<SID>
_TWILIO_RECORDING_RE = re.compile(
    r"api\.twilio\.com/(?:[^/]+/)*Recordings/(RE[A-Za-z0-9]+)"
)


# ── Twilio helper ─────────────────────────────────────────────────────────────

def _extract_twilio_sid(url: str) -> str | None:
    """Extract Recording SID from a Twilio recording URL.

    Returns None if the URL is not a Twilio recording URL.
    """
    if not url or "api.twilio.com" not in url or "Recordings/" not in url:
        return None
    m = _TWILIO_RECORDING_RE.search(url)
    return m.group(1) if m else None


async def _delete_twilio_recording(sid: str) -> str:
    """Delete a Twilio recording by SID.

    Returns one of: "deleted" | "not_twilio" | "404" | "error"
    Never raises — errors are logged and reported in the return value.
    """
    try:
        import os

        try:
            from twilio.base.exceptions import TwilioRestException
            from twilio.rest import Client as TwilioClient
        except ImportError:
            _log.debug("[expurgo] twilio package not available — skipping remote delete")
            return "not_twilio"

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        if not account_sid or not auth_token:
            _log.debug("[expurgo] Twilio credentials not configured — skipping remote delete")
            return "not_twilio"

        client = TwilioClient(account_sid, auth_token)
        # Twilio client is sync — run in executor to not block the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: client.recordings(sid).delete())
        _log.info("[expurgo] Twilio recording deleted: %s", sid)
        return "deleted"

    except Exception as exc:
        exc_name = type(exc).__name__
        status_code = getattr(exc, "status", None) or getattr(exc, "code", None)
        if status_code == 404 or "404" in str(exc):
            _log.debug("[expurgo] Twilio recording already gone (404): %s", sid)
            return "404"
        _log.warning("[expurgo] Twilio delete error for %s: %s(%s)", sid, exc_name, exc)
        return "error"


# ── Audit helper ──────────────────────────────────────────────────────────────

async def _emit_expurgo_audit(
    *,
    table_name: str,
    entity_id: str,
    company_id: str,
    cutoff: datetime,
    had_twilio_url: bool,
    twilio_delete_status: str,
) -> None:
    """Emit one AuditLog entry per nullified record.

    Best-effort — never raises (LGPD Art. 16 purge is primary).
    """
    try:
        from app.shared.compliance.audit_service import AuditService

        await AuditService().log_decision(
            company_id=company_id,
            agent_name="system:expurgo_job",
            decision_type="company_settings_change",
            action="expurgo_audio_recording",
            decision="completed",
            reasoning=[
                f"entity_type={table_name}",
                f"entity_id={entity_id}",
                f"cutoff_date={cutoff.isoformat()}",
                f"had_twilio_url={had_twilio_url}",
                f"twilio_delete_status={twilio_delete_status}",
                "lgpd_art_16_minimization",
            ],
            criteria_used=["lgpd_art_16", "recording_retention_12_months"],
            criteria_ignored=[],
            human_review_required=False,
        )
    except Exception as audit_err:  # noqa: BLE001
        _log.warning(
            "[expurgo] audit emission failed for %s/%s (non-blocking): %s",
            table_name,
            entity_id,
            audit_err,
        )


# ── Per-table expurgo phases ──────────────────────────────────────────────────

async def _expurgo_wsi_response_analyses(db, cutoff: datetime, stats: dict) -> None:
    """Phase 1: NULL wsi_response_analyses.response_audio_url > 12 months.

    Also attempts Twilio remote delete for urls matching api.twilio.com/Recordings/*.
    Uses `created_at` as cutoff column (no FK to consent_records on this table).
    """
    from sqlalchemy import text

    table = "wsi_response_analyses"
    nullified = 0

    try:
        while True:
            rows = (
                await db.execute(
                    text(
                        "SELECT id, response_audio_url "
                        "FROM wsi_response_analyses "
                        "WHERE response_audio_url IS NOT NULL "
                        "AND created_at < :cutoff "
                        "LIMIT :batch"
                    ),
                    {"cutoff": cutoff, "batch": _EXPURGO_BATCH_SIZE},
                )
            ).all()

            if not rows:
                break

            # Fetch company_id from joined session via session_id (best-effort)
            for row in rows:
                row_id = str(row[0])
                audio_url = row[1] or ""
                twilio_sid = _extract_twilio_sid(audio_url)
                had_twilio = bool(twilio_sid)
                delete_status = "not_twilio"

                if twilio_sid:
                    delete_status = await _delete_twilio_recording(twilio_sid)

                try:
                    await db.execute(
                        text(
                            "UPDATE wsi_response_analyses "
                            "SET response_audio_url = NULL "
                            "WHERE id = :id"
                        ),
                        {"id": row_id},
                    )
                    await db.commit()
                except Exception as row_exc:
                    _log.warning("[expurgo] %s row %s update failed: %s", table, row_id, row_exc)
                    await db.rollback()
                    continue

                # Audit (best-effort) — company_id unknown here, use "*"
                await _emit_expurgo_audit(
                    table_name=table,
                    entity_id=row_id,
                    company_id="*",
                    cutoff=cutoff,
                    had_twilio_url=had_twilio,
                    twilio_delete_status=delete_status,
                )
                nullified += 1

            if len(rows) < _EXPURGO_BATCH_SIZE:
                break

    except Exception as exc:  # noqa: BLE001
        stats.setdefault("errors", []).append(f"{table}:{type(exc).__name__}:{exc}")
        _log.warning("[expurgo] %s phase failed (continuing): %s", table, exc)
        try:
            await db.rollback()
        except Exception:
            pass

    stats["records_nullified_per_table"][table] = nullified


async def _expurgo_triagem_messages(db, cutoff: datetime, stats: dict) -> None:
    """Phase 2: NULL triagem_messages.audio_base64 > 12 months.

    triagem_messages has no company_id column — uses session_id → session for company_id.
    Audit uses company_id from triagem_sessions JOIN.
    """
    from sqlalchemy import text

    table = "triagem_messages"
    nullified = 0

    try:
        while True:
            rows = (
                await db.execute(
                    text(
                        "SELECT m.id, s.company_id "
                        "FROM triagem_messages m "
                        "LEFT JOIN triagem_sessions s ON s.id = m.session_id "
                        "WHERE m.audio_base64 IS NOT NULL "
                        "AND m.created_at < :cutoff "
                        "LIMIT :batch"
                    ),
                    {"cutoff": cutoff, "batch": _EXPURGO_BATCH_SIZE},
                )
            ).all()

            if not rows:
                break

            for row in rows:
                row_id = str(row[0])
                company_id = str(row[1]) if row[1] else "*"

                try:
                    await db.execute(
                        text(
                            "UPDATE triagem_messages SET audio_base64 = NULL WHERE id = :id"
                        ),
                        {"id": row_id},
                    )
                    await db.commit()
                except Exception as row_exc:
                    _log.warning("[expurgo] %s row %s update failed: %s", table, row_id, row_exc)
                    await db.rollback()
                    continue

                await _emit_expurgo_audit(
                    table_name=table,
                    entity_id=row_id,
                    company_id=company_id,
                    cutoff=cutoff,
                    had_twilio_url=False,
                    twilio_delete_status="not_twilio",
                )
                nullified += 1

            if len(rows) < _EXPURGO_BATCH_SIZE:
                break

    except Exception as exc:  # noqa: BLE001
        stats.setdefault("errors", []).append(f"{table}:{type(exc).__name__}:{exc}")
        _log.warning("[expurgo] %s phase failed (continuing): %s", table, exc)
        try:
            await db.rollback()
        except Exception:
            pass

    stats["records_nullified_per_table"][table] = nullified


async def _expurgo_interviews(db, cutoff: datetime, stats: dict) -> None:
    """Phase 3: NULL interviews.recording_url > 12 months.

    interviews.company_id is available directly (String(255) column).
    """
    from sqlalchemy import text

    table = "interviews"
    nullified = 0

    try:
        while True:
            rows = (
                await db.execute(
                    text(
                        "SELECT id, recording_url, company_id "
                        "FROM interviews "
                        "WHERE recording_url IS NOT NULL "
                        "AND created_at < :cutoff "
                        "LIMIT :batch"
                    ),
                    {"cutoff": cutoff, "batch": _EXPURGO_BATCH_SIZE},
                )
            ).all()

            if not rows:
                break

            for row in rows:
                row_id = str(row[0])
                recording_url = row[1] or ""
                company_id = str(row[2]) if row[2] else "*"
                twilio_sid = _extract_twilio_sid(recording_url)
                had_twilio = bool(twilio_sid)
                delete_status = "not_twilio"

                if twilio_sid:
                    delete_status = await _delete_twilio_recording(twilio_sid)

                try:
                    await db.execute(
                        text(
                            "UPDATE interviews SET recording_url = NULL WHERE id = :id"
                        ),
                        {"id": row_id},
                    )
                    await db.commit()
                except Exception as row_exc:
                    _log.warning("[expurgo] %s row %s update failed: %s", table, row_id, row_exc)
                    await db.rollback()
                    continue

                await _emit_expurgo_audit(
                    table_name=table,
                    entity_id=row_id,
                    company_id=company_id,
                    cutoff=cutoff,
                    had_twilio_url=had_twilio,
                    twilio_delete_status=delete_status,
                )
                nullified += 1

            if len(rows) < _EXPURGO_BATCH_SIZE:
                break

    except Exception as exc:  # noqa: BLE001
        stats.setdefault("errors", []).append(f"{table}:{type(exc).__name__}:{exc}")
        _log.warning("[expurgo] %s phase failed (continuing): %s", table, exc)
        try:
            await db.rollback()
        except Exception:
            pass

    stats["records_nullified_per_table"][table] = nullified


async def _expurgo_voice_screening_calls(db, cutoff: datetime, stats: dict) -> None:
    """Phase 4: NULL voice_screening_calls.transcript + transcript_object > 12 months.

    voice_screening_calls has no company_id — uses "*" in audit.
    """
    from sqlalchemy import text

    table = "voice_screening_calls"
    nullified = 0

    try:
        while True:
            rows = (
                await db.execute(
                    text(
                        "SELECT id "
                        "FROM voice_screening_calls "
                        "WHERE (transcript IS NOT NULL OR transcript_object::text != '[]') "
                        "AND created_at < :cutoff "
                        "LIMIT :batch"
                    ),
                    {"cutoff": cutoff, "batch": _EXPURGO_BATCH_SIZE},
                )
            ).all()

            if not rows:
                break

            for row in rows:
                row_id = str(row[0])

                try:
                    await db.execute(
                        text(
                            "UPDATE voice_screening_calls "
                            "SET transcript = NULL, transcript_object = '[]'::jsonb "
                            "WHERE id = :id"
                        ),
                        {"id": row_id},
                    )
                    await db.commit()
                except Exception as row_exc:
                    _log.warning("[expurgo] %s row %s update failed: %s", table, row_id, row_exc)
                    await db.rollback()
                    continue

                await _emit_expurgo_audit(
                    table_name=table,
                    entity_id=row_id,
                    company_id="*",
                    cutoff=cutoff,
                    had_twilio_url=False,
                    twilio_delete_status="not_twilio",
                )
                nullified += 1

            if len(rows) < _EXPURGO_BATCH_SIZE:
                break

    except Exception as exc:  # noqa: BLE001
        stats.setdefault("errors", []).append(f"{table}:{type(exc).__name__}:{exc}")
        _log.warning("[expurgo] %s phase failed (continuing): %s", table, exc)
        try:
            await db.rollback()
        except Exception:
            pass

    stats["records_nullified_per_table"][table] = nullified


# ── Summary email ─────────────────────────────────────────────────────────────

async def _send_summary_email(stats: dict) -> None:
    """Send summary email to company admins after expurgo run.

    Best-effort — never raises.
    Uses MailgunEmailService simple send_email (no template_id).
    Admin recipients: env var EXPURGO_ADMIN_EMAILS (comma-separated).
    Falls back to WEDOTALENT_ADMIN_EMAIL if set.
    Skips silently if no admin email configured.
    """
    import os

    try:
        from app.domains.communication.services.email_service import MailgunEmailService

        admin_emails_raw = os.getenv("EXPURGO_ADMIN_EMAILS") or os.getenv(
            "WEDOTALENT_ADMIN_EMAIL"
        )
        if not admin_emails_raw:
            _log.debug("[expurgo] no admin email configured — skipping summary email")
            return

        recipients = [e.strip() for e in admin_emails_raw.split(",") if e.strip()]
        if not recipients:
            return

        run_at = stats.get("run_at", "N/A")
        cutoff = stats.get("cutoff", "N/A")
        per_table = stats.get("records_nullified_per_table", {})
        total = sum(per_table.values())
        errors = stats.get("errors", [])

        subject = f"[WeDOTalent] Expurgo de Gravações LGPD — {run_at[:10]}"
        body_lines = [
            "Expurgo mensal de gravações de áudio (LGPD Art. 16) concluído.",
            "",
            f"Data/hora: {run_at}",
            f"Cutoff (registros anteriores a): {cutoff}",
            f"Total de registros expurgados: {total}",
            "",
            "Por tabela:",
        ]
        for tbl, count in per_table.items():
            body_lines.append(f"  - {tbl}: {count}")
        if errors:
            body_lines.extend(["", "Erros (não bloquearam o job):"])
            for err in errors:
                body_lines.append(f"  - {err}")

        body = "\n".join(body_lines)
        body_html = body.replace("\n", "<br>")

        svc = MailgunEmailService()
        for email in recipients:
            try:
                await svc.send_email(
                    to_email=email,
                    subject=subject,
                    body=body,
                    body_html=f"<pre>{body_html}</pre>",
                    categories=["expurgo_lgpd", "system_notification"],
                    metadata={"run_at": run_at, "total_expurgados": total},
                )
                _log.info("[expurgo] summary email sent to %s", email)
            except Exception as send_exc:
                _log.warning("[expurgo] summary email to %s failed: %s", email, send_exc)

    except Exception as exc:  # noqa: BLE001
        _log.warning("[expurgo] _send_summary_email failed (non-blocking): %s", exc)


# ── Core async runner ─────────────────────────────────────────────────────────

async def _run_expurgo_gravacoes() -> dict[str, Any]:
    """Execute monthly audio expurgo across all affected tables.

    Returns:
        {
            "tables_processed": list[str],
            "records_nullified_per_table": {table: count},
            "cutoff": str (ISO),
            "run_at": str (ISO),
            "errors": list[str],
        }
    """
    from app.core.database import AsyncSessionLocal

    # tz-naive UTC — DB columns are `timestamp without time zone`
    now = datetime.utcnow()
    cutoff = now - timedelta(days=_RETENTION_DAYS)

    stats: dict[str, Any] = {
        "tables_processed": [
            "wsi_response_analyses",
            "triagem_messages",
            "interviews",
            "voice_screening_calls",
        ],
        "records_nullified_per_table": {},
        "cutoff": cutoff.isoformat(),
        "run_at": now.isoformat(),
        "errors": [],
    }

    async with AsyncSessionLocal() as db:
        await _expurgo_wsi_response_analyses(db, cutoff, stats)
        await _expurgo_triagem_messages(db, cutoff, stats)
        await _expurgo_interviews(db, cutoff, stats)
        await _expurgo_voice_screening_calls(db, cutoff, stats)

    total = sum(stats["records_nullified_per_table"].values())
    _log.info(
        "[expurgo] monthly audio expurgo complete: total=%d cutoff=%s errors=%d",
        total,
        cutoff.isoformat(),
        len(stats["errors"]),
    )
    if stats["errors"]:
        _log.error("[expurgo] non-fatal errors during run: %s", stats["errors"])

    await _send_summary_email(stats)

    return stats


# ── Celery task ───────────────────────────────────────────────────────────────

@celery_app.task(
    base=TenantAwareTask,
    name="expurgo_gravacoes_audio",
    bind=True,
    max_retries=0,  # Monthly job — no retry (next month's run is idempotent)
    queue="onboarding_low",
)
def expurgo_gravacoes_audio(self) -> dict:
    """Monthly job (1st day of month, 02:00 BRT = 05:00 UTC).

    Nullifies audio references older than 12 months across:
      - wsi_response_analyses.response_audio_url → NULL + Twilio DELETE
      - triagem_messages.audio_base64             → NULL
      - interviews.recording_url                  → NULL + Twilio DELETE
      - voice_screening_calls.transcript + transcript_object → NULL

    ConsentRecord rows are NEVER touched (5-year statutory retention LGPD Art. 13).
    Response_text transcripts and WSI scores are NOT touched by this job
    (governed by voice_retention_purge_daily with different retention windows).

    Idempotent: re-run safe — NULL columns are skipped (RE-04).
    Fail-open per batch: single row errors log + continue (RE-03).

    Returns:
        {tables_processed, records_nullified_per_table, cutoff, run_at, errors}
    """
    span = _celery_span("celery.task_start", "expurgo_gravacoes_audio")

    try:
        result = asyncio.run(_run_expurgo_gravacoes())
        _finish_celery_success(span, "expurgo_gravacoes_audio")
        logger.info("expurgo_gravacoes_audio concluído: %s", result)
        try:
            from app.shared.resilience.cron_health import record_cron_run
            record_cron_run("expurgo_gravacoes_audio")
        except Exception:
            pass
        return result
    except Exception as exc:
        _finish_celery_failure(span, "expurgo_gravacoes_audio", exc)
        logger.error("expurgo_gravacoes_audio falhou: %s", exc)
        _emit_dlq_push("expurgo_gravacoes_audio", exc)
        # max_retries=0 → re-raise to mark task as failed in Celery result backend
        raise
