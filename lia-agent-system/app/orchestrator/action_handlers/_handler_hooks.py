"""
Shared cross-cutting hooks for action handlers:
- DB-level candidate name resolution (when UUID is unavailable)
- Audit trail logging for write operations
- Conditional Rails sync on data-modifying actions
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


_TRIGGER_MAP = {
    "candidate_created": "candidate_created",
    "candidate_updated": "candidate_updated",
    "candidate_moved": "status_change",
    "candidate_tagged": "candidate_updated",
    "candidate_favorited": "candidate_updated",
    "screening_started": "status_change",
    "interview_scheduled": "interview_scheduled",
    "interview_rescheduled": "interview_scheduled",
    "interview_cancelled": "interview_scheduled",
    "scheduling_link_created": "interview_scheduled",
}


async def resolve_candidate_by_name(
    candidate_name: str,
    company_id: str | None = None,
) -> dict[str, Any] | None:
    from sqlalchemy import text

    from app.core.database import AsyncSessionLocal

    if not candidate_name or candidate_name in ("o candidato", ""):
        return None

    async with AsyncSessionLocal() as db:
        sql = """
            SELECT c.id, c.name, c.email
            FROM candidates c
        """
        bind: dict[str, Any] = {"q": f"%{candidate_name}%"}

        if company_id:
            sql += """
                JOIN vacancy_candidates vc ON vc.candidate_id = c.id
                WHERE vc.company_id = :co
                  AND c.name ILIKE :q
            """
            bind["co"] = str(company_id)
        else:
            sql += " WHERE c.name ILIKE :q"

        sql += " ORDER BY c.name LIMIT 1"
        result = await db.execute(text(sql), bind)
        row = result.fetchone()
        if row:
            return {"id": str(row.id), "name": row.name, "email": row.email}
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
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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

