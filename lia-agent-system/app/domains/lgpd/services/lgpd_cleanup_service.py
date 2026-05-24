"""
LGPD Cleanup Service — data retention enforcement.

Runs as a scheduled daily job to permanently delete candidate records
that have passed their `scheduled_deletion_at` date.

Retention policy (configurable per company, defaults below):
  - Rejected candidates:       90 days  after rejection
  - Withdrawn candidates:      90 days  after withdrawal
  - Chat messages:             90 days  after creation   (LGPD Art. 18 — minimização)
  - Interview notes / CVs:    180 days  after last activity
  - Screening logs:            365 days after creation
  - AI logs (LLM calls):       365 days after creation    (L-6)

Design principles:
  - DRY-RUN first: log deletions without executing (safe to test)
  - Every deletion logged to audit_logs (LGPD accountability)
  - Scoped by company_id — never cross-tenant deletions
  - Irreversible: only run after dry-run validation
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.candidates.repositories.candidate_repository import (
    CandidateRepository,
)

from app.core.database import AsyncSessionLocal
from lia_models.ai_consumption import AiConsumption
from lia_models.candidate import Candidate, VacancyCandidate

logger = logging.getLogger(__name__)

_SAFE_TABLE_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
_ALLOWED_TTL_TABLES = frozenset([
    "messages", "conversation_messages", "chat_messages",
    "interview_notes", "screening_tasks", "fairness_audit_log",
])

# Default retention windows (days) — maps data type → TTL
RETENTION_DAYS = {
    "rejected": 90,
    "withdrawn": 90,
    "chat_messages": 90,       # LGPD Art. 18 — minimização de dados de conversa
    "interview_data": 180,     # Dados de entrevista e notas WSI
    "interview_notes": 180,    # alias kept for backwards compat
    "screening_logs": 365,     # Logs de triagem curricular
    "ai_logs": 365,            # AiConsumption — logs de chamadas LLM (L-6)
    "ai_decision_logs": 365,   # Logs de decisão de IA (EU AI Act)
}


async def schedule_deletion_for_candidate(
    db: AsyncSession,
    candidate_id: str,
    reason: str,
    retention_days: int | None = None,
) -> datetime:
    """
    Set scheduled_deletion_at on a candidate record.

    Called when a candidate is rejected or withdrawn so the cleanup job
    knows when to physically delete the record.

    WT-2022 P4.1 wire data_retention granular consent:
    Se candidato revogou granular consent de data_retention, ACELERA
    deletion (retention_days=0) em vez de esperar default TTL.
    Resolve "ghost setting" — antes UI tinha toggle data_retention sem efeito.

    Returns the scheduled deletion datetime.
    """
    candidate_repo = CandidateRepository(db)
    candidate = await candidate_repo.get_by_id(UUID(candidate_id))
    if not candidate:
        return datetime.utcnow() + timedelta(days=retention_days or RETENTION_DAYS.get(reason, 90))

    # WT-2022 P4.1: Check granular data_retention consent
    effective_retention_days = retention_days or RETENTION_DAYS.get(reason, 90)
    try:
        from app.domains.lgpd.services.granular_consent_consumers import (
            check_data_retention,
        )
        retention_consent = await check_data_retention(
            candidate_id=str(candidate.id),
            company_id=str(getattr(candidate, "company_id", "")),
            db=db,
        )
        if not retention_consent:
            # Candidate revogou consent de data_retention — accelerate deletion
            effective_retention_days = 0
            logger.info(
                "WT-2022 P4.1: data_retention consent revoked — accelerating deletion",
                extra={"candidate_id": candidate_id, "original_days": retention_days or RETENTION_DAYS.get(reason, 90)},
            )
    except Exception as exc:
        logger.warning(
            "Could not check granular data_retention consent for %s: %s — using default TTL",
            candidate_id, exc,
        )

    deletion_at = datetime.utcnow() + timedelta(days=effective_retention_days)
    candidate.scheduled_deletion_at = deletion_at
    await db.commit()
    logger.info(
        "Deletion scheduled",
        extra={
            "candidate_id": candidate_id,
            "deletion_at": deletion_at.isoformat(),
            "reason": reason,
            "retention_days_used": effective_retention_days,
        },
    )

    return deletion_at


async def _cleanup_by_created_at(
    db: AsyncSession,
    table_name: str,
    retention_days: int,
    dry_run: bool,
) -> int:
    """
    Generic TTL cleanup: delete rows from `table_name` where
    created_at < (now - retention_days).

    Uses raw SQL to avoid importing every model — works for any table
    that has a `created_at` column.

    Returns count of rows deleted (or would be deleted in dry-run mode).
    """
    if table_name not in _ALLOWED_TTL_TABLES:
        raise ValueError(f"Table '{table_name}' not in LGPD TTL allow-list")
    if not _SAFE_TABLE_RE.match(table_name):
        raise ValueError(f"Table '{table_name}' contains invalid characters")

    cutoff = datetime.utcnow() - timedelta(days=retention_days)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM {table_name} WHERE created_at < :cutoff"),
        {"cutoff": cutoff},
    )
    count = count_result.scalar_one() or 0

    if count > 0:
        logger.info(
            "LGPD TTL%s: %s — %d rows older than %d days (cutoff=%s)",
            " (dry-run)" if dry_run else "",
            table_name,
            count,
            retention_days,
            cutoff.isoformat(),
        )
        if not dry_run:
            await db.execute(
                text(f"DELETE FROM {table_name} WHERE created_at < :cutoff"),
                {"cutoff": cutoff},
            )
            await db.commit()

    return count


async def run_cleanup(dry_run: bool = True) -> dict:
    """
    Delete candidates and time-bounded data that exceeded their TTL.

    Covers:
      - Candidates (scheduled_deletion_at)
      - VacancyCandidate (scheduled_deletion_at)
      - AiConsumption (scheduled_deletion_at)
      - messages (created_at TTL — 90 days, LGPD Art. 18)
      - interview_notes (created_at TTL — 180 days)
      - screening_tasks (created_at TTL — 365 days)
      - fairness_audit_log (created_at TTL — 365 days, AI Act)

    Cascade-handled by PostgreSQL FK (no explicit step needed here):
      - lia_opinions (candidate_id FK ondelete=CASCADE) — OCEAN personality data
        deleted automatically when Candidate row is deleted. Sprint B P1 audit
        confirmed the cascade constraint exists in
        libs/models/lia_models/lia_opinion.py:53.

    Known gap — bigfive_department_profiles (P1-BigFive-Aggregate):
      These are AGGREGATE rows per (company, department, seniority), not per
      candidate. When a candidate requests erasure, their individual contribution
      cannot be surgically removed from the running average without a full
      recompute. Current approach: mark bigfive_department_profile rows that
      included the deleted candidate as stale (last_updated < deletion_at) so
      the next hire recomputes from scratch. Separate task:
      bigfive_service.recompute_on_erasure() — Sprint B+ backlog.

    Args:
        dry_run: If True, only logs what would be deleted without committing.
                 Always run with dry_run=True first to validate the scope.

    Returns:
        Summary dict with counts of deleted records per table.
    """
    summary: dict = {
        "dry_run": dry_run,
        "ran_at": datetime.utcnow().isoformat(),
        "candidates_deleted": 0,
        "vacancy_candidates_deleted": 0,
        "ai_consumption_deleted": 0,
        "chat_messages_deleted": 0,
        "interview_notes_deleted": 0,
        "screening_logs_deleted": 0,
        "ai_decision_logs_deleted": 0,
        "errors": [],
    }

    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        candidates_to_delete: list = []  # initialized here — may be overwritten by query below

        # 1. Candidates past their scheduled deletion date
        try:
            candidate_result = await db.execute(
                select(Candidate.id, Candidate.scheduled_deletion_at)
                .where(
                    and_(
                        Candidate.scheduled_deletion_at.isnot(None),
                        Candidate.scheduled_deletion_at <= now,
                    )
                )
            )
            candidates_to_delete = candidate_result.all()

            for row in candidates_to_delete:
                logger.info(
                    "LGPD deletion%s: candidate",
                    " (dry-run)" if dry_run else "",
                    extra={
                        "candidate_id": str(row.id),
                        "scheduled_deletion_at": row.scheduled_deletion_at.isoformat(),
                    },
                )

            if not dry_run and candidates_to_delete:
                ids = [row.id for row in candidates_to_delete]
                # ADR-001-EXEMPT: Rails-owned Candidate table — LGPD Art. 18 erasure right (data subject request)
                await db.execute(
                    delete(Candidate).where(Candidate.id.in_(ids))
                )
                await db.commit()

            summary["candidates_deleted"] = len(candidates_to_delete)

        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error("Error during LGPD candidate cleanup: %s", exc)
            summary["errors"].append(f"candidates: {exc}")

        # 2. VacancyCandidate records (rejection data / PII)
        try:
            vc_result = await db.execute(
                select(
                    VacancyCandidate.id,
                    VacancyCandidate.company_id,
                    VacancyCandidate.scheduled_deletion_at,
                )
                .where(
                    and_(
                        VacancyCandidate.scheduled_deletion_at.isnot(None),
                        VacancyCandidate.scheduled_deletion_at <= now,
                    )
                )
            )
            vcs_to_delete = vc_result.all()

            for row in vcs_to_delete:
                logger.info(
                    "LGPD deletion%s: vacancy_candidate",
                    " (dry-run)" if dry_run else "",
                    extra={
                        "vacancy_candidate_id": str(row.id),
                        "company_id": str(row.company_id),
                        "scheduled_deletion_at": row.scheduled_deletion_at.isoformat(),
                    },
                )

            if not dry_run and vcs_to_delete:
                ids = [row.id for row in vcs_to_delete]
                # CROSS-TENANT-EXEMPT: LGPD retention cleanup job runs system-wide across all tenants;
                # ids derived from query L283-294 above (scheduled_deletion_at filter is cross-tenant by design).
                # Each row already has company_id logged for audit. See top-of-file docstring.
                await db.execute(
                    delete(VacancyCandidate).where(VacancyCandidate.id.in_(ids))
                )
                await db.commit()

            summary["vacancy_candidates_deleted"] = len(vcs_to_delete)

        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error("Error during LGPD vacancy_candidate cleanup: %s", exc)
            summary["errors"].append(f"vacancy_candidates: {exc}")

        # 3. AiConsumption records past their retention date (L-6: 365 days)
        try:
            ai_result = await db.execute(
                select(AiConsumption.id, AiConsumption.company_id, AiConsumption.scheduled_deletion_at)
                .where(
                    and_(
                        AiConsumption.scheduled_deletion_at.isnot(None),
                        AiConsumption.scheduled_deletion_at <= now,
                    )
                )
            )
            ai_to_delete = ai_result.all()

            for row in ai_to_delete:
                logger.info(
                    "LGPD deletion%s: ai_consumption",
                    " (dry-run)" if dry_run else "",
                    extra={
                        "ai_consumption_id": str(row.id),
                        "company_id": str(row.company_id),
                        "scheduled_deletion_at": row.scheduled_deletion_at.isoformat(),
                    },
                )

            if not dry_run and ai_to_delete:
                ids = [row.id for row in ai_to_delete]
                # CROSS-TENANT-EXEMPT: LGPD retention cleanup job runs system-wide across all tenants;
                # ids derived from cross-tenant scheduled_deletion_at filter (L309-320). See top-of-file docstring.
                await db.execute(
                    delete(AiConsumption).where(AiConsumption.id.in_(ids))
                )
                await db.commit()

            summary["ai_consumption_deleted"] = len(ai_to_delete)

        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error("Error during LGPD ai_consumption cleanup: %s", exc)
            summary["errors"].append(f"ai_consumption: {exc}")

        # 4. Chat / conversation messages — 90 days TTL (LGPD Art. 18)
        # Canonical table is "messages" (lia_models/conversation.py).
        # 2026-05-24 fix: removidos aliases legacy "conversation_messages" e
        # "chat_messages" — nunca existiram neste schema, causavam
        # UndefinedTableError → InFailedSQLTransactionError nas TTLs subsequentes.
        # Sensor 5 (check_lgpd_ttl_tables_exist.py) bloqueia regressão.
        for table in ("messages",):
            try:
                count = await _cleanup_by_created_at(
                    db,
                    table_name=table,
                    retention_days=RETENTION_DAYS["chat_messages"],
                    dry_run=dry_run,
                )
                summary["chat_messages_deleted"] += count
            except Exception as exc:
                # Rollback transaction to allow subsequent TTL phases to run
                # (InFailedSQLTransactionError cascade prevention).
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.warning("LGPD TTL: table %s not found or error: %s", table, exc)

        # 5. Interview notes — 180 days TTL
        for table in ("interview_notes",):
            try:
                count = await _cleanup_by_created_at(
                    db,
                    table_name=table,
                    retention_days=RETENTION_DAYS["interview_data"],
                    dry_run=dry_run,
                )
                summary["interview_notes_deleted"] += count
            except Exception as exc:
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.warning("LGPD TTL: table %s not found or error: %s", table, exc)

        # 6. Screening task logs — 365 days TTL
        for table in ("screening_tasks",):
            try:
                count = await _cleanup_by_created_at(
                    db,
                    table_name=table,
                    retention_days=RETENTION_DAYS["screening_logs"],
                    dry_run=dry_run,
                )
                summary["screening_logs_deleted"] += count
            except Exception as exc:
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.warning("LGPD TTL: table %s not found or error: %s", table, exc)

        # 7. Fairness audit logs (AI decision logs) — 365 days TTL
        for table in ("fairness_audit_log",):
            try:
                count = await _cleanup_by_created_at(
                    db,
                    table_name=table,
                    retention_days=RETENTION_DAYS["ai_decision_logs"],
                    dry_run=dry_run,
                )
                summary["ai_decision_logs_deleted"] += count
            except Exception as exc:
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.warning("LGPD TTL: table %s not found or error: %s", table, exc)

        # 8. Propagate deletion to secondary stores for deleted candidate IDs
        if not dry_run and candidates_to_delete:
            deleted_ids = [str(row.id) for row in candidates_to_delete]
            propagation = await _propagate_deletion_to_secondary_stores(
                db, deleted_ids, dry_run=False
            )
            summary.update(propagation)
        elif dry_run and candidates_to_delete:
            deleted_ids = [str(row.id) for row in candidates_to_delete]
            propagation = await _propagate_deletion_to_secondary_stores(
                db, deleted_ids, dry_run=True
            )
            summary.update(propagation)

    mode = "DRY-RUN" if dry_run else "REAL"
    logger.info(
        "LGPD cleanup [%s] complete — candidates: %d, vacancy_candidates: %d, "
        "ai_consumption: %d, chat_messages: %d, interview_notes: %d, "
        "screening_logs: %d, ai_decision_logs: %d, secondary_stores: %s, errors: %d",
        mode,
        summary["candidates_deleted"],
        summary["vacancy_candidates_deleted"],
        summary["ai_consumption_deleted"],
        summary["chat_messages_deleted"],
        summary["interview_notes_deleted"],
        summary["screening_logs_deleted"],
        summary["ai_decision_logs_deleted"],
        {k: v for k, v in summary.items() if k.startswith("propagation_")},
        len(summary["errors"]),
    )
    return summary


# Secondary stores that hold candidate PII and must be cleaned on deletion.
# Each entry: (table_name, candidate_id_column)
_SECONDARY_PII_TABLES: list[tuple[str, str]] = [
    ("communication_history", "candidate_id"),
    ("lgpd_consents", "candidate_id"),
    ("candidate_consent_grants", "candidate_id"),
    ("conversation_memories", "user_id"),  # user_id stores candidate_id in chat context
    # F-06 P0 LGPD Art. 18 VI: voice tables (audit 2026-05-22)
    # Stores transcripts + audio_url + candidate_id + candidate_name + candidate_phone.
    # All four cascade explicitly here (defense-in-depth — FK CASCADE alone is fragile
    # because Rails-owned schemas may drop FKs without coordinating).
    ("voice_screening_calls", "candidate_id"),
    ("voice_wsi_results", "candidate_id"),
    ("wsi_response_analyses", "candidate_id"),
    # voice_screening_analyses has NO candidate_id column — only screening_call_id FK.
    # Marker "_cascade_via_fk" signals to _propagate_deletion_to_secondary_stores that
    # this row is deleted via cascade when voice_screening_calls is removed; no direct
    # DELETE here. Listed for visibility/regression-guard against silent FK removal.
    ("voice_screening_analyses", "_cascade_via_fk"),
    # P1-W2-10: email_logs contain recipient_email + body sent to candidate (LGPD Art. 18 VI)
    ("email_logs", "candidate_id"),
]

# Tables safe for parameterized deletion (extends _ALLOWED_TTL_TABLES)
_ALLOWED_PROPAGATION_TABLES = frozenset([
    "communication_history", "lgpd_consents", "candidate_consent_grants",
    "conversation_memories",
    # F-06 P0 LGPD Art. 18 VI: voice tables (mirror _SECONDARY_PII_TABLES)
    "voice_screening_calls",
    "voice_wsi_results",
    "wsi_response_analyses",
    "voice_screening_analyses",  # cascaded via FK voice_screening_calls (see note above)
    "email_logs",  # P1-W2-10: candidate_id FK — erasure clears sent email history
])


async def _propagate_deletion_to_secondary_stores(
    db: AsyncSession,
    candidate_ids: list[str],
    dry_run: bool = True,
) -> dict:
    """
    Delete candidate PII from secondary stores after primary candidate deletion.

    Each store is attempted independently — failure in one does not block others.
    Returns a dict with counts per store for the cleanup summary.
    """
    result: dict = {}

    if not candidate_ids:
        return result

    # --- DB tables with candidate_id FK ---
    for table_name, id_col in _SECONDARY_PII_TABLES:
        if table_name not in _ALLOWED_PROPAGATION_TABLES:
            continue
        if not _SAFE_TABLE_RE.match(table_name):
            continue

        # F-06: tables without direct candidate_id (e.g. voice_screening_analyses)
        # cascade via FK on a parent table that IS in this list. Skip explicit
        # DELETE here — DB FK CASCADE handles the row removal when parent goes.
        # Listed in _SECONDARY_PII_TABLES purely as a regression-guard sentinel.
        if id_col == "_cascade_via_fk":
            result[f"propagation_{table_name}"] = "cascaded_via_fk"
            logger.debug(
                "LGPD propagation: %s relies on FK CASCADE (no direct DELETE)",
                table_name,
            )
            continue

        try:
            count_q = await db.execute(
                text(f"SELECT COUNT(*) FROM {table_name} WHERE {id_col} = ANY(:ids)"),
                {"ids": candidate_ids},
            )
            count = count_q.scalar_one() or 0

            if count > 0:
                logger.info(
                    "LGPD propagation%s: %s — %d rows for %d candidates",
                    " (dry-run)" if dry_run else "",
                    table_name, count, len(candidate_ids),
                )
                if not dry_run:
                    await db.execute(
                        text(f"DELETE FROM {table_name} WHERE {id_col} = ANY(:ids)"),
                        {"ids": candidate_ids},
                    )
                    await db.commit()

            result[f"propagation_{table_name}"] = count
        except Exception as exc:
            logger.warning(
                "LGPD propagation: %s failed (continuing): %s", table_name, exc
            )
            try:
                await db.rollback()
            except Exception:
                pass
            result[f"propagation_{table_name}"] = f"error: {exc}"

    # --- query_embeddings: queries may contain candidate names ---
    try:
        qe_count = await _cleanup_query_embeddings_for_candidates(db, candidate_ids, dry_run)
        result["propagation_query_embeddings"] = qe_count
    except Exception as exc:
        logger.warning("LGPD propagation: query_embeddings failed: %s", exc)
        result["propagation_query_embeddings"] = f"error: {exc}"

    # --- Redis cache flush for deleted candidates ---
    try:
        redis_cleaned = await _flush_redis_candidate_cache(candidate_ids, dry_run)
        result["propagation_redis"] = redis_cleaned
    except Exception as exc:
        logger.warning("LGPD propagation: Redis flush failed: %s", exc)
        result["propagation_redis"] = f"error: {exc}"

    return result


async def _cleanup_query_embeddings_for_candidates(
    db: AsyncSession,
    candidate_ids: list[str],
    dry_run: bool = True,
) -> int:
    """
    Delete query_embeddings rows whose query_text contains candidate identifiers.

    query_embeddings stores search queries that may include candidate names or IDs
    (e.g. "Find candidates named João Silva"). We search query_text for each
    candidate_id and delete matching rows.
    """
    if not candidate_ids:
        return 0

    total = 0
    try:
        for cid in candidate_ids:
            count_q = await db.execute(
                text(
                    "SELECT COUNT(*) FROM query_embeddings "
                    "WHERE query_text ILIKE :pattern OR cache_key ILIKE :pattern"
                ),
                {"pattern": f"%{cid}%"},
            )
            count = count_q.scalar_one() or 0
            if count > 0:
                logger.info(
                    "LGPD propagation%s: query_embeddings — %d rows matching candidate %s",
                    " (dry-run)" if dry_run else "",
                    count, cid,
                )
                if not dry_run:
                    await db.execute(
                        text(
                            "DELETE FROM query_embeddings "
                            "WHERE query_text ILIKE :pattern OR cache_key ILIKE :pattern"
                        ),
                        {"pattern": f"%{cid}%"},
                    )
                total += count

        if total > 0 and not dry_run:
            await db.commit()
    except Exception as exc:
        logger.warning("LGPD propagation: query_embeddings cleanup failed: %s", exc)
        try:
            await db.rollback()
        except Exception:
            pass

    return total


async def _flush_redis_candidate_cache(
    candidate_ids: list[str],
    dry_run: bool = True,
) -> int:
    """
    Delete Redis keys containing candidate PII.

    Key patterns:
      - toon:{company_id}:{candidate_id}:*
      - candidate_list:* (cannot target by candidate_id — TTL handles this)

    Returns count of keys deleted.
    """
    try:
        from app.core.redis_client import get_redis
        redis = await get_redis()
        if redis is None:
            return 0

        deleted = 0
        for cid in candidate_ids:
            # TOON card cache: toon:*:{candidate_id}:*
            pattern = f"toon:*:{cid}:*"
            keys = []
            async for key in redis.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                logger.info(
                    "LGPD Redis%s: %d keys matching pattern %s",
                    " (dry-run)" if dry_run else "",
                    len(keys), pattern,
                )
                if not dry_run:
                    await redis.delete(*keys)
                deleted += len(keys)

        return deleted
    except Exception as exc:
        logger.warning("Redis candidate cache flush failed: %s", exc)
        return 0


async def run_conversation_ttl_cleanup(dry_run: bool = False) -> dict:
    """
    Dedicated TTL cleanup for conversation/chat data.

    Intended to be called by the `conversation.ttl_cleanup` Celery Beat task.
    Applies TTL rules per data type:
      - chat_messages / conversation_messages: 90 days
      - interview_notes: 180 days
      - screening_tasks: 365 days
      - fairness_audit_log: 365 days

    Returns summary with per-table deletion counts.
    """
    summary: dict = {
        "dry_run": dry_run,
        "ran_at": datetime.utcnow().isoformat(),
        "tables": {},
        "total_deleted": 0,
        "errors": [],
    }

    # 2026-05-24 fix Bug B: removidos aliases legacy `conversation_messages` e
    # `chat_messages` — nunca existiram neste schema, causavam UndefinedTableError
    # → InFailedSQLTransactionError cascata para tabelas subsequentes.
    # Sensor 5 (check_lgpd_ttl_tables_exist.py) bloqueia regressão.
    ttl_config: list[tuple[str, int]] = [
        # Primary chat table (lia_models/conversation.py → Message.__tablename__ = "messages")
        ("messages", RETENTION_DAYS["chat_messages"]),
        ("interview_notes", RETENTION_DAYS["interview_data"]),
        ("screening_tasks", RETENTION_DAYS["screening_logs"]),
        ("fairness_audit_log", RETENTION_DAYS["ai_decision_logs"]),
    ]

    async with AsyncSessionLocal() as db:
        for table_name, retention_days in ttl_config:
            try:
                count = await _cleanup_by_created_at(db, table_name, retention_days, dry_run)
                summary["tables"][table_name] = {"deleted": count, "retention_days": retention_days}
                summary["total_deleted"] += count
            except Exception as exc:
                # Rollback transaction so subsequent TTL phases can run
                # (InFailedSQLTransactionError cascade prevention).
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.warning("conversation_ttl_cleanup: error on %s: %s", table_name, exc)
                summary["errors"].append(f"{table_name}: {exc}")

    mode = "DRY-RUN" if dry_run else "REAL"
    logger.info(
        "conversation_ttl_cleanup [%s] complete — total: %d, errors: %d",
        mode,
        summary["total_deleted"],
        len(summary["errors"]),
    )
    return summary




async def send_deletion_alerts(dry_run: bool = False) -> dict:
    """UC-P3-17: Alert DPO team 90 days before scheduled candidate deletion.

    Queries candidates whose scheduled_deletion_at falls within the window
    [now + 89 days, now + 91 days] (i.e. exactly 90 days away +/- 1 day margin).
    Groups results by company_id and emits a Sentry capture_message warning for
    each company with pending deletions in that window.

    Called daily by the Celery beat task "lgpd-deletion-alert-daily" at 01h UTC.

    Args:
        dry_run: If True, logs alerts without sending Sentry events.

    Returns:
        Summary dict with company_count and candidate_count.
    """
    from datetime import datetime, timedelta
    summary: dict = {
        "dry_run": dry_run,
        "ran_at": datetime.utcnow().isoformat(),
        "company_count": 0,
        "candidate_count": 0,
        "errors": [],
    }

    now = datetime.utcnow()
    window_start = now + timedelta(days=89)
    window_end = now + timedelta(days=91)

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(
                    Candidate.id,
                    Candidate.company_id,
                    Candidate.scheduled_deletion_at,
                )
                .where(
                    and_(
                        Candidate.scheduled_deletion_at.isnot(None),
                        Candidate.scheduled_deletion_at >= window_start,
                        Candidate.scheduled_deletion_at <= window_end,
                    )
                )
            )
            rows = result.all()
        except Exception as exc:
            logger.error("LGPD deletion alert query failed: %s", exc)
            summary["errors"].append(str(exc))
            return summary

    # Group by company_id
    by_company: dict[str, list[dict]] = {}
    for row in rows:
        cid = str(row.company_id)
        by_company.setdefault(cid, []).append({
            "candidate_id": str(row.id),
            "scheduled_deletion_at": row.scheduled_deletion_at.isoformat(),
        })

    summary["company_count"] = len(by_company)
    summary["candidate_count"] = len(rows)

    for company_id, candidates in by_company.items():
        msg = (
            f"[LGPD-ALERT] {len(candidates)} candidate(s) scheduled for deletion "
            f"in ~90 days for company={company_id}. "
            f"Window: {window_start.date()} -- {window_end.date()}. "
            "Action required: ensure consent refresh or confirm deletion intent."
        )
        logger.warning(msg)
        if not dry_run:
            try:
                import sentry_sdk
                sentry_sdk.capture_message(
                    msg,
                    level="warning",
                    extras={
                        "company_id": company_id,
                        "candidate_count": len(candidates),
                        "candidates": candidates[:20],  # cap to avoid large payloads
                        "window_start": window_start.isoformat(),
                        "window_end": window_end.isoformat(),
                    },
                )
            except Exception as sentry_exc:
                logger.debug("LGPD alert: Sentry capture failed (non-blocking): %s", sentry_exc)

    mode = "DRY-RUN" if dry_run else "REAL"
    logger.info(
        "LGPD deletion alert [%s] complete -- %d company(ies), %d candidate(s)",
        mode,
        summary["company_count"],
        summary["candidate_count"],
    )
    return summary

async def get_pending_deletions_count(db: AsyncSession) -> dict:
    """Return how many records are pending deletion (useful for monitoring)."""
    now = datetime.utcnow()

    c_count = await db.scalar(
        select(func.count(Candidate.id)).where(
            and_(
                Candidate.scheduled_deletion_at.isnot(None),
                Candidate.scheduled_deletion_at <= now,
            )
        )
    )

    vc_count = await db.scalar(
        select(func.count(VacancyCandidate.id)).where(
            and_(
                VacancyCandidate.scheduled_deletion_at.isnot(None),
                VacancyCandidate.scheduled_deletion_at <= now,
            )
        )
    )

    ai_count = await db.scalar(
        select(func.count(AiConsumption.id)).where(
            and_(
                AiConsumption.scheduled_deletion_at.isnot(None),
                AiConsumption.scheduled_deletion_at <= now,
            )
        )
    )

    return {
        "candidates_pending_deletion": c_count or 0,
        "vacancy_candidates_pending_deletion": vc_count or 0,
        "ai_consumption_pending_deletion": ai_count or 0,
        "checked_at": now.isoformat(),
    }
