"""Shared prompts module."""
from .agent_prompts import get_agent_prompt
from .cot import ChainOfThoughtBuilder, CoTStrategy, cot_builder
from .few_shot_examples import (
    COMPETENCY_EXTRACTION_EXAMPLES,
    INTENT_CLASSIFICATION_EXAMPLES,
    JOB_EXTRACTION_EXAMPLES,
    ORCHESTRATION_DECISION_EXAMPLES,
    RESPONSIBILITY_GENERATION_EXAMPLES,
    SALARY_ANALYSIS_EXAMPLES,
    FewShotExamples,
)
from .job_wizard import (
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
from .loader import PromptLoader
from .prompt_registry import (
    PromptRegistry,
    PromptVersion,
    get_prompt_from_registry,
    init_prompts,
    prompt_registry,
)
from .templates import PromptLibrary, PromptTemplate, prompt_library

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
