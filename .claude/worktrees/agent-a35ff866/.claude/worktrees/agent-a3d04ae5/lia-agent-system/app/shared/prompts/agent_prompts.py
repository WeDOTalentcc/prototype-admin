"""
System prompts for specialized LIA agents.

Each agent has a unique persona, capabilities, and communication style.
Based on WeDOTalent Multi-Agent Architecture v2.2

Updated: 
- Adicionadas responsabilidades de persistência de dados e sincronização ATS
- Adicionado vocabulário técnico de RH brasileiro
- Adicionada persona LIA unificada
- Expandidos formatos de resposta com seções estruturadas
- Prompts now loaded from YAML files via PromptLoader
"""
from app.shared.prompts.loader import PromptLoader

_shared = PromptLoader.load("shared/lia_persona")
_agents = PromptLoader.load("shared/agent_prompts")

LIA_PERSONA = _shared["prompts"]["lia_persona"]
HR_VOCABULARY = _shared["prompts"]["hr_vocabulary"]
DATA_PERSISTENCE_GUIDELINES = _shared["prompts"]["data_persistence_guidelines"]
ETHICAL_GUIDELINES = _shared["prompts"]["ethical_guidelines"]

ORCHESTRATOR_PROMPT = _agents["prompts"]["orchestrator"]
JOB_PLANNER_PROMPT = _agents["prompts"]["job_planner"]
SOURCING_PROMPT = _agents["prompts"]["sourcing"]
CV_SCREENING_PROMPT = _agents["prompts"]["cv_screening"]
INTERVIEWER_PROMPT = _agents["prompts"]["interviewer"]
WSI_EVALUATOR_PROMPT = _agents["prompts"]["wsi_evaluator"]
SCHEDULING_PROMPT = _agents["prompts"]["scheduling"]
ANALYST_FEEDBACK_PROMPT = _agents["prompts"]["analyst_feedback"]
ATS_INTEGRATOR_PROMPT = _agents["prompts"]["ats_integrator"]
RECRUITER_ASSISTANT_PROMPT = _agents["prompts"]["recruiter_assistant"]
PROACTIVE_INSIGHTS_PROMPT = _agents["prompts"]["proactive_insights"]


def get_agent_prompt(agent_type: str, context: str = "") -> str:
    """Get the appropriate prompt for an agent type."""
    prompts = {
        "orchestrator": ORCHESTRATOR_PROMPT,
        "job_planner": JOB_PLANNER_PROMPT,
        "sourcing": SOURCING_PROMPT,
        "cv_screening": CV_SCREENING_PROMPT,
        "interviewer": INTERVIEWER_PROMPT,
        "wsi_evaluator": WSI_EVALUATOR_PROMPT,
        "scheduling": SCHEDULING_PROMPT,
        "analyst_feedback": ANALYST_FEEDBACK_PROMPT,
        "ats_integrator": ATS_INTEGRATOR_PROMPT,
        "recruiter_assistant": RECRUITER_ASSISTANT_PROMPT,
        "proactive_insights": PROACTIVE_INSIGHTS_PROMPT
    }

    prompt_template = prompts.get(agent_type, ORCHESTRATOR_PROMPT)
    return prompt_template.replace("{{context}}", context or "Nenhum contexto adicional")


def get_data_persistence_guidelines() -> str:
    """Get the universal data persistence guidelines for all agents."""
    return DATA_PERSISTENCE_GUIDELINES


def get_hr_vocabulary() -> str:
    """Get the Brazilian HR technical vocabulary reference."""
    return HR_VOCABULARY


def get_lia_persona() -> str:
    """Get the unified LIA persona prompt."""
    return LIA_PERSONA


def get_ethical_guidelines() -> str:
    """Get the ethical guidelines for all agents."""
    return ETHICAL_GUIDELINES
