"""Side-channel da diretiva ui_action para o caminho B (federado/bolha).

Espelha rrp_block_sink / hitl_pending_sink. O caminho A (MainOrchestrator/
agentic_loop) extrai a diretiva do tool result estruturado via
``_extract_tool_directive``. O caminho B (LangGraph ReAct) stringifica o retorno
da tool num ToolMessage — a diretiva (``data.ui_action`` + ``ui_action_params``)
se perderia. Este sink (contextvar async-task-local → SEM race no agente
singleton) captura a ULTIMA diretiva acionavel na EXECUCAO da tool; o federado
drena no fim do turno → ``AgentOutput.metadata['ui_action'/'ui_action_params']``
→ SSE/WS serializa → FE (useUIAction).

Padrao canonico do codebase (contextvar por-request). Nunca levanta (tee
defensivo — jamais quebra a tool).
"""
from __future__ import annotations

import contextvars
from typing import Any

_sink: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "_ui_action_sink", default=None
)

# Fallback se o import do allowlist canonico falhar (defensivo). Mantido em
# sincronia com agentic_loop._ACTIONABLE_TOOL_UI_ACTIONS (fonte unica abaixo).
_FALLBACK_ACTIONABLE = frozenset(
    {"open_modal", "navigate_to", "apply_table_state", "start_wizard_seeded"}
)


def _actionable() -> frozenset[str]:
    """Fonte unica: o allowlist do agentic_loop (caminho A). Lazy import p/
    evitar ciclo app.shared -> app.orchestrator no import-time."""
    try:
        from app.orchestrator.execution.agentic_loop import (
            _ACTIONABLE_TOOL_UI_ACTIONS,
        )
        return _ACTIONABLE_TOOL_UI_ACTIONS
    except Exception:
        return _FALLBACK_ACTIONABLE


def reset_sink() -> None:
    """Zera o sink no inicio do turno (evita leak entre turnos)."""
    _sink.set(None)


def append_from_result(result: Any) -> None:
    """Captura ``data.ui_action`` (acionavel) + ``ui_action_params`` de um tool
    result. Last-wins (a ultima diretiva do turno vence, igual caminho A).
    Nunca levanta."""
    try:
        if not isinstance(result, dict):
            return
        data = result.get("data")
        if not isinstance(data, dict):
            return
        action = data.get("ui_action")
        if not action or action not in _actionable():
            return
        entry = {
                "ui_action": action,
                "ui_action_params": data.get("ui_action_params"),
            }
        # T7 (2026-06-13): captura seed_source para start_wizard_seeded
        # (diretiva de start_creation_from_source). Sem isso a semente se
        # perdia no caminho federado (LangGraph ReAct → SSE).
        _seed = data.get("seed_source")
        if _seed is not None:
            entry["seed_source"] = _seed
        _sink.set(entry)
    except Exception:
        # tee defensivo: jamais propaga erro pro caminho de execucao da tool.
        return


def drain_sink() -> dict | None:
    """Retorna a diretiva acumulada e zera (consumo unico no fim do turno)."""
    cur = _sink.get()
    _sink.set(None)
    return cur


def tee_tool_function(fn):
    """Envolve a funcao de uma tool p/ tee da diretiva ui_action no sink
    (passthrough). Preserva a assinatura (functools.wraps) → StructuredTool
    infere o MESMO schema. Tee defensivo: append_from_result nunca levanta."""
    import functools
    import inspect

    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def _aw(*args, **kwargs):
            result = await fn(*args, **kwargs)
            append_from_result(result)
            return result

        return _aw

    @functools.wraps(fn)
    def _w(*args, **kwargs):
        result = fn(*args, **kwargs)
        append_from_result(result)
        return result

    return _w
