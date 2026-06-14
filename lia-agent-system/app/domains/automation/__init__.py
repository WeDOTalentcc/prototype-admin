__domain_type__ = "agentic"  # ADR-031 §6.1
# Automation & Tasks domain
from app.domains.automation.tools.automation_tools import (
    bulk_send_notifications,
    get_automation_logs,
    schedule_reminder,
    send_automated_email,
    trigger_workflow,
    update_candidate_status,
)

__all__ = [
    "trigger_workflow",
    "send_automated_email",
    "update_candidate_status",
    "bulk_send_notifications",
    "schedule_reminder",
    "get_automation_logs",
]
