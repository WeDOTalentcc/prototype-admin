"""
LangGraph ReAct Base — base para agentes ReAct migrados para LangGraph nativo.

Usa create_react_agent() do LangGraph prebuilt com:
- AuditCallback injetado via config["callbacks"] (automático)
- TimedToolNode para métricas de tool calls
- MemorySaver/PostgresSaver para persistência entre turnos
- Interface compatível com AgentInput/AgentOutput

Feature flag USE_LANGGRAPH_NATIVE:
  False → subclasse delega para ReActLoop customizado (react_loop.py)
  True  → usa create_react_agent nativo (este base)

Migração gradual: cada agente verifica a flag em process() e decide
qual implementação usar.
"""
import logging
from typing import Any, Dict, List, Optional

from lia_config.config import settings
from lia_agents_core.agent_interface import AgentInput, AgentOutput
from lia_agents_core.langgraph_base import LangGraphBase
from lia_agents_core.timed_tool_node import TimedToolNode

logger = logging.getLogger(__name__)

try:
    from langgraph.prebuilt import create_react_agent
    from langgraph.graph import MessagesState
    _HAS_LANGGRAPH_PREBUILT = True
except ImportError:
    _HAS_LANGGRAPH_PREBUILT = False
    create_react_agent = None  # type: ignore[assignment]
    MessagesState = None  # type: ignore[assignment]


