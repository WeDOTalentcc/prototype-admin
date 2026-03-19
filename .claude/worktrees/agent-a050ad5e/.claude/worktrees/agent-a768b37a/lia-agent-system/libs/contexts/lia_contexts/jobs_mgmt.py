"""Jobs Management context — re-exports from app/domains/recruiter_assistant/agents/."""
from app.domains.recruiter_assistant.agents.jobs_mgmt_system_prompt import get_jobs_mgmt_system_prompt
from app.domains.recruiter_assistant.agents.jobs_mgmt_stage_context import (
    get_stage_context,
    get_transition_prompt,
    get_pipeline_prediction_block,
)

__all__ = [
    "get_jobs_mgmt_system_prompt",
    "get_stage_context",
    "get_transition_prompt",
    "get_pipeline_prediction_block",
]
