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
try:
    from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_FULL as _ANTI_SYCO_FULL
except ImportError:
    _ANTI_SYCO_FULL = """
=== PREVENCAO DE SYCOPHANCY ===
REGRAS ABSOLUTAS:
1. NUNCA concorde com o recrutador apenas para evitar conflito

=== VERIFICACAO DE PREMISSAS ===
Valide afirmacoes antes de aceitar como verdade.
"""
# --- TRANSICOES (canonical source for confirmation/negation vocab) ---
_WIZARD_TRANSICOES_BLOCK = """
=== TRANSICOES ===
Entenda confirmacoes e processe-as corretamente.
Palavras de confirmacao (reconhecer como "sim"): "sim", "ok", "confirmo", "certo",
"pode", "vamos", "bora", "perfeito", "concordo", "aprovo", "seguir", "continuar",
"prosseguir".

Entenda negacoes e respeite-as imediatamente.
Palavras de negacao (reconhecer como "nao"): "nao", "espera", "cancelar", "cancela",
"para", "volta", "errei", "nao quero", "desistir", "nao e isso".

Para acoes irreversiveis: SEMPRE confirme explicitamente antes de executar.
"""

WIZARD_SYSTEM_PROMPT = WIZARD_DOMAIN_SPECIFIC + _WIZARD_TRANSICOES_BLOCK + _ANTI_SYCO_FULL
WIZARD_REASONING_PROMPT = """PROTOCOLO REACT — WIZARD DE VAGAS:

Contexto do estágio atual:
{stage_context}

Memória de trabalho:
{memory_summary}

Antes de CADA resposta, reflita:
1. Em qual etapa do wizard estamos? (título, requisitos, competências, JD, revisão, publicação)
2. O recrutador forneceu dados suficientes para avançar?
3. Há risco de discriminação nos requisitos coletados?
4. Os requisitos são realistas para o mercado? (benchmark)
5. As competências WSI estão completas? (mín 9 técnicas + 5 comportamentais)

FORMATO DE SAIDA: JSON puro.
Nao inclua texto fora do JSON."""


def build_system_prompt(
    stage_context: str = "",
    memory_summary: str = "",
    learning_adjustments: dict | None = None,
) -> str:
    """Build the complete system prompt for the job creation wizard.

    Sprint 15.4 (2026-05-24): adicionado parâmetro `learning_adjustments`
    para injetar Loop D (WizardFeedback) signals no prompt. Permite que
    LIA aprenda com correções históricas do recrutador (salary range
    adjustment, seniority preferences, etc.) por company.

    Args:
        stage_context: Contexto da stage atual do wizard.
        memory_summary: Resumo da memória de trabalho.
        learning_adjustments: Dict retornado por
            `feedback_learning_service.get_correction_patterns` ou
            `get_learning_adjustments` (lia_assistant/_shared.py).
            Formato esperado: {field_name: {direction, adjustment_pct,
            confidence, sample_size, ...}, ...}. Quando None ou vazio,
            seção não é injetada (backward compat).

    Returns:
        System prompt completo. Quando learning_adjustments populated,
        inclui seção "## Aprendizados desta empresa" antes do reasoning.
    """
    reasoning = WIZARD_REASONING_PROMPT.format(
        stage_context=stage_context or "",
        memory_summary=memory_summary or "Nenhuma memoria de trabalho disponivel.",
    )

    learning_section = ""
    if learning_adjustments:
        # Sprint 15.4 Loop D: format adjustments as markdown section
        lines = ["", "## Aprendizados desta empresa (Loop D)", ""]
        for field, adj in learning_adjustments.items():
            if not isinstance(adj, dict):
                continue
            sample = adj.get("sample_size", "?")
            confidence = adj.get("confidence", "?")
            if field == "salary_range":
                pct = adj.get("adjustment_pct", 0)
                direction = adj.get("direction", "stable")
                lines.append(
                    f"- **Salary range**: histórico mostra {direction} "
                    f"~{abs(pct):.0f}% (sample={sample}, conf={confidence}). "
                    f"Considere essa tendência ao sugerir."
                )
            elif field == "seniority":
                from_val = adj.get("from_value", "?")
                to_val = adj.get("to_value", "?")
                lines.append(
                    f"- **Seniority**: recrutadores frequentemente ajustam "
                    f"'{from_val}' → '{to_val}' (conf={confidence}). "
                    f"Verifique se está sendo apropriado."
                )
            else:
                # Generic fallback for future fields
                lines.append(f"- **{field}**: ajuste histórico disponível (sample={sample}, conf={confidence}).")
        lines.append("")
        lines.append(
            "Use esses sinais como context — NÃO substitua decisão do recrutador. "
            "Eles vêm de correções passadas e podem informar (não dictate) suas sugestões."
        )
        learning_section = "\n".join(lines) + "\n"

    return f"{WIZARD_SYSTEM_PROMPT}{learning_section}\n\n{reasoning}"
