"""
Pipeline System Prompt — loads domain-specific content from YAML.

Content source: app/prompts/domains/pipeline_transition.yaml
Compliance/guardrails: injected automatically by ComplianceDomainPrompt.
This file maintains the dynamic assembly function for backward compatibility.
"""
import logging
from typing import Any

from app.domains.pipeline.agents.pipeline_stage_context import (
    get_stage_context_prompt,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# YAML loader with hardcoded fallback
# ---------------------------------------------------------------------------

_yaml_cache: dict[str, Any] | None = None


def _load_yaml() -> dict[str, Any]:
    global _yaml_cache
    if _yaml_cache is not None:
        return _yaml_cache
    try:
        from app.shared.prompts.loader import PromptLoader
        _yaml_cache = PromptLoader.load("domains/pipeline_transition")
        return _yaml_cache
    except Exception as exc:
        logger.warning("[pipeline_system_prompt] YAML load failed, using fallback: %s", exc)
        _yaml_cache = {}
        return _yaml_cache


def _get(key: str, fallback: str = "") -> str:
    """Get a string value from the YAML config."""
    data = _load_yaml()
    val = data.get(key, fallback)
    return val if isinstance(val, str) else fallback


# ---------------------------------------------------------------------------
# Exported constants — loaded from YAML, backward-compatible names
# ---------------------------------------------------------------------------

def _load_identity() -> str:
    try:
        from app.shared.prompts.loader import PromptLoader
        shared = PromptLoader.load("shared/lia_persona")
        persona = shared.get("prompts", {}).get("lia_persona", "")
        if persona:
            return persona.strip() + "\n\n" + _get("identity", "")
    except Exception:
        pass
    return _get("identity", "Assistente de recrutamento da WeDOTalent.")


PIPELINE_IDENTITY = _load_identity()
SCOPE_IN = _get("scope_in", "")
SCOPE_OUT = _get("scope_out", "")
BEHAVIORAL_RULES = _get("behavioral_rules", "")
COMPANY_CALIBRATION = _get("company_calibration", "")
FAIRNESS_RULES = _get("fairness_rules", "")
LEARNING_RULES = _get("learning_rules", "")
COMMUNICATION_TRANSPARENCY_RULES = _get("communication_transparency", "")
INTERVIEW_CROSS_BEHAVIOR_RULES = _get("interview_cross_rules", "")
FEW_SHOT_EXAMPLES = _get("few_shot_examples", "")


# ---------------------------------------------------------------------------
# Dynamic prompt assembly — maintains original function signature
# ---------------------------------------------------------------------------

def get_pipeline_system_prompt(
    action_behavior: str,
    candidate_name: str = "",
    job_title: str = "",
    from_stage: str = "",
    to_stage: str = "",
    extra_context: str | None = None,
    company_type: str | None = None,
) -> str:
    stage_context = get_stage_context_prompt(
        action_behavior=action_behavior,
        candidate_name=candidate_name,
        job_title=job_title,
        from_stage=from_stage,
        to_stage=to_stage,
    )

    _DISPATCH_BEHAVIORS = {"screening", "scheduling", "evaluation", "offer", "conclusion_rejected"}
    behavior_specific = ""
    if action_behavior in ("conclusion_rejected",):
        behavior_specific = f"\n\n{FAIRNESS_RULES}"
    if action_behavior in _DISPATCH_BEHAVIORS:
        behavior_specific += f"\n\n{COMMUNICATION_TRANSPARENCY_RULES}"

    interview_rules = ""
    from_lower = (from_stage or "").lower()
    extra_lower = (extra_context or "").lower()
    if any(kw in from_lower for kw in ("interview", "entrevista")) or "entrevista agendada" in extra_lower:
        interview_rules = INTERVIEW_CROSS_BEHAVIOR_RULES

    prompt_parts = [
        PIPELINE_IDENTITY,
        stage_context,
        SCOPE_IN,
        SCOPE_OUT,
        BEHAVIORAL_RULES,
        COMPANY_CALIBRATION,
        behavior_specific,
        LEARNING_RULES,
        interview_rules,
        FEW_SHOT_EXAMPLES,
    ]

    if company_type:
        company_hint = f"\nPERFIL DA EMPRESA ATUAL: {company_type.upper()} — ajuste seu tom conforme as instruções de calibração acima."
        prompt_parts.append(company_hint)

    if extra_context:
        prompt_parts.append(f"\nCONTEXTO ADICIONAL (memórias e histórico):\n{extra_context}")

    return "\n\n".join(part for part in prompt_parts if part)
