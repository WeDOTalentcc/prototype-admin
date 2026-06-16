"""
CV Screening Pipeline System Prompt — loads from YAML.

Content source: app/prompts/domains/cv_screening.yaml
Compliance/guardrails: injected by ComplianceDomainPrompt.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_OPERATIONAL
except ImportError:
    ANTI_SYCOPHANCY_OPERATIONAL = ""

_yaml_cache: dict[str, Any] | None = None


def _load_yaml() -> dict[str, Any]:
    global _yaml_cache
    if _yaml_cache is not None:
        return _yaml_cache
    try:
        from app.shared.prompts.loader import PromptLoader
        _yaml_cache = PromptLoader.load("domains/cv_screening")
        return _yaml_cache
    except Exception as exc:
        logger.warning("[cv_screening_prompt] YAML load failed: %s", exc)
        _yaml_cache = {}
        return _yaml_cache


def _get(key: str, fallback: str = "") -> str:
    data = _load_yaml()
    val = data.get(key, fallback)
    return val if isinstance(val, str) else fallback


# Exported constants — backward compatible
PIPELINE_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Triagem Curricular.")
PIPELINE_SYSTEM_PROMPT = PIPELINE_DOMAIN_SPECIFIC  # legacy alias
PIPELINE_REASONING_PROMPT = """PROTOCOLO REACT — MEMORIA E CONTEXTO:

Contexto atual da conversa:
{stage_context}

Memoria de trabalho (historico recente):
{memory_summary}

Antes de CADA resposta, reflita internamente:
1. Qual acao o recrutador esta pedindo? (triagem, score, ranking, feedback?)
2. Tenho os dados necessarios ou preciso consultar ferramentas?
3. O candidato esta em situacao que exige cuidado especial? (fairness, LGPD)
4. Qual resposta seria mais util e acionavel?

FORMATO DE SAIDA: JSON puro.
Nao inclua texto fora do JSON."""


def get_pipeline_system_prompt(stage: str, context: dict[str, Any]) -> str:
    """Build the complete system prompt for the CV screening pipeline agent."""
    stage_context = context.get("stage_context", "")
    memory_summary = context.get(
        "memory_summary",
        "Nenhuma memoria de trabalho disponivel (primeira interacao).",
    )

    reasoning = PIPELINE_REASONING_PROMPT.format(
        stage_context=stage_context,
        memory_summary=memory_summary or "Nenhuma memoria de trabalho disponivel (primeira interacao).",
    )
    return f"{PIPELINE_SYSTEM_PROMPT}\n\n{reasoning}\n\n{ANTI_SYCOPHANCY_OPERATIONAL}"