class LangGraphReActBase(LangGraphBase):
    """
    Base para agentes ReAct nativos LangGraph.

    Subclasses precisam implementar:
    - domain_name (property)
    - available_tools (property)
    - _get_tools() → List[Any] (LangChain tools)
    - _get_model() → Any (LangChain LLM)
    - _get_system_prompt(input) → str
    - _state_to_output(state, input) → AgentOutput
    - process() — decide entre LangGraph nativo ou ReActLoop legado

    Uso padrão em process():
        if settings.USE_LANGGRAPH_NATIVE:
            return await self._process_langgraph(input)
        return await self._process_react_loop(input)  # legado
    """

    def _build_graph(self) -> Any:
        """Constrói o grafo ReAct com create_react_agent."""
        if not _HAS_LANGGRAPH_PREBUILT:
            raise ImportError("LangGraph prebuilt não disponível")

        model = self._get_model()
        tools = self._get_tools()

        graph = create_react_agent(
            model=model,
            tools=tools,
            checkpointer=self._checkpointer,
        )
        return graph

    def _get_compiled_graph(self) -> Optional[Any]:
        """create_react_agent já retorna grafo compilado."""
        if not _HAS_LANGGRAPH_PREBUILT:
            return None
        if self._compiled is None:
            try:
                model = self._get_model()
                tools = self._get_tools()
                # TimedToolNode: timeout 15s padrão + overrides por tool (André P4)
                tool_node = TimedToolNode(
                    tools=tools,
                    domain=self.domain_name,
                    default_timeout_seconds=getattr(self, "_tool_timeout_seconds", 15),
                    tool_timeouts=getattr(self, "_per_tool_timeouts", {}),
                )
                self._compiled = create_react_agent(
                    model=model,
                    tools=tool_node,
                    checkpointer=self._checkpointer,
                )
                logger.info("[%s] create_react_agent compilado com TimedToolNode (LangGraph nativo)",
                            self.__class__.__name__)
            except Exception as exc:
                logger.error("[%s] Falha ao criar react_agent: %s", self.__class__.__name__, exc)
                self._compiled = None
        return self._compiled

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """
        Executa o agente via LangGraph nativo.

        Fluxo:
          1. Injeta contexto de memória do EnhancedAgentMixin (se disponível)
          2. Executa pre-loop learning extractor (se disponível)
          3. Cria AuditCallback e invoca o grafo compilado
          4. Executa post-loop learning (se disponível)
          5. Converte estado final em AgentOutput via _state_to_output()
        """
        from app.shared.compliance.audit_callback import AuditCallback

        audit_callback = AuditCallback(
            user_id=str(input.user_id or "system"),
            company_id=str(input.company_id or ""),
            session_id=str(input.session_id),
            domain=self.domain_name,
            agent_type="langgraph_react",
        )

        # --- Memória de longa duração + guardrails (EnhancedAgentMixin) ---
        extra_context = ""
        if hasattr(self, "_get_memory_context"):
            try:
                extra_context = await self._get_memory_context(  # type: ignore[attr-defined]
                    session_id=input.session_id,
                    company_id=input.company_id,
                )
            except Exception as exc:
                logger.debug("[%s] memory_context indisponível: %s", self.__class__.__name__, exc)

        # --- System prompt enriquecido com memória ---
        system_prompt = self._get_system_prompt(input)
        if extra_context:
            system_prompt = f"{system_prompt}\n\n{extra_context}"

        # --- WorkingMemory: incrementa iteração e sincroniza stage ---
        if hasattr(self, "_memory_service"):
            try:
                await self._memory_service.increment_iteration(  # type: ignore[attr-defined]
                    input.session_id, self.domain_name
                )
            except Exception as exc:
                logger.debug("[%s] working_memory increment falhou: %s", self.__class__.__name__, exc)

        # --- Estado inicial LangGraph ---
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            initial_state = {
                "messages": [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=input.message),
                ]
            }
        except ImportError:
            initial_state = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input.message},
                ]
            }

        # Injeta histórico de conversa (últimas 5 trocas)
        if input.conversation_history:
            try:
                from langchain_core.messages import AIMessage, HumanMessage as HM
                history_msgs = []
                for m in input.conversation_history[-10:]:
                    role = m.get("role", "user")
                    content = m.get("content", "")
                    if role == "user":
                        history_msgs.append(HM(content=content))
                    elif role == "assistant":
                        history_msgs.append(AIMessage(content=content))
                if history_msgs:
                    # Inserir após SystemMessage, antes de HumanMessage atual
                    initial_state["messages"] = (
                        initial_state["messages"][:1]
                        + history_msgs
                        + initial_state["messages"][1:]
                    )
            except Exception as exc:
                logger.debug("[%s] histórico não injetado: %s", self.__class__.__name__, exc)

        # StreamingCallback — envia tokens ao WebSocket em tempo real.
        # Se não houver sessão WS ativa, os envios são silenciosamente descartados.
        streaming_cb = None
        try:
            from lia_agents_core.streaming_callback import StreamingCallback
            streaming_cb = StreamingCallback(
                session_id=str(input.session_id),
                company_id=str(input.company_id or ""),
                user_id=str(input.user_id or ""),
            )
        except Exception as exc:
            logger.debug("[%s] StreamingCallback indisponível: %s", self.__class__.__name__, exc)

        # C4: agent_latency_timer (agent_metrics.py) — wiring para Prometheus
        _agent_class = self.__class__.__name__
        try:
            from app.shared.observability.agent_metrics import agent_latency_timer
            _latency_ctx = agent_latency_timer(agent=_agent_class, domain=self.domain_name)
        except Exception:
            from contextlib import asynccontextmanager
            @asynccontextmanager
            async def _noop():
                yield
            _latency_ctx = _noop()

        import time as _time
        _t0 = _time.monotonic()
        try:
            async with _latency_ctx:
                result = await self._run_graph(
                    initial_state=initial_state,
                    session_id=input.session_id,
                    audit_callback=audit_callback,
                    streaming_callback=streaming_cb,
                )
        except Exception as _graph_exc:
            _duration = _time.monotonic() - _t0
            try:
                from app.observability.metrics import agent_request_duration_seconds, agent_errors_total
                agent_request_duration_seconds.labels(
                    domain=self.domain_name, agent_class=_agent_class
                ).observe(_duration)
                agent_errors_total.labels(
                    domain=self.domain_name, error_type=type(_graph_exc).__name__
                ).inc()
            except Exception:
                pass
            raise

        _duration = _time.monotonic() - _t0
        try:
            from app.observability.metrics import agent_request_duration_seconds
            agent_request_duration_seconds.labels(
                domain=self.domain_name, agent_class=_agent_class
            ).observe(_duration)
        except Exception:
            pass

        output = self._state_to_output(result, input)

        # --- Post-loop learning (EnhancedAgentMixin) ---
        if hasattr(self, "_post_loop_learning"):
            try:
                # Cria ReActState sintético para compatibilidade com learning extractor
                from lia_agents_core.react_loop import ReActState
                synth_state = ReActState(
                    final_response=output.message,
                    error=output.error,
                    tool_calls_made=[
                        {"tool_name": a.params.get("tool", ""), "result": {}, "duration_ms": 0}
                        for a in (output.actions or [])
                        if a.action_type == "call_tool"
                    ],
                )
                await self._post_loop_learning(  # type: ignore[attr-defined]
                    state=synth_state,
                    company_id=input.company_id,
                    session_id=input.session_id,
                    context=input.context,
                )
            except Exception as exc:
                logger.debug("[%s] post_loop_learning falhou: %s", self.__class__.__name__, exc)

        return output

    def _get_tools(self) -> List[Any]:
        """Retorna lista de LangChain tools. Subclasses devem sobrescrever."""
        return []

    def _get_model(self) -> Any:
        """Retorna o LLM LangChain com streaming=True para suporte a StreamingCallback."""
        try:
            from langchain_anthropic import ChatAnthropic
            from lia_config.config import settings
            return ChatAnthropic(
                model=settings.LLM_PRIMARY_MODEL,
                temperature=settings.LLM_AGENT_TEMPERATURE,
                api_key=settings.AI_INTEGRATIONS_ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY,
                streaming=True,  # habilita on_llm_new_token → StreamingCallback → WS
            )
        except ImportError:
            raise RuntimeError("langchain-anthropic não instalado")

    def _get_system_prompt(self, input: AgentInput) -> str:
        """Retorna system prompt. Subclasses devem sobrescrever."""
        return f"Você é LIA, assistente de recrutamento do domínio {self.domain_name}."

    def _state_to_output(self, state: Dict[str, Any], input: AgentInput) -> AgentOutput:
        """
        Converte estado final do grafo em AgentOutput.
        Subclasses podem sobrescrever para extração mais rica.
        """
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        if last_message is None:
            response = "Desculpe, não consegui processar sua solicitação."
        elif hasattr(last_message, "content"):
            response = last_message.content
        elif isinstance(last_message, dict):
            response = last_message.get("content", "")
        else:
            response = str(last_message)

        return AgentOutput(
            message=response,
            confidence=0.85,
            metadata={"source": "langgraph_native", "domain": self.domain_name},
        )
