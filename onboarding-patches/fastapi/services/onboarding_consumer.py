"""
RabbitMQ consumer for onboarding events.

Listens to 'onboarding_events' routing key on 'messages_exchange'.
Triggers OnboardingOrchestrator when user_invited events arrive.

Apply to: lia-agent-system/app/services/onboarding_consumer.py

Start as background task in main.py:
    import asyncio
    from app.services.onboarding_consumer import start_onboarding_consumer
    asyncio.create_task(start_onboarding_consumer())
"""

import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE = "messages_exchange"
ROUTING_KEY = "onboarding_events"
QUEUE = "onboarding_events_queue"


async def start_onboarding_consumer():
    """Start consuming onboarding events from RabbitMQ."""
    try:
        import aio_pika

        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True)
        queue = await channel.declare_queue(QUEUE, durable=True)
        await queue.bind(exchange, routing_key=ROUTING_KEY)

        logger.info(f"[Onboarding Consumer] Listening on {QUEUE}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        event = json.loads(message.body.decode())
                        await handle_onboarding_event(event)
                    except Exception as e:
                        logger.error(f"[Onboarding Consumer] Failed to process: {e}")

    except ImportError:
        logger.warning("[Onboarding Consumer] aio_pika not installed — using polling fallback")
        # Fallback: poll Rails API for new invites
        await _polling_fallback()
    except Exception as e:
        logger.error(f"[Onboarding Consumer] Connection failed: {e}")
        # Retry after 30s
        await asyncio.sleep(30)
        await start_onboarding_consumer()


async def handle_onboarding_event(event: dict):
    """Process a single onboarding event."""
    event_type = event.get("event_type", "")
    payload = event.get("payload", {})

    logger.info(f"[Onboarding Consumer] Event: {event_type} for user {payload.get('user_id')}")

    if event_type == "user_invited":
        await _handle_user_invited(payload)
    elif event_type == "magic_link_used":
        await _handle_magic_link_used(payload)
    else:
        logger.info(f"[Onboarding Consumer] Unknown event: {event_type}")


async def _handle_user_invited(payload: dict):
    """Start onboarding when a new user is invited."""
    from app.services.onboarding_orchestrator import OnboardingOrchestrator, OnboardingSession

    session = OnboardingSession.from_invite_event({"payload": payload})

    # Initialize dependencies
    orchestrator = OnboardingOrchestrator(
        # db=get_db(),
        # llm=get_llm(tier="fast"),
    )

    # Only start WhatsApp if phone available and LIA enabled
    if session.onboarding_lia_enabled and session.user_phone:
        try:
            from app.services.whatsapp_client import WhatsAppClient
            orchestrator.whatsapp_client = WhatsAppClient()
        except ImportError:
            logger.info("[Onboarding Consumer] WhatsApp client not available")

    result = await orchestrator.start(session)
    logger.info(f"[Onboarding Consumer] Started: {result.get('action')}")


async def _handle_magic_link_used(payload: dict):
    """Handle magic link verification event — prepare web welcome."""
    user_id = payload.get("user_id")
    first_login = payload.get("first_login", False)

    if not first_login:
        return  # Not a first login, skip

    # Load session and transition to first_login
    from app.services.onboarding_orchestrator import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()
    # session = await load_session(user_id)
    # result = await orchestrator.handle_web_event(session, "magic_link_used")
    logger.info(f"[Onboarding Consumer] Magic link used by user {user_id}")


async def _polling_fallback():
    """Fallback if RabbitMQ not available: poll Rails API."""
    while True:
        await asyncio.sleep(30)
        # TODO: Poll Rails for new invited users
        # GET /v1/users?activation_state=invited&onboarding_started=false
        pass
