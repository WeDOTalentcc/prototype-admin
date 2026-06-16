"""Kanban Agent System Prompt — loads from YAML.
Content source: app/prompts/domains/recruiter_assistant.yaml"""
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

KANBAN_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Análise Estratégica de Pipeline.")
KANBAN_SYSTEM_PROMPT = KANBAN_DOMAIN_SPECIFIC
_raw_kanban_few_shot_examples = _get("few_shot_examples", "")
KANBAN_FEW_SHOT_EXAMPLES = _raw_kanban_few_shot_examples if _raw_kanban_few_shot_examples.strip() else """
## Exemplos

**Cenário 1 — Visão do pipeline:**
- Usuário: "Como está o pipeline da vaga de Designer?"
- LIA: Resumo por fase: X na triagem, Y na entrevista, Z com proposta, com métricas de tempo.

**Cenário 2 — Movimentação:**
- Usuário: "Move Ana Lima para fase de proposta."
- LIA: Confirma candidata e vaga, executa movimentação e registra na trilha de auditoria.

**Cenário 3 — Gargalo:**
- Usuário: "Tem muita gente parada em alguma fase?"
- LIA: Identifica fase com maior acúmulo e tempo médio de espera, sugere ação.

**Cenário 4 — Rejeição:**
- Usuário: "Reprova o candidato Carlos Mendes."
- LIA: Confirma candidato e motivo antes de registrar rejeição e acionar template de feedback.

**Cenário 5 — SLA breach:**
- Usuário: "Tem alguém esperando há mais de 10 dias?"
- LIA: Lista candidatos com SLA excedido por fase e recrutador responsável.
"""
KANBAN_REASONING_PROMPT = """PROTOCOLO REACT — KANBAN PIPELINE:

Contexto atual:
{stage_context}

Memoria de trabalho:
{memory_summary}

Antes de CADA resposta, reflita:
1. Qual metrica ou visao o recrutador precisa?
2. Preciso consultar dados agregados (pipeline health, bottlenecks)?
3. Ha acoes recomendadas baseadas nos dados?
4. O recrutador quer analise ou acao?

FORMATO DE SAIDA: JSON puro.
Nao inclua texto fora do JSON."""


def get_kanban_system_prompt(stage: str, context: dict[str, Any]) -> str:
    """Build the complete system prompt for the kanban analysis agent."""
    stage_context = context.get("stage_context", "")
    memory_summary = context.get(
        "memory_summary",
        "Nenhuma memoria de trabalho disponivel (primeira interacao).",
    )
    reasoning = KANBAN_REASONING_PROMPT.format(
        stage_context=stage_context,
        memory_summary=memory_summary or "Nenhuma memoria de trabalho disponivel (primeira interacao).",
    )
    return f"{KANBAN_SYSTEM_PROMPT}\n\n{KANBAN_FEW_SHOT_EXAMPLES}\n\n{NEGATION_DETECTION_BLOCK}\n\n{CHAIN_OF_THOUGHT_BLOCK}\n\n{ANTI_SYCOPHANCY_BLOCK}\n\n{reasoning}"
