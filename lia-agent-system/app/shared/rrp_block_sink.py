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
    """Retorna blocks acumulados, dedup por (kind+source_tool) ou (type), e zera.

    Dedup estratégia: para cada chave de deduplicação, mantém APENAS o último
    bloco (a chamada mais recente da tool ganha). Isso evita que a mesma tool
    chamada 2× no mesmo turno produza blocos duplicados visíveis ao usuário.
    Blocos sem chave de dedup passam intactos.
    """
    cur = _sink.get() or []
    _sink.set([])
    if not cur:
        return []
    # Dedup: percorre em ordem, último vence (overwrite por chave).
    seen: dict = {}
    ordered_keys: list = []
    for block in cur:
        try:
            if not isinstance(block, dict):
                seen[id(block)] = block
                ordered_keys.append(id(block))
                continue
            kind = block.get("kind")
            btype = block.get("type")
            source = block.get("source_tool") or block.get("source", "")
            if kind:
                key = f"kind:{kind}:{source}"
            elif btype:
                key = f"type:{btype}"
            else:
                key = id(block)
            if key not in seen:
                ordered_keys.append(key)
            seen[key] = block
        except Exception:
            seen[id(block)] = block
            ordered_keys.append(id(block))
    return [seen[k] for k in ordered_keys]


def _strip_blocks_for_llm(result):
    """Apos teear os blocks pro sink, remove-os da copia que vai pra LLM
    (ToolMessage). O card RRP e a fonte visual unica -> sem os blocks no texto a
    LLM nao re-tabula (2-table P2). Nunca levanta; nao muta o original.

    P0-3: quando rendered_as_card=True, tambem remove colecoes (list/dict) do
    data para evitar que o LLM gere tabelas markdown a partir de status_breakdown
    ou outros dicts estruturados. Preserva jobs_index (necessario para follow-up
    via view_job_details).
    """
    try:
        if not isinstance(result, dict):
            return result
        data = result.get("data")
        if not isinstance(data, dict):
            return result
        stripped_data = {**data}
        # Sempre remove response_blocks (vao pro sink, nao pro LLM)
        if stripped_data.get("response_blocks"):
            stripped_data["response_blocks"] = None
        # Quando card ja foi renderizado, remove colecoes para evitar re-tabulacao
        if stripped_data.get("rendered_as_card"):
            keys_to_strip = [
                k for k, v in stripped_data.items()
                if isinstance(v, (list, dict)) and k not in ("jobs_index",)
            ]
            for k in keys_to_strip:
                stripped_data.pop(k, None)
        if stripped_data == data:
            return result
        return {**result, "data": stripped_data}
    except Exception:
        return result


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
            return _strip_blocks_for_llm(r)

        return _aw

    @functools.wraps(fn)
    def _sw(*args, **kwargs):
        r = fn(*args, **kwargs)
        append_from_result(r)
        return _strip_blocks_for_llm(r)

    return _sw
