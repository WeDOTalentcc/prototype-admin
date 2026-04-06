"""
DEPRECATED — Shim de retrocompatibilidade (Sprint I3b).

Local canônico: app/domains/recruiter_assistant/prompts/jobs_management_prompts.py

Re-exporta tudo para manter compatibilidade com imports legados.
Não adicionar lógica aqui.
"""
from app.domains.recruiter_assistant.prompts.jobs_management_prompts import (  # noqa: F401
    JobsManagementCommandType,
    build_jobs_management_prompt,
    detect_jobs_command_type,
    detect_jobs_command_type_enhanced,
    get_jobs_management_prompt_template,
    get_jobs_management_system_prompt,
    resolve_jobs_ui_action,
)

__all__ = [
    "JobsManagementCommandType",
    "detect_jobs_command_type",
    "detect_jobs_command_type_enhanced",
    "get_jobs_management_system_prompt",
    "get_jobs_management_prompt_template",
    "build_jobs_management_prompt",
    "resolve_jobs_ui_action",
]
