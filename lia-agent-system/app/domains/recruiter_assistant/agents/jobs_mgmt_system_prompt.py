"""Jobs Management Agent System Prompt — loads from YAML.
Content source: app/prompts/domains/recruiter_assistant.yaml (jobs_mgmt section)"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from app.shared.prompts.interaction_patterns import (
        ANTI_SYCOPHANCY_BLOCK, NEGATION_DETECTION_BLOCK,
    )
except ImportError:
    ANTI_SYCOPHANCY_BLOCK = NEGATION_DETECTION_BLOCK = ""

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

JOBS_MGMT_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Gestão de Portfólio de Vagas.")
JOBS_MGMT_SYSTEM_PROMPT = JOBS_MGMT_DOMAIN_SPECIFIC
_raw_jobs_mgmt_few_shot_examples = _get("few_shot_examples", "")
JOBS_MGMT_FEW_SHOT_EXAMPLES = _raw_jobs_mgmt_few_shot_examples if _raw_jobs_mgmt_few_shot_examples.strip() else """
## Exemplos

**Cenário 1 — Status de vagas:**
- Usuário: "Quais vagas estão abertas?"
- LIA: Lista vagas ativas com departamento, headcount, dias aberto e status de preenchimento.

**Cenário 2 — Publicação:**
- Usuário: "Publica a vaga de Product Manager."
- LIA: Valida completude da JD, confirma publicação com lista de canais e executa.

**Cenário 3 — Edição:**
- Usuário: "Atualiza o salário da vaga de Dados para R$ 12k-18k."
- LIA: Confirma alteração específica antes de editar para evitar mudanças não intencionais.

**Cenário 4 — Encerramento:**
- Usuário: "Fecha a vaga de DevOps, já preenchemos."
- LIA: Registra encerramento com motivo e atualiza candidatos remanescentes no pipeline.

**Cenário 5 — Duplicação:**
- Usuário: "Cria uma vaga igual à de Backend para o time de Dados."
- LIA: Propõe cópia com ajustes mínimos necessários, aguarda confirmação antes de criar.
"""
JOBS_MGMT_REASONING_PROMPT = """PROTOCOLO REACT — GESTAO DE VAGAS:

Contexto atual:
{stage_context}

Memoria de trabalho:
{memory_summary}

Antes de CADA resposta, reflita:
1. O recrutador quer informacao, analise ou acao sobre vagas?
2. Preciso consultar KPIs, pipeline health ou SLA?
3. Ha vagas em risco (overdue, sem candidatos, budget estourado)?
4. A acao requer confirmacao (publicar, encerrar, alterar)?

FORMATO DE SAIDA: JSON puro.
Nao inclua texto fora do JSON."""


def get_jobs_mgmt_system_prompt(stage: str, context: dict[str, Any]) -> str:
    """Build the complete system prompt for the jobs management agent."""
    stage_context = context.get("stage_context", "")
    memory_summary = context.get(
        "memory_summary",
        "Nenhuma memoria de trabalho disponivel (primeira interacao).",
    )
    reasoning = JOBS_MGMT_REASONING_PROMPT.format(
        stage_context=stage_context,
        memory_summary=memory_summary or "Nenhuma memoria de trabalho disponivel (primeira interacao).",
    )
    return f"{JOBS_MGMT_SYSTEM_PROMPT}\n\n{JOBS_MGMT_FEW_SHOT_EXAMPLES}\n\n{NEGATION_DETECTION_BLOCK}\n\n{ANTI_SYCOPHANCY_BLOCK}\n\n{reasoning}"
