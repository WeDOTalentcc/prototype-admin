"""
DEPRECATED — Shim de retrocompatibilidade (Sprint I3b).

Local canônico: app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py

Re-exporta tudo para manter compatibilidade com imports legados.
Não adicionar lógica aqui.
"""
from app.domains.recruiter_assistant.prompts.kanban_assistant_prompts import (  # noqa: F401
    KANBAN_COMMAND_TYPES,
    KanbanCommandType,
    detect_command_type,
    format_candidates_context,
    format_job_context,
    format_selected_candidates_context,
    get_kanban_prompt_template,
    get_system_prompt,
    resolve_ui_action,
)

__all__ = [
    "KanbanCommandType",
    "KANBAN_COMMAND_TYPES",
    "get_system_prompt",
    "detect_command_type",
    "resolve_ui_action",
    "get_kanban_prompt_template",
    "format_job_context",
    "format_candidates_context",
    "format_selected_candidates_context",
]
