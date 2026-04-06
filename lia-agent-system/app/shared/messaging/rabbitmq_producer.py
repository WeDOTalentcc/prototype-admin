"""
RabbitMQ Producer — Publisher aio-pika para despacho de mensagens de agentes.

Publica mensagens ao exchange `lia_agent_chat` (direct) com routing_key = domínio.
Cada worker Celery consome de sua fila de domínio correspondente.

Configuração:
  RABBITMQ_URL      = amqp://user:pass@host:5672/
  RABBITMQ_EXCHANGE = lia_agent_chat (default)
"""
from typing import Dict
import json
import logging
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger(__name__)

_EXCHANGE_NAME = getattr(settings, "RABBITMQ_EXCHANGE", "lia_agent_chat")
_RESPONSE_EXCHANGE = "lia_agent_responses"


class RabbitMQProducer:
    """Publisher assíncrono para filas de agentes via aio-pika."""

    def __init__(self):
        self._connection = None
        self._channel = None
        self._exchange = None

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

    async def close(self) -> None:
        """Fecha a conexão com RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("[RabbitMQProducer] Conexão fechada")


# Singleton — compartilhado pela aplicação
rabbitmq_producer = RabbitMQProducer()


async def publish_to_exchange(exchange: str, routing_key: str, message: dict) -> None:
    """
    Publica mensagem em um exchange RabbitMQ com routing key específica.

    Usado por PlatformEvents para comunicação assíncrona inter-API.
    Declara um exchange do tipo TOPIC se ainda não existir.

    Args:
        exchange:    Nome do exchange (ex: "platform.events").
        routing_key: Chave de roteamento (ex: "vagas.job.published").
        message:     Dicionário com o payload a publicar (será serializado em JSON).

    Raises:
        Exception: propaga se RabbitMQ não estiver disponível (caller deve tratar).
    """
    import aio_pika

    rabbitmq_url = getattr(settings, "RABBITMQ_URL", None)
    if not rabbitmq_url:
        raise ValueError("RABBITMQ_URL não configurado")

    connection = await aio_pika.connect_robust(rabbitmq_url)
    try:
        channel = await connection.channel()
        topic_exchange = await channel.declare_exchange(
            exchange,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
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
    finally:
        await connection.close()
