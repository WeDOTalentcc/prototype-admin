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
    from app.orchestrator.cascaded_router import RouteResult

logger = logging.getLogger(__name__)


OVERRIDE_SOURCE: Final[str] = "rail_a_hint_override"
TRUSTED_SOURCE: Final[str] = "rail_a"
HINT_CONFIDENCE: Final[float] = 0.99

# Routing targets that are valid Rail A destinations but are NOT registered
# via @register_domain (DomainPrompt pattern). These are LangGraph canonical
# flows or hard-coded WS handler branches — equally valid routing targets.
#
# "wizard" — JobCreationGraph canonical flow, handled at
#   agent_chat_ws.py:~1153 (`if active_domain == "wizard":`). Not in
#   DomainRegistry because it bypasses the DomainPrompt / ReAct agent path.
#
# Add new entries here when introducing non-DomainRegistry routing targets
# that the FE may hint at via Rail A metadata.
_RAIL_A_EXTRA_TARGETS: Final[frozenset[str]] = frozenset({
    "wizard",
})


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
    # Validar contra DomainRegistry + _RAIL_A_EXTRA_TARGETS — fail-safe contra
    # typos / drift. _RAIL_A_EXTRA_TARGETS cobre routing targets válidos que
    # existem como fluxos LangGraph ou branches hardcoded no WS handler mas
    # NÃO estão registrados via @register_domain (ex.: "wizard").
    try:
        from app.domains.registry import DomainRegistry
        registry = DomainRegistry()
        if (
            domain_hint not in registry.list_domains()
            and domain_hint not in _RAIL_A_EXTRA_TARGETS
        ):
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
    """
    from app.orchestrator.cascaded_router import RouteResult

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

    Lê o hint em duas estruturas (defesa em profundidade — INT-S04 followup):

    1. ``context["metadata"]`` — formato canônico, populado por
       ``ContextAdapter.from_ws``/``from_rabbitmq`` quando preservam o
       payload original do FE.
    2. ``context`` top-level — fallback usado quando o adapter promove
       ``extra`` para top-level via ``to_orchestrator_context()`` ou
       quando o handler popula ``context["domain_hint"]`` diretamente
       (ex.: HTTP handler simplificado).

    Em ambos os casos, ``get_hint_domain`` valida rigorosamente
    ``source == "rail_a"`` (anti-injection) e ``domain_hint ∈ DomainRegistry``
    (allowlist). Hint malformado em qualquer estrutura → fallback.

    Examples:
        >>> try_hint_route({"metadata": {"source": "rail_a", "domain_hint": "job_management"}}) is not None  # doctest: +SKIP
        True
        >>> try_hint_route({"metadata": {"domain_hint": "job_management"}}) is None  # missing source
        True
        >>> try_hint_route({"source": "rail_a", "domain_hint": "job_management"}) is not None  # doctest: +SKIP
        True
        >>> try_hint_route(None) is None
        True
    """
    if not context:
        return None

    # Caminho canônico: context["metadata"] populado pelo adapter.
    resolved = get_hint_domain(context.get("metadata"))

    # Fallback: hint em top-level (canal HTTP simplificado ou WS sem adapter).
    # Mantém as mesmas validações computacionais via get_hint_domain.
    if resolved is None:
        flat_hint = {
            "source": context.get("source"),
            "domain_hint": context.get("domain_hint"),
            "intent_hint": context.get("intent_hint"),
        }
        # Só tenta se há sinal de hint top-level (evita chamada inútil).
        if flat_hint["source"] or flat_hint["domain_hint"]:
            resolved = get_hint_domain(flat_hint)

    if resolved is None:
        return None
    domain_id, intent_id = resolved
    return build_hint_route(domain_id, intent_id)
