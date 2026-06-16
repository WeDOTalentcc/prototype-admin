"""
Broker Abstraction Layer — BrokerInterface + implementações concretas.

Permite troca de broker de mensageria por variável de ambiente (BROKER_BACKEND),
sem reescrita de código de aplicação.

Backends disponíveis:
  redis    — usa Redis como broker (padrão atual / produção on-prem)
  rabbitmq — usa RabbitMQ (on-prem, chat em produção)
  pubsub   — stub Google Cloud Pub/Sub (migração GCP, NotImplementedError claro)

Uso via factory:
    from app.shared.messaging.broker_interface import get_broker
    broker = get_broker()
    await broker.publish("my-topic", {"key": "value"})
    healthy = await broker.health_check()

Troca de backend:
    Setar BROKER_BACKEND=rabbitmq (ou pubsub para GCP stub).
    Todas as 4 filas Celery continuam funcionando — o broker Celery
    é controlado separadamente via CELERY_BROKER_URL no celery_app.py.
"""
from __future__ import annotations

import abc
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class BrokerInterface(abc.ABC):
    """Interface abstrata para brokers de mensagem.

    Todas as implementações concretas devem implementar os três métodos:
    - publish(): publica mensagem em um tópico/fila
    - consume(): consome mensagem de um tópico/fila (iteração assíncrona)
    - health_check(): verifica conectividade com o broker

    Este contrato garante que a troca de Redis → RabbitMQ → Pub/Sub seja
    uma mudança de configuração (BROKER_BACKEND), não uma reescrita.
    """

    @abc.abstractmethod
    async def publish(self, topic: str, message: dict[str, Any]) -> str:
        """Publica mensagem em um tópico ou fila.

        Args:
            topic:   Nome do tópico / fila / routing_key.
            message: Payload a publicar (será serializado em JSON).

        Returns:
            message_id: identificador da mensagem publicada (pode ser correlation_id,
                        message_id ou str(uuid4()) dependendo do backend).

        Raises:
            RuntimeError: se o broker estiver indisponível.
        """

    @abc.abstractmethod
    async def consume(self, topic: str) -> dict[str, Any] | None:
        """Consome a próxima mensagem disponível em um tópico/fila.

        Args:
            topic: Nome do tópico / fila.

        Returns:
            dict com o payload da mensagem, ou None se a fila estiver vazia.

        Raises:
            RuntimeError: se o broker estiver indisponível.
        """

    @abc.abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Verifica conectividade com o broker.

        Returns:
            dict com chave "status" ("healthy" | "unhealthy") e campos extras
            de diagnóstico (latência, versão, etc.).
        """


class RedisBroker(BrokerInterface):
    """Implementação Redis do BrokerInterface.

    Usa aioredis para publish/subscribe via Redis Lists (LPUSH / BRPOP).
    É o backend padrão — o mesmo Redis já usado pelo Celery e cache.

    Variável de ambiente:
        REDIS_URL (default: redis://localhost:6379/0)
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None

    async def _get_client(self):
        if self._client is None:
            try:
                import redis.asyncio as aioredis
                # from_url() returns a client synchronously (not awaitable)
                self._client = aioredis.from_url(
                    self._redis_url,
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                    socket_timeout=1.0,
                )
            except ImportError:
                import aioredis  # type: ignore[import]
                # Legacy aioredis v1: from_url() may be a coroutine — handle both
                result = aioredis.from_url(self._redis_url, decode_responses=True)
                if hasattr(result, "__await__"):
                    self._client = await result
                else:
                    self._client = result
        return self._client

    async def publish(self, topic: str, message: dict[str, Any]) -> str:
        import json
        from uuid import uuid4
        client = await self._get_client()
        message_id = message.get("correlation_id") or str(uuid4())
        payload = json.dumps({**message, "message_id": message_id}, default=str)
        await client.lpush(f"broker:{topic}", payload)
        logger.debug("[RedisBroker] publish topic=%s message_id=%s", topic, message_id)
        return message_id

    async def consume(self, topic: str) -> dict[str, Any] | None:
        import json
        client = await self._get_client()
        result = await client.brpop(f"broker:{topic}", timeout=1)
        if result is None:
            return None
        _, raw = result
        return json.loads(raw)

    async def health_check(self) -> dict[str, Any]:
        import time
        try:
            client = await self._get_client()
            t0 = time.monotonic()
            await client.ping()
            latency_ms = round((time.monotonic() - t0) * 1000, 2)
            info = await client.info("server")
            return {
                "status": "healthy",
                "backend": "redis",
                "url": self._redis_url.split("@")[-1],
                "latency_ms": latency_ms,
                "redis_version": info.get("redis_version", "unknown"),
            }
        except Exception as exc:
            logger.warning("[RedisBroker] health_check falhou: %s", exc)
            return {
                "status": "unhealthy",
                "backend": "redis",
                "error": str(exc)[:200],
            }


class RabbitMQBroker(BrokerInterface):
    """Implementação RabbitMQ do BrokerInterface.

    Wraps rabbitmq_producer.py existente via aio-pika.
    Usado para on-prem quando Redis não é adequado (ex: chat de agentes).

    Variável de ambiente:
        RABBITMQ_URL (default: amqp://guest:guest@localhost:5672/)
    """

    def __init__(self, rabbitmq_url: str | None = None) -> None:
        self._rabbitmq_url = rabbitmq_url or os.getenv(
            "RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"
        )
        self._connection = None

    async def _ensure_connected(self):
        try:
            import aio_pika
            if self._connection is None or self._connection.is_closed:
                self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        except ImportError as exc:
            raise RuntimeError(
                "[RabbitMQBroker] aio-pika não instalado. "
                "Instale com: pip install aio-pika"
            ) from exc

    async def publish(self, topic: str, message: dict[str, Any]) -> str:
        import json
        import aio_pika
        from uuid import uuid4

        await self._ensure_connected()
        channel = await self._connection.channel()
        message_id = message.get("correlation_id") or str(uuid4())
        body = json.dumps({**message, "message_id": message_id}, default=str).encode()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=body,
                content_type="application/json",
                correlation_id=message_id,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=topic,
        )
        logger.debug("[RabbitMQBroker] publish topic=%s message_id=%s", topic, message_id)
        return message_id

    async def consume(self, topic: str) -> dict[str, Any] | None:
        import json
        import aio_pika

        await self._ensure_connected()
        channel = await self._connection.channel()
        queue = await channel.declare_queue(topic, durable=True)
        msg = await queue.get(fail=False)
        if msg is None:
            return None
        async with msg.process():
            return json.loads(msg.body.decode())

    async def health_check(self) -> dict[str, Any]:
        import time
        try:
            await self._ensure_connected()
            t0 = time.monotonic()
            channel = await self._connection.channel()
            await channel.close()
            latency_ms = round((time.monotonic() - t0) * 1000, 2)
            return {
                "status": "healthy",
                "backend": "rabbitmq",
                "url": self._rabbitmq_url.split("@")[-1] if "@" in self._rabbitmq_url else self._rabbitmq_url,
                "latency_ms": latency_ms,
            }
        except Exception as exc:
            logger.warning("[RabbitMQBroker] health_check falhou: %s", exc)
            return {
                "status": "unhealthy",
                "backend": "rabbitmq",
                "error": str(exc)[:200],
            }


