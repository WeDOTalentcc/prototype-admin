"""
DEPRECATED — Shim de retrocompatibilidade (Sprint I3b).

Local canônico: app/domains/recruiter_assistant/prompts/talent_assistant_prompts.py

Re-exporta tudo para manter compatibilidade com imports legados.
Não adicionar lógica aqui.
"""
from app.domains.recruiter_assistant.prompts.talent_assistant_prompts import (  # noqa: F401
    TalentCommandType,
    build_talent_prompt,
    detect_talent_command_type,
    detect_talent_command_type_enhanced,
    get_talent_prompt_template,
    get_talent_system_prompt,
)

__all__ = [
    "TalentCommandType",
    "detect_talent_command_type",
    "detect_talent_command_type_enhanced",
    "get_talent_system_prompt",
    "get_talent_prompt_template",
    "build_talent_prompt",
]
