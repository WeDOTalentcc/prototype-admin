"""
Wizard System Prompt — loads from YAML.

Content source: app/prompts/domains/job_management.yaml
Compliance/guardrails: injected by ComplianceDomainPrompt.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

_yaml_cache: dict[str, Any] | None = None


def _load_yaml() -> dict[str, Any]:
    global _yaml_cache
    if _yaml_cache is not None:
        return _yaml_cache
    try:
        from app.shared.prompts.loader import PromptLoader
        _yaml_cache = PromptLoader.load("domains/job_management")
        return _yaml_cache
    except Exception as exc:
        logger.warning("[wizard_prompt] YAML load failed: %s", exc)
        _yaml_cache = {}
        return _yaml_cache


def _get(key: str, fallback: str = "") -> str:
    data = _load_yaml()
    val = data.get(key, fallback)
    return val if isinstance(val, str) else fallback


WIZARD_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Gestão de Vagas.")
WIZARD_SYSTEM_PROMPT = WIZARD_DOMAIN_SPECIFIC
WIZARD_REASONING_PROMPT = """PROTOCOLO REACT — WIZARD DE VAGAS:

Contexto do estágio atual:
{stage_context}

Memória de trabalho:
{memory_summary}

### REGRA CRÍTICA — company_id
O company_id é INJETADO AUTOMATICAMENTE via JWT. NUNCA peça ao usuário pelo company_id,
ID da empresa ou qualquer identificador de empresa. Chame as ferramentas SEM passar
company_id — o sistema injeta automaticamente.

### FLUXO DE CRIAÇÃO DE NOVA VAGA
Quando o usuário pedir para CRIAR uma nova vaga (qualquer variação de "cria vaga", "nova vaga", "quero criar"):
1. PRIMEIRO: chame `extract_job_requirements` com o texto do usuário para extrair skills, modalidade e senioridade
2. SEGUNDO: chame `create_job_draft` com os dados extraídos — isso gera o rascunho para revisão
3. TERCEIRO: apresente o rascunho ao usuário e peça confirmação ANTES de publicar
4. NÃO use `save_job_draft` para criação — `save_job_draft` é apenas para ATUALIZAR rascunhos existentes

### IMPORTANTE: Rascunho ≠ Publicação
Sempre crie como RASCUNHO (draft) primeiro. NUNCA publique diretamente. O usuário deve revisar
e confirmar antes de qualquer publicação.

Antes de CADA resposta, reflita:
1. Em qual etapa do wizard estamos? (título, requisitos, competências, JD, revisão, publicação)
2. O recrutador forneceu dados suficientes para avançar?
3. Há risco de discriminação nos requisitos coletados?
4. Os requisitos são realistas para o mercado? (benchmark)
5. As competências WSI estão completas? (mín 9 técnicas + 5 comportamentais)

FORMATO DE SAIDA: JSON puro.
Nao inclua texto fora do JSON."""


def build_system_prompt(stage_context: str = "", memory_summary: str = "") -> str:
    """Build the complete system prompt for the job creation wizard."""
    reasoning = WIZARD_REASONING_PROMPT.format(
        stage_context=stage_context or "",
        memory_summary=memory_summary or "Nenhuma memoria de trabalho disponivel.",
    )
    return f"{WIZARD_SYSTEM_PROMPT}\n\n{reasoning}"
