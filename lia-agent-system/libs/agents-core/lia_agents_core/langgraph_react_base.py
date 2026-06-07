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
from lia_agents_core.timed_tool_node import TimedToolNode, GovernanceToolNode

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
                        # Chat do recrutador: NOME de candidato/vaga é
                        # NECESSÁRIO e AUTORIZADO (mesmo tenant, propósito
                        # legítimo de recrutamento -- LGPD Art. 7º II / 10).
                        # mask_names=False preserva o nome (senão "Felipe
                        # Almeida"/"Diretor Jurídico" viravam "[PERSON REMOVIDO]"
                        # e identificação/busca quebravam -- transcript Paulo
                        # 2026-06-06); CPF/email/telefone seguem mascarados
                        # (layers regex). Consistente com o SSE inbound
                        # (agent_chat_sse: strip_pii_for_llm_prompt(mask_names=False)).
                        stripped = strip_pii_for_llm_prompt(
                            msg.content, mask_names=False
                        )
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

    def _get_tool_contracts(self) -> list:
        """
        Retorna lista de ToolContract para uso com GovernanceToolNode.

        Override em subclasses que declaram ToolContracts:
            def _get_tool_contracts(self):
                from app.domains.X.agents.x_tool_registry import TOOL_CONTRACTS
                return TOOL_CONTRACTS

        Retorna [] por default → usa TimedToolNode (backward compat).
        """
        return []

    def _get_compiled_graph(self) -> Optional[Any]:
        """create_react_agent já retorna grafo compilado."""
        if not _HAS_LANGGRAPH_PREBUILT:
            return None
        if self._compiled is None:
            try:
                model = self._get_model()
                tools = self._get_tools()
                # TimedToolNode: timeout 15s padrão + overrides por tool (André P4)
                _contracts = self._get_tool_contracts()
                _NodeClass = GovernanceToolNode if _contracts else TimedToolNode
                _node_kwargs = dict(
                    tools=tools,
                    domain=self.domain_name,
                    default_timeout_seconds=getattr(self, "_tool_timeout_seconds", 15),
                    tool_timeouts=getattr(self, "_per_tool_timeouts", {}),
                )
                if _contracts:
                    _node_kwargs["tool_contracts"] = _contracts
                tool_node = _NodeClass(**_node_kwargs)
                self._compiled = create_react_agent(
                    model=model,
                    tools=tool_node,
                    checkpointer=self._checkpointer,
                )
                logger.info("[%s] create_react_agent compilado com %s (LangGraph nativo)",
                            self.__class__.__name__, _NodeClass.__name__)
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

        # wire-B canonical (2026-06-06): zera o sink de response_blocks no inicio
        # do turno (drenado abaixo apos _state_to_output). Universal — TODOS os
        # domain agents passam por _process_langgraph. Ver app/shared/rrp_block_sink.
        try:
            from app.shared.rrp_block_sink import reset_sink
            reset_sink()
        except Exception:
            pass
        try:
            from app.shared.hitl_pending_sink import reset_sink as _hitl_reset
            _hitl_reset()
        except Exception:
            pass

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

        # LIA-C05: Automatic FairnessGuard check on agent input
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fairness_guard = FairnessGuard()
            _user_message = input.message if hasattr(input, "message") else str(input)
            _fairness_result = _fairness_guard.check(_user_message)
            if _fairness_result and _fairness_result.is_blocked:
                logger.warning(
                    "[LIA-C05] FairnessGuard blocked agent input: %s (domain=%s)",
                    _fairness_result.category, self.domain_name
                )
                return AgentOutput(
                    message=_fairness_result.educational_message or "Sua solicitacao contem termos que podem gerar vies no processo seletivo. Por favor, reformule.",
                    metadata={"fairness_blocked": True, "category": _fairness_result.category}
                )
        except Exception as e:
            logger.debug("[LIA-C05] FairnessGuard check skipped (fail-open): %s", e)

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

        # wire-B canonical (2026-06-06): drena response_blocks tee'd pelas tools
        # (via tool_definition_to_langchain_tool) pro metadata → SSE/WS serializa
        # → FE renderiza cards/tabelas/funis. Consumo unico no fim do turno.
        try:
            from app.shared.rrp_block_sink import drain_sink
            _rrp_blocks = drain_sink()
            logger.info("[RRP-DRAIN-DBG] %s drained=%d blocks", self.__class__.__name__, len(_rrp_blocks or []))
            if _rrp_blocks:
                output.metadata = {
                    **(output.metadata or {}),
                    "response_blocks": (
                        (output.metadata or {}).get("response_blocks") or []
                    )
                    + _rrp_blocks,
                }
        except Exception as _drain_exc:
            logger.debug("[%s] rrp drain falhou (fail-open): %s", self.__class__.__name__, _drain_exc)

        # HITL surfacing (AUD-4 1b, 2026-06-07): drena needs_confirmation tee'd
        # pela tool gateada -> metadata['hitl_pending'] -> o transporte SSE emite
        # o frame approval_required. Espelha o drain de response_blocks acima.
        try:
            from app.shared.hitl_pending_sink import drain_sink as _hitl_drain
            _hitl_pending = _hitl_drain()
            if _hitl_pending:
                output.metadata = {
                    **(output.metadata or {}),
                    "hitl_pending": _hitl_pending,
                }
        except Exception as _hdrain_exc:
            logger.debug("[%s] hitl drain falhou (fail-open): %s", self.__class__.__name__, _hdrain_exc)

        # --- Post-loop learning (EnhancedAgentMixin) ---
        if hasattr(self, "_post_loop_learning"):
            try:
                from lia_agents_core.tool_adapter import ReActState
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
        """Return the LangChain ChatModel for this agent — tenant-aware.

        Resolution order ("Choose Your AI" — hybrid DB-first → env fallback):

        1. **Per-tenant config** (preferred): if the current request has a
           ``company_id`` (set by ``AuthEnforcementMiddleware`` into
           ``tenant_llm_context``) and that tenant has an active row in
           ``tenant_llm_configs``, use its provider + model + decrypted API key.
           This is what the menu **Configurações > Integrações > LLM** writes.

        2. **Global env vars** (fallback): if the tenant has no entry, fall
           back to the platform-wide settings:
              ``AI_INTEGRATIONS_ANTHROPIC_API_KEY`` (or ``ANTHROPIC_API_KEY``)
              ``AI_INTEGRATIONS_GEMINI_API_KEY``
              ``AI_INTEGRATIONS_OPENAI_API_KEY`` (or ``OPENAI_API_KEY``)
           ``app.main.lifespan`` validates that at least one of these is set
           and refuses to boot in production if all are empty.

        3. **Default model** (last resort): if no api_key is found at all,
           ``ChatAnthropic(api_key=None)`` is constructed and will raise
           ``AuthenticationError`` on first invocation.

        Trade-off / known gap (PR3 Frente F documents this):
          Tenants without their own row share the same global env-var key,
          which means they share quota and rate-limit. This is acceptable for
          free/trial tenants (cost absorbed by the platform) but enterprise
          tenants should configure their own key via the menu to isolate
          quota and protect against noisy-neighbour throttling.
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
            # Use per-agent model config (E5: kanban/policy/automation/communication/ats = Haiku)
            try:
                from app.core.agent_model_config import get_model_for_agent
                model_name = get_model_for_agent(self.domain_name)
            except ImportError:
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
                gemini_kwargs = dict(
                    model=model_name,
                    temperature=settings.LLM_AGENT_TEMPERATURE,
                    google_api_key=api_key,
                    streaming=True,
                )
                # Task #1170 — route through modelfarm proxy when configured
                # (mirror of the Anthropic ``base_url`` injection a few lines
                # above). Without this the wrapper key from
                # ``AI_INTEGRATIONS_GEMINI_API_KEY`` is rejected by Google
                # with 400 API_KEY_INVALID.
                gemini_base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL") or getattr(
                    settings, "AI_INTEGRATIONS_GEMINI_BASE_URL", None
                )
                if gemini_base_url:
                    gemini_kwargs["base_url"] = gemini_base_url
                    # Task #1170 — modelfarm proxy is HTTP REST only;
                    # without ``transport="rest"`` ChatGoogleGenerativeAI
                    # defaults to gRPC and the call hangs against the proxy.
                    gemini_kwargs["transport"] = "rest"
                return ChatGoogleGenerativeAI(**gemini_kwargs)
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

    def _get_runtime_domain_instructions(self, input: AgentInput) -> str:
        """Hook for subclasses to compose DOMAIN_INSTRUCTIONS with runtime context.

        Sprint 2 Phase 4 (ADR-028 — runtime substitution):
        ====================================================================
        Default implementation: returns the static class-attr
        DOMAIN_INSTRUCTIONS (legacy / Phase 2 behavior).

        Subclasses with REASONING_PROMPT placeholders (memory_summary,
        stage_context) should OVERRIDE this method to call
        `PromptComposer.for_domain_runtime(...)` with `input.context`
        values, fixing the empty-placeholder defect (Audit G):

            def _get_runtime_domain_instructions(self, input):
                ctx = input.context or {}
                return PromptComposer.for_domain_runtime(
                    agent_type=self.domain_name,
                    domain_specific=KANBAN_DOMAIN_SPECIFIC,
                    few_shot_examples=KANBAN_FEW_SHOT_EXAMPLES,
                    reasoning_template=KANBAN_REASONING_PROMPT,  # unformatted
                    memory_summary=ctx.get("memory_summary", ""),
                    stage_context=ctx.get("stage_context", ""),
                ).text

        Agents WITHOUT reasoning placeholders (Tipo A: analytics,
        ats_integration, automation, communication, candidate) don't need
        to override — class-attr DOMAIN_INSTRUCTIONS is correct as-is.
        """
        return self.DOMAIN_INSTRUCTIONS

    def _get_system_prompt(self, input: AgentInput) -> str:
        """Compose system prompt via SystemPromptBuilder + domain-specific instructions.

        Subclasses set DOMAIN_INSTRUCTIONS class attribute (static) and
        optionally override `_get_runtime_domain_instructions(input)` for
        runtime placeholder substitution (Sprint 2 Phase 4).
        """
        from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

        ctx = input.context or {}
        base = SystemPromptBuilder.build(
            agent_type=self.domain_name,
            tenant_context_snippet=ctx.get("tenant_context_snippet", ""),
            user_name=ctx.get("user_name", ""),
            user_role=ctx.get("user_role", ""),
            recruiter_context=ctx.get("recruiter_context", ""),
            conversation_summary=ctx.get("conversation_summary", ""),
            conversation_history=ctx.get("conversation_history"),
            context_page=ctx.get("context_page", "general"),
            intent=ctx.get("intent", ""),
            entities=ctx.get("extracted_params", {}),
        )

        # Sprint 2 Phase 4: prefer runtime-substituted instructions over
        # static class-attr (so {memory_summary} / {stage_context}
        # placeholders are filled from input.context per request).
        runtime_domain = self._get_runtime_domain_instructions(input)
        if runtime_domain:
            return f"{base}\n\n---\n\n{runtime_domain}"
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
