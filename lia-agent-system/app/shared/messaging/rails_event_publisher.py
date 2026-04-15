"""
Rails Event Publisher — publishes domain events to RabbitMQ for Rails consumption.

Uses the RAILS_EVENT_EXCHANGE from rails_event_schemas and the existing
publish_to_exchange infrastructure from rabbitmq_producer.

Event Flow:
  Fork (FastAPI) → RabbitMQ (lia_rails_events) → Rails (Sneakers LiaEventsWorker)
"""
import logging
from typing import Any

from app.shared.messaging.rabbitmq_producer import publish_to_exchange
from app.shared.messaging.rails_event_schemas import (
    EVENT_REGISTRY,
    EVENT_VERSIONS,
    RAILS_EVENT_EXCHANGE,
)

logger = logging.getLogger(__name__)


async def publish_rails_event(
    event_type: str,
    payload: dict[str, Any],
    company_id: str,
) -> None:
    """Publish a typed Rails event using the registered schema.

    Looks up the event_type in EVENT_REGISTRY, builds the dataclass,
    and publishes to the Rails exchange with the event_type as routing key.
    """
    event_cls = EVENT_REGISTRY.get(event_type)
    if event_cls is None:
        logger.warning("[RailsEventPublisher] Unknown event_type=%s — publishing raw", event_type)
        await publish_rails_event_raw(
            event_type=event_type,
            event_version=EVENT_VERSIONS.get(event_type, "1.0"),
            payload=payload,
            company_id=company_id,
        )
        return

    event = event_cls(company_id=company_id, **payload)
    message = event.to_dict()

    await publish_to_exchange(
        exchange=RAILS_EVENT_EXCHANGE,
        routing_key=event_type,
        message=message,
    )
    logger.info(
        "[RailsEventPublisher] Published %s for company=%s",
        event_type,
        company_id,
    )


async def publish_rails_event_raw(
    event_type: str,
    event_version: str,
    payload: dict[str, Any],
    company_id: str,
) -> None:
    """Publish a raw event dict without schema validation.

    Used for testing version compatibility or forwarding events
    that don't have a registered schema class.
    """
    from datetime import UTC, datetime

    message = {
        "event_type": event_type,
        "company_id": company_id,
        "version": event_version,
        "source": "lia-agent-system",
        "timestamp": datetime.now(UTC).isoformat(),
        **payload,
    }

    await publish_to_exchange(
        exchange=RAILS_EVENT_EXCHANGE,
        routing_key=event_type,
        message=message,
    )
    logger.info(
        "[RailsEventPublisher] Published raw %s v%s for company=%s",
        event_type,
        event_version,
        company_id,
    )
