"""
AgentBus — Redis Pub/Sub based Agent-to-Agent communication.

Agents can publish events to other agents via Redis channels.
Channel pattern: lia:agent_bus:{company_id}:{to_agent}

Usage:
    # Publishing (from any agent)
    await agent_bus.publish(
        from_agent="sourcing",
        to_agent="pipeline",
        event_type="candidate_imported",
        payload={"candidate_id": "...", "job_id": "..."},
        company_id="...",
    )

    # Subscribing (at startup)
    await agent_bus.subscribe("pipeline", handler_coroutine)
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "lia:agent_bus"


@dataclass
class AgentEvent:
    from_agent: str
    to_agent: str
    event_type: str
    payload: dict[str, Any]
    company_id: str
    event_id: str = field(default_factory=lambda: __import__('uuid').uuid4().hex)
    published_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "event_type": self.event_type,
            "payload": self.payload,
            "company_id": self.company_id,
            "event_id": self.event_id,
            "published_at": self.published_at,
        }

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
        )


class AgentBus:
    """Redis Pub/Sub based agent communication bus."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    def channel(self, company_id: str, to_agent: str) -> str:
        return f"{CHANNEL_PREFIX}:{company_id}:{to_agent}"

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
            # Audit trail
            try:
                from app.services.audit_service import audit_service
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
