"""Communication ReAct Agent — loads from YAML.
Content source: app/prompts/domains/communication.yaml"""
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
        return PromptLoader.load("domains/communication")
    except Exception:
        return {}

_cache = None
def _get(key, fallback=""):
    global _cache
    if _cache is None: _cache = _load()
    v = _cache.get(key, fallback)
    return v if isinstance(v, str) else fallback

COMMUNICATION_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Comunicação Multi-canal.")

COMMUNICATION_EXEMPLOS = '''
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

# ---------------------------------------------------------------------------
# COMMUNICATION_TEMPLATES — canonical message templates (Task #Sprint V)
# Used by tests, UI template pickers, and system prompt assembly.
# ---------------------------------------------------------------------------
COMMUNICATION_TEMPLATES: str = """
## Templates de Comunicação

Todos os templates passam por FairnessGuard antes do envio.
Variáveis: {{candidato_nome}}, {{vaga_titulo}}, {{empresa_nome}}, {{data_entrevista}}.

### Convite para WSI (Triagem Assíncrona)
Olá, {{candidato_nome}}! Gostaríamos de convidá-lo(a) para a etapa de triagem da vaga {{vaga_titulo}}.
Clique no link para responder às perguntas: {{link_wsi}}

### Reprovação Gate 1 (Triagem)
Olá, {{candidato_nome}}. Agradecemos seu interesse na vaga {{vaga_titulo}}.
Após análise do seu perfil, não avançaremos neste processo seletivo. Sucesso na sua jornada!

### Reprovação Gate 2 (Entrevista)
Olá, {{candidato_nome}}. Foi um prazer conversar com você sobre a vaga {{vaga_titulo}}.
Após avaliação, decidimos seguir com outros candidatos neste momento.

### Convite Entrevista Final
Olá, {{candidato_nome}}! Você avançou para a Entrevista Final da vaga {{vaga_titulo}}.
Data: {{data_entrevista}}. Confirme sua presença respondendo este e-mail.

### Proposta de Contratação (Oferta)
Olá, {{candidato_nome}}. Com grande satisfação, gostaríamos de formalizar a proposta para {{vaga_titulo}}.
"""


# ---------------------------------------------------------------------------
# COMMUNICATION_TEMPLATES — canonical message templates (Task #Sprint V)
# Used by tests, UI template pickers, and system prompt assembly.
# ---------------------------------------------------------------------------
COMMUNICATION_TEMPLATES: str = """
## Templates de Comunicação

Todos os templates passam por FairnessGuard antes do envio.
Variáveis: {{candidato_nome}}, {{vaga_titulo}}, {{empresa_nome}}, {{data_entrevista}}.

### Convite para WSI (Triagem Assíncrona)
Olá, {{candidato_nome}}! Gostaríamos de convidá-lo(a) para a etapa de triagem da vaga {{vaga_titulo}}.
Clique no link para responder às perguntas: {{link_wsi}}

### Reprovação Gate 1 (Triagem)
Olá, {{candidato_nome}}. Agradecemos seu interesse na vaga {{vaga_titulo}}.
Após análise do seu perfil, não avançaremos neste processo seletivo. Sucesso na sua jornada!

### Reprovação Gate 2 (Entrevista)
Olá, {{candidato_nome}}. Foi um prazer conversar com você sobre a vaga {{vaga_titulo}}.
Após avaliação, decidimos seguir com outros candidatos neste momento.

### Convite Entrevista Final
Olá, {{candidato_nome}}! Você avançou para a Entrevista Final da vaga {{vaga_titulo}}.
Data: {{data_entrevista}}. Confirme sua presença respondendo este e-mail.

### Proposta de Contratação (Oferta)
Olá, {{candidato_nome}}. Com grande satisfação, gostaríamos de formalizar a proposta para {{vaga_titulo}}.
"""


def get_communication_system_prompt() -> str:
    base = COMMUNICATION_DOMAIN_SPECIFIC
    blocks = [
        b for b in [ANTI_SYCOPHANCY_BLOCK, CHAIN_OF_THOUGHT_BLOCK, NEGATION_DETECTION_BLOCK,
                    COMMUNICATION_EXEMPLOS]
        if b
    ]
    blocks.append(COMMUNICATION_TEMPLATES)
    blocks.append(COMMUNICATION_TEMPLATES)
    return base + "\n\n" + "\n\n".join(blocks) if blocks else base
