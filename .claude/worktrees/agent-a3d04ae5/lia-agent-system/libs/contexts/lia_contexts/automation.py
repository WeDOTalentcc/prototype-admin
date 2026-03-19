"""Automation context — re-exports from app/domains/automation/agents/."""
from app.domains.automation.agents.automation_system_prompt import get_automation_system_prompt
from app.domains.automation.agents.automation_stage_context import (
    get_stage_context,
    get_stage_tools,
    get_transition_prompt,
)

__all__ = [
    "get_automation_system_prompt",
    "get_stage_context",
    "get_stage_tools",
    "get_transition_prompt",
]
