"""DEPRECADO (Fase 2.5 Onda C1.5 — cutover canonical 2026-05-29).

Este consumer (Sprint 7C Part 2) operava na tabela LEGADA `pool_agent_assignments`,
escutando 4 eventos canonical (candidate_added_to_pool, candidate_screened,
agent_completed_review, weekly_summary) e despachando
`dispatch_pool_agent_assignment_task`.

A Onda C1 unificou o motor em `agent_deployments`. A migração de dados C1.5.1
(alembic 221) copiou assignments -> deployments, e o cutover C1.5.2 removeu o
registro deste consumer de `app/main.py`. O consumer canonical do motor unificado é
`app/jobs/consumers/agent_deployment_event_consumer.py` (C1.2), que escuta
`candidate_applied` e `stage_changed` na tabela canonical.

POR QUE NO-OP EM VEZ DE DELETE:
  - `tests/jobs/test_pool_agent_event_consumer.py` ainda importa este módulo (skip
    aplicado lá com razão de deprecação).
  - Manter o módulo importável (sem efeito) evita ImportError caso algum import
    residual exista; e documenta o cutover no lugar onde o código vivia.

ANTI-DOUBLE-DISPATCH:
  As funções abaixo são no-op. Mesmo se algo ainda chamar
  `register_pool_agent_event_handlers()` / `start_pool_agent_event_consumer()`,
  NENHUM handler é registrado e NENHUM consumer RabbitMQ sobe — então este caminho
  legado NÃO pode disparar um segundo dispatch concorrente com o consumer canonical.

EVENTOS ÓRFÃOS (só o legado escutava) — status no cutover C1.5:
  - candidate_added_to_pool  → equivale a talent_pool `on_create`. HANDOFF: o
    consumer canonical (C1.2) hoje só escuta candidate_applied/stage_changed; precisa
    passar a escutar candidate_added_to_pool pra deployments talent_pool on_create
    dispararem. Documentado no relatório C1.5 (ownership C1.2/C1.6, fora deste arquivo).
  - candidate_screened       → trigger vestigial do loop legado; sem deployment
    canonical equivalente hoje. Removido.
  - agent_completed_review   → emitido pelo PRÓPRIO loop legado (pool_agents task);
    sem semântica no motor unificado. Removido.
  - weekly_summary           → report agendado; não é trigger de deployment canonical.
    Removido.

Refs:
  - AGENT_STUDIO_FASE2.5_PLANO_CONSOLIDACAO.md §Onda C1.5
  - app/jobs/consumers/agent_deployment_event_consumer.py (canonical C1.2)
  - alembic/versions/221_migrate_pool_assignments_to_deployments.py
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Mantido só pra compat de import (alguns testes legados referenciam). Não é mais
# a fonte canonical — ver agent_deployment_event_consumer.CANONICAL_EVENT_TYPES.
CANONICAL_EVENT_TYPES: list[str] = [
    "candidate_added_to_pool",
    "candidate_screened",
    "agent_completed_review",
    "weekly_summary",
]


async def on_event_received(event_name: str, event_payload: dict) -> None:
    """DEPRECADO — no-op. Ver agent_deployment_event_consumer.on_event_received."""
    return None


def register_pool_agent_event_handlers() -> None:
    """DEPRECADO — no-op. Não registra handlers (cutover C1.5)."""
    logger.info(
        "[PoolAgentEventConsumer] DEPRECADO (C1.5) — register no-op. "
        "Motor unificado usa agent_deployment_event_consumer."
    )


async def start_pool_agent_event_consumer() -> None:
    """DEPRECADO — no-op. Não sobe consumer RabbitMQ (cutover C1.5)."""
    logger.info(
        "[PoolAgentEventConsumer] DEPRECADO (C1.5) — start no-op."
    )


async def stop_pool_agent_event_consumer() -> None:
    """DEPRECADO — no-op."""
    return None
