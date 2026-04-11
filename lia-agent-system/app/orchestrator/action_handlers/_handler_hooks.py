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
                WHERE vc.company_id = CAST(:co AS uuid)
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
) -> None:
    try:
        from app.shared.compliance.audit_service import audit_service

        await audit_service.log_decision(
            company_id=company_id or "system",
            agent_name="lia_chat_action",
            decision_type=action_type,
            action=action_type,
            decision="executed",
            reasoning=[f"Action {action_type} executed via chat"],
            criteria_used=[],
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
        )
    except Exception as e:
        logger.debug(f"Audit log skipped for {action_type}: {e}")


async def sync_to_rails(
    event_type: str,
    entity_type: str,
    entity_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    if not RAILS_ENABLED:
        return
    try:
        from app.domains.integrations_hub.services.rails_adapter import RailsAdapter

        adapter = RailsAdapter()
        await adapter.publish_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
        )
    except Exception as e:
        logger.warning(f"Rails sync skipped for {event_type}/{entity_type}: {e}")
