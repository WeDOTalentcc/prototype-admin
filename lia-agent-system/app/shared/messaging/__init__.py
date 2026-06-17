"""
Messaging — Camada de mensageria assíncrona para agentes LIA.

Componentes:
- message_schemas: Pydantic schemas para mensagens de fila (AgentChatMessage, AgentResponseMessage)
- rabbitmq_producer: Publisher aio-pika para despachar mensagens ao exchange
- rabbitmq_consumer: Consumer das filas de resposta → notifica WebSocketManager
- dispatchers: DomainDispatcher — mapeia domínio → fila Celery + publica
- celery_config: DOMAIN_QUEUES centraliza configuração de filas/prioridades
"""
from app.shared.messaging.dispatchers import DomainDispatcher, domain_dispatcher
from app.shared.messaging.message_schemas import AgentChatMessage, AgentResponseMessage

__all__ = [
    "AgentChatMessage",
    "AgentResponseMessage",
    "DomainDispatcher",
    "domain_dispatcher",
]
