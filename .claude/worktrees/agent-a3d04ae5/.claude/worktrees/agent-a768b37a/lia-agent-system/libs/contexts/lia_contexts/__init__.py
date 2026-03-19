"""
lia-contexts — agent system prompts and stage context definitions.

All 9 domain contexts are exposed as sub-modules:
    from lia_contexts.wizard import get_stage_context, build_system_prompt
    from lia_contexts.pipeline import get_pipeline_system_prompt
    from lia_contexts.pipeline_transition import get_pipeline_system_prompt
    from lia_contexts.sourcing import get_sourcing_system_prompt
    from lia_contexts.kanban import get_kanban_system_prompt
    from lia_contexts.talent import get_talent_system_prompt
    from lia_contexts.jobs_mgmt import get_jobs_mgmt_system_prompt
    from lia_contexts.policy import get_policy_system_prompt
    from lia_contexts.automation import get_automation_system_prompt
"""

__all__ = [
    "wizard",
    "pipeline",
    "pipeline_transition",
    "sourcing",
    "kanban",
    "talent",
    "jobs_mgmt",
    "policy",
    "automation",
]
