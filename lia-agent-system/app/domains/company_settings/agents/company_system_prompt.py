"""
Company Settings System Prompt — loads from YAML.

Content source: app/prompts/domains/company_settings.yaml
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
        _yaml_cache = PromptLoader.load("domains/company_settings")
        return _yaml_cache
    except Exception as exc:
        logger.warning("[company_prompt] YAML load failed: %s", exc)
        _yaml_cache = {}
        return _yaml_cache


def _get(key: str, fallback: str = "") -> str:
    data = _load_yaml()
    val = data.get(key, fallback)
    return val if isinstance(val, str) else fallback


COMPANY_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Configuração Empresarial.")
COMPANY_FEW_SHOT_EXAMPLES = _get("few_shot_examples", "")
COMPANY_REASONING_PROMPT = _get("reasoning_prompt", "")
# T6 (#993): regras comportamentais + contrato de tags estruturadas
# precisam fluir para o prompt efetivo do agente. Sem isto, as regras #8/#9
# (não perguntar dados do tenant_context_snippet) e o reconhecimento das
# tags `[ACTION:prefill_section][target_section:X]` enviadas pelo chat
# lateral (use-settings-conversational.ts) ficam só na documentação YAML
# e nunca chegam à LLM.
COMPANY_BEHAVIORAL_RULES = _get("behavioral_rules", "")
COMPANY_STRUCTURED_ACTION_TAGS = _get("structured_action_tags", "")
COMPANY_ETHICAL_VALIDATION = _get("ethical_validation", "")


def get_company_system_prompt() -> str:
    """Build the complete system prompt for the company settings agent."""
    return f"""Voce e a LIA, assistente de recrutamento inteligente da plataforma WeDOTalent.
Voce esta ajudando um recrutador a configurar os dados da empresa.

=== IDENTIDADE ===
- Nome: LIA (Assistente de Recrutamento com IA)
- Personalidade: Profissional, consultiva, etica e proativa
- Idioma: Portugues Brasileiro (PT-BR)

=== FILOSOFIA CENTRAL ===
O chat e a interface principal. Este chat e EXCLUSIVAMENTE sobre dados da empresa.

{COMPANY_DOMAIN_SPECIFIC}

=== REGRAS COMPORTAMENTAIS ===
{COMPANY_BEHAVIORAL_RULES}

=== TAGS ESTRUTURADAS (CONTRATO COM CHAT LATERAL — T6 #993) ===
{COMPANY_STRUCTURED_ACTION_TAGS}

=== VALIDACAO ETICA ===
{COMPANY_ETHICAL_VALIDATION}

{COMPANY_FEW_SHOT_EXAMPLES}

{ANTI_SYCOPHANCY_BLOCK}

{NEGATION_DETECTION_BLOCK}
"""
