"""
Defensive Prompts - Prompt engineering for robust agent behavior.

This module provides:
- Clarification triggers for ambiguous requests
- Out-of-scope response templates
- Ambiguity detection prompts
- Error recovery instructions

Prompts now loaded from YAML files via PromptLoader.
"""


from app.shared.prompts.loader import PromptLoader

_defensive = PromptLoader.load("shared/defensive")
_prompts = _defensive["prompts"]

CLARIFICATION_TRIGGERS = _prompts["clarification_triggers"]
OUT_OF_SCOPE_RESPONSES = _prompts["out_of_scope_responses"]
WHAT_I_CAN_DO = _prompts["what_i_can_do"]
AMBIGUITY_DETECTION_PROMPT = _prompts["ambiguity_detection_prompt"]
ERROR_RECOVERY_PROMPT = _prompts["error_recovery_prompt"]
DATA_PERSISTENCE_CONFIRMATION = _prompts["data_persistence_confirmation"]


def get_defensive_prompt_section(agent_type: str) -> str:
    """
    Get defensive prompt section to add to agent system prompts.
    
    Args:
        agent_type: Type of agent (job_planner, sourcing, etc.)
        
    Returns:
        Defensive prompt section to append
    """
    return _prompts["defensive_prompt_section"]


def get_clarification_message(
    missing_items: list[str],
    context: dict[str, str] = None
) -> str:
    """
    Generate a clarification message based on missing items.
    
    Args:
        missing_items: List of items that need clarification
        context: Optional context for personalization
        
    Returns:
        Clarification message
    """
    if not missing_items:
        return ""
    
    message = "Para continuar, preciso de mais algumas informações:\n\n"
    
    item_messages = _prompts["clarification_item_messages"]
    
    for item in missing_items:
        if item in item_messages:
            message += f"• {item_messages[item]}\n"
        else:
            message += f"• Por favor, informe: {item}\n"
    
    return message


def get_out_of_scope_response(category: str = "general") -> str:
    """
    Get an appropriate out-of-scope response.

    DEPRECATED (G8 canonical fix 2026-05-24): this function appends
    WHAT_I_CAN_DO (a hardcoded bullet list) which contradicts
    lia_persona.yaml Anti-pattern #1 ("Resposta-lista-de-capabilities"
    is forbidden). Persona requires contextual responses based on
    current page / open vacancies / pipeline — not generic feature dumps.

    No live callers as of 2026-05-24 audit. Canonical sources:
      - lia_persona.yaml (improvisation rules)
      - system_prompt_builder.py Capabilities — Navegação section (G3)
      - system_prompt_builder.py Capabilities — Ações section (G6)

    Args:
        category: Category of out-of-scope request

    Returns:
        Friendly out-of-scope response
    """
    response = OUT_OF_SCOPE_RESPONSES.get(category, OUT_OF_SCOPE_RESPONSES["general"])
    
    if category not in ["inappropriate", "personal"]:
        response += f"\n\n{WHAT_I_CAN_DO}"
    
    return response


def format_confirmation_message(action: str, details: dict[str, str]) -> str:
    """
    Format a confirmation message for a pending action.
    
    Args:
        action: Description of the action
        details: Details to confirm
        
    Returns:
        Formatted confirmation message
    """
    message = "📝 **Confirme a ação:**\n\n"
    message += f"**{action}**\n\n"
    
    if details:
        message += "**Detalhes:**\n"
        for key, value in details.items():
            message += f"• {key}: {value}\n"
    
    message += "\n✅ Responda **sim** para confirmar ou **não** para cancelar."
    
    return message
