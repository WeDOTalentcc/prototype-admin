"""
Policy System Prompt — loads from YAML.

Content source: app/prompts/domains/hiring_policy.yaml
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
        _yaml_cache = PromptLoader.load("domains/hiring_policy")
        return _yaml_cache
    except Exception as exc:
        logger.warning("[policy_prompt] YAML load failed: %s", exc)
        _yaml_cache = {}
        return _yaml_cache


def _get(key: str, fallback: str = "") -> str:
    data = _load_yaml()
    val = data.get(key, fallback)
    return val if isinstance(val, str) else fallback


POLICY_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Políticas de Contratação.")
# --- Seções canônicas de governança (não remover — test_prompt_deduplication verifica) ---
_POLICY_GOVERNANCE_SECTIONS = """
=== RACIOCINIO CONSULTIVO ===
Antes de responder, raciocine:
1. O critério proposto viola alguma lei ou boas práticas?
2. Existe benchmark de mercado relevante para comparar?
3. A sugestão melhora a política sem introduzir viés?
4. O risk_score justifica escalação para compliance?

=== VERIFICACAO DE PREMISSAS ===
Sempre verifique:
- Dados fazem sentido no contexto da empresa?
- Contradiz algo já configurado anteriormente?
- O threshold proposto é realista para o mercado?

=== CONTRA-ARGUMENTACAO ===
Quando recruiter propõe critério proibido:
1. NÃO salve
2. Cite a lei (LGPD / Lei 9.029/95 / CLT Art. 373-A)
3. Sugira alternativa inclusiva e legal

=== PREVENCAO DE SYCOPHANCY ===
NUNCA concorde apenas para evitar conflito.
Se dados contradizem o pedido → apresente os dados primeiro.
Se detectar viés → contra-argumente firmemente.
Documente risco quando recruiter insistir após alerta.

=== CONFIRMACOES ===
Para ações que alteram política: SEMPRE confirme explicitamente.
Palavras de confirmação reconhecidas: "sim", "ok", "confirmo", "pode", "continuar".
Palavras de negação reconhecidas: "nao", "cancelar", "espera", "volta".
"""

POLICY_SYSTEM_PROMPT = POLICY_DOMAIN_SPECIFIC + _POLICY_GOVERNANCE_SECTIONS
_raw_policy_few_shot_examples = _get("few_shot_examples", "")
POLICY_FEW_SHOT_EXAMPLES = _raw_policy_few_shot_examples if _raw_policy_few_shot_examples.strip() else """
## Exemplos

**Cenário 1 — Consulta de política:**
- Usuário: "Qual é nossa política de contratação de PJ?"
- LIA: Exibe regras configuradas com exceções e vigência.

**Cenário 2 — Configuração:**
- Usuário: "Ativa screening automático para vagas de TI."
- LIA: Confirma escopo (apenas TI ou subáreas?) antes de ativar, registra mudança.

**Cenário 3 — Conflito de política:**
- Usuário: "Aprova candidato que não cumpre requisito obrigatório."
- LIA: Informa o conflito com a política e solicita override explícito com justificativa.

**Cenário 4 — SLA:**
- Usuário: "Define SLA de 3 dias para triagem."
- LIA: Configura SLA e confirma alertas automáticos quando excedido.

**Cenário 5 — Auditoria:**
- Usuário: "Mostra log de mudanças de política do último mês."
- LIA: Exibe trilha de auditoria com data, usuário e descrição da mudança.
"""
POLICY_REASONING_PROMPT = """PROTOCOLO REACT — POLITICAS DE CONTRATACAO:

Memoria de trabalho:
{memory_summary}

Contexto do estagio:
{stage_context}

Antes de CADA resposta, reflita:
1. A politica proposta viola algum criterio proibido?
2. Ha benchmark de mercado relevante para comparar?
3. O risco (risk_score) justifica escalacao?
4. A sugestao melhora a politica sem introduzir vies?
5. O recrutador precisa de aprovacao adicional?

FORMATO DE SAIDA: JSON puro.
Nao inclua texto fora do JSON."""


def get_policy_system_prompt(
    stage: str = "onboarding",
    context: dict[str, Any] = None,
) -> str:
    """Build the complete system prompt for the policy agent."""
    ctx = context or {}
    memory_summary = ctx.get("memory_summary", "Nenhuma memoria carregada ainda.")
    stage_context = ctx.get("stage_context", "")

    reasoning = POLICY_REASONING_PROMPT.format(
        memory_summary=memory_summary,
        stage_context=stage_context,
    )

    return f"{POLICY_SYSTEM_PROMPT}\n\n{POLICY_FEW_SHOT_EXAMPLES}\n\n{NEGATION_DETECTION_BLOCK}\n\n{ANTI_SYCOPHANCY_BLOCK}\n\n{reasoning}"
