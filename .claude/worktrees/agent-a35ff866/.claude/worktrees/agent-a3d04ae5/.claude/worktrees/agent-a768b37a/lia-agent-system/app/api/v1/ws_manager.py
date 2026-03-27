"""
WebSocketManager — gerenciamento de conexões WebSocket por tenant.

Centraliza:
- Registro/desregistro de conexões por session_id e company_id
- Limite máximo de conexões por tenant (WS_MAX_CONNECTIONS_PER_TENANT)
- Broadcast por company ou por session
- Heartbeat (ping/pong) para detectar conexões mortas

Usado pelo endpoint /ws/chat/{session_id} para chat bidirecional com agentes.
"""
import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Optional, Set

from fastapi import WebSocket

from app.core.config import settings

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Gerencia conexões WebSocket multi-tenant para chat com agentes."""

    def __init__(self, max_per_tenant: int = settings.WS_MAX_CONNECTIONS_PER_TENANT):
        self._max_per_tenant = max_per_tenant
        # session_id → WebSocket
        self._connections: Dict[str, WebSocket] = {}
        # company_id → Set[session_id]
        self._company_sessions: Dict[str, Set[str]] = defaultdict(set)
        # session_id → company_id (reverse lookup)
        self._session_company: Dict[str, str] = {}

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        company_id: str,
    ) -> bool:
        """
        Aceita conexão WebSocket.

        Returns:
            True se conectado, False se limite por tenant foi atingido.
        """
        tenant_count = len(self._company_sessions.get(company_id, set()))
        if tenant_count >= self._max_per_tenant:
            logger.warning(
                "[WSManager] Limite atingido para company=%s (%d/%d)",
                company_id, tenant_count, self._max_per_tenant,
            )
            await websocket.accept()
            await websocket.send_text(json.dumps({
                "type": "error",
                "code": "LIMIT_EXCEEDED",
                "message": f"Limite de {self._max_per_tenant} conexões simultâneas atingido.",
            }))
            await websocket.close(code=1008)
            return False

        await websocket.accept()
        self._connections[session_id] = websocket
        self._company_sessions[company_id].add(session_id)
        self._session_company[session_id] = company_id

        logger.info(
            "[WSManager] Conectado session=%s company=%s (total_tenant=%d)",
            session_id, company_id, tenant_count + 1,
        )
        return True

    def disconnect(self, session_id: str) -> None:
        """Remove conexão do registro."""
        company_id = self._session_company.pop(session_id, None)
        if company_id:
            self._company_sessions[company_id].discard(session_id)
            if not self._company_sessions[company_id]:
                del self._company_sessions[company_id]
        self._connections.pop(session_id, None)
        logger.info("[WSManager] Desconectado session=%s", session_id)

    async def send_to_session(self, session_id: str, data: dict) -> bool:
        """
        Envia mensagem JSON para uma sessão específica.

        Returns:
            True se enviado, False se sessão não encontrada.
        """
        ws = self._connections.get(session_id)
        if ws is None:
            return False
        try:
            data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            await ws.send_text(json.dumps(data, default=str))
            return True
        except Exception as exc:
            logger.debug("[WSManager] Falha ao enviar para session=%s: %s", session_id, exc)
            self.disconnect(session_id)
            return False

    async def broadcast_to_company(self, company_id: str, data: dict) -> int:
        """
        Envia mensagem para todas as sessões de um tenant.

        Returns:
            Número de mensagens enviadas.
        """
        sessions = list(self._company_sessions.get(company_id, set()))
        sent = 0
        for session_id in sessions:
            if await self.send_to_session(session_id, data):
                sent += 1
        return sent

    def get_stats(self) -> dict:
        return {
            "total_connections": len(self._connections),
            "tenants_active": len(self._company_sessions),
            "connections_per_tenant": {
                cid: len(sids) for cid, sids in self._company_sessions.items()
            },
        }


# Singleton compartilhado pela aplicação
ws_manager = WebSocketManager()
