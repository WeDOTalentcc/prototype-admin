"""WebSocket connection manager for agent chat."""
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WSManager:
    def __init__(self):
        self._sessions: dict[str, WebSocket] = {}
        self._user_sessions: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, company_id: str, user_id: str = "anonymous") -> bool:
        try:
            await websocket.accept()
            self._sessions[session_id] = websocket
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(session_id)
            logger.info(f"[WS] Connected session={session_id} user={user_id} company={company_id}")
            return True
        except Exception as e:
            logger.error(f"[WS] Connection failed: {e}")
            return False

    def disconnect(self, session_id: str):
        ws = self._sessions.pop(session_id, None)
        for user_id, sessions in self._user_sessions.items():
            sessions.discard(session_id)
        if ws:
            logger.info(f"[WS] Disconnected session={session_id}")

    async def send_to_session(self, session_id: str, data: Any):
        ws = self._sessions.get(session_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"[WS] Send failed session={session_id}: {e}")
                self.disconnect(session_id)

    def get_user_sessions(self, user_id: str) -> set[str]:
        return self._user_sessions.get(user_id, set())


ws_manager = WSManager()
