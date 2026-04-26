"""
Technical response detector — heuristic for fallback gating.

Detects whether a generated response looks "too technical" (router internal
keywords leaking through to the user) and should trigger LIA-A04 fallback to
direct LLM handling.

## Origin

Extraído de `Orchestrator._is_technical_response()` (V1 LIA-D06 DEPRECATED)
linhas 383-388 + `_TECHNICAL_PATTERNS` em linhas 376-382.

Comportamento exato preservado para que characterization tests do Sprint I
continuem verdes.

## Behavior

Retorna `True` se a mensagem:
1. Igual exatamente a `"Processado com sucesso."` (caso especial)
2. Contém qualquer um dos patterns de `TECHNICAL_PATTERNS`

A correspondência é case-sensitive (substring match).

## Taxonomia harness-engineering

`[sensor]` puro — apenas classifica, não decide ação. O caller usa o
resultado para decidir se aciona fallback (que é `[guide]`).

## Reference

ADR-019 — Sprint II.3 (heuristics module extraction)
"""
from __future__ import annotations

from typing import Final

# Patterns canônicos — DO NOT modify without updating characterization tests
TECHNICAL_PATTERNS: Final[tuple[str, ...]] = (
    "Keyword heuristic matched",
    "Ferramenta '",
    "Ação '",
    "encaminhada para o agente",
    "executada para ação",
)

# Special-case exact match
_EXACT_MATCH_TECHNICAL: Final[str] = "Processado com sucesso."


def is_technical_response(message: str) -> bool:
    """
    Detecta se a mensagem é uma resposta "técnica" (router internals leaking).

    Args:
        message: Resposta gerada pelo orchestrator/router para classificar.

    Returns:
        True se mensagem contém marcadores técnicos que sinalizam que
        a classificação por keyword/heurística não produziu uma resposta
        adequada ao usuário e fallback deve ser acionado.

    Examples:
        >>> is_technical_response("Processado com sucesso.")
        True
        >>> is_technical_response("Ferramenta 'analyze_cv' executada com sucesso")
        True
        >>> is_technical_response("Olá! Como posso ajudar?")
        False
    """
    if message == _EXACT_MATCH_TECHNICAL:
        return True
    return any(p in message for p in TECHNICAL_PATTERNS)
