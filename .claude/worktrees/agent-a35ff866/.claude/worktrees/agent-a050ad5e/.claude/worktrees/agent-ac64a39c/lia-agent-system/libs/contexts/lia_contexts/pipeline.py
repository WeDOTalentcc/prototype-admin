"""Pipeline context — re-exports stage context and prompt builder."""
from app.domains.cv_screening.agents.pipeline_stage_context import get_stage_context
from app.domains.cv_screening.agents.pipeline_system_prompt import get_pipeline_system_prompt

__all__ = ["get_stage_context", "get_pipeline_system_prompt"]
