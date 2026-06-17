"""Shared utilities for analytics query tools."""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext

logger = logging.getLogger(__name__)


def extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    """Extract and remove _context from kwargs if present."""
    return kwargs.pop("_context", None)


def success_response(message: str, data: Any, **extra) -> dict[str, Any]:
    """Build a standard success response."""
    return {"success": True, "message": message, "data": data, **extra}


def error_response(message: str, error: Exception) -> dict[str, Any]:
    """Build a standard error response."""
    return {"success": False, "message": message, "error": str(error)}


@asynccontextmanager
async def analytics_db():
    """Context manager for analytics DB sessions COM contexto RLS.

    P0-RLS (2026-06-03): le o company_id da ContextVar canonical
    (_current_company_id, herdada no agentic loop via create_task) e seta o
    GUC app.company_id na transacao. Sem isso, RLS (FORCED em ~241 tabelas)
    bloqueia tudo -> analytics retorna 0 no chat (funnel/alerts/metricas).
    Fix em UM helper -> conserta todas as analytics query tools, zero mudanca
    nos callers. Se a contextvar estiver vazia, abre sem contexto (fail-closed).
    """
    from app.core.database import AsyncSessionLocal, set_tenant_context
    async with AsyncSessionLocal() as db:
        try:
            from app.middleware.auth_enforcement import _current_company_id
            _cid = _current_company_id.get("")
        except Exception:
            _cid = ""
        if _cid:
            await set_tenant_context(db, str(_cid))
        yield db
