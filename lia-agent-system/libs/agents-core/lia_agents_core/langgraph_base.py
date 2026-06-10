"""
LangGraph Base — classe base para agentes LangGraph nativos.

Fornece:
- StateGraph com AuditCallback injetado via config["callbacks"]
- Checkpointer (PostgresSaver em produção, MemorySaver em dev) via get_checkpointer()
- Compilação lazy do grafo (singleton por classe)
- Interface compatível com AgentInput/AgentOutput

Uso:
    class MyAgent(LangGraphBase):
        def _build_graph(self) -> StateGraph:
            graph = StateGraph(MyState)
            graph.add_node("agent", self._agent_node)
            graph.add_node("tools", TimedToolNode(self.tools, domain=self.domain_name))
            graph.add_edge(START, "agent")
            graph.add_conditional_edges("agent", self._should_continue)
            return graph
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from lia_config.config import settings
from lia_agents_core.agent_interface import AgentInput, AgentOutput, BaseAgent
from lia_agents_core.checkpointer import get_checkpointer

logger = logging.getLogger(__name__)


def _extract_ai_text(message: Any) -> str:
    """Extract plain text from a LangChain AIMessage (str or content blocks)."""
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts).strip()
    return ""


def _messages_for_continuation(messages, has_prior_state):
    """Turno de continuacao: o checkpointer ja preserva o historico COMPLETO.
    Injetar conversation_history junto com checkpointer causava duplicacao
    exponencial de mensagens - na 4a+ troca o contexto crescia a ponto de o
    Vertex AI retornar BadRequestError 'assistant message prefill'.
    Fix: retornar APENAS a nova HumanMessage para continuacoes; o checkpointer
    gerencia todo o resto. Turno 1 (has_prior_state=False): retorna inalterado.
    Fix P0 2026-06-10 (substitui fix 2026-06-06)."""
    if not has_prior_state:
        return messages
    # Para continuacoes: retornar somente a nova HumanMessage (ultima da lista).
    # O add_messages reducer apenda apenas ela ao estado do checkpointer.
    for m in reversed(messages or []):
        if type(m).__name__ == "HumanMessage":
            return [m]
    # Fallback: retornar ultima mensagem nao-SystemMessage
    filtered = [m for m in (messages or []) if type(m).__name__ != "SystemMessage"]
    return filtered[-1:] if filtered else []


async def _clear_corrupt_checkpoint(thread_key: str) -> None:
    """Deleta checkpoints corrompidos (INVALID_CHAT_HISTORY) do Postgres.
    Usa o pool singleton do checkpointer — fail-open se pool indisponível.
    Chamado automaticamente por _run_graph ao detectar dangling tool_calls.
    """
    try:
        from lia_agents_core.checkpointer import _POOL_SINGLETON, _SAVER_KIND
        if _POOL_SINGLETON is None or _SAVER_KIND != "async_postgres":
            return  # MemorySaver — sem Postgres para limpar
        async with _POOL_SINGLETON.connection() as _conn:
            await _conn.execute(
                "DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_key,)
            )
            await _conn.execute(
                "DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_key,)
            )
            await _conn.execute(
                "DELETE FROM checkpoints WHERE thread_id = %s", (thread_key,)
            )
    except Exception as _exc:
        logger.warning(
            "[clear_corrupt_checkpoint] falhou (fail-open): thread=%s err=%s",
            thread_key, _exc,
        )


try:
    from langgraph.graph import StateGraph, START, END
    _HAS_LANGGRAPH = True
except ImportError:
    _HAS_LANGGRAPH = False
    StateGraph = None  # type: ignore[assignment,misc]
    START = END = None  # type: ignore[assignment]


class LangGraphBase(BaseAgent, ABC):
    """
    Base para agentes LangGraph nativos.

    Subclasses implementam:
    - domain_name (property)
    - available_tools (property)
    - _build_graph() → StateGraph
    - process() → AgentOutput (pode chamar _run_graph())
    """

    _compiled_graph: Optional[Any] = None  # cache por instância

    def __init__(self) -> None:
        self._checkpointer = get_checkpointer()
        self._compiled: Optional[Any] = None

    def _get_compiled_graph(self) -> Optional[Any]:
        """Retorna o grafo compilado (lazy singleton)."""
        if not _HAS_LANGGRAPH:
            return None
        if self._compiled is None:
            try:
                graph = self._build_graph()
                self._compiled = graph.compile(checkpointer=self._checkpointer)
                logger.info("[%s] LangGraph compilado com checkpointer=%s",
                            self.__class__.__name__, type(self._checkpointer).__name__)
            except Exception as exc:
                logger.error("[%s] Falha ao compilar grafo: %s", self.__class__.__name__, exc)
                self._compiled = None
        return self._compiled

    @abstractmethod
    def _build_graph(self) -> Any:
        """Constrói e retorna o StateGraph não compilado."""

    async def _run_graph(
        self,
        initial_state: Dict[str, Any],
        session_id: str,
        audit_callback: Optional[Any] = None,
        streaming_callback: Optional[Any] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executa o grafo compilado com AuditCallback e StreamingCallback injetados.

        Args:
            initial_state: Estado inicial do grafo.
            session_id: ID da sessão (usado como thread_id no checkpointer).
            audit_callback: AuditCallback para rastreamento automático.
            streaming_callback: StreamingCallback para tokens via WebSocket (opcional).
                Quando fornecido, tokens são enviados ao WS em tempo real via
                on_llm_new_token. Requer que o modelo tenha streaming=True.

        Returns:
            Estado final do grafo.
        """
        compiled = self._get_compiled_graph()
        if compiled is None:
            raise RuntimeError(f"[{self.__class__.__name__}] Grafo LangGraph não disponível")

        # P40-RISK-2: explicit recursion_limit as safety net.
        # Default max_iterations=5 → recursion_limit=11 (2×5+1).
        # Subclasses that override _run_graph (Autonomous, CustomAgentRuntime) set their own.
        max_iter = getattr(self, "_max_steps", None) or getattr(self, "max_iterations", 5)
        # Sprint C #41 mitigation: thread_id includes domain to prevent
        # cross-agent state contamination ("Received multiple non-consecutive
        # system messages"). Each (session, domain) pair gets its own
        # checkpointer namespace — preserves conversation memory within a
        # domain while isolating messages between sequential domain hops.
        _agent_domain = (
            getattr(self, "domain_name", None) or self.__class__.__name__
        )
        # Isola estado por conversa (padrao enterprise: ChatGPT/Claude/Copilot).
        # conversation_id None -> fallback legado session::domain (backward compat).
        _thread_key = (
            f"{session_id}::{_agent_domain}::{conversation_id}"
            if _agent_domain and conversation_id
            else f"{session_id}::{_agent_domain}"
            if _agent_domain
            else session_id
        )
        config: Dict[str, Any] = {
            "configurable": {"thread_id": _thread_key},
            "recursion_limit": max_iter * 2 + 1,
        }
        # P0 fix (2026-06-06): em turno de continuacao o checkpointer (thread=
        # session::domain) ja tem o SystemMessage do turno 1. A base re-injeta
        # [System, Human] todo turno; o reducer add_messages APENDA o novo System
        # -> system nao-consecutivos -> "Received multiple non-consecutive system
        # messages" (quebrava todo turno apos o 1o). Remove o System do input novo
        # quando o thread ja tem estado (o checkpointer preserva o original).
        try:
            _prior_state = await compiled.aget_state(config)
            _has_prior = bool(
                getattr(_prior_state, "values", None)
                and _prior_state.values.get("messages")
            )
        except Exception:
            _has_prior = False
        # INVALID_CHAT_HISTORY guard: detecta AIMessages com tool_calls sem
        # ToolMessage correspondente (checkpoint corrompido por crash mid-turn).
        # Limpa o checkpoint e recomeça do zero — fail-open se detecção falhar.
        if _has_prior:
            try:
                _ckpt_msgs = (_prior_state.values or {}).get("messages") or []
                _pending_tc_ids: set = set()
                for _m in _ckpt_msgs:
                    for _tc in (getattr(_m, "tool_calls", None) or []):
                        _tc_id = (
                            _tc.get("id") if isinstance(_tc, dict)
                            else getattr(_tc, "id", None)
                        )
                        if _tc_id:
                            _pending_tc_ids.add(_tc_id)
                    _tcid = getattr(_m, "tool_call_id", None)
                    if _tcid:
                        _pending_tc_ids.discard(_tcid)
                if _pending_tc_ids:
                    logger.warning(
                        "[%s] INVALID_CHAT_HISTORY: %d tool_call(s) sem ToolMessage "
                        "(thread=%s ids=%s) — limpando checkpoint e reiniciando",
                        self.__class__.__name__, len(_pending_tc_ids),
                        _thread_key, list(_pending_tc_ids)[:3],
                    )
                    await _clear_corrupt_checkpoint(_thread_key)
                    _has_prior = False
            except Exception as _guard_exc:
                logger.debug(
                    "[%s] guard INVALID_CHAT_HISTORY (fail-open): %s",
                    self.__class__.__name__, _guard_exc,
                )
        if _has_prior:
            initial_state = {
                **initial_state,
                "messages": _messages_for_continuation(initial_state.get("messages"), True),
            }
        callbacks = [cb for cb in [audit_callback, streaming_callback] if cb is not None]
        if callbacks:
            config["callbacks"] = callbacks

        # Fase 2 (2026-06-03): optional live reasoning via astream. Default OFF —
        # when LIA_WS_ASTREAM is unset/false behavior is identical to the single
        # ainvoke below. When on (and a StreamingCallback is present) we stream
        # state snapshots and emit a reasoning_step for each intermediate
        # AIMessage that carries tool_calls. Any failure falls back to ainvoke,
        # so production behavior is never worse than before.
        import os

        _astream_on = (os.getenv("LIA_WS_ASTREAM", "") or "").strip().lower() in (
            "1", "true", "yes", "on",
        )
        if (
            _astream_on
            and streaming_callback is not None
            and hasattr(compiled, "astream")
        ):
            try:
                return await self._run_graph_streaming(
                    compiled, initial_state, config, streaming_callback
                )
            except Exception as exc:
                logger.warning(
                    "[%s] astream path falhou, fallback ainvoke: %s",
                    self.__class__.__name__, exc,
                )

        result = await compiled.ainvoke(initial_state, config=config)
        return result

    async def _run_graph_streaming(
        self,
        compiled: Any,
        initial_state: Dict[str, Any],
        config: Dict[str, Any],
        streaming_callback: Any,
    ) -> Dict[str, Any]:
        """Run the graph via astream(stream_mode="values"), emitting a
        reasoning_step for each intermediate AIMessage that carries tool_calls.
        Returns the final state (last values chunk), equivalent to ainvoke.
        """
        final_state: Optional[Dict[str, Any]] = None
        emitted: set = set()
        async for chunk in compiled.astream(
            initial_state, config=config, stream_mode="values"
        ):
            final_state = chunk
            if not isinstance(chunk, dict):
                continue
            for m in chunk.get("messages", []) or []:
                is_ai = (
                    getattr(m, "type", "") == "ai"
                    or m.__class__.__name__ == "AIMessage"
                )
                if not is_ai or not getattr(m, "tool_calls", None):
                    continue
                mid = getattr(m, "id", None) or id(m)
                if mid in emitted:
                    continue
                emitted.add(mid)
                text = _extract_ai_text(m)
                if text and hasattr(streaming_callback, "emit_reasoning_step"):
                    streaming_callback.emit_reasoning_step(text)
        if final_state is None:
            return await compiled.ainvoke(initial_state, config=config)
        return final_state

    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput:
        """Processa a entrada e retorna saída estruturada."""
