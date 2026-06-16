"""
WS streaming helpers — PM-02 (Auditoria Rev 4).

Provê uma camada fina sobre `LangGraph.astream_events(version="v2")` para
emitir tokens em tempo real ao cliente WebSocket.

Por que helper isolado?
  - Mantém `agent_chat_ws.py` enxuto (1.300+ linhas; ver N-04).
  - É testável em isolado com um stub de grafo emitindo eventos sintéticos.
  - Permite ligar/desligar streaming via flag `LIA_WS_TOKEN_STREAMING`
    sem reescrever o caller (rollout incremental).

Referências:
  - LangChain RFC: https://python.langchain.com/docs/expression_language/streaming
  - ws_message_schemas.WSTokenMessage
  - audit Rev 4 §PM-02
"""
from __future__ import annotations

import logging
import os
from typing import Any, AsyncIterator, Awaitable, Callable, Mapping

logger = logging.getLogger(__name__)


def is_token_streaming_enabled() -> bool:
    """Feature flag (`LIA_WS_TOKEN_STREAMING`). Default OFF.

    Rollout plan (mesma janela do `LIA_V2_USE_PLAN_SERVICE`):
      * 2026-05: enable em staging, validar UX.
      * 2026-06: 5% → 25% → 100% canary em prod.
      * 2026-07-01: flag removida, streaming default-on.
    """
    raw = os.environ.get("LIA_WS_TOKEN_STREAMING", "false").lower()
    return raw in ("1", "true", "yes")


# Sentinel returned by extractors to mean "no token in this event".
_NO_TOKEN: object = object()


def _extract_token_chunk(event: Mapping[str, Any]) -> str | object:
    """Extrai o chunk de texto de um evento `astream_events("v2")`.

    Os eventos relevantes são `on_chat_model_stream` (LLMs novos) e
    `on_llm_stream` (LLMs legados). O conteúdo fica em
    `event["data"]["chunk"]` — pode ser:
      * `AIMessageChunk` (`.content` é str ou lista de partes).
      * `ChatGenerationChunk` (`.text` direto).
      * dict com chave `content`/`text` (caminho defensivo).

    Retorna `_NO_TOKEN` quando o evento não carrega texto utilizável.
    """
    if not isinstance(event, Mapping):
        return _NO_TOKEN
    name = event.get("event", "")
    if name not in ("on_chat_model_stream", "on_llm_stream"):
        return _NO_TOKEN
    data = event.get("data") or {}
    if not isinstance(data, Mapping):
        return _NO_TOKEN
    chunk = data.get("chunk")
    if chunk is None:
        return _NO_TOKEN

    # AIMessageChunk / ChatGenerationChunk usually expose `.content`/`.text`.
    text = getattr(chunk, "content", None)
    if text is None:
        text = getattr(chunk, "text", None)
    if text is None and isinstance(chunk, Mapping):
        text = chunk.get("content") or chunk.get("text")

    if isinstance(text, list):
        # Multi-part content (e.g. images + text) — concat only str parts.
        text = "".join(
            part if isinstance(part, str)
            else (part.get("text", "") if isinstance(part, Mapping) else "")
            for part in text
        )

    if not isinstance(text, str) or not text:
        return _NO_TOKEN
    return text


async def stream_wizard_tokens(
    events: AsyncIterator[Mapping[str, Any]],
    *,
    on_token: Callable[[str], Awaitable[None]],
    max_tokens: int = 4096,
) -> int:
    """Consome `events` (AsyncIterator de `astream_events("v2")`) e
    chama `on_token(text)` para cada chunk de texto.

    Args:
      events: iterator vindo de `graph.astream_events(input, config, version="v2")`.
      on_token: callback async que envia o token ao WS (tipicamente
                `ws_mgr.send_to_session(session_id, WSTokenMessage(...).model_dump())`).
      max_tokens: limite hard de tokens emitidos por chamada (proteção contra
                  loop infinito em LLM mal-configurado).

    Returns:
      Número de tokens emitidos (útil para teste/observabilidade).
    """
    emitted = 0
    async for event in events:
        token_or_sentinel = _extract_token_chunk(event)
        if token_or_sentinel is _NO_TOKEN:
            continue
        token = token_or_sentinel  # type: ignore[assignment]
        try:
            await on_token(str(token))
        except Exception as exc:  # pragma: no cover — never break the stream
            logger.warning("[ws_stream] on_token raised: %s", exc)
            continue
        emitted += 1
        if max_tokens is not None and emitted >= max_tokens:
            logger.warning(
                "[ws_stream] max_tokens (%d) reached — truncating stream",
                max_tokens,
            )
            break
    return emitted


__all__ = [
    "is_token_streaming_enabled",
    "stream_wizard_tokens",
]
