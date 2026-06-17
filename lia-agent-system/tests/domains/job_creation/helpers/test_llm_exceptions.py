"""Tests do helper classify_llm_exception_reason (PR-5 F-2.9 Onda 2).

Substitui assertion-by-inspection do pattern inline copy-paste em 4 sites do
graph.py por sensor unit explicito (8 cases parametrized cobrindo tokens
canonical + cases edge).
"""
from __future__ import annotations

import pytest

from app.domains.job_creation.helpers.llm_exceptions import (
    classify_llm_exception_reason,
)


@pytest.mark.parametrize(
    "exc,expected",
    [
        # Tokens canonical -> provider_error
        (Exception("Rate limit exceeded"), "provider_error"),
        (Exception("HTTP 429 too many requests"), "provider_error"),
        (Exception("API quota exhausted"), "provider_error"),
        (Exception("503 Service Unavailable from provider"), "provider_error"),
        (Exception("provider gateway timeout"), "provider_error"),
        (Exception("401 Unauthorized"), "provider_error"),
        (Exception("403 Forbidden"), "provider_error"),
        # Sem token canonical -> exception
        (Exception("Random unknown error"), "exception"),
        (ValueError("schema validation failed"), "exception"),
        (RuntimeError("internal state corrupted"), "exception"),
        # Case-insensitive
        (Exception("PROVIDER OUTAGE"), "provider_error"),
        # Empty exception
        (Exception(""), "exception"),
    ],
)
def test_classify_llm_exception_reason(exc: Exception, expected: str) -> None:
    """Heuristica de classificacao bate em todos os tokens canonical."""
    assert classify_llm_exception_reason(exc) == expected


def test_classify_returns_literal_values_only() -> None:
    """Garantia de contrato: so retorna provider_error OR exception."""
    # Sample sweep — todas as combinacoes possiveis devem ficar no Literal type
    for exc in [Exception("rate"), Exception("anything else")]:
        result = classify_llm_exception_reason(exc)
        assert result in ("provider_error", "exception")
