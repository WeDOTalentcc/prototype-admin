"""
Action Handlers — decomposition of ActionExecutor by action category.

Modules:
- candidate_actions: move_candidate, reprovar, aprovar, atualizar_campo, analisar_perfil, start_screening
- job_actions: pause_job, close_job, duplicate_job, reopen_job
- pipeline_actions: create_task, create_note, generate_daily_briefing
- communication_actions: send_email, schedule_interview, create_generic_event
"""
from .candidate_actions import execute_candidate_action
from .communication_actions import execute_communication_action
from .job_actions import execute_job_action
from .pipeline_actions import execute_pipeline_action

__all__ = [
    "execute_candidate_action",
    "execute_job_action",
    "execute_pipeline_action",
    "execute_communication_action",
]
