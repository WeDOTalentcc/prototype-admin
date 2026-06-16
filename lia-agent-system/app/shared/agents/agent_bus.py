"""
AgentBus — Redis Pub/Sub based Agent-to-Agent communication.

# R-057: canonical AgentBus — see also libs/agents-core/lia_agents_core/agent_bus.py which is a re-export shim for backward compat

Agents can publish events to other agents via Redis channels.
Channel pattern: lia:agent_bus:{company_id}:{to_agent}

Supports two modes:
- Fire-and-forget (default): publish() sends event, no reply expected
- Request-reply (crew mode): request() sends event with correlation_id
  and awaits a reply on a dedicated reply channel with timeout

Usage:
    # Fire-and-forget (from any agent)
    await agent_bus.publish(
        from_agent="sourcing",
        to_agent="pipeline",
        event_type="candidate_imported",
        payload={"candidate_id": "...", "job_id": "..."},
        company_id="...",
    )

    # Request-reply (crew delegation)
    result = await agent_bus.request(
        from_agent="wizard",
        to_agent="sourcing",
        event_type="start_sourcing",
        payload={"job_id": "..."},
        company_id="...",
        timeout=30.0,
    )

    # Subscribing (at startup)
    await agent_bus.subscribe("pipeline", handler_coroutine)
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "lia:agent_bus"
REPLY_CHANNEL_PREFIX = "lia:agent_bus:reply"
DEFAULT_REQUEST_TIMEOUT = 30.0


@dataclass
class AgentEvent:
    from_agent: str
    to_agent: str
    event_type: str
    payload: dict[str, Any]
    company_id: str
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    published_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: str | None = None
    reply_to: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "event_type": self.event_type,
            "payload": self.payload,
            "company_id": self.company_id,
            "event_id": self.event_id,
            "published_at": self.published_at,
        }
        if self.correlation_id:
            d["correlation_id"] = self.correlation_id
        if self.reply_to:
            d["reply_to"] = self.reply_to
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentEvent:
        return cls(
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            event_type=data["event_type"],
            payload=data.get("payload", {}),
            company_id=data["company_id"],
            event_id=data.get("event_id", ""),
            published_at=data.get("published_at", ""),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
        )


ReplyKey = tuple[str, str]


class AgentBus:
    """Redis Pub/Sub based agent communication bus with request-reply support.

    Pending replies are keyed by ``(company_id, correlation_id)`` to
    guarantee tenant isolation — even if two tenants reuse the same
    caller-provided correlation_id they cannot collide.
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._pending_replies: dict[ReplyKey, asyncio.Future[dict[str, Any]]] = {}

    def channel(self, company_id: str, to_agent: str) -> str:
        return f"{CHANNEL_PREFIX}:{company_id}:{to_agent}"

    def reply_channel(self, correlation_id: str, company_id: str = "") -> str:
        if company_id:
            return f"{REPLY_CHANNEL_PREFIX}:{company_id}:{correlation_id}"
        return f"{REPLY_CHANNEL_PREFIX}:{correlation_id}"

    async def publish(
        self,
        from_agent: str,
        to_agent: str,
        event_type: str,
        payload: dict[str, Any],
        company_id: str,
    ) -> bool:
        """Publish event to target agent. Fail-open: returns False on error."""
        try:
            event = AgentEvent(
                from_agent=from_agent,
                to_agent=to_agent,
                event_type=event_type,
                payload=payload,
                company_id=company_id,
            )
            try:
                from app.shared.services.audit_service import audit_service
                await audit_service.log_decision(
                    decision_type="agent_communication",
                    decision=f"{from_agent}→{to_agent}:{event_type}",
                    agent_name=from_agent,
                    company_id=company_id,
                    session_id=payload.get("session_id", ""),
                    criteria_ignored=[],
                )
            except Exception:
                pass

            from app.core.redis_client import get_redis
            redis = await get_redis()
            channel = self.channel(company_id, to_agent)
            await redis.publish(channel, json.dumps(event.to_dict()))
            logger.info(
                "[AgentBus] published event_type=%s from=%s to=%s company=%s",
                event_type, from_agent, to_agent, company_id,
            )
            return True
        except Exception as exc:
            logger.warning("[AgentBus] publish failed (fail-open): %s", exc)
            return False

    async def request(
        self,
        from_agent: str,
        to_agent: str,
        event_type: str,
        payload: dict[str, Any],
        company_id: str,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        correlation_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Send a request to another agent and await a reply.

        Uses a correlation_id and a dedicated Redis reply channel.
        Subscribes to the reply channel **before** publishing to avoid
        race conditions where a fast reply is missed.

        Args:
            correlation_id: Optional caller-provided correlation ID for
                end-to-end traceability. Generated if not supplied.

        Returns the reply payload or None on timeout/error.
        """
        correlation_id = correlation_id or uuid.uuid4().hex
        reply_chan = self.reply_channel(correlation_id, company_id=company_id)
        reply_key: ReplyKey = (company_id, correlation_id)

        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending_replies[reply_key] = future

        listen_task: asyncio.Task | None = None
        pubsub = None

        try:
            from app.core.redis_client import get_redis
            redis = await get_redis()

            pubsub = redis.pubsub()
            await pubsub.subscribe(reply_chan)

            listen_task = asyncio.create_task(
                self._listen_reply_loop(pubsub, reply_key)
            )

            event = AgentEvent(
                from_agent=from_agent,
                to_agent=to_agent,
                event_type=event_type,
                payload=payload,
                company_id=company_id,
                correlation_id=correlation_id,
                reply_to=reply_chan,
            )

            channel = self.channel(company_id, to_agent)
            await redis.publish(channel, json.dumps(event.to_dict()))
            logger.info(
                "[AgentBus] request sent event_type=%s from=%s to=%s corr=%s company=%s timeout=%.1fs",
                event_type, from_agent, to_agent, correlation_id, company_id, timeout,
            )

            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            logger.warning(
                "[AgentBus] request timeout after %.1fs from=%s to=%s corr=%s company=%s",
                timeout, from_agent, to_agent, correlation_id, company_id,
            )
            return None
        except Exception as exc:
            logger.warning("[AgentBus] request failed: %s", exc)
            return None
        finally:
            self._pending_replies.pop(reply_key, None)
            if listen_task and not listen_task.done():
                listen_task.cancel()
            if pubsub:
                try:
                    await pubsub.unsubscribe(reply_chan)
                    await pubsub.close()
                except Exception:
                    pass

    async def reply(
        self,
        event: AgentEvent,
        payload: dict[str, Any],
        from_agent: str,
    ) -> bool:
        """Send a reply to a pending request using the event's reply_to channel.

        The reply_to channel is set by ``request()`` and already includes
        the tenant-scoped correlation channel, so we publish directly to it.
        """
        reply_chan = event.reply_to
        if not reply_chan:
            logger.warning("[AgentBus] reply called on event without reply_to (corr=%s)", event.correlation_id)
            return False
        try:
            from app.core.redis_client import get_redis
            redis = await get_redis()
            reply_data = {
                "correlation_id": event.correlation_id,
                "from_agent": from_agent,
                "payload": payload,
                "replied_at": datetime.utcnow().isoformat(),
            }
            await redis.publish(reply_chan, json.dumps(reply_data))
            logger.info("[AgentBus] reply sent corr=%s from=%s channel=%s", event.correlation_id, from_agent, reply_chan)
            return True
        except Exception as exc:
            logger.warning("[AgentBus] reply failed: %s", exc)
            return False

    async def reply_local(
        self,
        correlation_id: str,
        payload: dict[str, Any],
        from_agent: str,
        company_id: str = "",
    ) -> bool:
        """Resolve a pending request locally (in-process). Used in tests and same-process crews."""
        reply_key: ReplyKey = (company_id, correlation_id)
        future = self._pending_replies.get(reply_key)
        if future and not future.done():
            future.set_result(payload)
            logger.info("[AgentBus] reply_local resolved corr=%s company=%s from=%s", correlation_id, company_id, from_agent)
            return True
        return False

    async def _listen_reply_loop(
        self,
        pubsub,
        reply_key: ReplyKey,
    ) -> None:
        """Listen on an already-subscribed Pub/Sub for a reply and resolve the future."""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    future = self._pending_replies.get(reply_key)
                    if future and not future.done():
                        future.set_result(data.get("payload", {}))
                    break
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.warning("[AgentBus] _listen_reply_loop error: %s", exc)

    def subscribe(self, agent_name: str, handler: Callable) -> None:
        """Register event handler for an agent. In-memory for testing."""
        if agent_name not in self._subscribers:
            self._subscribers[agent_name] = []
        self._subscribers[agent_name].append(handler)
        logger.info("[AgentBus] agent=%s registered subscriber", agent_name)

    async def dispatch_local(self, event: AgentEvent) -> None:
        """Dispatch event to local (in-process) subscribers. Used in tests."""
        handlers = self._subscribers.get(event.to_agent, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as exc:
                logger.warning("[AgentBus] handler error for %s: %s", event.to_agent, exc)

    def list_subscribers(self) -> dict[str, int]:
        return {agent: len(handlers) for agent, handlers in self._subscribers.items()}


# Singleton
agent_bus = AgentBus()
