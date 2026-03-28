"""Talent context — re-exports from app/domains/recruiter_assistant/agents/."""
from app.domains.recruiter_assistant.agents.talent_system_prompt import get_talent_system_prompt
from app.domains.recruiter_assistant.agents.talent_stage_context import (
    get_stage_context,
    get_transition_prompt,
)

__all__ = [
    "get_talent_system_prompt",
    "get_stage_context",
    "get_transition_prompt",
]
