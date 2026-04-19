"""
Shared cross-cutting hooks for action handlers:
- DB-level candidate name resolution (when UUID is unavailable)
- Audit trail logging for write operations
- Conditional Rails sync on data-modifying actions
"""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

RAILS_ENABLED = bool(os.environ.get("RAILS_API_URL"))

_TRIGGER_MAP = {
    "candidate_created": "candidate_created",
    "candidate_updated": "candidate_updated",
    "candidate_moved": "status_change",
    "candidate_tagged": "candidate_updated",
    "candidate_favorited": "candidate_updated",
    "screening_started": "status_change",
    "candidate_rejected": "status_change",
    "interview_scheduled": "interview_scheduled",
    "interview_rescheduled": "interview_scheduled",
    "interview_cancelled": "interview_scheduled",
    "scheduling_link_created": "interview_scheduled",
}


async def resolve_candidate_by_name(
    candidate_name: str,
    company_id: str | None = None,
) -> dict[str, Any] | None:
    """
    Resolve a candidate UUID from a display name.

    Strategy:
    1. Direct ILIKE query on candidates, filtered by company via vacancy_candidates JOIN.
       Calls set_config for RLS before every query.
    2. Fallback: split into words (last name first), search each word, compare full
       names with accents stripped in Python (handles "Joao" <-> "Joao").

    Each sub-query uses an independent AsyncSessionLocal to avoid nested-session
    issues in asyncpg connection pools.
    """
    import unicodedata
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal

    if not candidate_name or candidate_name in ("o candidato", ""):
        return None

    def _strip_accents(s: str) -> str:
        return "".join(
            c for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        )

    co_str = str(company_id) if company_id else ""

    # ── Query 1: direct ILIKE match ─────────────────────────────────────────
    try:
        async with AsyncSessionLocal() as db:
            if co_str:
                await db.execute(
                    text("SELECT set_config('app.company_id', :co, true)"),
                    {"co": co_str},
                )
                sql = (
                    "SELECT c.id, c.name, c.email FROM candidates c"
                    " JOIN vacancy_candidates vc ON CAST(vc.candidate_id AS uuid) = c.id"
                    " WHERE vc.company_id = :co AND c.name ILIKE :q"
                    " ORDER BY c.name LIMIT 1"
                )
                bind: dict = {"q": f"%{candidate_name}%", "co": co_str}
            else:
                sql = (
                    "SELECT c.id, c.name, c.email FROM candidates c"
                    " WHERE c.name ILIKE :q ORDER BY c.name LIMIT 1"
                )
                bind = {"q": f"%{candidate_name}%"}

            result = await db.execute(text(sql), bind)
            row = result.fetchone()
            if row:
                logger.info("[resolve_by_name] Direct match: %s -> %s", candidate_name, row.name)
                return {"id": str(row.id), "name": row.name, "email": row.email}

        logger.info(
            "[resolve_by_name] No direct ILIKE match for '%s' company=%s — word fallback",
            candidate_name, co_str or "any",
        )
    except Exception as exc:
        logger.error("[resolve_by_name] Query-1 error for '%s': %s", candidate_name, exc)

    # ── Query 2: word-by-word fallback with accent stripping ────────────────
    target_unaccented = _strip_accents(candidate_name).lower()
    parts = candidate_name.strip().split()
    search_parts = (parts[-1:] + parts[:-1]) if len(parts) > 1 else parts
    rows_fb: list = []

    for part in search_parts:
        if len(part) < 3:
            continue
        try:
            async with AsyncSessionLocal() as db_fb:
                if co_str:
                    await db_fb.execute(
                        text("SELECT set_config('app.company_id', :co, true)"),
                        {"co": co_str},
                    )
                    sql_fb = (
                        "SELECT c.id, c.name, c.email FROM candidates c"
                        " JOIN vacancy_candidates vc ON CAST(vc.candidate_id AS uuid) = c.id"
                        " WHERE vc.company_id = :cofb AND c.name ILIKE :qfb"
                        " ORDER BY c.name LIMIT 20"
                    )
                    bind_fb: dict = {"qfb": f"%{part}%", "cofb": co_str}
                else:
                    sql_fb = (
                        "SELECT c.id, c.name, c.email FROM candidates c"
                        " WHERE c.name ILIKE :qfb ORDER BY c.name LIMIT 20"
                    )
                    bind_fb = {"qfb": f"%{part}%"}

                res_fb = await db_fb.execute(text(sql_fb), bind_fb)
                rows_fb = res_fb.fetchall()
        except Exception as exc:
            logger.error("[resolve_by_name] Fallback error part '%s': %s", part, exc)
        if rows_fb:
            break

    # Exact unaccented match
    for r in rows_fb:
        if _strip_accents(r.name).lower() == target_unaccented:
            logger.info("[resolve_by_name] Fallback exact match: %s", r.name)
            return {"id": str(r.id), "name": r.name, "email": r.email}
    # Partial unaccented match (first word)
    for r in rows_fb:
        if _strip_accents(r.name).lower().startswith(target_unaccented.split()[0]):
            logger.info("[resolve_by_name] Fallback partial match: %s", r.name)
            return {"id": str(r.id), "name": r.name, "email": r.email}

    logger.warning(
        "[resolve_by_name] No match found for '%s' company=%s",
        candidate_name, co_str or "any",
    )
    return None


