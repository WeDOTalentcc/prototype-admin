"""
System prompts for specialized LIA agents.

Uses SystemPromptBuilder for dynamic prompt composition.
Domain-specific additions are loaded from agent_prompts.yaml (lean format).
Persona/ethics inherited automatically from lia_persona.yaml via the builder.
"""
from app.shared.prompts.loader import PromptLoader
from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

_shared = PromptLoader.load("shared/lia_persona")

LIA_PERSONA = _shared["prompts"]["lia_persona"]
HR_VOCABULARY = _shared["prompts"]["hr_vocabulary"]
DATA_PERSISTENCE_GUIDELINES = _shared["prompts"]["data_persistence_guidelines"]
ETHICAL_GUIDELINES = _shared["prompts"]["ethical_guidelines"]


def get_agent_prompt(agent_type: str, context: str = "", **kwargs) -> str:
    """Get composed prompt for an agent type using SystemPromptBuilder.

    This is the primary entry point for getting agent prompts.
    The builder composes: persona_base + domain_additions + any dynamic context.
    """
    return SystemPromptBuilder.build(
        agent_type=agent_type,
        extra_instructions=context or "",
        **kwargs,
    )






def get_lia_persona() -> str:
    return LIA_PERSONA


