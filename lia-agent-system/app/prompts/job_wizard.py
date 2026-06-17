# Shim — real implementation moved to app/shared/prompts/job_wizard.py (I3b)
from app.shared.prompts.job_wizard import *  # noqa: F401,F403
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
