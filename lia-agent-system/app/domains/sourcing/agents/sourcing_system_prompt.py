"""
Sourcing System Prompt — loads from YAML.

Content source: app/prompts/domains/sourcing.yaml
Compliance/guardrails: injected by ComplianceDomainPrompt.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_OPERATIONAL
except ImportError:
    ANTI_SYCOPHANCY_OPERATIONAL = ""
try:
    from app.shared.prompts.interaction_patterns import NEGATION_DETECTION_BLOCK
except ImportError:
    NEGATION_DETECTION_BLOCK = ""

_yaml_cache: dict[str, Any] | None = None


def _load_yaml() -> dict[str, Any]:
    global _yaml_cache
    if _yaml_cache is not None:
        return _yaml_cache
    try:
        from app.shared.prompts.loader import PromptLoader
        _yaml_cache = PromptLoader.load("domains/sourcing")
        return _yaml_cache
    except Exception as exc:
        logger.warning("[sourcing_prompt] YAML load failed: %s", exc)
        _yaml_cache = {}
        return _yaml_cache


def _get(key: str, fallback: str = "") -> str:
    data = _load_yaml()
    val = data.get(key, fallback)
    return val if isinstance(val, str) else fallback


SOURCING_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Sourcing e Busca de Talentos.")
SOURCING_SYSTEM_PROMPT = SOURCING_DOMAIN_SPECIFIC
SOURCING_FEW_SHOT_EXAMPLES = _get("few_shot_examples", "")
SOURCING_REASONING_PROMPT = """PROTOCOLO REACT — MEMORIA E CONTEXTO SOURCING:

Contexto atual da conversa:
{stage_context}

Memoria de trabalho (historico recente):
{memory_summary}

Antes de CADA resposta, reflita internamente:
1. Quais ferramentas de busca sao mais adequadas para esta solicitacao?
2. O recrutador quer busca interna, externa (Pearch) ou ambas?
3. Ha risco de vies no criterio de busca? (ex: universidade especifica = proxy classe)
4. A shortlist e demograficamente diversa?
5. O custo da busca externa esta dentro do esperado?

USO CORRETO DO PEARCH (CONDICIONAL):
- Pearch NAO e uma ferramenta separada. A busca externa e ATIVADA passando o
  parametro `include_pearch=true` para `search_candidates`.
- Acionar Pearch e CONDICIONAL: so use quando o recrutador pedir explicitamente
  busca externa, quando o banco interno retornar poucos resultados (< 5), ou
  quando a vaga exigir cobertura global. Caso contrario, mantenha
  `include_pearch=false` (default) para controlar custo.

DISCLAIMER DE DADOS DE MERCADO:
- Numeros de mercado, salario e disponibilidade sao benchmark estimado a partir
  de fontes agregadas; NAO representam dados em tempo real do mercado.
- Sempre qualifique respostas de market intelligence como "benchmark estimado"
  e cite a janela temporal da amostra quando disponivel.

TRATAMENTO DE FALHAS DE FERRAMENTA:
- Se uma ferramenta retornar erro, timeout ou resultado vazio, NUNCA invente
  candidatos ou numeros. Reporte o erro de forma transparente ao recrutador.
- Sempre proponha uma alternativa concreta: refinar criterios, tentar busca
  interna quando a externa falhar (ou vice-versa), ou pedir mais contexto da
  vaga antes de tentar de novo.

FORMATO DE SAIDA: JSON puro.
Nao inclua texto fora do JSON."""


def get_sourcing_system_prompt(stage: str, context: dict) -> str:
    """Build the complete system prompt for sourcing."""
    stage_context = context.get("stage_context", "")
    memory_summary = context.get("memory_summary", "")

    reasoning = SOURCING_REASONING_PROMPT.format(
        stage_context=stage_context,
        memory_summary=memory_summary or "Nenhuma memoria de trabalho disponivel (primeira interacao).",
    )
    return f"{SOURCING_SYSTEM_PROMPT}\n\n{SOURCING_FEW_SHOT_EXAMPLES}\n\n{reasoning}\n\n{ANTI_SYCOPHANCY_OPERATIONAL}\n\n{NEGATION_DETECTION_BLOCK}"
