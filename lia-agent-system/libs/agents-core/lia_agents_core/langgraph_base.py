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
        _thread_key = (
            f"{session_id}::{_agent_domain}" if _agent_domain else session_id
        )
        config: Dict[str, Any] = {
            "configurable": {"thread_id": _thread_key},
            "recursion_limit": max_iter * 2 + 1,
        }
        callbacks = [cb for cb in [audit_callback, streaming_callback] if cb is not None]
        if callbacks:
            config["callbacks"] = callbacks

        result = await compiled.ainvoke(initial_state, config=config)
        return result

    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput:
        """Processa a entrada e retorna saída estruturada."""
