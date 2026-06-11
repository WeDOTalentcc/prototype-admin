"""Fase 2.5 Onda C1.2 — event-driven dispatch canonical pra agent_deployments.

A PONTE event-driven do MOTOR UNIFICADO. Fecha o silent contract break do
AUDIT 4: um agente acoplado a uma vaga com trigger_mode=on_apply finalmente
dispara quando o candidato aplica.

Espelha `app/jobs/consumers/pool_agent_event_consumer.py` (canonical-fix — não
reinventa broker/consumer pattern) mas faz lookup na tabela CANONICAL UNIFICADA
`agent_deployments` (não a legada `pool_agent_assignments`).

Arquitetura canonical (mesmo shape do consumer legado):
  1. `CANONICAL_EVENT_TYPES` — 2 eventos FLAT (C1.3): candidate_applied, stage_changed.
  2. `on_event_received(event_name, payload, company_id)` — handler único:
     - filtra event_name não-canonical (silent skip);
     - lookup agent_deployments WHERE is_active AND company_id=<event> AND
       target_type/trigger_mode coerentes com o evento;
     - match evento→deployment (vacancy_id / stage) conforme a matriz abaixo;
     - dispatch via `dispatch_agent_deployment_task.delay()` com
       trigger_source='event_driven' + trigger_context (event_type, ids, stages).
  3. `register_agent_deployment_event_handlers()` — registra o adapter no registry
     canonical de `app.shared.messaging.platform_events`.
  4. `start_agent_deployment_event_consumer()` — declara topic exchange
     `platform.events` + bind queue `agent_deployment_event_driven` aos routing
     keys canonical + delega cada mensagem a `dispatch_event` (registry).

═══════════════════════════════════════════════════════════════════════════════
Matriz canonical evento → trigger_mode (single source: app.shared.trigger_mode_validation)
═══════════════════════════════════════════════════════════════════════════════
  candidate_applied (payload {candidate_id, vacancy_id})
    → deployments target_type='job', trigger_mode='on_apply',
      target_id == vacancy_id

  stage_changed (payload {candidate_id, vacancy_id, from_stage, to_stage})
    → deployments target_type='pipeline_stage':
        trigger_mode='on_enter_stage'  → quando to_stage   == stage do deployment
        trigger_mode='on_exit_stage'   → quando from_stage == stage do deployment
        trigger_mode='on_stage_change' → quando from_stage OU to_stage == stage
      (on_stuck_in_stage NÃO é event-based — é detectado por scheduler, fora deste
       consumer; ver app/jobs/tasks/agent_deployments.py scan.)

IDENTIDADE DO STAGE (decisão de ambiguidade C1.2 — registrada 2026-05-29):
  O evento carrega from_stage/to_stage como NOME de stage (VacancyCandidate.stage
  é String(50), ex: "Triagem", "Contratado"). O deployment guarda o stage em
  target_id (UUID de recruitment_stages) E target_name (nome display). Para casar
  de forma robusta independente de o tenant ter gravado target_id ou target_name,
  o match compara o stage do evento contra AMBOS str(target_id) E target_name.
  Não há risco de falso positivo cross-stage: UUID e nome vivem em namespaces
  distintos, e um stage só casa quando seu próprio identificador bate.

REGRA ZERO multi-tenancy: company_id usado no dispatch vem SEMPRE do
agent_deployment (persistido), nunca do payload do evento. O lookup ainda filtra
company_id do envelope do evento (validado por C1.3 a partir da row do tenant) —
defesa em profundidade. A dispatch task re-resolve company_id do próprio
deployment (3ª camada).

REGRA 4 (falhar alto): erro ao processar um evento loga LOUD (logger.error
exc_info=True) e re-raise pro transporte fazer nack/retry. NUNCA engole
silenciosamente (senão o agente não dispara e ninguém sabe).

Refs:
- AGENT_STUDIO_FASE2.5_PLANO_CONSOLIDACAO.md §Onda C1.2
- app/jobs/consumers/pool_agent_event_consumer.py (pattern canonical espelhado)
- app/jobs/tasks/agent_deployments.py (dispatch task — C1-core f486fdf8a)
- app/shared/messaging/platform_events.py (CandidateAppliedEvent/StageChangedEvent — C1.3 c64bef950)
- app/shared/trigger_mode_validation.py (VALID_TRIGGER_MODES_BY_TARGET — single source matriz)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.jobs.tasks.agent_deployments import dispatch_agent_deployment_task

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Canonical events (FLAT names — alinhados C1.3 platform_events + EventTriggerPicker)
# ─────────────────────────────────────────────────────────────────────────────

EVENT_CANDIDATE_APPLIED = "candidate_applied"
EVENT_STAGE_CHANGED = "stage_changed"

CANONICAL_EVENT_TYPES: list[str] = [
    EVENT_CANDIDATE_APPLIED,
    EVENT_STAGE_CHANGED,
]

PLATFORM_EVENTS_EXCHANGE = "platform.events"
AGENT_DEPLOYMENT_EVENT_QUEUE = "agent_deployment_event_driven"


# ─────────────────────────────────────────────────────────────────────────────
# Match helpers (computacional, testável puro)
# ─────────────────────────────────────────────────────────────────────────────


def _stage_identifiers(deployment: Any) -> set[str]:
    """Identificadores aceitos de stage de um deployment pipeline_stage.

    Retorna {str(target_id), target_name} (sem vazios). O evento carrega o stage
    como NOME; o deployment pode tê-lo gravado em target_id (UUID) ou target_name.
    Comparar contra ambos é defense-in-depth canonical (ver docstring do módulo).
    """
    ids: set[str] = set()
    tid = getattr(deployment, "target_id", None)
    if tid is not None:
        ids.add(str(tid))
    tname = getattr(deployment, "target_name", None)
    if tname:
        ids.add(str(tname))
    return ids


def _deployment_matches_event(
    deployment: Any,
    event_name: str,
    payload: dict[str, Any],
) -> bool:
    """True se o deployment deve disparar para este evento (matriz canonical).

    Multi-tenancy: assume que o caller já filtrou company_id no lookup. Aqui só
    aplica a regra target_type × trigger_mode × payload.
    """
    target_type = getattr(deployment, "target_type", None)
    trigger_mode = getattr(deployment, "trigger_mode", None)

    if event_name == EVENT_CANDIDATE_APPLIED:
        # on_apply em vaga: target_id == vacancy_id do evento.
        if target_type != "job" or trigger_mode != "on_apply":
            return False
        vacancy_id = str(payload.get("vacancy_id") or "")
        if not vacancy_id:
            return False
        return str(getattr(deployment, "target_id", "")) == vacancy_id

    if event_name == EVENT_STAGE_CHANGED:
        if target_type != "pipeline_stage":
            return False
        from_stage = str(payload.get("from_stage") or "")
        to_stage = str(payload.get("to_stage") or "")
        stage_ids = _stage_identifiers(deployment)
        if not stage_ids:
            return False

        if trigger_mode == "on_enter_stage":
            return bool(to_stage) and to_stage in stage_ids
        if trigger_mode == "on_exit_stage":
            return bool(from_stage) and from_stage in stage_ids
        if trigger_mode == "on_stage_change":
            return (bool(to_stage) and to_stage in stage_ids) or (
                bool(from_stage) and from_stage in stage_ids
            )
        # on_stuck_in_stage é scheduler-detected (não event-based) → não dispara aqui.
        return False

    return False


# ─────────────────────────────────────────────────────────────────────────────
# Handler canonical (testável direto, decoupled do transport RabbitMQ)
# ─────────────────────────────────────────────────────────────────────────────


async def on_event_received(
    event_name: str,
    event_payload: dict[str, Any],
    company_id: str,
) -> None:
    """Handler canonical pra eventos event-driven do motor unificado.

    Args:
        event_name: routing key canonical (candidate_applied | stage_changed).
        event_payload: payload do PlatformEvent (já parseado de JSON).
        company_id: company_id do ENVELOPE do evento (validado por C1.3 a partir
            da row do tenant). Usado para filtrar o lookup (multi-tenancy
            fail-closed). O dispatch task re-resolve company_id do deployment.

    Behavior:
        - event_name fora de CANONICAL_EVENT_TYPES → silent skip (outros consumers
          podem processar — não é erro).
        - lookup agent_deployments is_active + company_id, filtra por match canonical
          (matriz evento→trigger_mode), dispatch via .delay() pra cada match.

    REGRA 4: exceção propaga (re-raise) para o transporte fazer nack/retry. O
    caller (_consume_loop) loga LOUD. Nunca silencia.
    """
    if event_name not in CANONICAL_EVENT_TYPES:
        # Silent skip canonical: event não-canonical não-dispara dispatch.
        return

    if not company_id:
        # Multi-tenancy fail-closed: sem company_id não há tenant a filtrar.
        # REGRA 4: loga LOUD e aborta (não dispara nada cross-tenant).
        logger.error(
            "[AgentDeploymentEventConsumer] event=%s SEM company_id no envelope — "
            "abortando dispatch (multi-tenancy fail-closed). payload=%s",
            event_name,
            event_payload,
        )
        return

    from lia_models.agent_deployment import AgentDeployment

    async with AsyncSessionLocal() as db:
        # Multi-tenancy fail-closed: lookup já filtra company_id do envelope.
        stmt = select(AgentDeployment).where(
            AgentDeployment.is_active == True,  # noqa: E712
            AgentDeployment.company_id == company_id,
        )
        result = await db.execute(stmt)
        deployments = result.scalars().all()

        dispatched_count = 0
        for d in deployments:
            if not _deployment_matches_event(d, event_name, event_payload):
                continue

            trigger_context = {
                "event_type": event_name,
                "candidate_id": event_payload.get("candidate_id"),
                "vacancy_id": event_payload.get("vacancy_id"),
                "from_stage": event_payload.get("from_stage"),
                "to_stage": event_payload.get("to_stage"),
            }
            dispatch_agent_deployment_task.delay(
                deployment_id=str(d.id),
                trigger_source="event_driven",
                trigger_context=trigger_context,
            )
            dispatched_count += 1

        if dispatched_count > 0:
            logger.info(
                "[AgentDeploymentEventConsumer] event=%s company=%s dispatched=%d deployments",
                event_name,
                company_id,
                dispatched_count,
            )


# ─────────────────────────────────────────────────────────────────────────────
# Registry wiring canonical (platform_events handlers)
# ─────────────────────────────────────────────────────────────────────────────


async def _platform_event_handler_wrapper(event):
    """Adapter PlatformEvent → on_event_received(event_name, payload, company_id).

    O registry canonical (`app.shared.messaging.platform_events`) dispatcha o
    PlatformEvent inteiro; nosso handler precisa do (event_name, payload,
    company_id). company_id vem do envelope (event.company_id), nunca do payload.
    """
    await on_event_received(
        event.event_type,
        event.payload or {},
        getattr(event, "company_id", "") or "",
    )


def register_agent_deployment_event_handlers() -> None:
    """Registra `_platform_event_handler_wrapper` pros eventos canonical.

    Chamado no startup canonical (app/main.py lifespan).
    Idempotente sob 1 boot — chamar 2x duplica handlers.
    """
    from app.shared.messaging.platform_events import register_event_handler

    for event_name in CANONICAL_EVENT_TYPES:
        register_event_handler(event_name, _platform_event_handler_wrapper)

    logger.info(
        "[AgentDeploymentEventConsumer] handlers registrados pra %d eventos canonical: %s",
        len(CANONICAL_EVENT_TYPES),
        CANONICAL_EVENT_TYPES,
    )


# ─────────────────────────────────────────────────────────────────────────────
# RabbitMQ subscription canonical (platform.events exchange → dispatch_event)
# ─────────────────────────────────────────────────────────────────────────────

_consumer_task: asyncio.Task | None = None


async def start_agent_deployment_event_consumer() -> None:
    """Inicializa subscription Redis pub-sub canonical pra platform.events.

    Escuta canal Redis "platform.events". Cada mensagem recebida vira chamada
    a dispatch_event (registry canonical), que invoca os handlers registrados.

    Migrado de RabbitMQ → Redis pub-sub (A2b 2026-06-11): Redis já roda em
    dev e prod, zero nova infra. Pattern: fire-and-forget suficiente para
    notificações Teams / agent dispatch event-driven.
    """
    global _consumer_task
    try:
        from app.shared.messaging.redis_pubsub_transport import (
            PLATFORM_EVENTS_CHANNEL,
            start_subscriber,
        )
        from app.shared.messaging.platform_events import dispatch_event

        _consumer_task = start_subscriber(
            PLATFORM_EVENTS_CHANNEL,
            dispatch_event,
            name="agent_deployment_event_consumer",
        )
        logger.info("[AgentDeploymentEventConsumer] Redis subscriber iniciado")
    except Exception as exc:
        logger.error(
            "[AgentDeploymentEventConsumer] falhou ao iniciar Redis subscriber: %s",
            exc,
            exc_info=True,
        )


async def _consume_loop(rabbitmq_url: str) -> None:
    """Loop de consumo canonical: declare exchange/queue + bind + iterate.

    Falhas de conexão logam + sleep 30s + retry (mesmo pattern do consumer legado).

    REGRA 4: falha individual de mensagem loga LOUD (exc_info=True) e faz NACK com
    requeue (message.process(requeue=True)) para retry — NUNCA engole silenciosa,
    senão o deployment não dispara e ninguém sabe.
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
                AGENT_DEPLOYMENT_EVENT_QUEUE,
                durable=True,
            )
            # Bind aos routing keys canonical
            for event_name in CANONICAL_EVENT_TYPES:
                await queue.bind(exchange, routing_key=event_name)

            logger.info(
                "[AgentDeploymentEventConsumer] conectado: queue=%s bound a %d routing keys",
                AGENT_DEPLOYMENT_EVENT_QUEUE,
                len(CANONICAL_EVENT_TYPES),
            )

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    try:
                        async with message.process(requeue=True):
                            raw = json.loads(message.body.decode())
                            await dispatch_event(raw)
                    except Exception:
                        # REGRA 4: loga LOUD. message.process(requeue=True) já fez
                        # NACK+requeue ao sair do bloco com exceção (retry pelo broker).
                        logger.error(
                            "[AgentDeploymentEventConsumer] falha ao processar mensagem "
                            "(NACK+requeue) — agente NÃO disparou neste ciclo.",
                            exc_info=True,
                        )
        except asyncio.CancelledError:
            logger.info("[AgentDeploymentEventConsumer] consumer cancelado")
            return
        except Exception as exc:
            logger.error(
                "[AgentDeploymentEventConsumer] conexão falhou: %s — retry em 30s", exc
            )
            await asyncio.sleep(30)


async def stop_agent_deployment_event_consumer() -> None:
    """Cancela task do consumer (shutdown canonical)."""
    global _consumer_task
    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except (asyncio.CancelledError, Exception):
            pass
    _consumer_task = None
