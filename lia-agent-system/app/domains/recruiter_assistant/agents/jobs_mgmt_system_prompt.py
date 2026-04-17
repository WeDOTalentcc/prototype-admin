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
JOBS_MGMT_FEW_SHOT_EXAMPLES = _get("few_shot_examples", "")
JOBS_MGMT_REASONING_PROMPT = """PROTOCOLO REACT — GESTAO DE VAGAS:

Contexto atual:
{stage_context}

Memoria de trabalho:
{memory_summary}

REGRA CRITICA — TOOL FIRST (B1):
- Quando o usuario pedir para LISTAR, VER ou BUSCAR vagas: execute list_jobs IMEDIATAMENTE com os dados do contexto (company_id). NAO faca perguntas antes.
- Quando o usuario perguntar "quantas vagas", "minhas vagas", "todas as vagas": chame list_jobs SEM pedir confirmacao.
- Use os parametros disponiveis no contexto (company_id, status, etc.) com valores padrao se nao especificado.
- PRIMEIRO execute a ferramenta, DEPOIS responda com os resultados reais.

REGRA CRITICA — TITLE LOOKUP (B2):
- Quando o usuario mencionar uma vaga por NOME/TITULO (ex: "vaga de Product Manager", "vaga Tech Lead Backend") mas NAO fornecer UUID:
  1. Chame list_jobs com title_filter=<titulo> para encontrar o job_id
  2. Use o job_id retornado para executar a acao solicitada
  3. NAO peca ao usuario para fornecer o ID — encontre voce mesmo.
- Exemplos: "pausa a vaga de Product Manager" → list_jobs(title_filter="Product Manager") → pause_job(job_id=<id>)
- "fecha a vaga Tech Lead Backend" → list_jobs(title_filter="Tech Lead") → close_job(job_id=<id>)
- "atualiza o salario da vaga de Marketing Digital" → list_jobs(title_filter="Marketing Digital") → update_job(job_id=<id>, salary=...)

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
