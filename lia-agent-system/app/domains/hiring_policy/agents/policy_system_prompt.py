"""
Policy System Prompt — loads from YAML.

Content source: app/prompts/domains/hiring_policy.yaml
Compliance/guardrails: injected by ComplianceDomainPrompt.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from app.shared.prompts.interaction_patterns import (
        ANTI_SYCOPHANCY_BLOCK,
        NEGATION_DETECTION_BLOCK,
    )
except ImportError:
    ANTI_SYCOPHANCY_BLOCK = ""
    NEGATION_DETECTION_BLOCK = ""

_yaml_cache: dict[str, Any] | None = None


def _load_yaml() -> dict[str, Any]:
    global _yaml_cache
    if _yaml_cache is not None:
        return _yaml_cache
    try:
        from app.shared.prompts.loader import PromptLoader
        _yaml_cache = PromptLoader.load("domains/hiring_policy")
        return _yaml_cache
    except Exception as exc:
        logger.warning("[policy_prompt] YAML load failed: %s", exc)
        _yaml_cache = {}
        return _yaml_cache


def _get(key: str, fallback: str = "") -> str:
    data = _load_yaml()
    val = data.get(key, fallback)
    return val if isinstance(val, str) else fallback


POLICY_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Políticas de Contratação.")
POLICY_SYSTEM_PROMPT = POLICY_DOMAIN_SPECIFIC
POLICY_FEW_SHOT_EXAMPLES = _get("few_shot_examples", "")
POLICY_REASONING_PROMPT = """PROTOCOLO REACT — POLITICAS DE CONTRATACAO:

Memoria de trabalho:
{memory_summary}

Contexto do estagio:
{stage_context}

Antes de CADA resposta, reflita:
1. A politica proposta viola algum criterio proibido?
2. Ha benchmark de mercado relevante para comparar?
3. O risco (risk_score) justifica escalacao?
4. A sugestao melhora a politica sem introduzir vies?
5. O recrutador precisa de aprovacao adicional?

FORMATO DE SAIDA: JSON puro.
Nao inclua texto fora do JSON."""


def get_policy_system_prompt(
    stage: str = "onboarding",
    context: dict[str, Any] = None,
) -> str:
    """Build the complete system prompt for the policy agent."""
    ctx = context or {}
    memory_summary = ctx.get("memory_summary", "Nenhuma memoria carregada ainda.")
    stage_context = ctx.get("stage_context", "")

    reasoning = POLICY_REASONING_PROMPT.format(
        memory_summary=memory_summary,
        stage_context=stage_context,
    )

    return f"{POLICY_SYSTEM_PROMPT}\n\n{POLICY_FEW_SHOT_EXAMPLES}\n\n{NEGATION_DETECTION_BLOCK}\n\n{ANTI_SYCOPHANCY_BLOCK}\n\n{reasoning}"
