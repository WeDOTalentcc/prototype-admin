"""
Wizard Stage Context - Alias for stage_context.py to follow the 4-file naming convention.

All domain agents follow the pattern: {domain}_react_agent.py, {domain}_tool_registry.py,
{domain}_system_prompt.py, {domain}_stage_context.py. This module re-exports from the
original stage_context module for consistency.
"""
from app.domains.job_management.agents.stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
    get_transition_prompt,
)

__all__ = [
    "STAGE_DEFINITIONS",
    "get_stage_context",
    "get_transition_prompt",
]
