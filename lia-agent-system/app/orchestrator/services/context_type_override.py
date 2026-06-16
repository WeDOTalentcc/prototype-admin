"""
Context-type override — hardcoded mapping de context_type para domain_id.

Sprint II.4 da migração V1→V2 (LIA-D06 cleanup). Extrai o mapping
hardcoded de `Orchestrator.process_request()` linhas 130-145 (V1) para
módulo canônico reutilizável.

## Comportamento preservado

V1 tem mapping inline:
```python
_CONTEXT_TYPE_DOMAIN_OVERRIDE = {
    "company_settings": "company_settings",
    "hiring_policy": "hiring_policy",
}
```

Quando `context["context_type"]` corresponde a uma chave, V1 cria um
`RouteResult` "fake" com confidence=1.0 e source="context_type_override",
**bypassing** o `CascadedRouter` completamente. Isso garante que requisições
do FE com contexto explícito de configuração (ex: tela de Configurações da
Empresa) sempre vão para o domain certo, sem depender de NLP.

## Taxonomia harness-engineering

`[guide]` — decide rota antes do router (feedforward override).

## Reference

ADR-019 — Sprint II.4
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from app.orchestrator.routing.cascaded_router import RouteResult


# Mapping canônico: context_type (string do FE) → domain_id (interno)
# DO NOT modify without updating characterization tests.
#
# Quando V1/V2 receberem `context["context_type"]` igual a uma chave aqui,
# o roteamento via CascadedRouter é bypassado e o domain_id correspondente
# é usado diretamente.
CONTEXT_TYPE_DOMAIN_MAPPING: Final[dict[str, str]] = {
    "company_settings": "company_settings",
    "hiring_policy": "hiring_policy",
}


# Source string usado em RouteResult.source para rastreabilidade
OVERRIDE_SOURCE: Final[str] = "context_type_override"


def get_domain_override(context_type: str) -> str | None:
    """
    Retorna domain_id se context_type mapeia para um override.

    Args:
        context_type: Valor de `context["context_type"]` enviado pelo FE.

    Returns:
        domain_id correspondente se mapping existe, None caso contrário.

    Examples:
        >>> get_domain_override("company_settings")
        'company_settings'
        >>> get_domain_override("hiring_policy")
        'hiring_policy'
        >>> get_domain_override("anything_else") is None
        True
        >>> get_domain_override("") is None
        True
    """
    return CONTEXT_TYPE_DOMAIN_MAPPING.get(context_type)


def build_override_route(domain_id: str) -> RouteResult:
    """
    Constrói RouteResult fake para um override de context_type.

    Imports `RouteResult` lazy para evitar circular dependency com
    `cascaded_router.py` (que pode crescer e importar de services/).

    Args:
        domain_id: Domain canônico (deve vir de `get_domain_override()`).

    Returns:
        RouteResult com confidence=1.0 e source=OVERRIDE_SOURCE.

    Examples:
        >>> route = build_override_route("company_settings")
        >>> route.domain_id
        'company_settings'
        >>> route.confidence
        1.0
        >>> route.source
        'context_type_override'
    """
    # Lazy import — evita circular deps + reduz custo de import-time
    from app.orchestrator.routing.cascaded_router import RouteResult

    return RouteResult(
        domain_id=domain_id,
        confidence=1.0,
        source=OVERRIDE_SOURCE,
        intent_details={"raw_intent": domain_id},
    )


def try_override_route(context: dict | None) -> RouteResult | None:
    """
    Conveniência: combina get_domain_override + build_override_route.

    Lê `context.get("context_type")`, decide se há override, e retorna
    RouteResult pronto ou None.

    Args:
        context: Dict de contexto da request (pode ser None).

    Returns:
        RouteResult se mapping existe, None caso contrário (caller deve
        usar CascadedRouter normal).

    Examples:
        >>> try_override_route({"context_type": "company_settings"}) is not None
        True
        >>> try_override_route({"context_type": "unknown"}) is None
        True
        >>> try_override_route(None) is None
        True
    """
    if not context:
        return None

    ctx_type = context.get("context_type", "")
    domain_override = get_domain_override(ctx_type)
    if domain_override is None:
        return None

    return build_override_route(domain_override)
