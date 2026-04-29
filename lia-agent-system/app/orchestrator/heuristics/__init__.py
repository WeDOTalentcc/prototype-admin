"""
Orchestrator heuristics — pattern-based detectors.

Extraídos do `Orchestrator` V1 (LIA-D06 DEPRECATED) para módulos canônicos
dedicados como parte do Sprint II.3 da migração V1→V2.

## Taxonomia harness-engineering

Estes módulos são `[sensor]` puros — observam mensagens e retornam classificação
booleana. Não decidem ação, apenas detectam padrões.

## Comportamento preservado

A intenção é que estes módulos retornem EXATAMENTE os mesmos resultados que
`Orchestrator._is_technical_response()` e `Orchestrator._is_cv_matching_request()`
do V1, para que characterization tests do Sprint I continuem verdes.

## Public API

    from app.orchestrator.heuristics import (
        is_technical_response,
        is_cv_matching_request,
    )

    if is_technical_response(message):
        ...

    if is_cv_matching_request(user_message):
        ...

## Reference

ADR-019 — Orchestrator V1→V2 Consolidation, Sprint II.3
"""
from .cv_matching_detector import is_cv_matching_request
from .technical_response_detector import is_technical_response

__all__ = [
    "is_cv_matching_request",
    "is_technical_response",
]
