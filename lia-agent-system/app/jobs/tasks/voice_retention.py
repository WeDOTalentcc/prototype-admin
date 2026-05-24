"""Voice retention enforcement — LGPD Art. 16 (data minimization).

Retention policy approved Paulo 2026-05-22:
  - audio_url + audio S3 file:  60 days (wsi_response_analyses.response_audio_url,
                                          voice_screening_calls.recording_url se existir)
  - transcript:                 180 days (wsi_response_analyses.response_text,
                                          voice_screening_calls.transcript,
                                          voice_screening_calls.transcript_object)
  - WSI score:                  365 days (voice_wsi_results row,
                                          voice_screening_analyses row)

Audit ref: F-05 (AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md)

Idempotent: re-running the task is safe — NULL columns stay NULL, rows already
deleted are no-ops. Aggregate stats logged per run for LGPD Art. 20 trail.

P1 ticket #2 (2026-05-23): each phase emits canonical AuditService.log_decision
row with phase_name + records_purged count. Best-effort: audit failure NUNCA
bloqueia o purge (LGPD Art. 16 compliance is primary; audit is secondary).

Cron: daily 03:15 UTC (00:15 Brasília) via beat schedule `voice-retention-daily`.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.jobs.tasks._utils import (
    celery_app,
    logger,
    _celery_span,
    _emit_celery_retry,
    _emit_dlq_push,
    _finish_celery_failure,
    _finish_celery_success,
)
from app.jobs.tenant_aware_task import TenantAwareTask

_log = logging.getLogger(__name__)


# F-05 P0 LGPD: retention windows approved Paulo 2026-05-22
AUDIO_RETENTION_DAYS = 60
TRANSCRIPT_RETENTION_DAYS = 180
WSI_SCORE_RETENTION_DAYS = 365


async def _emit_phase_audit(
    *,
    phase: str,
    action: str,
    records_purged: int,
    cutoff: datetime,
) -> None:
    """P1 ticket #2: emit canonical audit row per retention phase.

    Best-effort — never raises. LGPD Art. 16 purge is primary; audit
    failure (e.g., audit DB down, RLS misconfig) MUST NOT abort retention.

    `company_id="*"` because retention is a global cron task that scans
    cross-tenant by date. Per-company aggregate stats are out of scope
    for this phase (would require GROUP BY company_id at query level —
    deferred to Sprint 4+).
    """
    try:
        # Lazy import: AuditService pulls in DB / sentry / etc. Avoid hard
        # dependency at module load time (cron task may run in minimal env).
        from app.shared.compliance.audit_service import AuditService

        audit = AuditService()
        await audit.log_decision(
            company_id="*",  # cross-tenant retention cron — meta-audit row
            agent_name="voice_retention_cron",
            decision_type="lgpd_art16_purge_executed",
            action=action,
            decision="completed",
            reasoning=[
                f"records_purged={records_purged}",
                f"cutoff_date={cutoff.isoformat()}",
                f"phase={phase}",
            ],
            criteria_used=[
                "lgpd_art_16_minimization",
                "retention_canonical_paulo_2026_05_22",
            ],
            criteria_ignored=[],
            human_review_required=False,
        )
    except Exception as audit_err:  # noqa: BLE001
        logger.warning(
            "[voice.retention] audit emission failed for phase=%s "
            "(non-blocking, LGPD purge already completed): %s",
            phase,
            audit_err,
        )


async def _run_voice_retention(dry_run: bool = False) -> dict:
    """Execute purge per retention policy.

    Returns aggregate stats: { audio_purged, transcript_purged, wsi_score_purged,
                               wsi_analysis_purged, dry_run, ran_at }

    Each phase wraps with try/except to keep idempotent semantics and continue
    even if one phase fails (ANPD compliance: best-effort log + continue).
    """
    from app.core.database import AsyncSessionLocal

    # 2026-05-24 fix Bug C: DB columns are `timestamp without time zone`
    # (wsi_response_analyses.created_at, voice_wsi_results.created_at).
    # Passing tz-aware datetime causes asyncpg DataError "can't subtract
    # offset-naive and offset-aware". Use tz-naive UTC consistently.
    # Sensor 6 (check_tz_aware_cutoff_in_queries.py) blocks regression.
    now = datetime.utcnow()
    audio_cutoff = now - timedelta(days=AUDIO_RETENTION_DAYS)
    transcript_cutoff = now - timedelta(days=TRANSCRIPT_RETENTION_DAYS)
    wsi_cutoff = now - timedelta(days=WSI_SCORE_RETENTION_DAYS)

    stats = {
        "audio_purged": 0,
        "transcript_purged": 0,
        "wsi_score_purged": 0,
        "wsi_analysis_purged": 0,
        "dry_run": dry_run,
        "ran_at": now.isoformat(),
        "errors": [],
    }

    async with AsyncSessionLocal() as db:
        # ── Phase 1: audio_url null after 60d ────────────────────────────────
        try:
            if dry_run:
                res = await db.execute(
                    text(
                        "SELECT COUNT(*) FROM wsi_response_analyses "
                        "WHERE response_audio_url IS NOT NULL AND created_at < :cutoff"
                    ),
                    {"cutoff": audio_cutoff},
                )
                stats["audio_purged"] = int(res.scalar() or 0)
            else:
                res = await db.execute(
                    text(
                        "UPDATE wsi_response_analyses "
                        "SET response_audio_url = NULL "
                        "WHERE response_audio_url IS NOT NULL AND created_at < :cutoff"
                    ),
                    {"cutoff": audio_cutoff},
                )
                stats["audio_purged"] = res.rowcount or 0
                await db.commit()
                # P1 #2: canonical audit trail per phase (LGPD Art. 20)
                await _emit_phase_audit(
                    phase="audio",
                    action="audio_purge_60d",
                    records_purged=stats["audio_purged"],
                    cutoff=audio_cutoff,
                )
        except Exception as exc:  # noqa: BLE001
            stats["errors"].append(f"audio_phase:{type(exc).__name__}:{exc}")
            logger.warning("[voice.retention] audio phase failed (continuing): %s", exc)
            await db.rollback()

        # ── Phase 2: transcript null after 180d ───────────────────────────────
        try:
            if dry_run:
                res = await db.execute(
                    text(
                        "SELECT COUNT(*) FROM wsi_response_analyses "
                        "WHERE response_text IS NOT NULL AND created_at < :cutoff"
                    ),
                    {"cutoff": transcript_cutoff},
                )
                stats["transcript_purged"] = int(res.scalar() or 0)
            else:
                res = await db.execute(
                    text(
                        "UPDATE wsi_response_analyses "
                        "SET response_text = NULL "
                        "WHERE response_text IS NOT NULL AND created_at < :cutoff"
                    ),
                    {"cutoff": transcript_cutoff},
                )
                stats["transcript_purged"] = res.rowcount or 0
                await db.commit()

                # Also null voice_screening_calls.transcript / transcript_object
                res2 = await db.execute(
                    text(
                        "UPDATE voice_screening_calls "
                        "SET transcript = NULL, transcript_object = '[]'::jsonb "
                        "WHERE (transcript IS NOT NULL OR transcript_object::text != '[]') "
                        "AND created_at < :cutoff"
                    ),
                    {"cutoff": transcript_cutoff},
                )
                stats["transcript_purged"] += res2.rowcount or 0
                await db.commit()
                # P1 #2: canonical audit trail per phase (LGPD Art. 20)
                await _emit_phase_audit(
                    phase="transcript",
                    action="transcript_purge_180d",
                    records_purged=stats["transcript_purged"],
                    cutoff=transcript_cutoff,
                )
        except Exception as exc:  # noqa: BLE001
            stats["errors"].append(f"transcript_phase:{type(exc).__name__}:{exc}")
            logger.warning("[voice.retention] transcript phase failed (continuing): %s", exc)
            await db.rollback()

        # ── Phase 3: WSI score row delete after 365d ──────────────────────────
        try:
            if dry_run:
                res = await db.execute(
                    text(
                        "SELECT COUNT(*) FROM voice_wsi_results WHERE created_at < :cutoff"
                    ),
                    {"cutoff": wsi_cutoff},
                )
                stats["wsi_score_purged"] = int(res.scalar() or 0)
                res2 = await db.execute(
                    text(
                        "SELECT COUNT(*) FROM voice_screening_analyses WHERE created_at < :cutoff"
                    ),
                    {"cutoff": wsi_cutoff},
                )
                stats["wsi_analysis_purged"] = int(res2.scalar() or 0)
            else:
                res = await db.execute(
                    text("DELETE FROM voice_wsi_results WHERE created_at < :cutoff"),
                    {"cutoff": wsi_cutoff},
                )
                stats["wsi_score_purged"] = res.rowcount or 0
                await db.commit()

                res2 = await db.execute(
                    text("DELETE FROM voice_screening_analyses WHERE created_at < :cutoff"),
                    {"cutoff": wsi_cutoff},
                )
                stats["wsi_analysis_purged"] = res2.rowcount or 0
                await db.commit()
                # P1 #2: canonical audit trail per phase (LGPD Art. 20).
                # Aggregate both wsi_score + wsi_analysis purges into single
                # audit row (same retention window, semantically same phase).
                await _emit_phase_audit(
                    phase="wsi_score",
                    action="wsi_purge_365d",
                    records_purged=stats["wsi_score_purged"] + stats["wsi_analysis_purged"],
                    cutoff=wsi_cutoff,
                )
        except Exception as exc:  # noqa: BLE001
            stats["errors"].append(f"wsi_score_phase:{type(exc).__name__}:{exc}")
            logger.warning("[voice.retention] wsi_score phase failed (continuing): %s", exc)
            await db.rollback()

    logger.info(
        "[voice.retention] LGPD Art. 16 purge complete: %s",
        {k: v for k, v in stats.items() if k != "errors"},
    )
    if stats["errors"]:
        logger.error("[voice.retention] errors during run: %s", stats["errors"])

    return stats


@celery_app.task(
    base=TenantAwareTask,
    name="voice.retention_purge_daily",
    bind=True,
    max_retries=3,
    queue="onboarding_low",
)
def voice_retention_purge_daily_task(self, dry_run: bool = False) -> dict:
    """
    F-05 P0 LGPD: daily voice data retention enforcement.

    Retention windows (Paulo approved 2026-05-22):
      - 60d:  audio_url null (wsi_response_analyses.response_audio_url)
      - 180d: transcript null (response_text, voice_screening_calls.transcript)
      - 365d: WSI score row delete (voice_wsi_results, voice_screening_analyses)

    Schedule: daily 03:15 UTC via beat schedule `voice-retention-daily`.
    Idempotent: re-run safe.

    Args:
        dry_run: when True, counts rows that would be purged without modifying DB.

    Returns:
        Aggregate stats dict per phase.
    """
    span = _celery_span("celery.task_start", "voice.retention_purge_daily")
    span.set_attribute("dry_run", str(dry_run))

    try:
        result = asyncio.run(_run_voice_retention(dry_run=dry_run))
        _finish_celery_success(span, "voice.retention_purge_daily")
        logger.info("voice.retention_purge_daily concluído: %s", result)
        from app.shared.resilience.cron_health import record_cron_run

        record_cron_run("voice.retention_purge_daily")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "voice.retention_purge_daily", exc)
        logger.error("voice.retention_purge_daily falhou: %s", exc)
        _emit_celery_retry(
            "voice.retention_purge_daily", exc, self.request.retries, self.max_retries, 600
        )

        if self.request.retries >= self.max_retries:
            _emit_dlq_push("voice.retention_purge_daily", exc)
        raise self.retry(exc=exc, countdown=600)
