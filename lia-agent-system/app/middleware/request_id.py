"""
Request ID / Correlation ID Middleware.

Gera um correlation_id único por request e o disponibiliza via:
  1. request.state.correlation_id (acesso direto em handlers)
  2. ContextVar _current_correlation_id (acesso em serviços downstream)
  3. Header X-Correlation-ID na response
  4. Retrocompat: request.state.request_id e header X-Request-ID (inalterados)

Padrão idêntico ao _current_company_id em auth_enforcement.py (R-008).
"""
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# ContextVar canônico — acessível de qualquer coroutine no mesmo contexto asyncio,
# incluindo serviços chamados pelo handler, graph nodes LangGraph, workers async.
# NUNCA setar diretamente — usar _set_correlation_id_from_request() abaixo.
_current_correlation_id: ContextVar[str] = ContextVar("_current_correlation_id", default="")


def _set_correlation_id_from_request(correlation_id: str) -> str:
    """Helper canonical — ÚNICA forma válida de popular o ContextVar a partir
    de um request HTTP. Documenta intent e separa do uso ad-hoc."""
    _current_correlation_id.set(correlation_id)
    return correlation_id


def get_correlation_id() -> str:
    """Retorna o correlation_id do contexto atual (vazio string se não disponível)."""
    return _current_correlation_id.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Aceita X-Correlation-ID ou X-Request-ID do cliente (inbound tracing)
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )

        # 1. request.state — acesso direto em handlers
        request.state.correlation_id = correlation_id
        request.state.request_id = correlation_id  # retrocompat

        # 2. ContextVar — propagado automaticamente para coroutines filhas
        _set_correlation_id_from_request(correlation_id)

        response = await call_next(request)

        # 3. Headers de response (permite inbound clients rastrearem)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = correlation_id  # retrocompat
        return response
