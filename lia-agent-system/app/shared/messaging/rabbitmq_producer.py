"""
RabbitMQ Producer — Publisher aio-pika para despacho de mensagens de agentes.

Publica mensagens ao exchange `lia_agent_chat` (direct) com routing_key = domínio.
Cada worker Celery consome de sua fila de domínio correspondente.

Configuração:
  RABBITMQ_URL      = amqp://user:pass@host:5672/
  RABBITMQ_EXCHANGE = lia_agent_chat (default)

---------------------------------------------------------------------------
Sprint R.2 — aio_pika cross-loop close leak fix (2026-05-21)
---------------------------------------------------------------------------
LangGraph sync nodes and Celery worker threads invoke
`publish_to_exchange()` via `asyncio.run(...)` on a transient event loop.
The previous implementation opened a fresh `connect_robust()` per call and
closed it in `finally`. The internal `RobustConnection.close()` then
schedules a `_GatheringFuture` of child task cancellations. When that
gather is awaited after the transient loop has been torn down, aio_pika
emits "got Future ... attached to a different loop" tracebacks to stdout.

Fix mirrors the canonical pattern in
`app/shared/compliance/audit_service.py` (Sprint I — Audit-loop-leak fix):

  1. Capture the FastAPI main event loop at startup
     via `register_main_loop()` called from `app/main.py` lifespan.
  2. When `publish_to_exchange()` is invoked from a non-main loop,
     redispatch the actual publish onto the main loop via
     `asyncio.run_coroutine_threadsafe` and block on the resulting Future.
  3. Reuse the singleton `rabbitmq_producer` connection instead of opening
     a fresh `connect_robust()` per call — connection stays bound to the
     main loop for its whole lifetime.

This keeps all aio_pika `RobustConnection` state bound to the long-lived
main loop. No cross-loop close leaks.
"""
import json
import logging
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger(__name__)

_EXCHANGE_NAME = getattr(settings, "RABBITMQ_EXCHANGE", "lia_agent_chat")
_RESPONSE_EXCHANGE = "lia_agent_responses"


# ---------------------------------------------------------------------------
# Event-loop ownership (Sprint R.2 — 2026-05-21)
# ---------------------------------------------------------------------------
import asyncio as _asyncio_loop_mod
import concurrent.futures as _cf_loop_mod

_MAIN_LOOP: "_asyncio_loop_mod.AbstractEventLoop | None" = None


def register_main_loop(loop: "_asyncio_loop_mod.AbstractEventLoop | None" = None) -> None:
    """Register the FastAPI app's main event loop.

    Called from `app/main.py` lifespan startup. Idempotent: calling twice with
    different loops overwrites (lifespan reload in dev) but logs a warning.
    """
    global _MAIN_LOOP
    if loop is None:
        try:
            loop = _asyncio_loop_mod.get_running_loop()
        except RuntimeError:
            loop = None
    if loop is None:
        return
    if _MAIN_LOOP is not None and _MAIN_LOOP is not loop:
        logger.warning(
            "[RabbitMQProducer] main loop already registered (%s); overwriting with %s",
            id(_MAIN_LOOP), id(loop),
        )
    _MAIN_LOOP = loop
    logger.info("[RabbitMQProducer] main loop registered id=%s", id(loop))


def _running_on_main_loop() -> bool:
    """Return True if the current task runs on the registered main loop."""
    if _MAIN_LOOP is None:
        return True  # no main loop registered yet — caller is presumed safe
    try:
        running = _asyncio_loop_mod.get_running_loop()
    except RuntimeError:
        return False
    return running is _MAIN_LOOP


def _dispatch_on_main_loop(coro_factory, *, timeout: float = 10.0):
    """Schedule `coro_factory()` on the main loop and block for the result.

    `coro_factory` is a zero-arg callable that returns a fresh coroutine —
    we use a factory (not a bare coroutine) because a coroutine bound to
    `asyncio.run`'s transient loop cannot be safely transferred. The factory
    is called from the main loop's thread context (inside the wrapped
    coroutine below), so the coroutine is created on the right loop.
    """
    if _MAIN_LOOP is None or _MAIN_LOOP.is_closed():
        raise RuntimeError("RabbitMQProducer main loop not registered or closed")

    async def _runner():
        return await coro_factory()

    fut = _asyncio_loop_mod.run_coroutine_threadsafe(_runner(), _MAIN_LOOP)
    try:
        return fut.result(timeout=timeout)
    except _cf_loop_mod.TimeoutError:
        fut.cancel()
        raise RuntimeError(f"RabbitMQProducer dispatch to main loop timed out after {timeout}s")


