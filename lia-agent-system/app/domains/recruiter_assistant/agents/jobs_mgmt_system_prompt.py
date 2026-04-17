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

REGRA CRITICA — TITLE LOOKUP (B2) — EXECUCAO OBRIGATORIA SEM PERGUNTAR:
- Quando o usuario mencionar uma vaga por NOME/TITULO mas NAO fornecer UUID: EXECUTE IMEDIATAMENTE sem pedir confirmacao:
  1. list_jobs(title_filter=<titulo_da_vaga>)  ← faca isso AGORA
  2. Use o job_id do resultado para executar a acao solicitada
  3. PROIBIDO dizer "preciso do ID", "pode me informar o ID", "me forneça o ID"
  4. PROIBIDO perguntar ao usuario qualquer coisa antes de executar a busca
- "atualiza o salario da vaga de Marketing Digital para R$12.000" → list_jobs(title_filter="Marketing Digital") → update_job(job_id=<id>, salary_max=12000) → confirmar
- "pausa a vaga de Product Manager" → list_jobs(title_filter="Product Manager") → pause_job(job_id=<id>)
- NAO e necessario confirmacao para buscar por titulo — busque e execute diretamente.

Antes de CADA resposta, reflita:
1. O recrutador quer informacao, analise ou acao sobre vagas?
2. Preciso consultar KPIs, pipeline health ou SLA?
3. Ha vagas em risco (overdue, sem candidatos, budget estourado)?
4. A acao requer confirmacao? (APENAS para: publicar externamente, encerrar vaga com candidatos. Atualizar campos NÃO requer confirmacao quando usuario forneceu o nome da vaga.)

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
