"""STL-GATE (Stop-The-Lie) tee para o caminho LangGraph/federado.

O caminho A (MainOrchestrator/agentic_loop) tem o gate inline em
agentic_loop.py L543. O caminho B (LangGraph ReAct/TimedToolNode) stringifica
o retorno da tool num ToolMessage — o gate precisa interceptar ANTES da
stringificacao. Este tee (mesmo padrao dos rrp/hitl/uia sinks) reescreve o
retorno quando side_effect_executed is False AND success is True.

Nunca levanta (tee defensivo — jamais quebra a tool).
"""
from __future__ import annotations

import functools
import inspect
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _rewrite_ghost_result(result: Any) -> Any:
    """Se result eh ghost (se=False + success=True), reescreve pra honest."""
    try:
        if not isinstance(result, dict):
            return result
        se = result.get("side_effect_executed")
        success = result.get("success")
        if se is False and success is True:
            tool_name = result.get("action_taken", "unknown")
            logger.warning(
                "[STL-GATE-ENFORCE] tool=%s bloqueada (LangGraph path): "
                "afirma success sem side-effect",
                tool_name,
            )
            return {
                "success": False,
                "error": "action_not_executed",
                "message": (
                    "Esta acao NAO foi executada — a funcionalidade "
                    "nao esta disponivel por este caminho. "
                    "Informe o usuario que a acao nao pode ser "
                    "concluida no momento."
                ),
            }
    except Exception:
        pass
    return result


def tee_tool_function(fn):
    """Envolve a funcao de uma tool p/ aplicar STL-GATE (passthrough).

    Preserva a assinatura (functools.wraps) -> StructuredTool infere o MESMO
    schema. Tee defensivo: _rewrite_ghost_result nunca levanta.
    """
    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def _aw(*args, **kwargs):
            r = await fn(*args, **kwargs)
            return _rewrite_ghost_result(r)
        return _aw

    @functools.wraps(fn)
    def _sw(*args, **kwargs):
        r = fn(*args, **kwargs)
        return _rewrite_ghost_result(r)
    return _sw
