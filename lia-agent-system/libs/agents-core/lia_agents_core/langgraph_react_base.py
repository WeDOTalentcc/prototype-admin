"""
LangGraph ReAct Base — base para agentes ReAct nativos LangGraph.

Usa create_react_agent() do LangGraph prebuilt com:
- AuditCallback injetado via config["callbacks"] (automático)
- TimedToolNode para métricas de tool calls
- PostgresSaver/MemorySaver para persistência entre turnos
- Interface compatível com AgentInput/AgentOutput

Migração concluída: react_loop.py legado removido.
Todos os agentes ReAct herdam desta classe sem path alternativo.
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
    - process() → AgentOutput (chama _process_langgraph)

    LIA-C04: PII auto-sanitization em mensagens antes do LLM.
    Subclasses podem setar `_enable_pii_strip = False` apenas em casos excepcionais
    onde PII é necessário por design (ex: serviço de armazenamento de CV).
    """

    # LIA-C04: PII auto-sanitization (True por padrão — desative explicitamente se necessário)
    _enable_pii_strip: bool = True

    # ------------------------------------------------------------------
    # LIA-C04: PII sanitization automática antes de enviar mensagens ao LLM
    # ------------------------------------------------------------------

    async def _sanitize_messages_pii(self, messages: list) -> list:
        """Remove PII de HumanMessage e AIMessage antes de enviar ao LLM.

        SystemMessage não é sanitizado — pode conter placeholders necessários.
        Falha silenciosamente (retorna lista original) em caso de erro.

        LIA-C04 — LGPD Art. 12: minimização de dados pessoais em sistemas de IA.
        EU AI Act Art. 13: transparência sobre dados em sistemas de alto risco.
        """
        if not getattr(self, "_enable_pii_strip", True):
            return messages

        try:
            from app.shared.pii_masking import strip_pii_for_llm_prompt
            _pii_logger = logging.getLogger("app.shared.pii_masking")
            sanitized = []
            for msg in messages:
                if hasattr(msg, "content") and isinstance(msg.content, str):
                    msg_type = msg.__class__.__name__
                    # Apenas HumanMessage e AIMessage — SystemMessage preservado
                    if msg_type in ("HumanMessage", "AIMessage"):
                        stripped = strip_pii_for_llm_prompt(msg.content)
                        if stripped != msg.content:
                            _pii_logger.warning(
                                "[LIA-C04][%s] PII removido de %s domain=%s",
                                self.__class__.__name__,
                                msg_type,
                                self.domain_name,
                            )
                            msg = msg.__class__(content=stripped)
                sanitized.append(msg)
            return sanitized
        except Exception as exc:
            logger.warning(
                "[LIA-C04][%s] PII sanitization falhou (fail-safe): %s",
                self.__class__.__name__, exc,
            )
            return messages

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

        _agent_class = self.__class__.__name__
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _noop():
            yield
        _latency_ctx = _noop()

        # LIA-C04: Sanitização de PII nas mensagens antes de enviar ao LLM
        initial_state["messages"] = await self._sanitize_messages_pii(
            initial_state["messages"]
        )

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
            raise

        _duration = _time.monotonic() - _t0

        output = self._state_to_output(result, input)

        # --- Post-loop learning (EnhancedAgentMixin) ---
        if hasattr(self, "_post_loop_learning"):
            try:
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
        """Retorna o LLM LangChain — tenant-aware via TenantProviderRegistry.

        Choose Your AI: If tenant has a custom provider configured,
        uses that instead of the global default.
        """
        try:
            from lia_config.config import settings
            import os

            # Check tenant config first
            company_id = ""
            try:
                from app.shared.tenant_llm_context import get_current_llm_tenant, get_tenant_llm_config
                company_id = get_current_llm_tenant()
            except ImportError:
                pass

            # Default to Claude (LangChain agents need ChatModel interface)
            provider = "claude"
            model_name = settings.LLM_PRIMARY_MODEL
            api_key = settings.AI_INTEGRATIONS_ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY
            base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL") or getattr(settings, "AI_INTEGRATIONS_ANTHROPIC_BASE_URL", None)

            # Tenant override (if configured)
            if company_id:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Can't await in sync context, use cached config
                        from app.shared.tenant_llm_context import _tenant_configs
                        config = _tenant_configs.get(company_id)
                    else:
                        config = loop.run_until_complete(get_tenant_llm_config(company_id))

                    if config:
                        routing = config.get("routing", {})
                        tenant_provider = routing.get("screening") or config.get("primary_provider")
                        providers = config.get("providers", {})
                        if tenant_provider and tenant_provider in providers:
                            prov_config = providers[tenant_provider]
                            if prov_config.get("api_key"):
                                api_key = prov_config["api_key"]
                            if prov_config.get("model"):
                                model_name = prov_config["model"]
                            provider = tenant_provider
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).debug("[_get_model] Tenant config error: %s", e)

            # Build the appropriate ChatModel
            if provider == "claude":
                from langchain_anthropic import ChatAnthropic
                kwargs = dict(
                    model=model_name,
                    temperature=settings.LLM_AGENT_TEMPERATURE,
                    api_key=api_key,
                    streaming=True,
                )
                if base_url:
                    kwargs["base_url"] = base_url
                return ChatAnthropic(**kwargs)
            elif provider == "openai":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name,
                    temperature=settings.LLM_AGENT_TEMPERATURE,
                    api_key=api_key,
                    streaming=True,
                )
            elif provider == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=settings.LLM_AGENT_TEMPERATURE,
                    google_api_key=api_key,
                    streaming=True,
                )
            else:
                # Fallback to Claude
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=model_name,
                    temperature=settings.LLM_AGENT_TEMPERATURE,
                    api_key=api_key,
                    streaming=True,
                )
        except ImportError as e:
            raise RuntimeError(f"LLM provider not installed: {e}")

    # Class attribute: subclasses set this to their domain-specific instructions
    DOMAIN_INSTRUCTIONS: str = ""

    def _get_system_prompt(self, input: AgentInput) -> str:
        """Compose system prompt via SystemPromptBuilder + domain-specific instructions.

        Subclasses set DOMAIN_INSTRUCTIONS class attribute instead of overriding this method.
        """
        from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

        ctx = input.context or {}
        base = SystemPromptBuilder.build(
            agent_type=self.domain_name,
            tenant_context_snippet=ctx.get("tenant_context_snippet", ""),
            user_name=ctx.get("user_name", ""),
            user_role=ctx.get("user_role", ""),
            conversation_summary=ctx.get("conversation_summary", ""),
            conversation_history=ctx.get("conversation_history"),
            context_page=ctx.get("context_page", "general"),
            intent=ctx.get("intent", ""),
            entities=ctx.get("extracted_params", {}),
        )

        if self.DOMAIN_INSTRUCTIONS:
            return f"{base}\n\n---\n\n{self.DOMAIN_INSTRUCTIONS}"
        return base
    def _extract_text_content(self, content: Any) -> str:
        """Extrai texto de content que pode ser string, lista de blocos ou dict."""
        if isinstance(content, str):
            if content.startswith("[{") and "'text'" in content:
                import ast
                try:
                    parsed = ast.literal_eval(content)
                    if isinstance(parsed, list):
                        return self._extract_text_content(parsed)
                except (ValueError, SyntaxError):
                    pass
            stripped = content.strip()
            raw = stripped
            if stripped.startswith("```json"):
                raw = stripped[len("```json"):].strip()
                if raw.endswith("```"):
                    raw = raw[:-3].strip()
            elif stripped.startswith("```"):
                raw = stripped[3:].strip()
                if raw.endswith("```"):
                    raw = raw[:-3].strip()
            if raw.startswith("{"):
                try:
                    import json as _json
                    parsed_obj = _json.loads(raw)
                    if isinstance(parsed_obj, dict) and "response" in parsed_obj:
                        resp = parsed_obj["response"]
                        if resp:
                            return resp
                        return "Desculpe, não consegui gerar uma resposta. Tente novamente."
                except (ValueError, _json.JSONDecodeError):
                    pass
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and "text" in block:
                    parts.append(block["text"])
                elif hasattr(block, "text"):
                    parts.append(block.text)
            return "".join(parts) if parts else str(content)
        return str(content)

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
            response = self._extract_text_content(last_message.content)
        elif isinstance(last_message, dict):
            response = self._extract_text_content(last_message.get("content", ""))
        else:
            response = str(last_message)

        return AgentOutput(
            message=response,
            confidence=0.85,
            metadata={"source": "langgraph_native", "domain": self.domain_name},
        )
