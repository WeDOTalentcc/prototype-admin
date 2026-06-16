"""
Domain Dispatcher — Despacha mensagens de agentes para filas Celery via RabbitMQ.

Fluxo para domínios assíncronos (sourcing, screening):
  WS endpoint → DomainDispatcher.dispatch() → RabbitMQ → Celery worker → agent.process()
                                             ↑
                             cria fila de resposta + inicia consumer

Fluxo para domínios síncronos (wizard, pipeline, etc.):
  WS endpoint → agent.process() diretamente (sem passar por aqui)

Uso:
  job_id = await domain_dispatcher.dispatch(chat_message)
  # WS envia { "type": "thinking", "job_id": job_id } ao cliente
"""
import logging
from uuid import uuid4

from app.shared.messaging.celery_config import get_domain_config
from app.shared.messaging.message_schemas import AgentChatMessage

logger = logging.getLogger(__name__)

# Mapeamento domínio → nome da fila de request
_DOMAIN_QUEUE_MAP = {
    "sourcing": "agent.sourcing",
    "cv_screening": "agent.screening",
    "wsi_assessment": "agent.screening",
    "automation": "agent.automation",
    "wizard": "agent.wizard",
    "pipeline": "agent.pipeline",
    "pipeline_transition": "agent.pipeline",
    "kanban": "agent.kanban",
    "talent": "agent.kanban",
    "recruiter_assistant": "agent.kanban",
    "policy": "agent.policy",
    "hiring_policy": "agent.policy",
    "job_management": "agent.wizard",
}

_DEFAULT_QUEUE = "agent.wizard"


class DomainDispatcher:
    """
    Despacha mensagens para filas Celery de agentes.

    Responsabilidades:
    1. Determinar a fila correta para o domínio
    2. Criar fila de resposta para a sessão (via RabbitMQ Consumer)
    3. Publicar mensagem na fila de request (via RabbitMQ Producer)
    4. Retornar correlation_id para rastreamento
    """

    def __init__(self):
        self._available: bool | None = None  # None = não testado ainda

    async def is_available(self) -> bool:
        """Retorna True se RabbitMQ está configurado e acessível."""
        if self._available is not None:
            return self._available
        try:
            from app.core.config import settings
            has_url = bool(getattr(settings, "RABBITMQ_URL", None))
            self._available = has_url
        except Exception:
            self._available = False
        return self._available

    async def dispatch(self, message: AgentChatMessage) -> str:
        """
        Despacha uma AgentChatMessage para a fila Celery do domínio.

        Cria a fila de resposta para o session_id e publica na fila de request.

        Args:
            message: Mensagem de chat do usuário.

        Returns:
            correlation_id para rastreamento do job.

        Raises:
            RuntimeError se RabbitMQ não estiver disponível.
        """
        if not await self.is_available():
            raise RuntimeError("RabbitMQ não configurado — use execução síncrona")

        from app.shared.messaging.rabbitmq_consumer import rabbitmq_consumer
        from app.shared.messaging.rabbitmq_producer import rabbitmq_producer

        # Garante fila de resposta para a sessão
        reply_to = await rabbitmq_consumer.subscribe_session(message.session_id)
        if not reply_to:
            reply_to = f"agent.response.{message.session_id}"

        correlation_id = str(uuid4())
        queue_name = _DOMAIN_QUEUE_MAP.get(message.domain, _DEFAULT_QUEUE)
        domain_cfg = get_domain_config(message.domain)

        msg_dict = message.dict()
        msg_dict["reply_to"] = reply_to
        msg_dict["correlation_id"] = correlation_id
        msg_dict["priority"] = domain_cfg.get("priority", 5)

        await rabbitmq_producer.publish_chat_message(
            message_data=msg_dict,
            routing_key=queue_name,
        )

        logger.info(
            "[DomainDispatcher] Despachado domain=%s queue=%s session=%s correlation=%s",
            message.domain,
            queue_name,
            message.session_id,
            correlation_id,
        )
        return correlation_id

    async def dispatch_via_celery(self, message: AgentChatMessage) -> str:
        """
        Alternativa: despacha diretamente via Celery (sem RabbitMQ como intermediário WS).

        IMPORTANTE — Limitação conhecida:
          Esta rota NÃO entrega o resultado de volta ao WebSocket do usuário.
          O Celery executa o agente, mas sem RabbitMQ não há canal para publicar
          a resposta de volta para `ws_manager.send_to_session()`.
          Use apenas para tarefas fire-and-forget ou quando o cliente fizer polling
          de resultado via REST API.

          O endpoint WS (`agent_chat_ws.py`) NÃO chama este método — usa `dispatch()`
          com fallback para execução síncrona inline quando RabbitMQ indisponível.

        Returns:
            task_id do Celery.
        """

        agent_input_dict = {
            "message": message.message,
            "context": {
                **message.context,
                "company_id": message.company_id,
                "user_id": message.user_id,
            },
            "session_id": message.session_id,
            "company_id": message.company_id,
            "user_id": message.user_id,
            "conversation_history": message.conversation_history,
        }

        domain_cfg = get_domain_config(message.domain)
        task_name = domain_cfg.get("task", "agents.kanban.execute")

        from app.core.celery_app import celery_app
        task = celery_app.send_task(
            task_name,
            kwargs={
                "agent_input_dict": agent_input_dict,
                "session_id": message.session_id,
                "company_id": message.company_id,
                "domain": message.domain,
            },
            queue=domain_cfg.get("queue", "vagas_normal"),
            priority=domain_cfg.get("priority", 5),
        )

        logger.info(
            "[DomainDispatcher] Celery task dispatched domain=%s task=%s id=%s",
            message.domain,
            task_name,
            task.id,
        )
        return task.id


# Singleton compartilhado
domain_dispatcher = DomainDispatcher()
