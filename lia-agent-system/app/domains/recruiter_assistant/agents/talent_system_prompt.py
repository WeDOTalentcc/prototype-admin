"""Talent Agent System Prompt — loads from YAML.
Content source: app/prompts/domains/recruiter_assistant.yaml (talent section)"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from app.shared.prompts.interaction_patterns import (
        ANTI_SYCOPHANCY_BLOCK, CHAIN_OF_THOUGHT_BLOCK, NEGATION_DETECTION_BLOCK,
    )
except ImportError:
    ANTI_SYCOPHANCY_BLOCK = CHAIN_OF_THOUGHT_BLOCK = NEGATION_DETECTION_BLOCK = ""

_cache = None
def _load():
    global _cache
    if _cache is None:
        try:
            from app.shared.prompts.loader import PromptLoader
            _cache = PromptLoader.load("domains/recruiter_assistant")
        except Exception:
            _cache = {}
    return _cache

def _get(key, fallback=""):
    v = _load().get(key, fallback)
    return v if isinstance(v, str) else fallback

TALENT_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Gestão de Funil de Talentos.")
TALENT_SYSTEM_PROMPT = TALENT_DOMAIN_SPECIFIC
_raw_talent_few_shot_examples = _get("few_shot_examples", "")
TALENT_FEW_SHOT_EXAMPLES = _raw_talent_few_shot_examples if _raw_talent_few_shot_examples.strip() else """
## Exemplos

**Cenário 1 — Busca de candidatos:**
- Usuário: "Mostra candidatos para engenheiro sênior."
- LIA: Lista candidatos com pontuação de fit e principais skills, ordenados por aderência.

**Cenário 2 — Triagem automatizada:**
- Usuário: "Triagem automática para os 20 novos candidatos."
- LIA: Confirma critérios, executa triagem e exibe resumo por categoria (aprovado/reprovado/review).

**Cenário 3 — Análise de perfil:**
- Usuário: "Analisa o perfil de João Silva."
- LIA: Exibe análise estruturada com pontos fortes, gaps e recomendação de próximo passo.

**Cenário 4 — Comparação:**
- Usuário: "Compara os 3 finalistas."
- LIA: Tabela comparativa por dimensão (técnico, comportamental, fit cultural) com recomendação.

**Cenário 5 — Ação em massa:**
- Usuário: "Avança os 5 aprovados para entrevista."
- LIA: Solicita confirmação com lista nomeada antes de executar.
"""
TALENT_REASONING_PROMPT = """PROTOCOLO REACT — FUNIL DE TALENTOS:

Contexto atual:
{stage_context}

Memoria de trabalho:
{memory_summary}

Antes de CADA resposta, reflita:
1. O recrutador quer analisar, buscar ou agir sobre candidatos?
2. Preciso consultar scores, historico ou dados de perfil?
3. A acao solicitada requer confirmacao (mover, rejeitar, contactar)?
4. Ha fairness concerns nos criterios mencionados?

FORMATO DE SAIDA: JSON puro.
Nao inclua texto fora do JSON."""


def get_talent_system_prompt(stage: str, context: dict[str, Any]) -> str:
    """Build the complete system prompt for the talent funnel agent."""
    stage_context = context.get("stage_context", "")
    memory_summary = context.get(
        "memory_summary",
        "Nenhuma memoria de trabalho disponivel (primeira interacao).",
    )
    reasoning = TALENT_REASONING_PROMPT.format(
        stage_context=stage_context,
        memory_summary=memory_summary or "Nenhuma memoria de trabalho disponivel (primeira interacao).",
    )
    return f"{TALENT_SYSTEM_PROMPT}\n\n{TALENT_FEW_SHOT_EXAMPLES}\n\n{NEGATION_DETECTION_BLOCK}\n\n{CHAIN_OF_THOUGHT_BLOCK}\n\n{ANTI_SYCOPHANCY_BLOCK}\n\n{reasoning}"
