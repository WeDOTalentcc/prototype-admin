"""Shared prompts module."""
from .agent_prompts import get_agent_prompt
from .prompt_registry import (
    prompt_registry,
    init_prompts,
    get_prompt_from_registry,
    PromptVersion,
    PromptRegistry,
)
from .loader import PromptLoader
from .templates import PromptTemplate, PromptLibrary, prompt_library
from .few_shot_examples import (
    FewShotExamples,
    JOB_EXTRACTION_EXAMPLES,
    INTENT_CLASSIFICATION_EXAMPLES,
    SALARY_ANALYSIS_EXAMPLES,
    COMPETENCY_EXTRACTION_EXAMPLES,
    ORCHESTRATION_DECISION_EXAMPLES,
    RESPONSIBILITY_GENERATION_EXAMPLES,
)
from .cot import ChainOfThoughtBuilder, CoTStrategy, cot_builder
from .job_wizard import (
    register_job_wizard_templates,
    get_orchestrator_prompt,
    get_field_extraction_prompt,
    get_salary_analysis_prompt,
    get_competency_prompt,
    get_intent_prompt,
    ORCHESTRATOR_TEMPLATE,
    FIELD_EXTRACTION_TEMPLATE,
    SALARY_ANALYSIS_TEMPLATE,
    COMPETENCY_SUGGESTION_TEMPLATE,
    RESPONSIBILITY_GENERATION_TEMPLATE,
    INTENT_CLASSIFICATION_TEMPLATE,
    JD_GENERATION_TEMPLATE,
)

__all__ = [
    "get_agent_prompt",
    "prompt_registry",
    "init_prompts",
    "get_prompt_from_registry",
    "PromptVersion",
    "PromptRegistry",
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
]
