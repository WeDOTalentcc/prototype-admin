"""Side-channel de response_blocks para o caminho B (federado/bolha).

O caminho A (MainOrchestrator/agentic_loop) extrai response_blocks dos tool
results estruturados (AD3). O caminho B (LangGraph ReAct) stringifica o retorno
da tool num ToolMessage — `response_blocks` (list[dict]) se perderia. Este sink
(contextvar, async-task-local → SEM race no agente singleton) captura os blocks
na EXECUÇÃO da tool, antes da stringificação. O federado drena no fim do turno
→ AgentOutput.metadata['response_blocks'] → SSE/WS serializa → FE.

Padrão canônico do codebase (contextvar por-request, igual _current_company_id /
_llm_streaming_callback). Nunca levanta (tee defensivo — jamais quebra a tool).
"""
from __future__ import annotations

import contextvars
from typing import Any

_sink: contextvars.ContextVar[list[dict] | None] = contextvars.ContextVar(
    "_rrp_blocks_sink", default=None
)


def reset_sink() -> None:
    """Zera o sink no início do turno (evita leak entre turnos)."""
    _sink.set([])


def append_from_result(result: Any) -> None:
    """Extrai `data.response_blocks` de um tool result e acumula. Nunca levanta."""
    try:
        if not isinstance(result, dict):
            return
        data = result.get("data")
        if not isinstance(data, dict):
            return
        blocks = data.get("response_blocks")
        if not blocks:
            return
        cur = _sink.get()
        if cur is None:
            cur = []
            _sink.set(cur)
        cur.extend(blocks)
    except Exception:
        # tee defensivo: jamais propaga erro pro caminho de execução da tool.
        return


def drain_sink() -> list[dict]:
    """Retorna os blocks acumulados e zera (consumo único no fim do turno)."""
    cur = _sink.get() or []
    _sink.set([])
    return list(cur)


def tee_tool_function(fn):
    """Envolve a função de uma tool p/ tee `response_blocks` no sink (passthrough).

    Preserva a assinatura (functools.wraps) → StructuredTool infere o MESMO
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
