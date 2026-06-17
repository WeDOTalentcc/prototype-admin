"""
CV matching request detector — heuristic for routing override.

Detects whether a user message is requesting CV/candidate analysis,
regardless of the intent classified by `CascadedRouter`. Used to trigger
the rubric-based CV screening tool path even when intent classification
returns a different domain.

## Origin

Extraído de `Orchestrator._is_cv_matching_request()` (V1 LIA-D06 DEPRECATED)
linhas 400-403 + `_CV_MATCHING_PATTERNS` em linhas 390-399.

Comportamento exato preservado para que characterization tests do Sprint I
continuem verdes.

## Behavior

Retorna `True` se a mensagem (lowercased) contém qualquer um dos patterns
de `CV_MATCHING_PATTERNS`. Match é substring case-insensitive.

## Taxonomia harness-engineering

`[sensor]` puro — apenas classifica, não decide ação. O caller (V1
`_handle_directly` ou Sprint III V2 services) usa o resultado para decidir
se chama o rubric tool em vez do flow padrão.

## Reference

ADR-019 — Sprint II.3 (heuristics module extraction)
"""
from __future__ import annotations

from typing import Final

# Patterns canônicos — DO NOT modify without updating characterization tests.
# Patterns são em PT-BR pois é o idioma majoritário das interações na plataforma WeDo Talent.
CV_MATCHING_PATTERNS: Final[tuple[str, ...]] = (
    "analise o cv", "analisa o cv", "analisar o cv", "análise do cv",
    "compatibilidade do candidato", "compatibilidade de candidato",
    "match do candidato", "match de cv", "match score",
    "triagem de cv", "triagem do candidato",
    "score do candidato", "avaliar cv", "avalie o cv",
    "analise a compatibilidade", "análise de compatibilidade",
    "quanto o candidato", "como o candidato se encaixa",
    "candidato para a vaga", "candidato está alinhado",
)


def is_cv_matching_request(message: str) -> bool:
    """
    Detecta se a mensagem requisita análise de CV/compatibilidade de candidato.

    Args:
        message: Mensagem do usuário (qualquer caso/idioma — patterns são PT-BR).

    Returns:
        True se a mensagem solicita análise de CV/match de candidato,
        independente de qual intent o router classificou.

    Examples:
        >>> is_cv_matching_request("Analise o CV desse candidato para a vaga")
        True
        >>> is_cv_matching_request("Match score do candidato Maria")
        True
        >>> is_cv_matching_request("Olá, tudo bem?")
        False
        >>> is_cv_matching_request("ANALISE O CV")  # case-insensitive
        True
    """
    msg_lower = message.lower()
    return any(p in msg_lower for p in CV_MATCHING_PATTERNS)
