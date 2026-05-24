"""
RabbitMQ Consumer — Consumer das filas de resposta de agentes.

Escuta filas de resposta por session_id (`agent.response.{session_id}`) e
notifica o WebSocketManager quando uma resposta chega de um Celery worker.

Ciclo de vida:
  - Iniciado no lifespan do FastAPI (app/main.py)
  - Cria subscriptions conforme sessões WS são abertas
  - Remove subscriptions quando sessões WS fecham

Configuração:
  RABBITMQ_URL = amqp://user:pass@host:5672/

Self-healing (F-BG.3):
  Em falha de conexão inicial, dispara `_reconnect_loop` com exponential
  backoff (5s → 300s). Health endpoint `/health/messaging` retorna 503
  enquanto `_running=False`, expondo o estado pro Kubernetes/canary.
"""
import asyncio
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_RESPONSE_QUEUE_PREFIX = "agent.response."
_QUEUE_TTL_MS = 600_000  # 10 minutos


class RabbitMQConsumer:
    """
    Consumer de filas de resposta de agentes.

    Cada sessão WS ativa tem uma fila de resposta exclusiva:
      `agent.response.{session_id}` (auto-delete, TTL=10min)

    Quando uma resposta chega, o consumer a encaminha ao WebSocketManager.
    """

    def __init__(self):
        self._connection = None
        self._channel = None
        self._subscriptions: dict[str, asyncio.Task] = {}
        self._running = False
        self._last_error: str | None = None
        self._reconnect_task: asyncio.Task | None = None

    async def _connect(self) -> None:
        """Cria conexão + canal. Levanta exceção em falha."""
        import aio_pika
        import os
        # Auditoria 2026-05-24 (P2 fix): usa os.getenv direto sem cair no default
        # canonical de settings.RABBITMQ_URL="amqp://guest:guest@localhost:5672/"
        # que em dev sem RabbitMQ rodando causava retry-loop exponential infinito
        # (log warning a cada 5-300s + stack trace de 40 linhas).
        rabbitmq_url = os.getenv("RABBITMQ_URL")
        if not rabbitmq_url:
            raise RuntimeError("RABBITMQ_URL não configurado (env var ausente)")
        self._connection = await aio_pika.connect_robust(rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=50)
        self._running = True
        self._last_error = None

    async def start(self) -> None:
        """Conecta ao RabbitMQ e inicia o consumer.

        Em falha: agenda `_reconnect_loop` com exponential backoff.
        """
        import os
        # Auditoria 2026-05-24 (P2 fix): vide _connect — usar os.getenv direto.
        rabbitmq_url = os.getenv("RABBITMQ_URL")
        if not rabbitmq_url:
            logger.info("[RabbitMQConsumer] RABBITMQ_URL não configurado — consumer inativo")
            return

        try:
            import aio_pika  # noqa: F401
        except ImportError:
            logger.info(
                "[RabbitMQConsumer] aio_pika não instalado — consumer inativo "
                "(instale com: pip install aio-pika)"
            )
            return

        try:
            await self._connect()
            logger.info("[RabbitMQConsumer] Iniciado e conectado ao RabbitMQ")
        except Exception as exc:
            self._last_error = str(exc)
            logger.error(
                "[RabbitMQConsumer] Falha ao conectar: %s — consumer inativo, agendando retry",
                exc, exc_info=True,
            )
            # F-BG.3 fix: schedule exponential backoff reconnect
            self._schedule_reconnect()

    def _schedule_reconnect(self, initial_delay: float = 5.0) -> None:
        """Agenda `_reconnect_loop` se ainda não estiver rodando (idempotente)."""
        if self._reconnect_task and not self._reconnect_task.done():
            logger.debug("[RabbitMQConsumer] reconnect already scheduled, skip")
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.error(
                "[RabbitMQConsumer] no running event loop — cannot schedule reconnect"
            )
            return
        self._reconnect_task = loop.create_task(
            self._reconnect_loop(initial_delay=initial_delay),
            name="rabbitmq_reconnect_loop",
        )

    async def _reconnect_loop(
        self, initial_delay: float = 5.0, max_delay: float = 300.0
    ) -> None:
        """Exponential backoff reconnect; roda até `_running=True` ou consumer parado."""
        delay = initial_delay
        while not self._running:
            await asyncio.sleep(delay)
            if self._running:
                # outro caller já reconectou enquanto dormíamos
                return
            logger.info(
                "[RabbitMQConsumer] retry connection (delay=%.1fs)", delay
            )
            try:
                await self._connect()
                logger.info(
                    "[RabbitMQConsumer] reconnect succeeded — consumer ativo"
                )
                return
            except Exception as exc:
                self._last_error = str(exc)
                next_delay = min(delay * 2, max_delay)
                logger.warning(
                    "[RabbitMQConsumer] retry failed: %s (next delay=%.1fs)",
                    exc, next_delay,
                )
                delay = next_delay

    async def subscribe_session(self, session_id: str) -> str:
        """
        Cria uma fila de resposta para a sessão e inicia consumer.

        Args:
            session_id: ID da sessão WS.

        Returns:
            Nome da fila de resposta criada (ou string vazia se consumer inativo).
        """
        if not self._running or not self._channel:
            return ""

        queue_name = f"{_RESPONSE_QUEUE_PREFIX}{session_id}"
        if session_id in self._subscriptions:
            return queue_name

        try:
            queue = await self._channel.declare_queue(
                queue_name,
                auto_delete=True,
                exclusive=False,
                arguments={
                    "x-message-ttl": _QUEUE_TTL_MS,
                    "x-expires": _QUEUE_TTL_MS,
                },
            )
            task = asyncio.create_task(
                self._consume_queue(queue, session_id),
                name=f"consumer_{session_id}",
            )
            self._subscriptions[session_id] = task
            logger.info("[RabbitMQConsumer] Subscribed session=%s queue=%s", session_id, queue_name)
        except Exception as exc:
            logger.error("[RabbitMQConsumer] subscribe_session error: %s", exc)
            return ""

        return queue_name

    async def unsubscribe_session(self, session_id: str) -> None:
        """Remove subscription para a sessão (chamado quando WS desconecta)."""
        task = self._subscriptions.pop(session_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("[RabbitMQConsumer] Unsubscribed session=%s", session_id)

    async def _consume_queue(self, queue, session_id: str) -> None:
        """Loop de consumo de uma fila de resposta."""
        from app.api.v1.ws_manager import ws_manager

        try:
            async with queue.iterator() as messages:
                async for message in messages:
                    async with message.process():
                        try:
                            data = json.loads(message.body.decode())
                            _domain = data.get("domain", "")
                            _task_id = data.get("job_id", data.get("task_id", f"async-{session_id[:8]}"))
                            _is_error = bool(data.get("error"))
                            _task_type_map = {
                                "sourcing": "sourcing", "cv_screening": "screening",
                                "communication": "communication",
                            }
                            _bg_status = "failed" if _is_error else "completed"
                            await ws_manager.send_to_session(session_id, {
                                "type": "background_task_update",
                                "task_id": _task_id,
                                "task_type": _task_type_map.get(_domain, "analysis"),
                                "label": f"Agente {_domain}" if _domain else "Tarefa async",
                                "status": _bg_status,
                                "progress": 0 if _is_error else 100,
                                "message": data.get("error", data.get("content", "")[:120]),
                            })
                            await ws_manager.send_to_session(session_id, {
                                "type": "message",
                                "content": data.get("content", ""),
                                "confidence": data.get("confidence", 0.7),
                                "actions": data.get("actions", []),
                                "navigation": data.get("navigation"),
                                "state_updates": data.get("state_updates", {}),
                                "domain": _domain,
                                "source": "celery_worker",
                            })
                            if data.get("done", True):
                                logger.debug(
                                    "[RabbitMQConsumer] Resposta entregue session=%s", session_id
                                )
                        except Exception as exc:
                            logger.error(
                                "[RabbitMQConsumer] Erro ao processar mensagem session=%s: %s",
                                session_id, exc,
                            )
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error("[RabbitMQConsumer] Queue consumer error session=%s: %s", session_id, exc)

    async def stop(self) -> None:
        """Para todos os consumers e fecha conexão."""
        self._running = False
        # cancela reconnect loop pendente
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        self._reconnect_task = None
        for session_id in list(self._subscriptions.keys()):
            await self.unsubscribe_session(session_id)
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("[RabbitMQConsumer] Parado")

    @property
    def active_subscriptions(self) -> int:
        return len(self._subscriptions)


# Singleton — compartilhado pela aplicação
rabbitmq_consumer = RabbitMQConsumer()
