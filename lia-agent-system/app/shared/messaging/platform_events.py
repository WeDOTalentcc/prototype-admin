"""
Platform Events — comunicação assíncrona entre APIs de domínio via RabbitMQ.

Contrato de eventos:
  Exchange: "platform.events" (topic exchange)
  Routing keys: "{dominio}.{entidade}.{acao}"
    Ex: "vagas.job.published"
        "funil.candidate.moved"
        "onboarding.company.configured"

Por que eventos em vez de HTTP sync entre APIs?
  - Desacopla deploys (api-vagas pode estar down sem afetar api-funil)
  - Escala independente (muitos eventos publicados sem overhead de HTTP)
  - Auditável (exchange topic persiste mensagens)

André (reunião 08/03/2026): "Evitar chamadas HTTP síncronas entre APIs.
  Preferir RabbitMQ (eventos) ou shared database."
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

PLATFORM_EVENTS_EXCHANGE = "platform.events"


class PlatformEvent(BaseModel):
    """Schema base para todos os eventos inter-API."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str  # "vagas.job.published", "funil.candidate.moved", etc.
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    company_id: str
    payload: dict[str, Any]
    source_api: str  # "api-vagas" | "api-funil" | "api-onboarding"
    version: str = "1.0"


# ---------------------------------------------------------------------------
# Eventos específicos
# ---------------------------------------------------------------------------

class JobPublishedEvent(PlatformEvent):
    """Emitido quando uma vaga é publicada em api-vagas."""
    event_type: str = "vagas.job.published"
    source_api: str = "api-vagas"


class JobClosedEvent(PlatformEvent):
    """Emitido quando uma vaga é encerrada em api-vagas."""
    event_type: str = "vagas.job.closed"
    source_api: str = "api-vagas"


class CandidateMovedEvent(PlatformEvent):
    """Emitido quando um candidato muda de estágio em api-funil."""
    event_type: str = "funil.candidate.moved"
    source_api: str = "api-funil"


class CompanyConfiguredEvent(PlatformEvent):
    """Emitido quando uma empresa completa o onboarding em api-onboarding."""
    event_type: str = "onboarding.company.configured"
    source_api: str = "api-onboarding"


class ScreeningCompletedEvent(PlatformEvent):
    """Emitido quando a triagem WSI de um candidato é concluída."""
    event_type: str = "screening.wsi.completed"
    source_api: str = "api-funil"


# ---------------------------------------------------------------------------
# Agent Studio Fase 2.5 — Onda C1.3 (registrado 2026-05-29)
#
# Eventos event-driven que o motor de execução (C1.2 consumer) escuta para
# disparar deployments com trigger_mode correspondente:
#   on_apply                                          -> candidate_applied
#   on_enter_stage / on_exit_stage / on_stage_change  -> stage_changed
#   (on_stuck_in_stage e detectado por scheduler, nao por evento)
#
# Convencao de routing key: nome FLAT (candidate_applied, stage_changed),
# alinhado com CANONICAL_EVENT_TYPES do pool_agent_event_consumer e com a
# matriz canonical de app.shared.trigger_mode_validation. NAO usa o padrao
# dotted; o consumer event-driven faz match do event_type contra a
# allowlist de event_triggers do deployment.
# ---------------------------------------------------------------------------

class CandidateAppliedEvent(PlatformEvent):
    """Emitido quando um candidato se inscreve numa vaga (apply nativo).

    Dispara deployments com trigger_mode=on_apply acoplados ao target
    job=vacancy_id. payload canonical: {candidate_id, vacancy_id}.
    company_id vem do contexto do tenant (vacancy.company_id), NUNCA do
    payload do request -- multi-tenancy fail-closed (REGRA ZERO).
    """
    event_type: str = "candidate_applied"
    source_api: str = "lia-agent-system"


class StageChangedEvent(PlatformEvent):
    """Emitido quando o stage de um candidato muda no pipeline.

    Cobre os trigger_modes on_enter_stage / on_exit_stage / on_stage_change
    (on_stuck_in_stage e detectado por scheduler, fora do escopo de evento).
    payload canonical: {candidate_id, vacancy_id, from_stage, to_stage}.
    company_id vem do contexto do tenant, NUNCA do payload do request.
    """
    event_type: str = "stage_changed"
    source_api: str = "lia-agent-system"


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------

async def publish_platform_event(event: PlatformEvent) -> bool:
    """
    Publica evento no exchange platform.events.

    Routing key = event.event_type  (ex: "vagas.job.published")
    Retorna True se publicado com sucesso, False em caso de falha (graceful).

    Falha silenciosa intencional: a indisponibilidade do RabbitMQ não deve
    impedir o fluxo principal da aplicação. O evento é logado como erro
    para análise posterior.
    """
    try:
        from app.shared.messaging.rabbitmq_producer import publish_to_exchange
        await publish_to_exchange(
            exchange=PLATFORM_EVENTS_EXCHANGE,
            routing_key=event.event_type,
            message=event.model_dump(mode="json"),
        )
        logger.info(
            "[PlatformEvents] Published: %s company=%s event_id=%s",
            event.event_type,
            event.company_id,
            event.event_id,
        )
        return True
    except Exception as exc:
        logger.error(
            "[PlatformEvents] Failed to publish %s event_id=%s: %s",
            event.event_type,
            event.event_id,
            exc,
        )
        return False


# ---------------------------------------------------------------------------
# Handlers registry
# ---------------------------------------------------------------------------

_event_handlers: dict[str, list[Callable]] = {}


def register_event_handler(
    event_type: str,
    handler: Callable[[PlatformEvent], Awaitable[None]],
) -> None:
    """
    Registra handler para um tipo de evento.

    Múltiplos handlers podem ser registrados para o mesmo event_type.
    São executados em ordem de registro.

    Args:
        event_type: Routing key do evento (ex: "vagas.job.published").
        handler:    Coroutine que recebe PlatformEvent e não retorna valor.
    """
    if event_type not in _event_handlers:
        _event_handlers[event_type] = []
    _event_handlers[event_type].append(handler)
    logger.debug("[PlatformEvents] Handler registered for: %s", event_type)


def get_registered_handlers() -> dict[str, list[Callable]]:
    """Retorna cópia profunda do registry de handlers (útil para debug e testes)."""
    return {k: list(v) for k, v in _event_handlers.items()}


def clear_event_handlers() -> None:
    """Remove todos os handlers registrados. Útil em testes."""
    _event_handlers.clear()


async def dispatch_event(raw_message: dict) -> None:
    """
    Despacha evento recebido para os handlers registrados.

    Chamado pelo consumer RabbitMQ ao receber mensagem no exchange platform.events.
    Falhas individuais de handlers são capturadas e logadas sem interromper os demais.

    Args:
        raw_message: Dict com os campos de PlatformEvent serializado.
    """
    event_type = raw_message.get("event_type", "")
    handlers = _event_handlers.get(event_type, [])

    if not handlers:
        logger.debug("[PlatformEvents] No handlers for: %s", event_type)
        return

    try:
        event = PlatformEvent(**raw_message)
    except Exception as exc:
        logger.error("[PlatformEvents] Failed to parse event: %s — raw: %s", exc, raw_message)
        return

    for handler in handlers:
        try:
            await handler(event)
        except Exception as exc:
            logger.error(
                "[PlatformEvents] Handler %s failed for %s: %s",
                getattr(handler, "__name__", repr(handler)),
                event_type,
                exc,
            )
