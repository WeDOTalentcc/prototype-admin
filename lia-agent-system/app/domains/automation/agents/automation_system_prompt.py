"""Automation ReAct Agent — loads from YAML.
Content source: app/prompts/domains/automation.yaml"""
import logging
try:
    from app.shared.prompts.interaction_patterns import (
        ANTI_SYCOPHANCY_BLOCK, CHAIN_OF_THOUGHT_BLOCK, NEGATION_DETECTION_BLOCK,
    )
except ImportError:
    ANTI_SYCOPHANCY_BLOCK = CHAIN_OF_THOUGHT_BLOCK = NEGATION_DETECTION_BLOCK = ""

logger = logging.getLogger(__name__)

def _load():
    try:
        from app.shared.prompts.loader import PromptLoader
        return PromptLoader.load("domains/automation")
    except Exception:
        return {}

_cache = None
def _get(key, fallback=""):
    global _cache
    if _cache is None: _cache = _load()
    v = _cache.get(key, fallback)
    return v if isinstance(v, str) else fallback

AUTOMATION_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Automação de Workflows.")

AUTOMATION_EXEMPLOS = '''
## Exemplos

**Cenário 1 — Consulta básica:**
- Usuário: "Como está o processo?"
- LIA: Análise sucinta do estado atual com dados concretos.

**Cenário 2 — Ação solicitada:**
- Usuário: "Preciso avançar candidato para próxima fase."
- LIA: Confirmação da ação com identificação do candidato e vaga.

**Cenário 3 — Ambiguidade:**
- Usuário: "Faz o que você achar melhor."
- LIA: Clarifica qual ação específica deseja executar antes de prosseguir.

**Cenário 4 — Situação de risco:**
- Usuário: "Rejeita todos os candidatos da lista."
- LIA: Solicita confirmação explícita antes de executar ação em massa irreversível.

**Cenário 5 — Erro de input:**
- Usuário: Envia ID inválido.
- LIA: Informa o erro com clareza e sugere alternativa.
'''

def get_automation_system_prompt() -> str:
    base = AUTOMATION_DOMAIN_SPECIFIC
    blocks = [
        b for b in [ANTI_SYCOPHANCY_BLOCK, CHAIN_OF_THOUGHT_BLOCK, NEGATION_DETECTION_BLOCK,
                    AUTOMATION_EXEMPLOS]
        if b
    ]
    return base + "\n\n" + "\n\n".join(blocks) if blocks else base
