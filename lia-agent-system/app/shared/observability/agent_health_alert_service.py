"""
Agent Health Alert Service — Sprint I2

# CROSS-CUTTING: kept in app/shared/services because it monitors ALL agent types
# (wizard, pipeline, automation, etc.) across multiple domains. Moving it into any
# single domain would break the single-responsibility boundary. The service is
# deliberately domain-agnostic.

Monitora falhas consecutivas de agentes ReAct e dispara alertas automáticos
via Bell + Teams quando thresholds são atingidos.

Arquitetura:
- Contador Redis com TTL de janela deslizante (WINDOW_MINUTES)
- Fallback in-memory quando Redis indisponível
- 3 falhas consecutivas → WARNING
- 5 falhas consecutivas → CRITICAL
- Qualquer sucesso → reset do contador

Referências:
- Crença #7 (Autonomia Progressiva — o sistema avisa antes de o humano perceber)
- Padrão: interview_session_store.py (Redis lazy init + fallback)
- Padrão: drift_alert_service.py (notification_service)
"""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


def _now() -> float:
    """Indirection over ``time.monotonic`` so tests can fast-forward."""
    return time.monotonic()

try:
    import redis.asyncio as aioredis
    _AIOREDIS_AVAILABLE = True
except ImportError:
    aioredis = None  # type: ignore[union-attr]
    _AIOREDIS_AVAILABLE = False

FAILURE_THRESHOLD = 3          # falhas consecutivas → WARNING
CRITICAL_THRESHOLD = 5         # falhas consecutivas → CRITICAL
WINDOW_MINUTES = 30            # janela de análise (Redis TTL)
REDIS_KEY_PREFIX = "agent_failures"


