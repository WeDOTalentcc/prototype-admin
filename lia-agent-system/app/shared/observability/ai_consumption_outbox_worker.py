"""Audit task #544 — worker que drena ``ai_consumption_outbox``.

Mecânica:

* ``enqueue_outbox_payload`` insere payload (chamado pelo callback síncrono
  em ``usage_tracking_callback.py``).
* ``OutboxDrainerWorker`` roda em background (lifespan-tied em
  ``app/main.py``); a cada ``interval_s`` segundos seleciona até
  ``batch_size`` linhas pendentes (``delivered_at IS NULL``), tenta
  persistir em ``AiConsumption`` via ``TokenTrackingService.record_usage``
  e marca ``delivered_at``.
* Falha individual incrementa ``attempts`` e grava ``last_error`` — o
  worker tenta de novo no próximo ciclo. Sem dead-letter dedicado:
  contagem de pendentes serve como métrica.

Sem PII no payload — apenas IDs/contadores. Sem retries com backoff
exponencial sofisticado: o intervalo do worker já provê espaçamento.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from lia_models.ai_consumption import AiConsumptionOutbox

logger = logging.getLogger(__name__)


async def enqueue_outbox_payload(payload: dict[str, Any]) -> None:
    """Insere o payload no outbox em uma sessão dedicada.

    Chamado pelo callback síncrono no contexto async do request — usa
    ``AsyncSessionLocal`` para evitar acoplar com a transação do caller.
    """
    async with AsyncSessionLocal() as db:
        row = AiConsumptionOutbox(payload=payload)
        db.add(row)
        await db.commit()


async def _drain_one(db: AsyncSession, row: AiConsumptionOutbox) -> bool:
    """Persiste uma linha do outbox em ``AiConsumption``.

    Retorna ``True`` se entregou, ``False`` se falhou (linha permanece
    pendente para a próxima rodada).
    """
    from app.shared.observability.token_tracking_service import (
        TokenTrackingService,
    )

    payload: dict[str, Any] = dict(row.payload or {})
    try:
        svc = TokenTrackingService(db)
        await svc.record_usage(
            user_id=str(payload.get("user_id") or ""),
            company_id=str(payload.get("company_id") or ""),
            agent_type=str(payload.get("agent_type") or "unknown"),
            intent=str(payload.get("intent") or "unknown"),
            input_tokens=int(payload.get("input_tokens") or 0),
            output_tokens=int(payload.get("output_tokens") or 0),
            model=str(payload.get("model") or "unknown"),
            latency_ms=float(payload.get("latency_ms") or 0.0),
            candidate_id=payload.get("candidate_id"),
            vacancy_id=payload.get("vacancy_id"),
            extra_data=payload.get("extra_data") or {},
        )
        await db.execute(
            update(AiConsumptionOutbox)
            .where(AiConsumptionOutbox.id == row.id)
            .values(delivered_at=datetime.utcnow(), last_error=None)
        )
        await db.commit()
        return True
    except Exception as exc:
        await db.rollback()
        async with AsyncSessionLocal() as fail_db:
            await fail_db.execute(
                update(AiConsumptionOutbox)
                .where(AiConsumptionOutbox.id == row.id)
                .values(
                    attempts=(row.attempts or 0) + 1,
                    last_error=str(exc)[:500],
                )
            )
            await fail_db.commit()
        logger.warning(
            "Outbox drain failed for row %s (attempts=%d): %s",
            row.id, (row.attempts or 0) + 1, exc,
        )
        return False


async def drain_batch(batch_size: int = 50) -> int:
    """Drena até ``batch_size`` linhas pendentes. Retorna nº de entregues."""
    delivered = 0
    async with AsyncSessionLocal() as db:
        stmt = (
            select(AiConsumptionOutbox)
            .where(AiConsumptionOutbox.delivered_at.is_(None))
            .order_by(AiConsumptionOutbox.created_at.asc())
            .limit(batch_size)
        )
        result = await db.execute(stmt)
        rows = list(result.scalars().all())

    for row in rows:
        async with AsyncSessionLocal() as db:
            ok = await _drain_one(db, row)
            if ok:
                delivered += 1
    return delivered


class OutboxDrainerWorker:
    """Loop assíncrono que chama ``drain_batch`` periodicamente."""

    def __init__(self, *, interval_s: float = 5.0, batch_size: int = 50) -> None:
        self._interval_s = interval_s
        self._batch_size = batch_size
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def _run(self) -> None:
        logger.info(
            "AiConsumptionOutbox worker started (interval=%.1fs batch=%d)",
            self._interval_s, self._batch_size,
        )
        try:
            while not self._stop_event.is_set():
                try:
                    delivered = await drain_batch(self._batch_size)
                    if delivered:
                        logger.debug("Outbox drained %d rows", delivered)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.warning("Outbox drain cycle error: %s", exc)
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), timeout=self._interval_s
                    )
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            logger.info("AiConsumptionOutbox worker cancelled")
            raise
        finally:
            logger.info("AiConsumptionOutbox worker stopped")

    async def start(self) -> None:
        if self.running:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if not self._task:
            return
        self._stop_event.set()
        # Drena um último lote antes de sair para minimizar resíduo.
        try:
            await drain_batch(self._batch_size)
        except Exception as exc:
            logger.warning("Final outbox drain failed: %s", exc)
        try:
            await asyncio.wait_for(self._task, timeout=5.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            self._task.cancel()
        self._task = None


_worker_singleton: OutboxDrainerWorker | None = None


def get_outbox_worker() -> OutboxDrainerWorker:
    global _worker_singleton
    if _worker_singleton is None:
        _worker_singleton = OutboxDrainerWorker()
    return _worker_singleton
