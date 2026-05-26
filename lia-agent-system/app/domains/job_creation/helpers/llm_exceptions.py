"""Helper canonical para classificar excecoes de LLM em sync nodes do wizard.

Sprint Onda 2 PR-5 (2026-05-26) extraiu pattern copy-paste inline em 4 sites
de graph.py (F-2.9). Antes da extracao cada site repetia heuristica de 8
tokens substring contra str(exc).lower().

Pattern canonical (substitui inline):

```python
# ANTES (inline copy-paste em 4 sites do graph.py)
_exc_str = str(exc).lower()
if any(t in _exc_str for t in (
    "rate", "quota", "429", "503", "provider", "api",
    "unauthorized", "forbidden", "401", "403",
)):
    reason = "provider_error"
else:
    reason = "exception"

# DEPOIS (canonical, single source of truth)
from app.domains.job_creation.helpers.llm_exceptions import (
    classify_llm_exception_reason,
)
reason = classify_llm_exception_reason(exc)
```
"""
from __future__ import annotations

import logging
from typing import Literal

logger = logging.getLogger(__name__)

LlmExceptionReason = Literal["provider_error", "exception"]


# Tokens canonical que sinalizam erro de provedor LLM (rate-limit, quota,
# HTTP 4xx/5xx auth). Single source of truth — mudancas aqui afetam os 4
# sites de uma vez. Lower-case porque comparacao usa str(exc).lower().
_PROVIDER_ERROR_TOKENS: tuple[str, ...] = (
    "rate",
    "quota",
    "429",
    "503",
    "provider",
    "api",
    "unauthorized",
    "forbidden",
    "401",
    "403",
)


def classify_llm_exception_reason(exc: BaseException) -> LlmExceptionReason:
    """Classifica excecao de LLM call em motivo canonical para fallback metric.

    Heuristica leve por substring na mensagem (case-insensitive). Erros HTTP
    /quota do provedor LLM costumam carregar termos como "rate", "quota",
    "429", "503", "provider". Os 4 sites originais usavam exatamente este
    set de tokens.

    Args:
        exc: Excecao capturada em call LLM (timeout NAO entra aqui — timeouts
             sao tratados antes via `asyncio.TimeoutError` e reason="timeout").

    Returns:
        "provider_error" quando substring match com tokens canonical,
        "exception" caso contrario.
    """
    exc_str = str(exc).lower()
    if any(token in exc_str for token in _PROVIDER_ERROR_TOKENS):
        return "provider_error"
    return "exception"
