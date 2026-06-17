"""
Streaming Callback — Captura tokens LLM em streaming e publica via WebSocket.

Implementa `BaseCallbackHandler.on_llm_new_token()` do LangChain para
interceptar cada token gerado e enviá-lo ao cliente via WebSocket em tempo real.

Integração:
  - Funciona com qualquer LangChain/LangGraph LLM que suporte streaming
  - Envia chunks do tipo { "type": "token", "content": "..." } ao WebSocket
  - Após todos os tokens: envia { "type": "token_done" }

Uso nos agentes LangGraph nativos (Fase 3):
    callback = StreamingCallback(session_id="...", company_id="...")
    await agent.astream(input, config={"callbacks": [callback]})
"""
import asyncio
import contextvars
import logging
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
from uuid import UUID

from app.shared.pii_masking import get_masked_logger

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.callbacks.base import BaseCallbackHandler
        _LANGCHAIN_AVAILABLE = True
    except ImportError:
        class BaseCallbackHandler:  # type: ignore[no-redef]
            pass
        _LANGCHAIN_AVAILABLE = False

logger = get_masked_logger(__name__)

# wire-B (2026-06-06): transporte SSE para eventos de atividade.
# O StreamingCallback emite tool_started/tool_finished/reasoning_step só pro
# ws_manager (_send). O chat lateral ao vivo roda em SSE e nao escutava nada
# disso -> "Pensando" estatico. O handler SSE registra um sink (contextvar,
# espelha _llm_streaming_callback) e _send repassa os frames de atividade.
_SSE_FORWARD_TYPES = {"tool_started", "tool_finished", "reasoning_step", "token", "token_done"}
_sse_frame_sink: contextvars.ContextVar[Optional[Callable[[Dict[str, Any]], Awaitable[None]]]] = (
    contextvars.ContextVar("_sse_frame_sink", default=None)
)


def set_sse_frame_sink(fn: Callable[[Dict[str, Any]], Awaitable[None]]) -> Any:
    """Registra o sink SSE (async callable que recebe um frame ja serializado).

    Retorna o token p/ reset (chamar reset_sse_frame_sink no cleanup do turno).
    """
    return _sse_frame_sink.set(fn)


def reset_sse_frame_sink(token: Any) -> None:
    """Limpa o sink SSE. Defensivo: nunca levanta."""
    try:
        _sse_frame_sink.reset(token)
    except Exception:
        pass


