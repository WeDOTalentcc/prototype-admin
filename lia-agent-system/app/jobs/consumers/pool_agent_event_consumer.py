"""Sprint 7C Part 2 — event-driven dispatch canonical pra pool_agent_assignments.

Wireia 4 eventos canonical (alinhados ao EventTriggerPicker frontend Agent B
948abf887) → dispatch via Celery task `dispatch_pool_agent_assignment_task`.

Arquitetura canonical:
  1. `CANONICAL_EVENT_TYPES` — 4 nomes canonical (UI ↔ backend contract).
  2. `on_event_received(event_name, payload)` — handler único:
     - filtra event_name não-canonical (silent skip);
     - lookup pool_agent_assignments WHERE schedule_type='event_driven'
       AND status='active';
     - filtra event_triggers (schedule_config['event_triggers']) match;
     - dispatch via .delay() com trigger_source='event_driven'.
  3. `register_pool_agent_event_handlers()` — registra `on_event_received`
     no registry canonical de `app.shared.messaging.platform_events`.
  4. `start_pool_agent_event_consumer()` — declara topic exchange
     `platform.events` + bind queue `pool_agent_event_driven` aos 4 routing
     keys canonical + delega cada mensagem a `dispatch_event` (registry).

REGRA ZERO multi-tenancy: `company_id` lido do próprio assignment
(persistido) — nunca do payload do evento. Defesa em profundidade caso
emit point esqueça de incluir company_id.

Refs:
- AGENT_STUDIO_SPRINT7_PLAN.md §4 Sprint 7C Part 2
- Agent B 948abf887 (EventTriggerPicker frontend exporta CANONICAL_EVENT_TYPES)
- app/jobs/tasks/pool_agents.py (Part 1 v2 cron scan + dispatch task)
- app/shared/messaging/platform_events.py (registry canonical)
- app/services/onboarding_consumer.py (pattern exchange+bind+iterator)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.jobs.tasks.pool_agents import dispatch_pool_agent_assignment_task

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Canonical events (alinhados frontend EventTriggerPicker Agent B 948abf887)
# ─────────────────────────────────────────────────────────────────────────────

CANONICAL_EVENT_TYPES: list[str] = [
    "candidate_added_to_pool",
    "candidate_screened",
    "agent_completed_review",
    "weekly_summary",
]

PLATFORM_EVENTS_EXCHANGE = "platform.events"
POOL_AGENT_EVENT_QUEUE = "pool_agent_event_driven"


# ─────────────────────────────────────────────────────────────────────────────
# Handler canonical (testável direto, decoupled do transport RabbitMQ)
# ─────────────────────────────────────────────────────────────────────────────


async def on_event_received(event_name: str, event_payload: dict[str, Any]) -> None:
    """Handler canonical pra eventos canonical Pool-Agent.

    Args:
        event_name: routing key canonical (ex: 'candidate_added_to_pool').
        event_payload: payload do PlatformEvent (já parseado de JSON).

    Behavior:
        - event_name fora de CANONICAL_EVENT_TYPES → silent skip
          (não-canonical não dispara dispatch).
        - lookup assignments active+event_driven, filtra event_triggers match,
          dispatch via .delay() pra cada match.

    REGRA ZERO: company_id usado no dispatch vem do assignment row, nunca do
    event_payload (defesa em profundidade contra cross-tenant via payload
    forjado).
    """
    if event_name not in CANONICAL_EVENT_TYPES:
        # Silent skip canonical: event não-canonical não-dispara dispatch.
        # Não é erro — outros consumers podem processar.
        return

    from lia_models.pool_agent_assignment import PoolAgentAssignment

    async with AsyncSessionLocal() as db:
        stmt = select(PoolAgentAssignment).where(
            PoolAgentAssignment.schedule_type == "event_driven",
            PoolAgentAssignment.status == "active",
        )
        result = await db.execute(stmt)
        assignments = result.scalars().all()

        dispatched_count = 0
        for a in assignments:
            triggers = (a.schedule_config or {}).get("event_triggers", [])
            if event_name not in triggers:
                continue

            dispatch_pool_agent_assignment_task.delay(
                assignment_id=str(a.id),
                trigger_source="event_driven",
            )
            dispatched_count += 1

        if dispatched_count > 0:
            logger.info(
                "[PoolAgentEventConsumer] event=%s dispatched=%d assignments",
                event_name,
                dispatched_count,
            )


# ─────────────────────────────────────────────────────────────────────────────
# Registry wiring canonical (platform_events handlers)
# ─────────────────────────────────────────────────────────────────────────────


async def _platform_event_handler_wrapper(event):
    """Adapter PlatformEvent → on_event_received(event_name, payload).

    O registry canonical (`app.shared.messaging.platform_events`) dispatcha
    o PlatformEvent inteiro; nosso handler precisa do (event_name, payload).
    """
    await on_event_received(event.event_type, event.payload or {})


def register_pool_agent_event_handlers() -> None:
    """Registra `_platform_event_handler_wrapper` pros 4 eventos canonical.

    Chamado no startup canonical (app/main.py lifespan).
    Idempotente sob 1 boot — chamar 2x duplica handlers.
    """
    from app.shared.messaging.platform_events import register_event_handler

    for event_name in CANONICAL_EVENT_TYPES:
        register_event_handler(event_name, _platform_event_handler_wrapper)

    logger.info(
        "[PoolAgentEventConsumer] handlers registrados pra %d eventos canonical: %s",
        len(CANONICAL_EVENT_TYPES),
        CANONICAL_EVENT_TYPES,
    )


# ─────────────────────────────────────────────────────────────────────────────
# RabbitMQ subscription canonical (platform.events exchange → dispatch_event)
# ─────────────────────────────────────────────────────────────────────────────

_consumer_task: asyncio.Task | None = None


async def start_pool_agent_event_consumer() -> None:
    """Inicializa subscription RabbitMQ canonical pra platform.events.

    Declara topic exchange `platform.events` + queue `pool_agent_event_driven`
    bound a 4 routing keys canonical. Cada mensagem recebida vira chamada a
    `dispatch_event` (registry canonical), que invoca os handlers registrados.

    No-op canonical se:
      - RABBITMQ_URL não configurado (dev local sem broker);
      - aio_pika não instalado;
      - falha de conexão (loga + retorna; não trava startup).

    Pattern derivado de `app/services/onboarding_consumer.py` (canonical).
    """
    global _consumer_task

    rabbitmq_url = os.getenv("RABBITMQ_URL")
    if not rabbitmq_url:
        logger.info(
            "[PoolAgentEventConsumer] RABBITMQ_URL não configurado — consumer inativo "
            "(handlers continuam registrados; dispatch_event direto via testes ainda funciona)."
        )
        return

    try:
        import aio_pika  # noqa: F401
    except ImportError:
        logger.info(
            "[PoolAgentEventConsumer] aio_pika não instalado — consumer inativo."
        )
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.error(
            "[PoolAgentEventConsumer] no running event loop — cannot start consumer."
        )
        return

    _consumer_task = loop.create_task(
        _consume_loop(rabbitmq_url), name="pool_agent_event_consumer"
    )
    logger.info("[PoolAgentEventConsumer] consumer task agendado")


async def _consume_loop(rabbitmq_url: str) -> None:
    """Loop de consumo canonical: declare exchange/queue + bind + iterate.

    Falhas de conexão logam + sleep 30s + retry (mesmo pattern
    onboarding_consumer). Falhas individuais de mensagem logam + continue.
    """
    import aio_pika
    from app.shared.messaging.platform_events import dispatch_event

    while True:
        try:
            connection = await aio_pika.connect_robust(rabbitmq_url)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)

            exchange = await channel.declare_exchange(
                PLATFORM_EVENTS_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            queue = await channel.declare_queue(
                POOL_AGENT_EVENT_QUEUE,
                durable=True,
            )
            # Bind aos 4 routing keys canonical
            for event_name in CANONICAL_EVENT_TYPES:
                await queue.bind(exchange, routing_key=event_name)

            logger.info(
                "[PoolAgentEventConsumer] conectado: queue=%s bound a %d routing keys",
                POOL_AGENT_EVENT_QUEUE,
                len(CANONICAL_EVENT_TYPES),
            )

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            raw = json.loads(message.body.decode())
                            await dispatch_event(raw)
                        except Exception as exc:
                            logger.error(
                                "[PoolAgentEventConsumer] falha ao processar mensagem: %s",
                                exc,
                            )
        except asyncio.CancelledError:
            logger.info("[PoolAgentEventConsumer] consumer cancelado")
            return
        except Exception as exc:
            logger.error(
                "[PoolAgentEventConsumer] conexão falhou: %s — retry em 30s", exc
            )
            await asyncio.sleep(30)


async def stop_pool_agent_event_consumer() -> None:
    """Cancela task do consumer (shutdown canonical)."""
    global _consumer_task
    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except (asyncio.CancelledError, Exception):
            pass
    _consumer_task = None
