"""
WebSocket connection manager with Redis Pub/Sub broadcast.

Each Uvicorn worker maintains its own dict of local WebSocket connections.
When send_to_session is called, the message is published to a Redis channel.
Every worker's subscriber picks it up and delivers to its local connections.

Fallback: if Redis is unavailable, sends directly to local connections only
(single-worker mode — same as before this change).
"""
import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

_CHANNEL_PREFIX = "ws:session:"


class WSManager:
    def __init__(self):
        self._sessions: dict[str, WebSocket] = {}
        self._user_sessions: dict[str, set[str]] = {}
        self._subscriber_task: asyncio.Task | None = None
        self._pubsub = None
        self._redis = None

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        company_id: str,
        user_id: str = "anonymous",
    ) -> bool:
        try:
            await websocket.accept()
            self._sessions[session_id] = websocket
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(session_id)

            # Subscribe this session to its Redis channel
            await self._subscribe_session(session_id)

            logger.info(
                "[WS] Connected session=%s user=%s company=%s",
                session_id,
                user_id,
                company_id,
            )
            return True
        except Exception as e:
            logger.error("[WS] Connection failed: %s", e)
            return False

    async def connect_already_accepted(
        self,
        websocket: WebSocket,
        session_id: str,
        company_id: str,
        user_id: str = "anonymous",
    ) -> bool:
        """Register a WebSocket that has already been accepted (UC-P0-19 first-message auth path).

        Identical to connect() but skips websocket.accept() to avoid
        "websocket already accepted" errors when the auth handshake pre-accepted it.
        """
        try:
            # Do NOT call websocket.accept() — already done before first-message auth
            self._sessions[session_id] = websocket
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(session_id)

            # Subscribe this session to its Redis channel
            await self._subscribe_session(session_id)

            logger.info(
                "[WS] Connected (pre-accepted) session=%s user=%s company=%s",
                session_id,
                user_id,
                company_id,
            )
            return True
        except Exception as e:
            logger.error("[WS] Connection failed (pre-accepted): %s", e)
            return False

    def disconnect(self, session_id: str):
        self._sessions.pop(session_id, None)
        for sessions in self._user_sessions.values():
            sessions.discard(session_id)
        # Unsubscribe handled lazily — pubsub ignores messages for absent sessions
        logger.info("[WS] Disconnected session=%s", session_id)

    # ------------------------------------------------------------------
    # Send — publish to Redis, fallback to local
    # ------------------------------------------------------------------

    async def send_to_session(self, session_id: str, data: Any):
        """Send data to a session. Publishes via Redis so all workers receive it."""
        published = await self._publish_to_redis(session_id, data)
        if not published:
            # Fallback: deliver locally only (single-worker mode)
            await self._deliver_local(session_id, data)

    def get_user_sessions(self, user_id: str) -> set[str]:
        return self._user_sessions.get(user_id, set())

    # ------------------------------------------------------------------
    # Redis Pub/Sub internals
    # ------------------------------------------------------------------

    async def _get_redis(self):
        """Lazy-init Redis connection for pub/sub."""
        if self._redis is not None:
            return self._redis
        try:
            from app.core.redis_client import get_redis
            self._redis = await get_redis()
            return self._redis
        except Exception as e:
            logger.debug("[WS] Redis not available for pub/sub: %s", e)
            return None

    async def _publish_to_redis(self, session_id: str, data: Any) -> bool:
        """Publish message to Redis channel for the session."""
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            channel = f"{_CHANNEL_PREFIX}{session_id}"
            payload = json.dumps(data, default=str)
            await redis.publish(channel, payload)
            return True
        except Exception as e:
            logger.debug("[WS] Redis publish failed: %s", e)
            return False

    async def _subscribe_session(self, session_id: str):
        """Ensure we are subscribed to the Redis channel for this session."""
        try:
            redis = await self._get_redis()
            if redis is None:
                return

            if self._pubsub is None:
                self._pubsub = redis.pubsub()
                self._subscriber_task = asyncio.create_task(self._subscriber_loop())

            channel = f"{_CHANNEL_PREFIX}{session_id}"
            await self._pubsub.subscribe(channel)
        except Exception as e:
            logger.debug("[WS] Redis subscribe failed for session=%s: %s", session_id, e)

    async def _subscriber_loop(self):
        """Background task that listens to all subscribed Redis channels."""
        try:
            while True:
                if self._pubsub is None:
                    break
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    channel = message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode()
                    session_id = channel.removeprefix(_CHANNEL_PREFIX)
                    try:
                        data = json.loads(message["data"])
                    except (json.JSONDecodeError, TypeError):
                        data = message["data"]
                    await self._deliver_local(session_id, data)
                else:
                    await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("[WS] Subscriber loop error: %s", e)

    async def _deliver_local(self, session_id: str, data: Any):
        """Deliver message to a locally connected WebSocket (if present)."""
        ws = self._sessions.get(session_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning("[WS] Send failed session=%s: %s", session_id, e)
                self.disconnect(session_id)

    async def shutdown(self):
        """Clean up Redis pub/sub on app shutdown."""
        if self._subscriber_task:
            self._subscriber_task.cancel()
            self._subscriber_task = None
        if self._pubsub:
            try:
                await self._pubsub.unsubscribe()
                await self._pubsub.aclose()
            except Exception:
                pass
            self._pubsub = None


# Shared singleton -- import this from any layer
ws_manager = WSManager()


def get_ws_manager() -> "WSManager":
    """Returns the shared WSManager singleton. NEVER create a new instance."""
    return ws_manager
