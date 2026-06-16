"""
Talent Pool System Prompt — loads from YAML.

Content source: app/prompts/domains/talent_pool.yaml
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
        _yaml_cache = PromptLoader.load("domains/talent_pool")
        return _yaml_cache
    except Exception as exc:
        logger.warning("[talent_pool_prompt] YAML load failed: %s", exc)
        _yaml_cache = {}
        return _yaml_cache


def _get(key: str, fallback: str = "") -> str:
    data = _load_yaml()
    val = data.get(key, fallback)
    return val if isinstance(val, str) else fallback


TALENT_POOL_DOMAIN_SPECIFIC = _get(
    "system_prompt",
    "Especialista em gerenciamento de bancos de talentos vivos.",
)
TALENT_POOL_SYSTEM_PROMPT = TALENT_POOL_DOMAIN_SPECIFIC

TALENT_POOL_REASONING_PROMPT = """PROTOCOLO REACT — BANCOS DE TALENTOS:

Memoria de trabalho:
{memory_summary}

Contexto do estagio:
{stage_context}

Antes de CADA resposta, reflita:
1. O candidato sendo adicionado/movido respeita criterios de equidade?
2. Migracao para vaga preserva o screening_data existente?
3. A acao envolve dados sensiveis de PII? Usar mascaramento.
4. Confirmacao obrigatoria para move_pool_to_job (acao de alto impacto).
5. Pools inativos precisam de atencao especial antes de operar sobre eles.

TOM: profissional, orientado a resultados, sem verbosidade desnecessaria."""


def get_talent_pool_system_prompt(
    stage: str = "browsing",
    context: dict[str, Any] | None = None,
) -> str:
    """Build the complete system prompt for the talent pool agent."""
    ctx = context or {}
    memory_summary = ctx.get("memory_summary", "Nenhuma memoria carregada ainda.")
    stage_context = ctx.get("stage_context", "")

    reasoning = TALENT_POOL_REASONING_PROMPT.format(
        memory_summary=memory_summary,
        stage_context=stage_context,
    )

    parts = [TALENT_POOL_SYSTEM_PROMPT]
    if NEGATION_DETECTION_BLOCK:
        parts.append(NEGATION_DETECTION_BLOCK)
    if ANTI_SYCOPHANCY_BLOCK:
        parts.append(ANTI_SYCOPHANCY_BLOCK)
    parts.append(reasoning)

    return "\n\n".join(p for p in parts if p)