class PubSubBroker(BrokerInterface):
    """Stub Google Cloud Pub/Sub — para migração GCP (Sprint de Infra dedicado).

    TODOS os métodos levantam NotImplementedError com mensagem clara.
    Esta implementação existe para:
    1. Garantir que o contrato BrokerInterface está definido
    2. Ser substituída por implementação real na sprint de migração GCP
    3. Ser testada via factory (BROKER_BACKEND=pubsub retorna este stub)

    Migração GCP: ver docs/infra/gcp-migration-guide.md para passo a passo.
    """

    def __init__(self, project_id: str | None = None) -> None:
        self._project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        logger.warning(
            "[PubSubBroker] Usando stub GCP Pub/Sub. "
            "Implemente a integração real antes de usar em produção. "
            "Ver: docs/infra/gcp-migration-guide.md"
        )

    async def publish(self, topic: str, message: dict[str, Any]) -> str:
        raise NotImplementedError(
            "[PubSubBroker] publish() não implementado. "
            "Este é um stub para migração GCP. "
            "Instale google-cloud-pubsub e implemente a integração real. "
            "Ver: docs/infra/gcp-migration-guide.md"
        )

    async def consume(self, topic: str) -> dict[str, Any] | None:
        raise NotImplementedError(
            "[PubSubBroker] consume() não implementado. "
            "Este é um stub para migração GCP. "
            "Instale google-cloud-pubsub e implemente a integração real. "
            "Ver: docs/infra/gcp-migration-guide.md"
        )

    async def health_check(self) -> dict[str, Any]:
        return {
            "status": "stub",
            "backend": "pubsub",
            "project_id": self._project_id or "not_configured",
            "note": "PubSubBroker é um stub. Ver docs/infra/gcp-migration-guide.md",
        }


def get_broker(backend: str | None = None) -> BrokerInterface:
    """Factory: retorna instância de BrokerInterface conforme BROKER_BACKEND.

    Args:
        backend: Override do env var. Se None, usa BROKER_BACKEND (default: "redis").

    Returns:
        BrokerInterface configurado para o backend solicitado.

    Trocar de Redis para outro backend:
        Setar BROKER_BACKEND=rabbitmq  →  retorna RabbitMQBroker
        Setar BROKER_BACKEND=pubsub    →  retorna PubSubBroker (stub GCP)
        Setar BROKER_BACKEND=redis     →  retorna RedisBroker (padrão)
    """
    resolved = (backend or os.getenv("BROKER_BACKEND", "redis")).lower().strip()

    if resolved == "redis":
        return RedisBroker()
    elif resolved == "rabbitmq":
        return RabbitMQBroker()
    elif resolved == "pubsub":
        return PubSubBroker()
    else:
        logger.warning(
            "[get_broker] Backend '%s' desconhecido. Usando redis (fallback).", resolved
        )
        return RedisBroker()


_broker_instance: BrokerInterface | None = None


def get_default_broker() -> BrokerInterface:
    """Retorna singleton do broker padrão (lazy init, thread-safe via GIL)."""
    global _broker_instance
    if _broker_instance is None:
        _broker_instance = get_broker()
        logger.info(
            "[get_default_broker] Broker inicializado: %s (BROKER_BACKEND=%s)",
            type(_broker_instance).__name__,
            os.getenv("BROKER_BACKEND", "redis"),
        )
    return _broker_instance