class StreamingCallback(BaseCallbackHandler):
    """
    LangChain callback que transmite tokens LLM ao WebSocket em tempo real.

    Thread-safe: usa `asyncio.get_event_loop().call_soon_threadsafe()` para
    garantir que `send_to_session()` (coroutine) seja chamada no event loop certo.

    Compatível com:
    - LangGraph `.astream()` e `stream_events()`
    - LangChain `ChatAnthropic`, `ChatOpenAI` com `streaming=True`
    """

    def __init__(
        self,
        session_id: str,
        company_id: str = "",
        user_id: str = "",
        buffer_chunks: int = 1,
    ):
        """
        Args:
            session_id: ID da sessão WS para entrega dos tokens.
            company_id: ID da empresa (para logging multi-tenant).
            user_id: ID do usuário (para logging).
            buffer_chunks: Número de tokens a acumular antes de enviar (1 = sem buffer).
        """
        super().__init__()
        self.session_id = session_id
        self.company_id = company_id
        self.user_id = user_id
        self._buffer_chunks = buffer_chunks
        self._token_buffer: List[str] = []
        self._tokens_sent = 0
        self._start_time = time.time()
        # run_id -> (tool_name, start_epoch) for tool duration tracking (Fase 1)
        self._tool_starts: Dict[Any, tuple] = {}
        # wire-B (2026-06-06): captura o sink SSE AGORA (no contexto da task,
        # que tem o contextvar setado). Usa instance-attr em _send — NAO
        # contextvar — porque o langchain pode despachar on_tool_start/end de
        # uma THREAD (run_coroutine_threadsafe), onde contextvar nao propaga.
        self._sse_sink = _sse_frame_sink.get(None)

    def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Any = None,
        run_id: UUID = None,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Chamado para cada token gerado pelo LLM durante streaming."""
        if not token:
            return

        if isinstance(token, list):
            token = "".join(str(t) for t in token)
        elif not isinstance(token, str):
            token = str(token)

        self._token_buffer.append(token)
        self._tokens_sent += 1

        if len(self._token_buffer) >= self._buffer_chunks:
            chunk_text = "".join(self._token_buffer)
            self._token_buffer.clear()
            self._schedule_send({"type": "token", "content": chunk_text})

    def on_llm_end(
        self,
        response: Any,
        *,
        run_id: UUID = None,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Chamado quando o LLM termina de gerar. Flush de buffer pendente."""
        if self._token_buffer:
            chunk_text = "".join(self._token_buffer)
            self._token_buffer.clear()
            self._schedule_send({"type": "token", "content": chunk_text})

        elapsed_ms = (time.time() - self._start_time) * 1000
        self._schedule_send({"type": "token_done", "tokens_sent": self._tokens_sent})

        logger.debug(
            "[StreamingCallback] Stream complete session=%s tokens=%d elapsed=%.1fms",
            self.session_id,
            self._tokens_sent,
            elapsed_ms,
        )

    def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID = None,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Chamado em caso de erro durante streaming."""
        logger.error(
            "[StreamingCallback] LLM error session=%s: %s", self.session_id, error
        )
        self._schedule_send({
            "type": "error",
            "message": "Erro durante geração de resposta.",
        })

    # ── Tool / activity events (Fase 1) ────────────────────────────────────────
    # LangChain fires these during ainvoke (no astream needed). Payloads come
    # from app.shared.chat_event_serializer (single source of truth — never an
    # inline {"type": ...} dict).
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID = None,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        name = self._tool_name(serialized, kwargs)
        self._tool_starts[run_id] = (name, time.time())
        try:
            from app.shared.chat_event_serializer import serialize_tool_started
            self._schedule_send(serialize_tool_started(
                name=name, args=self._summarize(input_str), tool_id=str(run_id or ""),
            ))
        except Exception as exc:
            logger.debug("[StreamingCallback] tool_started send falhou: %s", exc)

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID = None,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        name, started = self._tool_starts.pop(run_id, (None, None))
        duration_ms = int((time.time() - started) * 1000) if started else None
        try:
            from app.shared.chat_event_serializer import serialize_tool_finished
            self._schedule_send(serialize_tool_finished(
                name=name or "tool", status="ok", duration_ms=duration_ms,
                result=self._summarize(output), tool_id=str(run_id or ""),
            ))
        except Exception as exc:
            logger.debug("[StreamingCallback] tool_finished send falhou: %s", exc)

    def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID = None,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        name, started = self._tool_starts.pop(run_id, (None, None))
        duration_ms = int((time.time() - started) * 1000) if started else None
        try:
            from app.shared.chat_event_serializer import serialize_tool_finished
            self._schedule_send(serialize_tool_finished(
                name=name or "tool", status="error", duration_ms=duration_ms,
                result=self._summarize(str(error)), tool_id=str(run_id or ""),
            ))
        except Exception as exc:
            logger.debug("[StreamingCallback] tool_error send falhou: %s", exc)

    def emit_reasoning_step(self, label: str, detail: str = "") -> None:
        """Fase 2: emit a reasoning_step event (intermediate agent thought).

        Called by LangGraphBase._run_graph_streaming when LIA_WS_ASTREAM is on.
        Text is PII-masked + truncated via _summarize. No-op on empty text.
        """
        try:
            from app.shared.chat_event_serializer import serialize_reasoning_step
            text = self._summarize(label)
            if text:
                self._schedule_send(
                    serialize_reasoning_step(label=text, detail=detail or "")
                )
        except Exception as exc:
            logger.debug("[StreamingCallback] reasoning_step send falhou: %s", exc)


    async def emit_reasoning_step_async(self, label: str, detail: str = "") -> None:
        """Async variant: directly awaits _send so the frame lands in sse_queue
        BEFORE the caller puts _done.  Use this for the composing step (after
        _run_graph) where create_task ordering would otherwise lose the frame.
        """
        try:
            from app.shared.chat_event_serializer import serialize_reasoning_step
            text = self._summarize(label)
            if text:
                await self._send(
                    serialize_reasoning_step(label=text, detail=detail or "")
                )
        except Exception as exc:
            logger.debug("[StreamingCallback] reasoning_step_async falhou: %s", exc)

    @staticmethod
    def _tool_name(serialized: Any, kwargs: Dict[str, Any]) -> str:
        try:
            if isinstance(serialized, dict):
                _n = serialized.get("name")
                if _n:
                    return str(_n)
        except Exception:
            pass
        return str(kwargs.get("name") or "tool")

    def _summarize(self, value: Any, limit: int = 200) -> str:
        try:
            text = value if isinstance(value, str) else str(value)
        except Exception:
            return ""
        try:
            from app.shared.pii_masking import mask_pii
            text = mask_pii(text)
        except Exception:
            pass
        text = text.strip()
        return text[:limit] + ("\u2026" if len(text) > limit else "")

    def _schedule_send(self, data: Dict[str, Any]) -> None:
        """
        Agenda envio do payload ao WebSocket no event loop correto.

        Lida com o caso de ser chamado de thread síncrona (Celery worker).
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._send(data))
        except RuntimeError:
            # Sem event loop ativo — tenta via run_coroutine_threadsafe
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(self._send(data), loop)
                else:
                    loop.run_until_complete(self._send(data))
            except Exception as exc:
                logger.debug(
                    "[StreamingCallback] Falha ao agendar envio session=%s: %s",
                    self.session_id, exc,
                )

    async def _send(self, data: Dict[str, Any]) -> None:
        """Entrega o frame ao WS (ws_manager) e, em SSE, ao sink registrado."""
        try:
            from app.api.v1.ws_manager import ws_manager
            await ws_manager.send_to_session(self.session_id, data)
        except Exception as exc:
            logger.debug(
                "[StreamingCallback] send error session=%s: %s", self.session_id, exc
            )
        # wire-B (2026-06-06): repassa frames de ATIVIDADE pro transporte SSE via
        # instance-attr (capturado no __init__, no contexto da task).
        try:
            _is_activity = isinstance(data, dict) and data.get("type") in _SSE_FORWARD_TYPES
            if _is_activity:
                import threading as _thr
                logger.info(
                    "[SSE-SINK-DBG] _send type=%s sink_present=%s thread=%s",
                    data.get("type"), self._sse_sink is not None, _thr.current_thread().name,
                )
            if _is_activity and self._sse_sink is not None:
                await self._sse_sink(data)
        except Exception as exc:
            logger.debug("[StreamingCallback] sse sink forward falhou: %s", exc)
