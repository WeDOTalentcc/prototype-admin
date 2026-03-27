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
import logging
import time
from typing import Any, Dict, List, Optional, Union
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
        """Envia dados ao WebSocket via ws_manager."""
        try:
            from app.api.v1.ws_manager import ws_manager
            await ws_manager.send_to_session(self.session_id, data)
        except Exception as exc:
            logger.debug(
                "[StreamingCallback] send error session=%s: %s", self.session_id, exc
            )
