"""
Rail A hint override — domain/intent hints emitidos pelo trilho do chat (FE).

Sprint III.X (PR-A — Rail A metadata routing). Resolve FE-H03 do audit
enterprise 2026-04-26: cards do `ChatWorkflowReels` agora enviam metadata
estruturada via `context.metadata` no payload WS.

## Comportamento

Quando `context["metadata"]` foi populado pelo `ContextAdapter.from_ws` a
partir do payload WS do FE, e contém `source: "rail_a"` mais um
`domain_hint` válido (registrado em `DomainRegistry`), retorna um
`RouteResult` com confidence=0.99 e source="rail_a_hint_override",
bypassing o `CascadedRouter`.

Defensivo:
- ``source`` deve ser exatamente ``"rail_a"`` — hint sem essa flag é
  ignorado (evita prompt injection via context arbitrário).
- ``domain_hint`` deve estar registrado em `DomainRegistry` — typos /
  drift caem no fallback.

## Taxonomia harness-engineering

``[guide computacional]`` — decide rota antes do router via metadata
estruturada do FE (feedforward, P(erro)≈0 quando hint presente).

## Precedência

Esta função é chamada **antes** de `context_type_override.try_override_route`
em `Orchestrator.process_request`, para permitir que o Rail A roteie de
forma determinística mesmo quando context_type genérico (ex.: "general").

## Reference

- Audit enterprise 2026-04-26: FE-H03, INT-S04 (`~/.claude/plans/ssh-i-ssh-replit-p-mellow-simon.md`)
- ADR-019 — Sprint II.4 (padrão de override via service module)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from app.orchestrator.routing.cascaded_router import RouteResult

logger = logging.getLogger(__name__)


OVERRIDE_SOURCE: Final[str] = "rail_a_hint_override"
TRUSTED_SOURCE: Final[str] = "rail_a"
HINT_CONFIDENCE: Final[float] = 0.99


def get_hint_domain(metadata: dict | None) -> tuple[str, str | None] | None:
    """Retorna ``(domain_id, intent_id)`` se metadata declara hint válido.

    Args:
        metadata: Conteúdo de ``context["metadata"]`` (vindo do FE Rail A).

    Returns:
        Tupla ``(domain_id, intent_hint)`` se hint válido (source=rail_a +
        domain_hint registrado). ``intent_id`` pode ser ``None`` quando
        card só especifica domínio (ex.: 5.1 send-offer pré-PR-B).
        ``None`` caso contrário (caller cai no próximo override / router).
    """
    if not isinstance(metadata, dict):
        return None
    if metadata.get("source") != TRUSTED_SOURCE:
        return None
    domain_hint = metadata.get("domain_hint")
    if not isinstance(domain_hint, str) or not domain_hint:
        return None
    # Validar contra DomainRegistry — fail-safe contra typos / drift.
    try:
        from app.domains.registry import DomainRegistry
        registry = DomainRegistry()
        if domain_hint not in registry.list_domains():
            logger.warning(
                "[rail_a_hint] domain_hint=%s não registrado — fallback",
                domain_hint,
            )
            return None
    except Exception as exc:
        logger.debug("[rail_a_hint] DomainRegistry lookup skipped: %s", exc)
        return None

    intent_hint = metadata.get("intent_hint")
    intent_id = intent_hint if isinstance(intent_hint, str) and intent_hint else None
    return (domain_hint, intent_id)


def build_hint_route(domain_id: str, intent_id: str | None) -> RouteResult:
    """Constrói RouteResult para hint do Rail A.

    Lazy import de ``RouteResult`` para evitar circular dependency.
    Returns intent_details as a plain dict for backward-compat (callers use .get()).
    """
    from app.orchestrator.routing.cascaded_router import RouteResult

    return RouteResult(
        domain_id=domain_id,
        confidence=HINT_CONFIDENCE,
        source=OVERRIDE_SOURCE,
        intent_details={"raw_intent": intent_id or domain_id},
    )


def try_hint_route(context: dict | None) -> RouteResult | None:
    """Conveniência: combina ``get_hint_domain`` + ``build_hint_route``.

    Args:
        context: Dict de contexto da request (pode ser None).

    Returns:
        ``RouteResult`` se hint válido, ``None`` caso contrário.

    Examples:
        >>> try_hint_route({"metadata": {"source": "rail_a", "domain_hint": "job_management"}}) is not None  # doctest: +SKIP
        True
        >>> try_hint_route({"metadata": {"domain_hint": "job_management"}}) is None
        True
        >>> try_hint_route(None) is None
        True
    """
    if not context:
        return None
    # Primary path: metadata sub-dict (standard WS message format)
    metadata = context.get("metadata")
    resolved = get_hint_domain(metadata)
    if resolved is None:
        # Fallback: some WS adapters promote context.extra to top-level context.
        # Accept context itself as the "metadata" when source+domain_hint are present.
        resolved = get_hint_domain(context)
    if resolved is None:
        return None
    domain_id, intent_id = resolved
    return build_hint_route(domain_id, intent_id)