class AgentHealthAlertService:
    """
    Rastreia falhas consecutivas de agentes e notifica quando thresholds são atingidos.

    Usage:
        service = AgentHealthAlertService()
        await service.record_failure("company-uuid", "wizard", "TimeoutError", user_id)
        await service.record_success("company-uuid", "wizard")
    """

    def __init__(self) -> None:
        self._redis: Any | None = None
        # In-process fallback when Redis is unavailable. Each entry is a
        # ``(count, monotonic_expires_at)`` tuple so failure counters for
        # agents that never recover are evicted after ``WINDOW_MINUTES``,
        # mirroring the Redis ``EXPIRE`` semantics. Without this the dict
        # accumulated one entry per (company, agent) pair forever. (Task #871)
        self._memory: dict[str, tuple[int, float]] = {}

    def _sweep_memory(self) -> None:
        """Drop entries whose sliding window has elapsed."""
        now = _now()
        expired = [k for k, (_, exp) in self._memory.items() if exp <= now]
        for key in expired:
            self._memory.pop(key, None)

    async def _get_redis(self) -> Any | None:
        if not _AIOREDIS_AVAILABLE:
            return None
        if self._redis is not None:
            return self._redis
        try:
            from app.core.config import settings
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
            await self._redis.ping()
            logger.debug("[AgentHealthAlertService] Connected to Redis")
        except Exception as exc:
            logger.warning(
                "[AgentHealthAlertService] Redis unavailable (%s), using in-memory fallback", exc
            )
            self._redis = None
        return self._redis

    def _redis_key(self, company_id: str, agent_id: str) -> str:
        return f"{REDIS_KEY_PREFIX}:{company_id}:{agent_id}"

    async def _increment(self, company_id: str, agent_id: str) -> int:
        """Incrementa contador e retorna valor atual."""
        key = self._redis_key(company_id, agent_id)
        redis = await self._get_redis()
        if redis:
            try:
                count = await redis.incr(key)
                await redis.expire(key, WINDOW_MINUTES * 60)
                return int(count)
            except Exception as exc:
                logger.warning("[AgentHealthAlertService] Redis incr failed (%s), using fallback", exc)

        # fallback in-memory — TTL-aware so silent agents don't pin counters.
        self._sweep_memory()
        existing = self._memory.get(key)
        new_count = (existing[0] if existing else 0) + 1
        self._memory[key] = (new_count, _now() + WINDOW_MINUTES * 60)
        return new_count

    async def _reset(self, company_id: str, agent_id: str) -> None:
        """Reseta contador após sucesso."""
        key = self._redis_key(company_id, agent_id)
        redis = await self._get_redis()
        if redis:
            try:
                await redis.delete(key)
                return
            except Exception as exc:
                logger.warning("[AgentHealthAlertService] Redis delete failed (%s), using fallback", exc)

        self._sweep_memory()
        self._memory.pop(key, None)

    async def _alert(
        self,
        company_id: str,
        agent_id: str,
        level: str,
        count: int,
        notify_user_id: str | None,
    ) -> None:
        """Envia notificação Bell + Teams."""
        if not notify_user_id:
            logger.warning(
                "[AgentHealthAlertService] Alerta %s para %s/%s (count=%d) sem notify_user_id",
                level, company_id, agent_id, count,
            )
            return

        try:
            from app.services.notification_service import (
                NotificationChannel,
                NotificationType,
                notification_service,
            )

            ntype = NotificationType.URGENT if level == "CRITICAL" else NotificationType.WARNING
            channels = [NotificationChannel.BELL, NotificationChannel.TEAMS]

            await notification_service.send_multi_channel_notification(
                user_id=notify_user_id,
                title=f"Agente {agent_id} com falhas consecutivas — {level}",
                message=(
                    f"{count} falhas consecutivas em {WINDOW_MINUTES} min. "
                    f"Empresa: {company_id}. Agente: {agent_id}."
                ),
                channels=channels,
                notification_type=ntype,
            )
            logger.info(
                "[AgentHealthAlertService] Alerta %s enviado: agent=%s company=%s count=%d",
                level, agent_id, company_id, count,
            )
        except Exception as exc:
            logger.error(
                "[AgentHealthAlertService] Falha ao enviar alerta: %s", exc, exc_info=True
            )

    async def record_failure(
        self,
        company_id: str,
        agent_id: str,
        error: str,
        notify_user_id: str | None = None,
    ) -> int:
        """
        Registra uma falha do agente. Dispara alerta se threshold atingido.

        Args:
            company_id: ID do tenant.
            agent_id: Identificador do agente/domínio (ex: "wizard", "pipeline").
            error: Mensagem de erro para contexto de log.
            notify_user_id: ID do usuário para notificação. Se None, loga sem notificar.

        Returns:
            Contagem atual de falhas consecutivas.
        """
        count = await self._increment(company_id, agent_id)

        logger.warning(
            "[AgentHealthAlertService] Falha registrada: agent=%s company=%s count=%d error=%.200s",
            agent_id, company_id, count, error,
        )

        if count >= CRITICAL_THRESHOLD:
            await self._alert(company_id, agent_id, "CRITICAL", count, notify_user_id)
        elif count >= FAILURE_THRESHOLD:
            await self._alert(company_id, agent_id, "WARNING", count, notify_user_id)

        return count

    async def record_success(self, company_id: str, agent_id: str) -> None:
        """
        Registra sucesso do agente, resetando o contador de falhas consecutivas.
        """
        await self._reset(company_id, agent_id)
        logger.debug(
            "[AgentHealthAlertService] Sucesso registrado, contador resetado: agent=%s company=%s",
            agent_id, company_id,
        )

    async def get_failure_count(self, company_id: str, agent_id: str) -> int:
        """Retorna contagem atual de falhas consecutivas (para testes e monitoramento)."""
        key = self._redis_key(company_id, agent_id)
        redis = await self._get_redis()
        if redis:
            try:
                val = await redis.get(key)
                return int(val) if val else 0
            except Exception:
                pass
        self._sweep_memory()
        entry = self._memory.get(key)
        return entry[0] if entry else 0


agent_health_alert_service = AgentHealthAlertService()
