"""Side-channel de HITL needs_confirmation para o caminho do agente (ReAct).

Irmao do rrp_block_sink. A tool gateada (@tool_handler requires_confirmation, ou
close_job pre-flight) retorna {needs_confirmation: True, hitl:{tool,domain},
message, data}. No caminho ReAct esse dict vira um ToolMessage stringificado e o
sinal estruturado se perderia -> a LLM so cospe texto. Este sink (contextvar,
async-task-local -> SEM race no agente singleton) captura o needs_confirmation na
EXECUCAO da tool, antes da stringificacao. O agente drena no fim do turno ->
AgentOutput.metadata['hitl_pending'] -> o transporte SSE emite approval_required.

Padrao canonico (igual rrp_block_sink / _current_company_id). Nunca levanta.
Captura o PRIMEIRO needs_confirmation do turno (1 aprovacao/turno).
"""
from __future__ import annotations

import contextvars
from typing import Any

_sink: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "_hitl_pending_sink", default=None
)


def reset_sink() -> None:
    """Zera no inicio do turno (evita leak entre turnos)."""
    _sink.set(None)


def append_from_result(result: Any) -> None:
    """Captura needs_confirmation de um tool result (1o do turno). Nunca levanta."""
    try:
        if not isinstance(result, dict):
            return
        if not result.get("needs_confirmation"):
            return
        if _sink.get() is not None:
            return  # ja capturado neste turno (primeiro vence)
        _hitl = result.get("hitl") if isinstance(result.get("hitl"), dict) else {}
        _data = result.get("data") if isinstance(result.get("data"), dict) else {}
        _sink.set({
            "tool": _hitl.get("tool", "") or "",
            "domain": _hitl.get("domain", "") or "",
            "message": result.get("message")
            or result.get("confirmation_message")
            or "",
            "data": _data,
        })
    except Exception:
        # tee defensivo: jamais propaga erro pro caminho de execucao da tool.
        return


def drain_sink() -> dict | None:
    """Retorna o pending capturado e zera (consumo unico no fim do turno)."""
    cur = _sink.get()
    _sink.set(None)
    return cur


def tee_tool_function(fn):
    """Envolve a funcao da tool p/ tee needs_confirmation no sink (passthrough).

    Preserva a assinatura (functools.wraps) -> StructuredTool infere o MESMO
    schema. Tee defensivo: append_from_result nunca levanta.
    """
    import functools
    import inspect

    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def _aw(*args, **kwargs):
            r = await fn(*args, **kwargs)
            append_from_result(r)
            return r

        return _aw

    @functools.wraps(fn)
    def _sw(*args, **kwargs):
        r = fn(*args, **kwargs)
        append_from_result(r)
        return r

    return _sw
