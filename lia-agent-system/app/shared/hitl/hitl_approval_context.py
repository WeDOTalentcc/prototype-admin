"""HITL approval ContextVar (AUD-4, 2026-06-06).

Sinal de aprovacao SERVER-SIDE para o gate de @tool_handler. Setado pelo
transporte (SSE/WS) APENAS quando o USUARIO humano confirma uma acao pendente
- NUNCA pela LLM (que nao tem acesso a esta ContextVar). Per-turno, herdado
pelas tasks via copy_context (asyncio.create_task), entao cobre as duas trilhas
(federado e supervisor).

Flag de ativacao (LIA_HITL_GATE): o gate so ENFORCA quando a flag esta ligada.
Default OFF (dormante) - permite marcar tools sensiveis (1c) e fazer o pre-flight
do close_job SEM regressao enquanto o loop de aprovacao nao esta wired ponta-a-
ponta (incl. botao de aprovar no FE). Paulo liga via Secret apos a validacao.
"""
from __future__ import annotations

import os
from contextvars import ContextVar, Token

_hitl_approved: ContextVar[bool] = ContextVar("_hitl_approved", default=False)

_GATE_TRUTHY = frozenset({"1", "true", "on", "yes"})


def hitl_gate_enabled() -> bool:
    """True se o gate HITL deve ENFORCAR (Secret LIA_HITL_GATE ligado).

    Default OFF: marcar tools requires_confirmation e o pre-flight do close_job
    ficam dormentes -> zero regressao ate o loop de aprovacao estar completo.
    Lido por-chamada (Secrets exigem restart de qualquer forma) p/ testabilidade.
    """
    return os.environ.get("LIA_HITL_GATE", "").strip().lower() in _GATE_TRUTHY


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


def hitl_preflight(
    *,
    tool: str,
    domain: str = "",
    message: str = "",
    data: dict | None = None,
    extra: dict | None = None,
) -> dict | None:
    """Pre-flight HITL para o PRODUTOR (tools sensiveis que NAO passam pelo
    chokepoint @tool_handler — ex. close_job/send_email/reject_candidate).

    Retorna o dict needs_confirmation se a acao deve ser BLOQUEADA (gate ON E
    nao aprovado), senao None (a tool segue normal). Usar no TOPO da tool, ANTES
    de qualquer side-effect (padrao OfferService.check_can_send). Dormante com
    LIA_HITL_GATE off -> zero regressao. O frame approval_required e o replay
    sao tratados pelo transporte (sink + _detect_hitl_approval no SSE).
    """
    if not hitl_gate_enabled() or is_hitl_approved():
        return None
    out: dict = {
        "success": False,
        "needs_confirmation": True,
        "requires_user_input": True,
        "message": message
        or (
            "Esta acao precisa da sua confirmacao antes de ser executada. "
            "Confirme para prosseguir."
        ),
        "hitl": {"tool": tool, "domain": domain},
        "data": data or {},
    }
    if extra:
        out.update(extra)
    return out
