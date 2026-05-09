"""
Dead Letter Queue Service — F2-04.

Armazena tasks Celery que esgotaram todas as retries no Redis.
Permite inspecionar, re-enfileirar e limpar entradas com falha.

Chaves Redis:
  dlq:{queue}         → Redis LIST (LPUSH) com entradas JSON, cap MAX_ENTRIES
  dlq:index           → Redis SET com nomes de filas que têm entradas

TTL: DLQ_TTL_SECONDS (30 dias -- R-024)
Cap por fila: MAX_ENTRIES (1000)
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from app.shared.tracing import trace_span

logger = logging.getLogger(__name__)

DLQ_TTL_SECONDS = int(os.getenv("DLQ_TTL_DAYS", "30")) * 24 * 3600  # default 30d, max 90d recommended (R-035)
MAX_ENTRIES = 1000
_KEY_PREFIX = "dlq"
_INDEX_KEY = "dlq:index"

# Filas conhecidas (mesmas do celery_app.py)
KNOWN_QUEUES = [
    "sourcing_high",
    "evaluation_normal",
    "vagas_normal",
    "onboarding_low",
    "celery",
]


def _queue_key(queue: str) -> str:
    return f"{_KEY_PREFIX}:{queue}"


async def _get_redis():
    """Retorna cliente Redis async. Retorna None se indisponível."""
    from app.core.redis_client import get_redis_connection
    return await get_redis_connection()


class DLQService:
    """
    Dead Letter Queue baseado em Redis para tasks Celery.

    Uso (em on_failure da LIATask):
        await dlq_service.push_failure(
            task_name="drift.run_batch",
            queue="onboarding_low",
            args=[], kwargs={},
            exc=exc, tb=tb_str,
        )

    Inspecionar via endpoint admin:
        GET  /api/v1/admin/dlq
        POST /api/v1/admin/dlq/{queue}/requeue/{entry_id}
        DEL  /api/v1/admin/dlq/{queue}
    """

    @trace_span("dlq.push_failure", attributes={"component": "dlq_service"})
    async def push_failure(
        self,
        task_name: str,
        queue: str,
        args: list[Any],
        kwargs: dict[str, Any],
        exc: BaseException,
        tb: str = "",
        retries: int = 0,
        company_id: str | None = None,
    ) -> str | None:
        """
        Persiste uma task com falha na DLQ.

        Args:
            task_name: nome da task Celery (ex: "drift.run_batch")
            queue: fila de origem (ex: "onboarding_low")
            args: argumentos posicionais da task
            kwargs: argumentos nomeados da task
            exc: exceção que causou a falha
            tb: traceback formatado (string)
            retries: número de retries já realizados
            company_id: company_id extraído dos kwargs quando disponível

        Returns:
            entry_id gerado, ou None se falhar (fail-safe).
        """
        try:
            # PII masking nos args/kwargs antes de persistir
            safe_kwargs = self._mask_pii(kwargs)
            safe_args = args  # args posicionais geralmente não têm PII

            entry_id = str(uuid.uuid4())
            entry = {
                "entry_id": entry_id,
                "task_name": task_name,
                "queue": queue,
                "args": safe_args,
                "kwargs": safe_kwargs,
                "exception_type": type(exc).__name__,
                "exception_msg": str(exc)[:500],  # truncar para não estourar Redis
                "traceback": tb[:2000] if tb else "",
                "retries": retries,
                "company_id": company_id or kwargs.get("company_id"),
                "failed_at": datetime.now(UTC).isoformat(),
            }

            redis = await _get_redis()
            if redis is None:
                logger.warning("[DLQ] Redis indisponível — falha não registrada: %s", task_name)
                return None

            async with redis:
                key = _queue_key(queue)
                # LPUSH + LTRIM para manter cap MAX_ENTRIES
                await redis.lpush(key, json.dumps(entry))
                await redis.ltrim(key, 0, MAX_ENTRIES - 1)
                await redis.expire(key, DLQ_TTL_SECONDS)
                # Atualiza índice de filas com entradas
                await redis.sadd(_INDEX_KEY, queue)
                await redis.expire(_INDEX_KEY, DLQ_TTL_SECONDS)

            logger.warning(
                "[DLQ] task=%s queue=%s company=%s entry=%s retries=%d",
                task_name, queue, entry.get("company_id"), entry_id, retries,
            )

            # Notificação Bell para tasks críticas (fail-safe)
            await self._notify_if_critical(task_name, entry)

            return entry_id

        except Exception as push_exc:
            logger.debug("[DLQ] push_failure falhou (fail-safe): %s", push_exc)
            return None

    async def list_entries(
        self, queue: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Retorna as últimas `limit` entradas da DLQ de uma fila."""
        try:
            redis = await _get_redis()
            if redis is None:
                return []
            async with redis:
                raw_list = await redis.lrange(_queue_key(queue), 0, limit - 1)
            return [json.loads(r) for r in raw_list]
        except Exception as exc:
            logger.debug("[DLQ] list_entries falhou queue=%s: %s", queue, exc)
            return []

    async def list_queues(self) -> list[str]:
        """Retorna filas que têm entradas na DLQ."""
        try:
            redis = await _get_redis()
            if redis is None:
                return []
            async with redis:
                members = await redis.smembers(_INDEX_KEY)
            return sorted(members)
        except Exception as exc:
            logger.debug("[DLQ] list_queues falhou: %s", exc)
            return []

    async def queue_size(self, queue: str) -> int:
        """Retorna número de entradas na DLQ de uma fila."""
        try:
            redis = await _get_redis()
            if redis is None:
                return 0
            async with redis:
                return await redis.llen(_queue_key(queue))
        except Exception as exc:
            logger.debug("[DLQ] queue_size falhou queue=%s: %s", queue, exc)
            return 0

    async def requeue(self, queue: str, entry_id: str) -> bool:
        """
        Re-enfileira uma task da DLQ na fila original.

        Busca a entrada pelo entry_id, envia via celery send_task,
        e remove da DLQ em caso de sucesso.

        Returns:
            True se re-enfileirado, False caso contrário.
        """
        try:
            entries = await self.list_entries(queue, limit=MAX_ENTRIES)
            entry = next((e for e in entries if e.get("entry_id") == entry_id), None)
            if entry is None:
                logger.warning("[DLQ] entry_id=%s não encontrado em queue=%s", entry_id, queue)
                return False

            from app.core.celery_app import celery_app
            celery_app.send_task(
                entry["task_name"],
                args=entry.get("args", []),
                kwargs=entry.get("kwargs", {}),
                queue=queue,
            )

            # Remove da DLQ (LREM por entry_id)
            await self._remove_entry(queue, entry_id)

            logger.info(
                "[DLQ] requeue task=%s queue=%s entry=%s",
                entry["task_name"], queue, entry_id,
            )
            return True

        except Exception as exc:
            logger.error("[DLQ] requeue falhou queue=%s entry=%s: %s", queue, entry_id, exc)
            return False

    async def clear(self, queue: str) -> int:
        """
        Limpa todas as entradas da DLQ de uma fila.

        Returns:
            Número de entradas removidas.
        """
        try:
            redis = await _get_redis()
            if redis is None:
                return 0
            async with redis:
                size = await redis.llen(_queue_key(queue))
                await redis.delete(_queue_key(queue))
                await redis.srem(_INDEX_KEY, queue)
            logger.info("[DLQ] clear queue=%s entries=%d", queue, size)
            return size
        except Exception as exc:
            logger.error("[DLQ] clear falhou queue=%s: %s", queue, exc)
            return 0

    async def summary(self) -> dict[str, Any]:
        """Retorna resumo de todas as filas com entradas na DLQ."""
        queues = await self.list_queues()
        result: dict[str, Any] = {"queues": {}, "total_entries": 0}
        for q in queues:
            size = await self.queue_size(q)
            result["queues"][q] = size
            result["total_entries"] += size
        return result

    # ── internals ──────────────────────────────────────────────────────────────

    @staticmethod
    def _mask_pii(kwargs: dict[str, Any]) -> dict[str, Any]:
        """Remove/mascara campos sensíveis dos kwargs antes de persistir."""
        _PII_KEYS = {
            "password", "token", "secret", "cpf", "email",
            "phone", "telefone", "whatsapp", "credit_card",
        }
        masked = {}
        for k, v in kwargs.items():
            if any(pii in k.lower() for pii in _PII_KEYS):
                masked[k] = "***"
            elif isinstance(v, dict):
                masked[k] = DLQService._mask_pii(v)
            else:
                masked[k] = v
        return masked

    async def _remove_entry(self, queue: str, entry_id: str) -> None:
        """Remove entrada específica da DLQ pelo entry_id (LREM)."""
        try:
            entries = await self.list_entries(queue, limit=MAX_ENTRIES)
            entry = next((e for e in entries if e.get("entry_id") == entry_id), None)
            if entry is None:
                return
            redis = await _get_redis()
            if redis is None:
                return
            async with redis:
                await redis.lrem(_queue_key(queue), 1, json.dumps(entry))
        except Exception as exc:
            logger.debug("[DLQ] _remove_entry falhou: %s", exc)

    async def _notify_if_critical(
        self, task_name: str, entry: dict[str, Any]
    ) -> None:
        """Envia notificação Bell para tasks críticas (fail-safe)."""
        _CRITICAL_TASKS = {
            "lgpd.run_cleanup_daily",
            "audit.apply_lifecycle_policy",
            "drift.run_batch",
            "followup.process_pending",
            "wsi.check_abandoned",
        }
        if task_name not in _CRITICAL_TASKS:
            return
        try:
            from app.services.notification_service import notification_service
            company_id = entry.get("company_id")
            if not company_id:
                return
            await notification_service.send(
                company_id=company_id,
                event_type="dlq_critical_failure",
                title="Task crítica falhou",
                body=f"Task `{task_name}` esgotou todas as retries e foi para a DLQ.",
                severity="critical",
                channels=["bell"],
                metadata={
                    "task_name": task_name,
                    "entry_id": entry.get("entry_id"),
                    "queue": entry.get("queue"),
                    "exception_type": entry.get("exception_type"),
                },
            )
        except Exception as exc:
            logger.debug("[DLQ] _notify_if_critical falhou (fail-safe): %s", exc)


# Singleton compartilhado
dlq_service = DLQService()