async def log_action_audit(
    action_type: str,
    company_id: str | None,
    candidate_id: str | None = None,
    job_vacancy_id: str | None = None,
    details: dict[str, Any] | None = None,
    *,
    actor_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    changes_summary: str | None = None,
) -> None:
    import json
    from datetime import datetime, timezone

    effective_actor = actor_id or "system"
    effective_entity_type = entity_type or _infer_entity_type(action_type)
    effective_entity_id = entity_id or candidate_id or job_vacancy_id

    structured_log = {
        "audit_event": "action_handler_write",
        "actor_id": effective_actor,
        "action_type": action_type,
        "entity_type": effective_entity_type,
        "entity_id": effective_entity_id,
        "company_id": company_id or "system",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "changes_summary": changes_summary or (details.get("summary") if details else None),
    }
    logger.info("AUDIT_TRAIL %s", json.dumps(structured_log, default=str))

    try:
        from app.shared.compliance.audit_service import audit_service

        reasoning_parts = [
            f"Action {action_type} executed via chat",
            f"actor_id={effective_actor}",
            f"entity_type={effective_entity_type}",
            f"entity_id={effective_entity_id}",
        ]
        if changes_summary:
            reasoning_parts.append(f"changes: {changes_summary}")

        criteria_used = [
            f"actor:{effective_actor}",
            f"entity_type:{effective_entity_type}",
        ]
        if effective_entity_id:
            criteria_used.append(f"entity_id:{effective_entity_id}")
        if changes_summary:
            criteria_used.append(f"summary:{changes_summary[:200]}")

        await audit_service.log_decision(
            company_id=company_id or "system",
            agent_name="lia_chat_action",
            decision_type=action_type,
            action=action_type,
            decision="executed",
            reasoning=reasoning_parts,
            criteria_used=criteria_used,
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
        )
    except Exception as e:
        logger.warning(f"Audit log skipped for {action_type}: {e}")


def _infer_entity_type(action_type: str) -> str:
    if "candidate" in action_type:
        return "candidate"
    if "job" in action_type or "vacancy" in action_type:
        return "job_vacancy"
    if "interview" in action_type or "schedule" in action_type:
        return "interview"
    if "email" in action_type or "template" in action_type:
        return "email_template"
    if "whatsapp" in action_type or "message" in action_type:
        return "message"
    return "action"


async def sync_to_rails(
    event_type: str,
    entity_type: str,
    entity_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    if not RAILS_ENABLED:
        return
    try:
        from app.domains.ats_integration.services.ats_sync_service import (
            ATSSyncService,
            ATSSyncTrigger,
        )

        trigger_value = _TRIGGER_MAP.get(event_type, "candidate_updated")
        try:
            trigger = ATSSyncTrigger(trigger_value)
        except ValueError:
            trigger = ATSSyncTrigger.CANDIDATE_UPDATED

        candidate_id = (data or {}).get("candidate_id") or (entity_id if entity_type == "candidate" else None)
        job_id = (data or {}).get("job_id") or (entity_id if entity_type == "job" else None)

        sync_svc = ATSSyncService()
        await sync_svc.trigger_sync(
            trigger=trigger,
            source_agent="lia_chat_action",
            ats_type="rails",
            candidate_id=candidate_id,
            job_id=job_id,
            data=data,
        )
    except Exception as e:
        logger.warning(f"Rails sync skipped for {event_type}/{entity_type}: {e}")
