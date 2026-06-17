"""
TDD A2b — Redis pub-sub transport para platform events.

Testa:
  1. publish_platform_event usa Redis (não RabbitMQ)
  2. publish_event publica no canal correto
  3. dispatch_event → handler chamado após mensagem Redis
  4. start_agent_deployment_event_consumer usa Redis subscriber
  5. Falha de Redis em publish → retorna False, não levanta exceção
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1. publish_platform_event usa Redis (não rabbitmq_producer)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_publish_platform_event_usa_redis_nao_rabbitmq():
    from app.shared.messaging.platform_events import (
        CandidateAppliedEvent,
        publish_platform_event,
    )

    published = {}

    async def fake_publish(channel, message):
        published["channel"] = channel
        published["message"] = message
        return True

    with patch(
        "app.shared.messaging.redis_pubsub_transport.publish_event",
        side_effect=fake_publish,
    ):
        event = CandidateAppliedEvent(
            company_id="company-001",
            payload={"candidate_id": "c1", "vacancy_id": "v1"},
        )
        result = await publish_platform_event(event)

    assert result is True
    assert published["channel"] == "platform.events"
    msg = published["message"]
    assert msg["event_type"] == "candidate_applied"
    assert msg["company_id"] == "company-001"


# ---------------------------------------------------------------------------
# 2. publish_event coloca mensagem no canal Redis correto
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_publish_event_canal_correto():
    from app.shared.messaging.redis_pubsub_transport import (
        PLATFORM_EVENTS_CHANNEL,
        publish_event,
    )

    calls = []
    mock_conn = AsyncMock()
    mock_conn.publish = AsyncMock(side_effect=lambda ch, data: calls.append((ch, data)))
    mock_conn.aclose = AsyncMock()

    with patch("redis.asyncio.from_url", return_value=mock_conn):
        ok = await publish_event(PLATFORM_EVENTS_CHANNEL, {"event_type": "candidate_applied"})

    assert ok is True
    assert len(calls) == 1
    channel, data = calls[0]
    assert channel == "platform.events"
    assert json.loads(data)["event_type"] == "candidate_applied"


# ---------------------------------------------------------------------------
# 3. dispatch_event → handler chamado com payload correto
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_event_chama_handler():
    from app.shared.messaging.platform_events import (
        clear_event_handlers,
        dispatch_event,
        register_event_handler,
    )

    received = []

    async def my_handler(event):
        received.append(event)

    clear_event_handlers()
    register_event_handler("candidate_applied", my_handler)

    await dispatch_event({
        "event_type": "candidate_applied",
        "company_id": "company-001",
        "payload": {"candidate_id": "c1", "vacancy_id": "v1"},
        "source_api": "lia-agent-system",
        "version": "1.0",
    })

    assert len(received) == 1
    assert received[0].event_type == "candidate_applied"

    clear_event_handlers()


# ---------------------------------------------------------------------------
# 4. start_agent_deployment_event_consumer usa Redis, não aio_pika
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_consumer_usa_redis_subscriber():
    from app.jobs.consumers.agent_deployment_event_consumer import (
        start_agent_deployment_event_consumer,
        stop_agent_deployment_event_consumer,
    )

    tasks_created = []

    def fake_start_subscriber(channel, handler, *, name="redis_pubsub_subscriber"):
        task = asyncio.create_task(asyncio.sleep(9999), name=name)
        tasks_created.append(task)
        return task

    with patch(
        "app.shared.messaging.redis_pubsub_transport.start_subscriber",
        side_effect=fake_start_subscriber,
    ):
        await start_agent_deployment_event_consumer()

    assert len(tasks_created) == 1
    assert tasks_created[0].get_name() == "agent_deployment_event_consumer"

    await stop_agent_deployment_event_consumer()


# ---------------------------------------------------------------------------
# 5. Falha de Redis em publish → retorna False, não levanta exceção
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_publish_event_redis_down_retorna_false():
    from app.shared.messaging.redis_pubsub_transport import publish_event

    with patch("redis.asyncio.from_url", side_effect=ConnectionRefusedError("redis down")):
        result = await publish_event("platform.events", {"event_type": "test"})

    assert result is False
