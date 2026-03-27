"""Wizard context — re-exports stage definitions and prompt builder."""
from app.domains.job_management.agents.stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
)
from app.domains.job_management.agents.wizard_system_prompt import build_system_prompt

__all__ = ["STAGE_DEFINITIONS", "get_stage_context", "build_system_prompt"]
