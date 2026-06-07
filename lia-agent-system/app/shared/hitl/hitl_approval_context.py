"""HITL approval ContextVar (AUD-4, 2026-06-06).

Sinal de aprovacao SERVER-SIDE para o gate de @tool_handler. Setado pelo
transporte (SSE/WS) APENAS quando o USUARIO humano confirma uma acao pendente
— NUNCA pela LLM (que nao tem acesso a esta ContextVar). Per-turno, herdado
pelas tasks via copy_context (asyncio.create_task), entao cobre as duas trilhas
(federado e supervisor).
"""
from __future__ import annotations

from contextvars import ContextVar, Token

_hitl_approved: ContextVar[bool] = ContextVar("_hitl_approved", default=False)


def set_hitl_approved(value: bool = True) -> Token:
    """Marca o turno atual como aprovado pelo usuario. Retorna token p/ reset."""
    return _hitl_approved.set(value)


def is_hitl_approved() -> bool:
    """True se o usuario aprovou a acao sensivel neste turno (server-side)."""
    return _hitl_approved.get(False)


def reset_hitl_approved(token: Token) -> None:
    try:
        _hitl_approved.reset(token)
    except (ValueError, LookupError):
        pass