class RabbitMQProducer:
    """Publisher assíncrono para filas de agentes via aio-pika."""

    def __init__(self):
        self._connection = None
        self._channel = None
        self._exchange = None
        # Sprint R.2: cache topic exchanges for publish_to_exchange reuse
        self._topic_exchanges: dict[str, object] = {}

    async def _ensure_connected(self):
        """Conecta ao RabbitMQ lazily (cria conexão na primeira chamada)."""
        if self._connection and not self._connection.is_closed:
            return

        try:
            import aio_pika
            rabbitmq_url = getattr(settings, "RABBITMQ_URL", None)
            if not rabbitmq_url:
                raise ValueError("RABBITMQ_URL não configurado")

            self._connection = await aio_pika.connect_robust(rabbitmq_url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(
                prefetch_count=getattr(settings, "RABBITMQ_PREFETCH", 10)
            )
            self._exchange = await self._channel.declare_exchange(
                _EXCHANGE_NAME,
                aio_pika.ExchangeType.DIRECT,
                durable=True,
            )
            logger.info("[RabbitMQProducer] Conectado ao RabbitMQ exchange=%s", _EXCHANGE_NAME)
        except Exception as exc:
            logger.error("[RabbitMQProducer] Falha ao conectar: %s", exc)
            raise

    async def _get_topic_exchange(self, exchange_name: str):
        """Sprint R.2: get-or-declare a topic exchange on the singleton channel."""
        import aio_pika
        await self._ensure_connected()
        cached = self._topic_exchanges.get(exchange_name)
        if cached is not None:
            return cached
        topic_exchange = await self._channel.declare_exchange(
            exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        self._topic_exchanges[exchange_name] = topic_exchange
        return topic_exchange

    async def publish_chat_message(self, message_data: dict, routing_key: str) -> str:
        """
        Publica uma mensagem de chat na fila do domínio.

        Args:
            message_data: Dict com AgentChatMessage serializado.
            routing_key: Nome da fila/domínio (ex: "agent.sourcing").

        Returns:
            correlation_id gerado para rastrear a mensagem.
        """
        import aio_pika
        await self._ensure_connected()

        correlation_id = message_data.get("correlation_id") or str(uuid4())
        message_data["correlation_id"] = correlation_id

        # Garante que a fila existe antes de publicar
        await self._channel.declare_queue(
            routing_key,
            durable=True,
            arguments={"x-max-priority": 10},
        )
        await self._channel.declare_queue(routing_key, passive=True)

        msg = aio_pika.Message(
            body=json.dumps(message_data, default=str).encode(),
            content_type="application/json",
            correlation_id=correlation_id,
            reply_to=message_data.get("reply_to", ""),
            priority=message_data.get("priority", 5),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self._exchange.publish(msg, routing_key=routing_key)
        logger.info(
            "[RabbitMQProducer] Publicado routing_key=%s correlation_id=%s",
            routing_key,
            correlation_id,
        )
        return correlation_id

    async def publish_agent_response(self, response_data: dict, reply_to: str) -> None:
        """
        Publica resposta do agente na fila de retorno (reply_to).

        Usado pelos Celery workers para devolver resultados ao WS Gateway.

        Args:
            response_data: Dict com AgentResponseMessage serializado.
            reply_to: Nome da fila de resposta (ex: "agent.response.{session_id}").
        """
        import aio_pika
        await self._ensure_connected()

        if not reply_to:
            logger.warning("[RabbitMQProducer] publish_agent_response sem reply_to — ignorado")
            return

        msg = aio_pika.Message(
            body=json.dumps(response_data, default=str).encode(),
            content_type="application/json",
            correlation_id=response_data.get("correlation_id", ""),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        # Publica diretamente na fila de resposta (default exchange)
        await self._channel.default_exchange.publish(msg, routing_key=reply_to)
        logger.info(
            "[RabbitMQProducer] Resposta publicada reply_to=%s session=%s",
            reply_to,
            response_data.get("session_id", ""),
        )

    async def publish_topic(self, exchange: str, routing_key: str, message: dict) -> None:
        """Sprint R.2: publish to a TOPIC exchange via singleton channel.

        Internal helper used by `publish_to_exchange`. Reuses the singleton
        connection so the underlying aio_pika `RobustConnection` lives only
        on the main loop.
        """
        import aio_pika
        topic_exchange = await self._get_topic_exchange(exchange)
        body = json.dumps(message, default=str).encode()
        msg = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await topic_exchange.publish(msg, routing_key=routing_key)
        logger.debug(
            "[publish_to_exchange] exchange=%s routing_key=%s size=%d bytes",
            exchange,
            routing_key,
            len(body),
        )

    async def close(self) -> None:
        """Fecha a conexão com RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            self._topic_exchanges.clear()
            logger.info("[RabbitMQProducer] Conexão fechada")


# Singleton — compartilhado pela aplicação
rabbitmq_producer = RabbitMQProducer()


async def publish_to_exchange(exchange: str, routing_key: str, message: dict) -> None:
    """
    Publica mensagem em um exchange RabbitMQ com routing key específica.

    Usado por PlatformEvents para comunicação assíncrona inter-API.
    Declara um exchange do tipo TOPIC se ainda não existir.

    Sprint R.2 (2026-05-21): refactored to reuse the singleton
    `rabbitmq_producer` connection and redispatch onto the main event loop
    when called from a transient worker loop. See module-level docstring
    above `register_main_loop` for the rationale.

    Args:
        exchange:    Nome do exchange (ex: "platform.events").
        routing_key: Chave de roteamento (ex: "vagas.job.published").
        message:     Dicionário com o payload a publicar (será serializado em JSON).

    Raises:
        Exception: propaga se RabbitMQ não estiver disponível (caller deve tratar).
    """
    rabbitmq_url = getattr(settings, "RABBITMQ_URL", None)
    if not rabbitmq_url:
        raise ValueError("RABBITMQ_URL não configurado")

    # If we're on a transient (worker) loop, redispatch to the main loop.
    # The singleton connection lives on the main loop, so this also
    # eliminates the per-call connect/close cycle that emitted
    # "got Future attached to a different loop" stack traces.
    if not _running_on_main_loop():
        return _dispatch_on_main_loop(
            lambda: rabbitmq_producer.publish_topic(exchange, routing_key, message),
            timeout=10.0,
        )

    await rabbitmq_producer.publish_topic(exchange, routing_key, message)
