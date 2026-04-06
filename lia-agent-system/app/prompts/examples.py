# Shim — real implementation moved to app/shared/prompts/few_shot_examples.py (I3b)
from app.shared.prompts.few_shot_examples import *  # noqa: F401,F403
from app.shared.prompts.few_shot_examples import (  # noqa: F401
    COMPETENCY_EXTRACTION_EXAMPLES,
    INTENT_CLASSIFICATION_EXAMPLES,
    JOB_EXTRACTION_EXAMPLES,
    ORCHESTRATION_DECISION_EXAMPLES,
    RESPONSIBILITY_GENERATION_EXAMPLES,
    SALARY_ANALYSIS_EXAMPLES,
    FewShotExamples,
)
