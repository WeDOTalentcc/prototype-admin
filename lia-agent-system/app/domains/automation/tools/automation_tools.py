# LIA-T02 | LGPD Art. 7 (legitimate interest – HR automation) / EU AI Act Annex III (high-risk HR systems)
"""LangChain tools for Automation domain."""
import logging
import uuid
from datetime import UTC, datetime

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def trigger_workflow(workflow_id: str, trigger_data: str) -> dict:
    """Trigger an automated workflow with the provided parameters.

    trigger_data should be a JSON string containing the workflow input parameters.
    """
    logger.info("trigger_workflow: workflow_id=%s data=%s", workflow_id, trigger_data)
    run_id = f"WF-{uuid.uuid4().hex[:10].upper()}"
    return {
        "workflow_run_id": run_id,
        "status": "triggered",
        "workflow_id": workflow_id,
        "trigger_data": trigger_data,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool
def send_automated_email(
    template_id: str, recipient_email: str, template_vars: str
) -> dict:
    """Send an automated email to a recipient using a predefined template.

    template_vars should be a JSON string with the variable substitutions for the template.
    """
    # LGPD Art. 12: Do not log recipient_email (PII) — log only template identifier
    logger.info("send_automated_email: template=%s", template_id)
    message_id = f"MSG-{uuid.uuid4().hex[:10].upper()}"
    return {
        "message_id": message_id,
        "status": "sent",
        "template_id": template_id,
        "recipient": recipient_email,
        "template_vars": template_vars,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool
def update_candidate_status(
    candidate_id: str, new_status: str, pipeline_stage: str
) -> dict:
    """Automate a candidate's status update within the recruitment pipeline.

    new_status must be one of: 'active', 'on_hold', 'rejected', 'hired'.
    """
    logger.info(
        "update_candidate_status: candidate=%s status=%s stage=%s",
        candidate_id, new_status, pipeline_stage,
    )
    return {
        "candidate_id": candidate_id,
        "old_status": "unknown",
        "new_status": new_status,
        "pipeline_stage": pipeline_stage,
        "updated_at": datetime.now(UTC).isoformat(),
    }


@tool
def bulk_send_notifications(
    recipient_ids: str, notification_type: str, message_template: str
) -> dict:
    """Send bulk notifications to a set of recipients.

    recipient_ids should be a comma-separated string of recipient IDs.
    """
    logger.info(
        "bulk_send_notifications: type=%s recipients=%s", notification_type, recipient_ids
    )
    ids = [r.strip() for r in recipient_ids.split(",") if r.strip()]
    sent_count = len(ids)
    return {
        "sent_count": sent_count,
        "failed_count": 0,
        "notification_type": notification_type,
        "recipient_ids": ids,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool
def schedule_reminder(
    entity_id: str,
    entity_type: str,
    reminder_datetime: str,
    reminder_message: str,
) -> dict:
    """Schedule a future reminder for a given entity (candidate, interviewer, job, or application).

    entity_type must be one of: 'candidate', 'interviewer', 'job', 'application'.
    """
    logger.info(
        "schedule_reminder: entity_id=%s type=%s trigger=%s",
        entity_id, entity_type, reminder_datetime,
    )
    reminder_id = f"REM-{uuid.uuid4().hex[:8].upper()}"
    return {
        "reminder_id": reminder_id,
        "status": "scheduled",
        "trigger_at": reminder_datetime,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "message": reminder_message,
        "created_at": datetime.now(UTC).isoformat(),
    }


@tool
def get_automation_logs(workflow_id: str, limit: int = 10) -> dict:
    """Retrieve the most recent execution logs for a given workflow.

    Returns up to `limit` log entries with simulated execution details.
    """
    logger.info("get_automation_logs: workflow_id=%s limit=%d", workflow_id, limit)
    logs = []
    for i in range(min(limit, 5)):
        logs.append(
            {
                "run_id": f"WF-{uuid.uuid4().hex[:8].upper()}",
                "status": "success",
                "executed_at": datetime.now(UTC).isoformat(),
                "duration_ms": (i + 1) * 120,
            }
        )
    return {
        "workflow_id": workflow_id,
        "logs": logs,
        "count": len(logs),
    }
