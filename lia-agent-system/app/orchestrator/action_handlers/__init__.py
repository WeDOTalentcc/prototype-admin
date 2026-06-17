"""
Action Handlers — decomposition of ActionExecutor by action category.

Modules:
- candidate_actions: move_candidate, reprovar, aprovar, atualizar_campo, analisar_perfil, start_screening, batch_move
- job_actions: pause_job, close_job, duplicate_job, reopen_job, set_job_urgent
- pipeline_actions: create_task, create_note, generate_daily_briefing, create_automation, check_proactive_alerts
- communication_actions: send_email, schedule_interview, create_generic_event, send_feedback, send_whatsapp, send_screening_invite, send_candidate_report, send_progress_report, share_candidate_profile
- sourcing_actions: tag_candidates, rank_candidates, compare_candidates, search_candidates, suggest_candidates, add_candidate, export_candidates, favorite_candidate
- analytics_actions: generate_kpi_report, job_health_check, analyze_funnel
- interview_actions: reschedule_interview, cancel_interview, send_interview_reminder, list_today_interviews, generate_self_scheduling_link
"""
from .analytics_actions import execute_analytics_action
from .candidate_actions import execute_candidate_action
from .communication_actions import execute_communication_action
from .interview_actions import execute_interview_action
from .job_actions import execute_job_action
from .pipeline_actions import execute_pipeline_action
from .sourcing_actions import execute_sourcing_action

__all__ = [
    "execute_candidate_action",
    "execute_job_action",
    "execute_pipeline_action",
    "execute_communication_action",
    "execute_sourcing_action",
    "execute_analytics_action",
    "execute_interview_action",
]
