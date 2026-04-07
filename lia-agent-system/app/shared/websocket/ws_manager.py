"""
WebSocket connection manager -- shared infrastructure.
Moved to app/shared/websocket/ to avoid circular imports (domain->api).
"""
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WSManager:
    def __init__(self):
        self._sessions: dict[str, WebSocket] = {}
        self._user_sessions: dict[str, set[str]] = {}

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

    def disconnect(self, session_id: str):
        self._sessions.pop(session_id, None)
        for sessions in self._user_sessions.values():
            sessions.discard(session_id)
        logger.info("[WS] Disconnected session=%s", session_id)

    async def send_to_session(self, session_id: str, data: Any):
        ws = self._sessions.get(session_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning("[WS] Send failed session=%s: %s", session_id, e)
                self.disconnect(session_id)

    def get_user_sessions(self, user_id: str) -> set[str]:
        return self._user_sessions.get(user_id, set())


# Shared singleton -- import this from any layer
ws_manager = WSManager()


def get_ws_manager() -> "WSManager":
    """Returns the shared WSManager singleton. NEVER create a new instance."""
    return ws_manager
