"""
LIA Prompt Engineering System.

Shim module — real implementations moved to app/shared/prompts/ (I3b cleanup).
All public symbols re-exported for backwards compatibility.
"""
# Re-export everything from shared/prompts
from app.domains.recruiter_assistant.prompts.kanban_assistant_prompts import (  # noqa: F401
    KANBAN_COMMAND_TYPES,
    detect_command_type,
    get_kanban_prompt_template,
    get_system_prompt,
)
from app.shared.prompts.cot import ChainOfThoughtBuilder, CoTStrategy, cot_builder  # noqa: F401
from app.shared.prompts.few_shot_examples import (  # noqa: F401
    COMPETENCY_EXTRACTION_EXAMPLES,
    INTENT_CLASSIFICATION_EXAMPLES,
    JOB_EXTRACTION_EXAMPLES,
    ORCHESTRATION_DECISION_EXAMPLES,
    RESPONSIBILITY_GENERATION_EXAMPLES,
    SALARY_ANALYSIS_EXAMPLES,
    FewShotExamples,
)
from app.shared.prompts.job_wizard import (  # noqa: F401
    COMPETENCY_SUGGESTION_TEMPLATE,
    FIELD_EXTRACTION_TEMPLATE,
    INTENT_CLASSIFICATION_TEMPLATE,
    JD_GENERATION_TEMPLATE,
    ORCHESTRATOR_TEMPLATE,
    RESPONSIBILITY_GENERATION_TEMPLATE,
    SALARY_ANALYSIS_TEMPLATE,
    get_competency_prompt,
    get_field_extraction_prompt,
    get_intent_prompt,
    get_orchestrator_prompt,
    get_salary_analysis_prompt,
    register_job_wizard_templates,
)
from app.shared.prompts.loader import PromptLoader  # noqa: F401
from app.shared.prompts.templates import PromptLibrary, PromptTemplate, prompt_library  # noqa: F401

__all__ = [
    "PromptLoader",
    "PromptTemplate",
    "PromptLibrary",
    "prompt_library",
    "FewShotExamples",
    "JOB_EXTRACTION_EXAMPLES",
    "INTENT_CLASSIFICATION_EXAMPLES",
    "SALARY_ANALYSIS_EXAMPLES",
    "COMPETENCY_EXTRACTION_EXAMPLES",
    "ORCHESTRATION_DECISION_EXAMPLES",
    "RESPONSIBILITY_GENERATION_EXAMPLES",
    "ChainOfThoughtBuilder",
    "CoTStrategy",
    "cot_builder",
    "register_job_wizard_templates",
    "get_orchestrator_prompt",
    "get_field_extraction_prompt",
    "get_salary_analysis_prompt",
    "get_competency_prompt",
    "get_intent_prompt",
    "ORCHESTRATOR_TEMPLATE",
    "FIELD_EXTRACTION_TEMPLATE",
    "SALARY_ANALYSIS_TEMPLATE",
    "COMPETENCY_SUGGESTION_TEMPLATE",
    "RESPONSIBILITY_GENERATION_TEMPLATE",
    "INTENT_CLASSIFICATION_TEMPLATE",
    "JD_GENERATION_TEMPLATE",
    "KANBAN_COMMAND_TYPES",
    "get_kanban_prompt_template",
    "get_system_prompt",
    "detect_command_type",
]
