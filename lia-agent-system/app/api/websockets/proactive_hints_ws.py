"""WT-2022: WebSocket endpoint pra push real-time de ProactiveHints.

Cliente conecta com JWT em query param (?token=<jwt>). Server valida via
`app.auth.security.decode_token` (mesmo canonical do REST middleware), extrai
`company_id` do payload, e adiciona conexão ao pool indexado por company_id.

Quando `ProactiveDetectorService._persist_hints` insere uma hint nova, faz
broadcast via `proactive_pool.broadcast_to_company`. Push best-effort:
falha no broadcast NUNCA quebra o persist — polling 60s do hook frontend
permanece como fallback canonical.

Multi-tenancy invariant: company_id NUNCA vem de payload do client; vem
sempre do JWT decoded server-side (fail-closed = close 4003).
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


class ProactiveHintsConnectionPool:
    """In-memory connection pool indexado por company_id.

    Single-instance (singleton `proactive_pool`). Para deploy multi-worker
    (gunicorn workers > 1), broadcast só atinge clients conectados ao mesmo
    worker — limitação aceita; fallback polling 60s cobre o gap. Próxima
    iteração pode evoluir pra Redis pub/sub (vide ws_manager canonical).
    """

    def __init__(self) -> None:
        self._pool: dict[str, set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, company_id: str) -> None:
        await ws.accept()
        self._pool.setdefault(company_id, set()).add(ws)
        logger.debug(
            "ProactiveWS connect company_id=%s total=%d",
            company_id,
            len(self._pool[company_id]),
        )

    def disconnect(self, ws: WebSocket, company_id: str) -> None:
        bucket = self._pool.get(company_id)
        if bucket is not None:
            bucket.discard(ws)
            if not bucket:
                # Limpa bucket vazio pra não vazar memória per tenant
                self._pool.pop(company_id, None)

    async def broadcast_to_company(
        self, company_id: str, hint: dict[str, Any]
    ) -> int:
        """Broadcast hint pra todos os WS conectados de uma company.

        Returns: nº de clients que receberam com sucesso.
        Conexões mortas (send raise) são removidas silenciosamente.
        """
        bucket = self._pool.get(company_id)
        if not bucket:
            return 0

        delivered = 0
        dead_connections: list[WebSocket] = []
        for ws in list(bucket):
            try:
                await ws.send_json({"type": "hint", "data": hint})
                delivered += 1
            except Exception as exc:
                logger.debug("ProactiveWS send failed (will discard): %s", exc)
                dead_connections.append(ws)

        for ws in dead_connections:
            bucket.discard(ws)
        if not bucket:
            self._pool.pop(company_id, None)

        return delivered

    def connection_count(self, company_id: str | None = None) -> int:
        """Diagnóstico: total de conexões abertas (global ou per company)."""
        if company_id is not None:
            return len(self._pool.get(company_id, set()))
        return sum(len(b) for b in self._pool.values())


# Singleton canonical — broadcast caller usa esta instância
proactive_pool = ProactiveHintsConnectionPool()


def _extract_company_id_from_token(token: str) -> str | None:
    """Decode JWT canonical e extrai company_id do payload.

    Returns None em qualquer falha (token inválido, expirado, sem claim).
    Caller fecha WS com código 4003 quando None.
    """
    try:
        from app.auth.security import decode_token

        payload = decode_token(token)
    except Exception as exc:
        logger.info("ProactiveWS token decode failed: %s", exc.__class__.__name__)
        return None

    # Canonical claim: payload pode carregar company_id em diferentes campos
    # dependendo do issuer (Rails JWT vs internal). Tentamos os 3 canonical.
    company_id = (
        payload.get("company_id")
        or payload.get("companyId")
        or payload.get("tenant_id")
    )
    if not company_id:
        logger.info("ProactiveWS token sem company_id claim")
        return None
    return str(company_id)


@router.websocket("/ws/proactive-hints")
async def proactive_hints_websocket(ws: WebSocket) -> None:
    """WebSocket endpoint pra push de hints proativas per company.

    Protocol:
    - Connect com `?token=<JWT>` em query string.
    - Server valida + accepta connection OU close(4001/4003).
    - Client envia `{"type": "ping"}` a cada 30s (keepalive).
    - Server envia `{"type": "hint", "data": <hint-dict>}` quando broadcast.
    - Server responde ping com `{"type": "pong"}`.
    """
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4001, reason="Missing token")
        return

    company_id = _extract_company_id_from_token(token)
    if not company_id:
        await ws.close(code=4003, reason="Invalid token")
        return

    await proactive_pool.connect(ws, company_id)
    try:
        while True:
            data = await ws.receive_json()
            if isinstance(data, dict) and data.get("type") == "ping":
                await ws.send_json({"type": "pong"})
            # Outros message types são ignorados (extensão futura)
    except WebSocketDisconnect:
        proactive_pool.disconnect(ws, company_id)
    except Exception as exc:
        logger.warning("ProactiveWS loop error: %s", exc)
        proactive_pool.disconnect(ws, company_id)
        try:
            await ws.close(code=1011, reason="Server error")
        except Exception:
            pass


__all__ = ["router", "proactive_pool", "ProactiveHintsConnectionPool"]
