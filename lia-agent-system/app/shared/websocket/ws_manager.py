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
# Task #1110 — Redis SET key holding the session_ids currently owned by
# a recruiter, across all workers. Populated on connect, cleaned on
# disconnect, with a TTL refresh so a crashed worker doesn't leave
# orphan ids forever. Read by broadcast_to_user() to enumerate sessions
# living on OTHER workers (the local _user_sessions only covers this
# worker's connections; without the Redis registry the cross-tab fan-out
# would silently drop frames in any multi-worker deployment).
_USER_SESSIONS_KEY_PREFIX = "ws:user:"
_USER_SESSIONS_TTL_S = 24 * 3600  # 1 day — refreshed on every connect

# Task #1355 — backoff on unexpected listen() exit to avoid tight loops
_RECONNECT_BASE_DELAY_S = 1.0
_RECONNECT_MAX_DELAY_S = 30.0


class WSManager:
    def __init__(self):
        self._sessions: dict[str, WebSocket] = {}
        self._user_sessions: dict[str, set[str]] = {}
        # Task #1110 — reverse mapping session_id → user_id, used by
        # broadcast_to_user() so HITL pendings sent to the originating tab
        # are also fanned out to the user's other open tabs in real time.
        self._session_user: dict[str, str] = {}
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
            self._session_user[session_id] = user_id

            # Subscribe this session to its Redis channel
            await self._subscribe_session(session_id)
            # Task #1110 — register in cross-worker user registry
            await self._register_user_session_redis(user_id, session_id)

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
            self._session_user[session_id] = user_id

            # Subscribe this session to its Redis channel
            await self._subscribe_session(session_id)
            # Task #1110 — register in cross-worker user registry
            await self._register_user_session_redis(user_id, session_id)

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
        owner_user_id = self._session_user.pop(session_id, None)
        # Task #1110 — clean Redis registry so a stale session id is not
        # broadcast to after the tab closed. Best-effort: schedule async
        # cleanup but never block disconnect.
        if owner_user_id:
            try:
                asyncio.get_event_loop().create_task(
                    self._unregister_user_session_redis(owner_user_id, session_id)
                )
            except RuntimeError:
                # No running loop (rare during shutdown) — accept the leak;
                # _USER_SESSIONS_TTL_S will eventually expire the SET.
                pass
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

    def get_user_for_session(self, session_id: str) -> str | None:
        """Reverse lookup: which user owns this session_id, if any.

        Task #1110 — used by HITL broadcast so that the originating tab's
        session_id is enough to identify the recruiter and fan an
        ``approval_required`` frame out to their other open tabs.
        """
        return self._session_user.get(session_id)

    async def broadcast_to_user(
        self,
        user_id: str,
        data: Any,
        exclude_session_id: str | None = None,
    ) -> int:
        """Send ``data`` to every session owned by ``user_id``.

        Task #1110 — fan-out helper used by the HITL service so that the
        approval card shown in the originating tab is mirrored to every
        other open tab of the same recruiter in real time. Returns the
        number of sessions the message was published to (excluding
        ``exclude_session_id``).

        Worker-safe: enumerates sessions via the cross-worker Redis SET
        (``ws:user:{user_id}``) UNIONed with the local in-memory set,
        then publishes per-session via ``send_to_session`` (which itself
        publishes to Redis Pub/Sub keyed by session_id, so the receiving
        worker picks it up regardless of where the session lives).
        Failures on a single session are logged but never block the
        others — the originating-tab path remains the source of truth,
        the broadcast is best-effort UX sync.
        """
        if not user_id:
            return 0
        # Local set seeds the union; Redis SET fills in sessions that
        # live on other workers. Falling back to local-only on Redis
        # outage keeps the single-worker dev path identical to before.
        sessions: set[str] = set(self._user_sessions.get(user_id, set()))
        try:
            from app.core.redis_client import get_redis  # lazy
            redis_client = await get_redis()
            if redis_client is not None:
                key = f"{_USER_SESSIONS_KEY_PREFIX}{user_id}"
                redis_sessions = await redis_client.smembers(key)
                for raw in redis_sessions or []:
                    sessions.add(
                        raw.decode() if isinstance(raw, bytes) else str(raw)
                    )
        except Exception as exc:  # pragma: no cover — best-effort
            logger.debug(
                "[WS] broadcast_to_user Redis enumerate failed (user=%s): %s",
                user_id,
                exc,
            )

        delivered = 0
        for sid in sessions:
            if exclude_session_id is not None and sid == exclude_session_id:
                continue
            try:
                await self.send_to_session(sid, data)
                delivered += 1
            except Exception as exc:  # pragma: no cover — best-effort
                logger.warning(
                    "[WS] broadcast_to_user delivery to session=%s failed: %s",
                    sid,
                    exc,
                )
        return delivered

    # ------------------------------------------------------------------
    # Task #1110 — cross-worker user→sessions registry (Redis-backed)
    # ------------------------------------------------------------------

    async def _register_user_session_redis(
        self, user_id: str, session_id: str
    ) -> None:
        """Add ``session_id`` to the recruiter's cross-worker registry.

        Best-effort: a Redis outage degrades gracefully to single-worker
        behavior (the local ``_user_sessions`` dict still serves
        ``broadcast_to_user`` within this worker).
        """
        if not user_id or user_id == "anonymous":
            return
        try:
            from app.core.redis_client import get_redis
            redis_client = await get_redis()
            if redis_client is None:
                return
            key = f"{_USER_SESSIONS_KEY_PREFIX}{user_id}"
            await redis_client.sadd(key, session_id)
            await redis_client.expire(key, _USER_SESSIONS_TTL_S)
        except Exception as exc:  # pragma: no cover — best-effort
            logger.debug(
                "[WS] _register_user_session_redis failed user=%s: %s",
                user_id,
                exc,
            )

    async def _unregister_user_session_redis(
        self, user_id: str, session_id: str
    ) -> None:
        """Remove ``session_id`` from the recruiter's cross-worker registry."""
        if not user_id or user_id == "anonymous":
            return
        try:
            from app.core.redis_client import get_redis
            redis_client = await get_redis()
            if redis_client is None:
                return
            key = f"{_USER_SESSIONS_KEY_PREFIX}{user_id}"
            await redis_client.srem(key, session_id)
        except Exception as exc:  # pragma: no cover — best-effort
            logger.debug(
                "[WS] _unregister_user_session_redis failed user=%s: %s",
                user_id,
                exc,
            )

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
        """Background task that listens to all subscribed Redis channels.

        Task #1355 — uses async listen() (event-driven) instead of polling
        get_message() in a tight loop. This reduces Redis commands to zero
        when there are no Pub/Sub messages, eliminating the ~100 req/s
        idle consumption that exhausted the Upstash daily limit.

        On unexpected exit (connection drop, etc.) the loop reconnects with
        exponential backoff up to _RECONNECT_MAX_DELAY_S.
        """
        delay = _RECONNECT_BASE_DELAY_S
        while True:
            try:
                if self._pubsub is None:
                    break
                async for raw_message in self._pubsub.listen():
                    if raw_message is None:
                        continue
                    if raw_message.get("type") != "message":
                        continue
                    channel = raw_message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode()
                    session_id = channel.removeprefix(_CHANNEL_PREFIX)
                    try:
                        data = json.loads(raw_message["data"])
                    except (json.JSONDecodeError, TypeError):
                        data = raw_message["data"]
                    await self._deliver_local(session_id, data)
                # listen() returned normally (channel closed / unsubscribed)
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "[WS] Subscriber loop error (reconnecting in %.1fs): %s",
                    delay,
                    e,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, _RECONNECT_MAX_DELAY_S)
                # Re-acquire pubsub on reconnect so listen() gets a fresh iterator
                try:
                    redis = await self._get_redis()
                    if redis is not None and self._pubsub is not None:
                        await self._pubsub.reset()
                        logger.info("[WS] Subscriber loop reconnected")
                        delay = _RECONNECT_BASE_DELAY_S
                except Exception as reconnect_err:
                    logger.warning("[WS] Reconnect failed: %s", reconnect_err)

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
